"""Ketersediaan guru: simpan/hapus/baca, cari guru kosong, hitung sisa jam."""
from app.core.database import Database
from app.core.errors import BadRequest, NotFound
from app.lib.names import NameUtil
from app.lib.timeutil import TimeUtil
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.teacher_repository import TeacherRepository
from app.services.conflict_checker import ConflictChecker
from app.services.teacher_resolver import TeacherResolver


class AvailabilityService:
    def __init__(self, db: Database, conflicts: ConflictChecker):
        self.db = db
        self.conflicts = conflicts

    # ---- tulis ----

    @staticmethod
    def _clean_ranges(ranges):
        if not isinstance(ranges, list) or not ranges:
            raise BadRequest("ranges tidak boleh kosong. Untuk menghapus ketersediaan, "
                             "pakai DELETE /api/teachers/{id}/availability.")
        parsed = []
        for r in ranges:
            if not isinstance(r, (list, tuple)) or len(r) != 2:
                raise BadRequest(f"Rentang harus berbentuk [mulai, selesai], mis. [\"07:00\",\"10:00\"]: {r!r}")
            parsed.append(TimeUtil.parse_range(r[0], r[1]))
        return TimeUtil.merge_ranges(parsed)

    def set_bulk(self, items):
        """items: [(nama_guru, hari, ranges)]. Semua divalidasi dulu; tersimpan atomik.
        Rentang yang saling menempel/beririsan digabung."""
        prepared = [(NameUtil.clean(n, "Nama guru", 100), TimeUtil.normalize_day(d), self._clean_ranges(r))
                    for n, d, r in items]
        with self.db.begin() as conn:
            resolved = TeacherResolver(TeacherRepository(conn)).resolve([p[0] for p in prepared])
            by_lower = {name.lower(): (tid, name) for tid, name in resolved}
            repo = AvailabilityRepository(conn)
            for name, day, rng in prepared:
                tid, canon = by_lower[name.lower()]
                repo.upsert(tid, canon, day, rng)
        return len(prepared)

    def delete(self, teacher_id, day=None):
        """Hapus ketersediaan satu guru (satu hari, atau semua hari bila day=None)."""
        with self.db.begin() as conn:
            if not TeacherRepository(conn).find_active(teacher_id):
                raise NotFound(f"Guru dengan id {teacher_id} tidak ditemukan.")
            day = TimeUtil.normalize_day(day) if day is not None else None
            n = AvailabilityRepository(conn).delete(teacher_id, day)
        if not n:
            raise NotFound("Tidak ada data ketersediaan yang cocok untuk dihapus.")
        return {"deleted": n}

    # ---- baca ----

    def by_day(self, days=None):
        """{hari: {nama_guru: [(start_menit, end_menit)]}} - hanya guru aktif."""
        with self.db.connect() as conn:
            return AvailabilityRepository(conn).by_day(days)

    def list(self, day):
        with self.db.connect() as conn:
            return AvailabilityRepository(conn).list(day)

    def _snapshot(self, day):
        with self.db.connect() as conn:
            teachers = TeacherRepository(conn).active()
            avail = AvailabilityRepository(conn).by_teacher(day)
            busy = ConflictChecker.busy_by_teacher(SessionRepository(conn).assignment_rows(day))
        return teachers, avail, busy

    def find_available(self, day, start, end, school=None, buffer=None):
        """Guru yang tersedia di hari + jam tertentu. Tidak menyimpan apa pun."""
        s, e = TimeUtil.parse_range(start, end)
        teachers, avail, busy = self._snapshot(day)

        tersedia, tidak_ada_data, ditolak = [], [], []
        for tid, name in teachers:
            b = self.conflicts.find(busy.get(tid, []), s, e, school, buffer)
            konflik = (f"sudah bertugas {TimeUtil.hhmm(b['start'])}-{TimeUtil.hhmm(b['end'])} "
                       f"di {b['school']}") if b else None
            if tid in avail:
                if not any(a <= s and e <= z for a, z in avail[tid]):
                    ditolak.append({"name": name, "alasan": "di luar jam ketersediaan"})
                elif konflik:
                    ditolak.append({"name": name, "alasan": konflik})
                else:
                    tersedia.append(name)
            elif konflik:
                ditolak.append({"name": name, "alasan": konflik})
            else:
                tidak_ada_data.append(name)
        return {"tersedia": tersedia, "belum_ada_data_ketersediaan": tidak_ada_data,
                "tidak_tersedia": ditolak}

    def remaining_hours(self, day, school=None, buffer=None):
        """Sisa jam kosong tiap guru = jam tersedia - jam sudah ditugaskan.
        Jika `school` diisi, tugas di sekolah LAIN diperlebar `buffer` menit (waktu pindah)."""
        buffer = self.conflicts.travel_buffer if buffer is None else buffer
        teachers, avail, busy = self._snapshot(day)

        result, no_data = [], []
        for tid, name in teachers:
            used = sorted(busy.get(tid, []), key=lambda r: r["start"])
            assigned = [{"school": u["school"], "class_name": u["class_name"],
                         "start": TimeUtil.hhmm(u["start"]), "end": TimeUtil.hhmm(u["end"])} for u in used]
            used_min = sum(u["end"] - u["start"] for u in used)
            if tid not in avail:
                no_data.append({"name": name, "assigned": assigned})
                continue
            blocks = []
            for u in used:
                jeda = buffer if (school and not NameUtil.same(u["school"], school)) else 0
                blocks.append((u["start"] - jeda, u["end"] + jeda))
            free = TimeUtil.subtract(avail[tid], blocks)
            free_min = sum(b - a for a, b in free)
            avail_min = sum(b - a for a, b in avail[tid])
            result.append({
                "teacher_id": tid, "name": name,
                "available": [[TimeUtil.hhmm(a), TimeUtil.hhmm(b)] for a, b in avail[tid]],
                "assigned": assigned,
                "free": [[TimeUtil.hhmm(a), TimeUtil.hhmm(b)] for a, b in free],
                "available_minutes": avail_min, "used_minutes": used_min,
                "free_minutes": free_min, "free_hours": TimeUtil.fmt(free_min),
            })
        return {"teachers": result, "belum_ada_data_ketersediaan": no_data}
