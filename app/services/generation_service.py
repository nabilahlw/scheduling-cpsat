# """Generate jadwal: validasi input -> solver CP-SAT -> simpan."""
# import logging

# from sqlalchemy.exc import SQLAlchemyError

# from app.core.errors import BadRequest, ServerError
# from app.lib.names import NameUtil
# from app.lib.timeutil import TimeUtil
# from app.services.availability_service import AvailabilityService
# from app.services.schedule_service import ScheduleService
# from app.services.teacher_service import TeacherService
# from app.solver.scheduler import ScheduleSolver

# log = logging.getLogger("scheduling")


# class GenerationService:
#     def __init__(self, teachers: TeacherService, availability: AvailabilityService,
#                  schedule: ScheduleService, solver: ScheduleSolver):
#         self.teachers = teachers
#         self.availability = availability
#         self.schedule = schedule
#         self.solver = solver

#     def generate(self, days_in, opts):
#         """days_in: [(hari_mentah, [SchoolItem])]; opts: GenerateOptions. Validasi -> solver -> simpan."""
#         warnings = []
#         if not days_in:
#             raise BadRequest("Minimal satu hari.")

#         names = self.teachers.resolve_names(opts.available_teachers)  # 400 + saran bila salah eja
#         if not names:
#             raise BadRequest("available_teachers tidak boleh kosong.")

#         priorities = self._priorities(opts.teacher_priority, names, warnings)
#         days_data, meta, ignore_keys = self._prepare_days(days_in, warnings)

#         max_req = max(m["required"] for m in meta.values())
#         if len(names) < max_req:
#             raise BadRequest(f"available_teachers hanya {len(names)} guru, padahal ada sesi yang butuh "
#                              f"{max_req} guru. Tambah guru atau kurangi kuota.")

#         days = [d["day"] for d in days_data]
#         replace_days = set(days) if opts.replace_day else set()
#         existing = self.schedule.existing_assignments(ignore_keys, replace_days)
#         data = {"teachers": names, "days": days_data,
#                 "availability": self.availability.by_day(days), "existing": existing,
#                 "max_daily_minutes": opts.max_daily_minutes, "max_weekly_minutes": opts.max_weekly_minutes,
#                 "continuity": opts.continuity, "priorities": priorities}

#         result = self.solver.solve(data)
#         result["existing_assignments_considered"] = len(existing)
#         result["warnings"] = warnings
#         result["saved_to_db"] = False
#         if result["status"] != "SUCCESS":
#             return result

#         items = []
#         for a in result["assigned_schedule"]:
#             m = meta[(a["day"], a["school"], a["class_name"], a["time_slot"])]
#             items.append({"day": a["day"], "school": a["school"], "class_name": a["class_name"],
#                           "start": m["start"], "end": m["end"], "duration": m["duration"],
#                           "required": m["required"], "teachers": a["assigned_teachers"]})
#         try:
#             saved = self.schedule.save_generated(items, replace_days)
#         except SQLAlchemyError:
#             log.exception("Gagal menyimpan jadwal hasil generate")
#             raise ServerError("Solver berhasil menemukan jadwal, tetapi gagal menyimpannya ke database "
#                               "(tidak ada data yang berubah). Coba lagi; detail ada di log server.")
#         result["saved_to_db"] = True
#         if saved["created_schools"]:
#             result["warnings"].append("Sekolah baru dibuat otomatis: " + ", ".join(saved["created_schools"]) +
#                                       ". Periksa ejaannya jika tidak sengaja.")
#         return result

#     @staticmethod
#     def _priorities(teacher_priority, names, warnings):
#         priorities = {}
#         lower = {n.lower(): n for n in names}
#         for k, v in teacher_priority.items():
#             if not 1 <= v <= ScheduleSolver.PRIORITY_MAX:
#                 raise BadRequest(f"Prioritas '{k}' harus 1-{ScheduleSolver.PRIORITY_MAX}.")
#             if k.strip().lower() not in lower:
#                 warnings.append(f"Prioritas untuk '{k}' diabaikan: guru ini tidak ada di available_teachers.")
#                 continue
#             priorities[lower[k.strip().lower()]] = v
#         return priorities

#     def _prepare_days(self, days_in, warnings):
#         days_data, meta, seen_days, ignore_keys = [], {}, set(), set()
#         for raw_day, schools in days_in:
#             day = TimeUtil.normalize_day(raw_day)
#             if day in seen_days:
#                 raise BadRequest(f"Hari {day} muncul lebih dari sekali.")
#             seen_days.add(day)
#             if not schools:
#                 raise BadRequest(f"Hari {day} tidak punya sekolah.")
#             school_dicts = []
#             for sc in schools:
#                 sname = NameUtil.clean(sc.school_name, "Nama sekolah", 150)
#                 if not sc.sessions:
#                     raise BadRequest(f"Sekolah '{sname}' tidak punya sesi.")
#                 sess_dicts = []
#                 for se in sc.sessions:
#                     cname = NameUtil.clean(se.class_name, "Nama kelas", 50)
#                     s, e = TimeUtil.parse_slot(se.time_slot)
#                     key = ScheduleService.session_key(day, sname, cname, s, e)
#                     if key in ignore_keys:
#                         raise BadRequest(f"Sesi ganda: {day} {sname} {cname} {se.time_slot}.")
#                     ignore_keys.add(key)
#                     if se.duration_minutes != e - s:
#                         warnings.append(f"{day} {sname} {cname} {se.time_slot}: duration_minutes "
#                                         f"({se.duration_minutes}) != lama slot ({e - s} menit). "
#                                         f"Beban dihitung dari jam slot.")
#                     meta[(day, sname, cname, se.time_slot)] = {
#                         "start": s, "end": e, "duration": se.duration_minutes,
#                         "required": se.required_teachers_count}
#                     sess_dicts.append({"time_slot": se.time_slot, "class_name": cname,
#                                        "required_teachers_count": se.required_teachers_count})
#                 school_dicts.append({"school_name": sname, "sessions": sess_dicts})
#             days_data.append({"day": day, "schools": school_dicts})
#         return days_data, meta, ignore_keys
