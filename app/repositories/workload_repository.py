"""teacher_workload = ringkasan turunan dari assignments; selalu dibangun ulang
lewat rebuild() supaya tidak pernah selisih."""
import json
from typing import List

from app.lib.timeutil import TimeUtil
from app.repositories.availability_repository import load_json
from app.repositories.base import BaseRepository
from app.repositories.session_repository import SessionRepository


class WorkloadRepository(BaseRepository):
    def rebuild(self, days) -> None:
        sessions = SessionRepository(self.conn)
        for day in set(days):
            self.execute("DELETE FROM teacher_workload WHERE day = :d", {"d": day})
            per = {}
            for r in sessions.assignment_rows(day):
                per.setdefault((r["teacher_id"], r["teacher"]), []).append((r["start"], r["end"]))
            for (tid, name), ranges in per.items():
                ranges.sort()
                total = sum(b - a for a, b in ranges)
                self.execute("""
                    INSERT INTO teacher_workload
                      (teacher_id, teacher_name, day, records, record_count, total_minutes, total_hours)
                    VALUES (:t, :n, :d, :r, :c, :m, :h)
                """, {"t": tid, "n": name, "d": day,
                      "r": json.dumps([[TimeUtil.hhmm(a), TimeUtil.hhmm(b)] for a, b in ranges]),
                      "c": len(ranges), "m": total, "h": TimeUtil.fmt(total)})

    def list(self, day: str) -> List[dict]:
        rows = self.execute("""
            SELECT teacher_id, teacher_name, day, records, record_count, total_minutes, total_hours
            FROM teacher_workload WHERE day = :day ORDER BY teacher_name
        """, {"day": day}).mappings().all()
        return [{**dict(r), "records": load_json(r["records"])} for r in rows]
