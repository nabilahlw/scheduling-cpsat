"""Kelas, sesi, dan penugasan (assignments = sumber kebenaran jadwal)."""
from typing import List, Optional

from app.lib.names import NameUtil
from app.lib.timeutil import TimeUtil
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository):
    # ---- kelas ----

    def class_id(self, school_id: int, name: str) -> int:
        name = NameUtil.clean(name, "Nama kelas", 50)
        self.execute("INSERT IGNORE INTO classes (school_id, name) VALUES (:s, :n)",
                     {"s": school_id, "n": name})
        return self.execute("SELECT id FROM classes WHERE school_id = :s AND name = :n",
                            {"s": school_id, "n": name}).scalar()

    # ---- baca penugasan ----

    def assignment_rows(self, day=None) -> List[dict]:
        sql = """
            SELECT a.teacher_id, t.name, se.id, se.day, sc.name, c.name,
                   HOUR(se.start_time)*60 + MINUTE(se.start_time),
                   HOUR(se.end_time)*60 + MINUTE(se.end_time)
            FROM assignments a
            JOIN sessions se ON se.id = a.session_id
            JOIN classes c ON c.id = se.class_id
            JOIN schools sc ON sc.id = c.school_id
            JOIN teachers t ON t.id = a.teacher_id
        """
        params = {}
        if day is not None:
            sql += " WHERE se.day = :d"
            params["d"] = day
        return [{"teacher_id": r[0], "teacher": r[1], "session_id": r[2], "day": r[3],
                 "school": r[4], "class_name": r[5], "start": int(r[6]), "end": int(r[7])}
                for r in self.execute(sql, params).all()]

    def teacher_assignment_days(self, teacher_id: int) -> List[str]:
        return [r[0] for r in self.execute(
            "SELECT DISTINCT se.day FROM assignments a JOIN sessions se ON se.id = a.session_id "
            "WHERE a.teacher_id = :i", {"i": teacher_id}).all()]

    def count_teacher_assignments(self, teacher_id: int) -> int:
        return self.execute("SELECT COUNT(*) FROM assignments WHERE teacher_id = :i",
                            {"i": teacher_id}).scalar()

    def delete_teacher_assignments(self, teacher_id: int) -> None:
        self.execute("DELETE FROM assignments WHERE teacher_id = :i", {"i": teacher_id})

    # ---- sesi ----

    def sessions_of_school(self, school_id: int):
        return self.execute(
            "SELECT se.id, se.day FROM sessions se JOIN classes c ON c.id = se.class_id "
            "WHERE c.school_id = :i", {"i": school_id}).all()

    def session_ids_for_day(self, day: str) -> List[int]:
        return [r[0] for r in self.execute("SELECT id FROM sessions WHERE day = :d", {"d": day}).all()]

    def session_ids_for_day_and_school(self, day: str, school_name: Optional[str] = None) -> List[int]:
        sql = ("SELECT se.id FROM sessions se JOIN classes c ON c.id = se.class_id "
               "JOIN schools sc ON sc.id = c.school_id WHERE se.day = :d")
        params = {"d": day}
        if school_name:
            sql += " AND sc.name = :s"
            params["s"] = school_name.strip()
        return [r[0] for r in self.execute(sql, params).all()]

    def session_keys_in_days(self, days):
        """Baris (id, hari, sekolah, kelas, start, end) untuk hari-hari tertentu."""
        stmt, p = self.in_stmt("""
            SELECT se.id, se.day, sc.name, c.name,
                   HOUR(se.start_time)*60 + MINUTE(se.start_time),
                   HOUR(se.end_time)*60 + MINUTE(se.end_time)
            FROM sessions se JOIN classes c ON c.id = se.class_id
            JOIN schools sc ON sc.id = c.school_id WHERE se.day IN :ids""", days)
        return self.conn.execute(stmt, p).all()

    def find_same(self, class_id: int, day: str, s: int, e: int) -> List[int]:
        return [r[0] for r in self.execute(
            "SELECT id FROM sessions WHERE class_id = :c AND day = :d AND start_time = :st AND end_time = :et",
            {"c": class_id, "d": day, "st": TimeUtil.to_sql_time(s), "et": TimeUtil.to_sql_time(e)}).all()]

    def day_of(self, session_id: int) -> Optional[str]:
        r = self.execute("SELECT day FROM sessions WHERE id = :i", {"i": session_id}).first()
        return r[0] if r else None

    def insert_session(self, day, class_id, s, e, duration, required, teacher_ids) -> int:
        sid = self.execute(
            "INSERT INTO sessions (class_id, day, start_time, end_time, duration_minutes, "
            "required_teachers_count) VALUES (:c, :d, :st, :et, :dur, :req)",
            {"c": class_id, "d": day, "st": TimeUtil.to_sql_time(s), "et": TimeUtil.to_sql_time(e),
             "dur": duration, "req": required}).lastrowid
        self.add_assignments(sid, teacher_ids)
        return sid

    def add_assignments(self, session_id: int, teacher_ids) -> None:
        for tid in dict.fromkeys(teacher_ids):
            self.execute("INSERT INTO assignments (session_id, teacher_id) VALUES (:s, :t)",
                         {"s": session_id, "t": tid})

    def replace_assignments(self, session_id: int, teacher_ids) -> None:
        self.execute("DELETE FROM assignments WHERE session_id = :i", {"i": session_id})
        for tid in teacher_ids:
            self.execute("INSERT INTO assignments (session_id, teacher_id) VALUES (:s, :t)",
                         {"s": session_id, "t": tid})

    def delete_sessions(self, ids) -> None:
        ids = list(ids)
        if not ids:
            return
        stmt, p = self.in_stmt("DELETE FROM assignments WHERE session_id IN :ids", ids)
        self.conn.execute(stmt, p)
        stmt, p = self.in_stmt("DELETE FROM sessions WHERE id IN :ids", ids)
        self.conn.execute(stmt, p)

    def get_detail(self, session_id: int):
        return self.execute("""
            SELECT se.id, se.day, sc.name, c.name,
                   TIME_FORMAT(se.start_time, '%H:%i'), TIME_FORMAT(se.end_time, '%H:%i'),
                   se.duration_minutes, se.required_teachers_count
            FROM sessions se JOIN classes c ON c.id = se.class_id JOIN schools sc ON sc.id = c.school_id
            WHERE se.id = :i""", {"i": session_id}).first()

    def teacher_names(self, session_id: int) -> List[str]:
        return [x[0] for x in self.execute(
            "SELECT t.name FROM assignments a JOIN teachers t ON t.id = a.teacher_id "
            "WHERE a.session_id = :i ORDER BY t.name", {"i": session_id}).all()]

    def get_for_update(self, session_id: int):
        """(id, hari, sekolah, kelas, start_menit, end_menit, required)"""
        return self.execute("""
            SELECT se.id, se.day, sc.name, c.name,
                   HOUR(se.start_time)*60 + MINUTE(se.start_time),
                   HOUR(se.end_time)*60 + MINUTE(se.end_time), se.required_teachers_count
            FROM sessions se JOIN classes c ON c.id = se.class_id JOIN schools sc ON sc.id = c.school_id
            WHERE se.id = :i""", {"i": session_id}).first()

    def assigned_teachers(self, session_id: int):
        return [(r[0], r[1]) for r in self.execute(
            "SELECT t.id, t.name FROM assignments a JOIN teachers t ON t.id = a.teacher_id "
            "WHERE a.session_id = :i", {"i": session_id}).all()]

    def update_session(self, session_id, class_id, day, s, e, required) -> None:
        self.execute("""
            UPDATE sessions SET class_id = :c, day = :d, start_time = :st, end_time = :et,
                   duration_minutes = :dur, required_teachers_count = :req WHERE id = :i""",
                     {"c": class_id, "d": day, "st": TimeUtil.to_sql_time(s), "et": TimeUtil.to_sql_time(e),
                      "dur": e - s, "req": required, "i": session_id})

    def schedule_rows(self, day: str):
        return self.execute("""
            SELECT s.id, sc.name AS school, cl.name AS class_name,
                   TIME_FORMAT(s.start_time, '%H:%i') AS start_time,
                   TIME_FORMAT(s.end_time, '%H:%i') AS end_time,
                   s.required_teachers_count AS required, t.name AS teacher
            FROM sessions s
            JOIN classes cl ON s.class_id = cl.id
            JOIN schools sc ON cl.school_id = sc.id
            LEFT JOIN assignments a ON a.session_id = s.id
            LEFT JOIN teachers t ON a.teacher_id = t.id
            WHERE s.day = :day
            ORDER BY s.start_time, sc.name, cl.name, s.id, t.name
        """, {"day": day}).mappings().all()
