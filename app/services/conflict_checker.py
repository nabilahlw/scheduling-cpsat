"""Aturan bentrok jadwal + jeda pindah sekolah (logika murni, tanpa database)."""
from app.lib.names import NameUtil
from app.lib.timeutil import TimeUtil


class ConflictChecker:
    def __init__(self, travel_buffer: int):
        self.travel_buffer = travel_buffer

    @staticmethod
    def busy_by_teacher(rows, exclude_session_ids=()):
        busy = {}
        for r in rows:
            if r["session_id"] not in exclude_session_ids:
                busy.setdefault(r["teacher_id"], []).append(r)
        return busy

    def find(self, blocks, s, e, school, buffer=None):
        """Bentrok jika beririsan; pindah sekolah butuh jeda `buffer` (sekolah sama: boleh berdempetan)."""
        buffer = self.travel_buffer if buffer is None else buffer
        for b in blocks:
            jeda = 0 if (school and NameUtil.same(b["school"], school)) else buffer
            if s < b["end"] + jeda and b["start"] < e + jeda:
                return b
        return None

    def problems(self, teachers, avail, busy, s, e, school):
        """Validasi penugasan manual: ketersediaan + bentrok/jeda. Return daftar masalah.
        teachers: [(id, nama)]; avail: {id: [(a,b)]}; busy: {id: [baris penugasan]}"""
        out = []
        for tid, name in teachers:
            if tid in avail and not any(a <= s and e <= z for a, z in avail[tid]):
                rng = ", ".join(f"{TimeUtil.hhmm(a)}-{TimeUtil.hhmm(z)}" for a, z in avail[tid])
                out.append({"teacher": name, "reason": f"di luar jam ketersediaan (tersedia: {rng})"})
                continue
            b = self.find(busy.get(tid, []), s, e, school)
            if b:
                out.append({"teacher": name, "reason":
                            f"bentrok dengan tugas {TimeUtil.hhmm(b['start'])}-{TimeUtil.hhmm(b['end'])} "
                            f"di {b['school']} (pindah sekolah butuh jeda {self.travel_buffer} menit)"})
        return out
