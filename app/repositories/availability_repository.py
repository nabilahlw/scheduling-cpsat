"""Ketersediaan guru (tabel teacher_schedules = ATURAN jam guru bisa mengajar)."""
import json
from typing import Dict, List, Tuple

from app.lib.timeutil import TimeUtil
from app.repositories.base import BaseRepository


def load_json(value):
    return json.loads(value) if isinstance(value, str) else value


class AvailabilityRepository(BaseRepository):
    def upsert(self, teacher_id, teacher_name, day, ranges: List[Tuple[int, int]]) -> None:
        total = sum(b - a for a, b in ranges)
        records = [[TimeUtil.hhmm(a), TimeUtil.hhmm(b)] for a, b in ranges]
        self.execute("""
            INSERT INTO teacher_schedules
              (teacher_id, teacher_name, day, records, record_count, total_minutes, total_hours)
            VALUES (:t, :n, :d, :r, :c, :m, :h)
            ON DUPLICATE KEY UPDATE
              teacher_name = VALUES(teacher_name), records = VALUES(records),
              record_count = VALUES(record_count), total_minutes = VALUES(total_minutes),
              total_hours = VALUES(total_hours)
        """, {"t": teacher_id, "n": teacher_name, "d": day, "r": json.dumps(records),
              "c": len(records), "m": total, "h": TimeUtil.fmt(total)})

    def delete(self, teacher_id: int, day=None) -> int:
        sql, params = "DELETE FROM teacher_schedules WHERE teacher_id = :t", {"t": teacher_id}
        if day is not None:
            sql += " AND day = :d"
            params["d"] = day
        return self.execute(sql, params).rowcount

    def by_day(self, days=None) -> Dict[str, Dict[str, List[Tuple[int, int]]]]:
        """{hari: {nama_guru: [(start_menit, end_menit)]}} - hanya guru aktif."""
        sql = ("SELECT ts.day, t.name, ts.records FROM teacher_schedules ts "
               "JOIN teachers t ON t.id = ts.teacher_id WHERE t.deleted_at IS NULL")
        if days:
            stmt, params = self.in_stmt(sql.replace("WHERE", "WHERE ts.day IN :ids AND", 1), days)
            rows = self.conn.execute(stmt, params).all()
        else:
            rows = self.execute(sql).all()
        out = {}
        for day, name, rec in rows:
            out.setdefault(day, {})[name] = [(TimeUtil.to_minutes(a), TimeUtil.to_minutes(b))
                                             for a, b in load_json(rec)]
        return out

    def by_teacher(self, day: str) -> Dict[int, List[Tuple[int, int]]]:
        out = {}
        for tid, rec in self.execute(
                "SELECT teacher_id, records FROM teacher_schedules WHERE day = :d", {"d": day}).all():
            out[tid] = [(TimeUtil.to_minutes(a), TimeUtil.to_minutes(b)) for a, b in load_json(rec)]
        return out

    def list(self, day: str) -> List[dict]:
        rows = self.execute("""
            SELECT ts.teacher_id, ts.teacher_name, ts.day, ts.records, ts.record_count, ts.total_hours
            FROM teacher_schedules ts JOIN teachers t ON t.id = ts.teacher_id
            WHERE ts.day = :day AND t.deleted_at IS NULL ORDER BY ts.teacher_name
        """, {"day": day}).mappings().all()
        return [{**dict(r), "records": load_json(r["records"])} for r in rows]
