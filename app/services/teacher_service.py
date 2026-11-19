"""Guru: daftar guru resmi + soft delete."""
from app.core.database import Database
from app.core.errors import Conflict, NotFound
from app.lib.names import NameUtil
from app.repositories.session_repository import SessionRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.workload_repository import WorkloadRepository
from app.services.teacher_resolver import TeacherResolver


class TeacherService:
    def __init__(self, db: Database):
        self.db = db

    def count_active(self):
        with self.db.connect() as conn:
            return TeacherRepository(conn).count_active()

    def list(self, include_deleted=False):
        with self.db.connect() as conn:
            return [t.to_dict() for t in TeacherRepository(conn).list(include_deleted)]

    def get(self, teacher_id, include_deleted=False):
        with self.db.connect() as conn:
            t = TeacherRepository(conn).find(teacher_id)
        if not t or (t.deleted_at is not None and not include_deleted):
            raise NotFound(f"Guru dengan id {teacher_id} tidak ditemukan.")
        return t.to_dict()

    def create(self, name, confirm_new=False):
        """Tambah guru. Jika namanya milik guru yang sudah dihapus -> dipulihkan.
        Jika mirip guru lain (mis. 'Mr Prisca' vs 'Ms Prisca') -> 409 kecuali confirm_new=True."""
        name = NameUtil.clean(name, "Nama guru", 100)
        with self.db.begin() as conn:
            teachers = TeacherRepository(conn)
            row = teachers.find_by_name(name)
            if row:
                if row.deleted_at is None:
                    raise Conflict(f"Guru '{row.name}' sudah ada (id {row.id}).")
                teachers.restore(row.id)
                return {"id": row.id, "name": row.name, "restored": True}

            if not confirm_new:
                sim = NameUtil.similar(name, teachers.active_names())
                if sim:
                    raise Conflict(
                        f"Nama '{name}' mirip dengan guru yang sudah ada: {', '.join(sim)}. "
                        f"Jika benar guru baru, kirim ulang dengan confirm_new=true.",
                        extra={"similar": sim})
            new_id = teachers.insert(name)
        return {"id": new_id, "name": name, "restored": False}

    def rename(self, teacher_id, name, confirm_new=False):
        name = NameUtil.clean(name, "Nama guru", 100)
        with self.db.begin() as conn:
            teachers = TeacherRepository(conn)
            if not teachers.find_active(teacher_id):
                raise NotFound(f"Guru dengan id {teacher_id} tidak ditemukan.")
            other = teachers.find_other_by_name(name, teacher_id)
            if other:
                if other.deleted_at is None:
                    raise Conflict(f"Nama '{name}' sudah dipakai guru lain (id {other.id}).")
                raise Conflict(f"Nama '{name}' dipakai guru yang sudah dihapus (id {other.id}). "
                               f"Pulihkan lewat POST /api/teachers.")
            if not confirm_new:
                sim = NameUtil.similar(name, teachers.active_names(exclude_id=teacher_id))
                if sim:
                    raise Conflict(f"Nama '{name}' mirip dengan guru lain: {', '.join(sim)}. "
                                   f"Kirim ulang dengan confirm_new=true jika memang berbeda.",
                                   extra={"similar": sim})
            teachers.rename(teacher_id, name)
        return {"id": teacher_id, "name": name}

    def delete(self, teacher_id, force=False):
        """Soft delete. Jika guru punya penugasan -> 409, kecuali force=True (penugasannya dihapus)."""
        with self.db.begin() as conn:
            teachers = TeacherRepository(conn)
            sessions = SessionRepository(conn)
            if not teachers.find_active(teacher_id):
                raise NotFound(f"Guru dengan id {teacher_id} tidak ditemukan.")
            days = sessions.teacher_assignment_days(teacher_id)
            n = sessions.count_teacher_assignments(teacher_id)
            if n and not force:
                raise Conflict(f"Guru masih punya {n} penugasan (hari: {', '.join(sorted(days))}). "
                               f"Hapus dengan ?force=true untuk ikut menghapus penugasannya.",
                               extra={"assignments": n})
            sessions.delete_teacher_assignments(teacher_id)
            teachers.soft_delete(teacher_id)
            WorkloadRepository(conn).rebuild(days)
        return {"deleted": teacher_id, "assignments_removed": n}

    def resolve_names(self, names):
        """Untuk dipakai sebelum solver: kembalikan nama kanonik (urutan terjaga)."""
        with self.db.connect() as conn:
            return [n for _, n in TeacherResolver(TeacherRepository(conn)).resolve(names)]
