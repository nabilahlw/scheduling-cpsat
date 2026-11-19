"""Jadwal tersimpan: simpan hasil solver, simpan manual, ubah, hapus, baca.

Prinsip:
- assignments      = penugasan tersimpan (sumber kebenaran jadwal).
- teacher_workload = turunan assignments; dibangun ulang tiap ada perubahan.
"""
from app.core.database import Database
from app.core.errors import BadRequest, Conflict, NotFound
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.workload_repository import WorkloadRepository
from app.services.conflict_checker import ConflictChecker
from app.services.teacher_resolver import TeacherResolver


class ScheduleService:
    def __init__(self, db: Database, conflicts: ConflictChecker):
        self.db = db
        self.conflicts = conflicts

    @staticmethod
    def session_key(day, school, class_name, s, e):
        return (day, school.strip().lower(), class_name.strip().lower(), s, e)

    # ---- penugasan tersimpan untuk solver ----

    def existing_assignments(self, ignore_keys=(), replace_days=()):
        """Penugasan tersimpan (semua hari) untuk solver. `ignore_keys` = sesi yang akan ditimpa
        ulang, key = (hari, sekolah.lower, kelas.lower, start, end); `replace_days` = hari yang dikosongkan."""
        ignore_keys, replace_days = set(ignore_keys), set(replace_days)
        with self.db.connect() as conn:
            rows = SessionRepository(conn).assignment_rows()
        out = []
        for r in rows:
            if r["day"] in replace_days:
                continue
            if (r["day"], r["school"].lower(), r["class_name"].lower(), r["start"], r["end"]) in ignore_keys:
                continue
            out.append({"teacher": r["teacher"], "day": r["day"], "school": r["school"],
                        "start": r["start"], "end": r["end"]})
        return out

    # ---- simpan hasil solver ----

    def save_generated(self, items, replace_days=()):
        """Simpan hasil solver (satu transaksi).
        items: [{day, school, class_name, start, end, duration, required, teachers:[nama kanonik]}]
        - Sesi dengan kunci sama (hari+sekolah+kelas+jam) ditimpa.
        - replace_days: hari yang dikosongkan dulu sebelum menyimpan.
        - Sesi lain yang sudah tersimpan TIDAK disentuh."""
        replace_days = set(replace_days)
        created_schools = []
        with self.db.begin() as conn:
            sessions = SessionRepository(conn)
            schools = SchoolRepository(conn)
            resolver = TeacherResolver(TeacherRepository(conn))

            for d in replace_days:
                sessions.delete_sessions(sessions.session_ids_for_day(d))

            days = {it["day"] for it in items}
            if days:
                keys = {self.session_key(it["day"], it["school"], it["class_name"], it["start"], it["end"])
                        for it in items}
                dup = [r[0] for r in sessions.session_keys_in_days(days)
                       if self.session_key(r[1], r[2], r[3], int(r[4]), int(r[5])) in keys]
                sessions.delete_sessions(dup)

            for it in items:
                teachers = resolver.resolve(it["teachers"]) if it["teachers"] else []
                school_id, created = schools.find_or_create(it["school"])
                if created:
                    created_schools.append(it["school"])
                class_id = sessions.class_id(school_id, it["class_name"])
                sessions.insert_session(it["day"], class_id, it["start"], it["end"],
                                        it["duration"], it["required"], [t[0] for t in teachers])
            WorkloadRepository(conn).rebuild(days | replace_days)
        return {"sessions_saved": len(items), "created_schools": sorted(set(created_schools))}

    # ---- simpan manual ----

    def _check_teachers(self, conn, teachers, day, s, e, school, exclude_session_ids=()):
        avail = AvailabilityRepository(conn).by_teacher(day)
        busy = ConflictChecker.busy_by_teacher(SessionRepository(conn).assignment_rows(day),
                                               exclude_session_ids)
        return self.conflicts.problems(teachers, avail, busy, s, e, school)

    @staticmethod
    def _validate_required(required, n_teachers):
        if required is None:
            return n_teachers
        if required < 1:
            raise BadRequest("required_teachers_count minimal 1.")
        if required < n_teachers:
            raise BadRequest(f"required_teachers_count ({required}) lebih kecil dari "
                             f"jumlah guru dipilih ({n_teachers}).")
        return required

    def save_manual(self, day, school, class_name, s, e, teacher_names, required=None):
        """Simpan pilihan admin untuk SATU sesi. Sesi dengan kunci sama ditimpa."""
        if not teacher_names:
            raise BadRequest("Pilih minimal satu guru.")
        with self.db.begin() as conn:
            sessions = SessionRepository(conn)
            schools = SchoolRepository(conn)
            teachers = TeacherResolver(TeacherRepository(conn)).resolve(teacher_names, reject_duplicates=True)
            required = self._validate_required(required, len(teachers))
            school_id, created = schools.find_or_create(school)
            class_id = sessions.class_id(school_id, class_name)
            same = sessions.find_same(class_id, day, s, e)
            school_name = schools.name_of(school_id)
            problems = self._check_teachers(conn, teachers, day, s, e, school_name, same)
            if problems:
                raise Conflict("Sebagian guru tidak bisa ditugaskan: " +
                               "; ".join(f"{p['teacher']} {p['reason']}" for p in problems),
                               extra={"problems": problems})
            sessions.delete_sessions(same)
            sid = sessions.insert_session(day, class_id, s, e, e - s, required, [t[0] for t in teachers])
            WorkloadRepository(conn).rebuild([day])
        return {"session_id": sid, "replaced": bool(same), "school_created": created,
                "teachers": [t[1] for t in teachers]}

    # ---- sesi: baca / ubah / hapus ----

    def get_session(self, session_id):
        with self.db.connect() as conn:
            sessions = SessionRepository(conn)
            r = sessions.get_detail(session_id)
            if not r:
                raise NotFound(f"Sesi dengan id {session_id} tidak ditemukan.")
            teachers = sessions.teacher_names(session_id)
        return {"session_id": r[0], "day": r[1], "school": r[2], "class_name": r[3],
                "time_slot": f"{r[4]} - {r[5]}", "duration_minutes": r[6],
                "required_teachers_count": r[7], "teachers": teachers}

    def update_session(self, session_id, changes):
        """Ubah satu sesi. changes (hanya yang dikirim): day, school, class_name, slot(start,end),
        teachers, required. Ketersediaan & bentrok dicek ulang bila hari/jam/sekolah/guru berubah."""
        with self.db.begin() as conn:
            sessions = SessionRepository(conn)
            schools = SchoolRepository(conn)
            cur = sessions.get_for_update(session_id)
            if not cur:
                raise NotFound(f"Sesi dengan id {session_id} tidak ditemukan.")
            old_day = cur[1]
            day = changes.get("day", cur[1])
            school = changes.get("school", cur[2])
            class_name = changes.get("class_name", cur[3])
            s, e = changes.get("slot", (int(cur[4]), int(cur[5])))

            if "teachers" in changes:
                teachers = TeacherResolver(TeacherRepository(conn)).resolve(
                    changes["teachers"], reject_duplicates=True)
                if not teachers:
                    raise BadRequest("Daftar guru tidak boleh kosong. Untuk menghapus sesi pakai DELETE.")
            else:
                teachers = sessions.assigned_teachers(session_id)

            if "required" in changes:
                required = self._validate_required(changes["required"], len(teachers))
            elif "teachers" in changes:
                required = len(teachers)
            else:
                required = cur[6]

            school_id, _ = schools.find_or_create(school)
            school_name = schools.name_of(school_id)
            class_id = sessions.class_id(school_id, class_name)

            if any(k in changes for k in ("day", "school", "slot", "teachers")):
                problems = self._check_teachers(conn, teachers, day, s, e, school_name, [session_id])
                if problems:
                    raise Conflict("Perubahan ditolak: " +
                                   "; ".join(f"{p['teacher']} {p['reason']}" for p in problems),
                                   extra={"problems": problems})

            sessions.update_session(session_id, class_id, day, s, e, required)
            if "teachers" in changes:
                sessions.replace_assignments(session_id, [tid for tid, _ in teachers])
            WorkloadRepository(conn).rebuild({old_day, day})
        return self.get_session(session_id)

    def delete_session(self, session_id):
        with self.db.begin() as conn:
            sessions = SessionRepository(conn)
            day = sessions.day_of(session_id)
            if day is None:
                raise NotFound(f"Sesi dengan id {session_id} tidak ditemukan.")
            sessions.delete_sessions([session_id])
            WorkloadRepository(conn).rebuild([day])
        return {"deleted": session_id}

    def delete_schedule(self, day, school=None):
        """Hapus seluruh jadwal hari tertentu (opsional: hanya satu sekolah)."""
        with self.db.begin() as conn:
            sessions = SessionRepository(conn)
            ids = sessions.session_ids_for_day_and_school(day, school)
            if not ids:
                raise NotFound("Tidak ada jadwal yang cocok untuk dihapus.")
            sessions.delete_sessions(ids)
            WorkloadRepository(conn).rebuild([day])
        return {"deleted_sessions": len(ids)}

    # ---- baca jadwal & beban ----

    def get_schedule(self, day):
        with self.db.connect() as conn:
            rows = SessionRepository(conn).schedule_rows(day)
        result = {}
        for r in rows:
            if r["id"] not in result:
                result[r["id"]] = {
                    "session_id": r["id"],
                    "school": r["school"],
                    "class_name": r["class_name"],
                    "time_slot": f'{r["start_time"]} - {r["end_time"]}',
                    "required_teachers_count": r["required"],
                    "teachers": [],
                }
            if r["teacher"]:
                result[r["id"]]["teachers"].append(r["teacher"])
        return list(result.values())

    def list_workload(self, day):
        with self.db.connect() as conn:
            return WorkloadRepository(conn).list(day)
