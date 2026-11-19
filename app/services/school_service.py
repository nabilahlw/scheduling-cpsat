"""Sekolah (soft delete)."""
from app.core.database import Database
from app.core.errors import Conflict, NotFound
from app.lib.names import NameUtil
from app.repositories.school_repository import SchoolRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.workload_repository import WorkloadRepository


class SchoolService:
    def __init__(self, db: Database):
        self.db = db

    def list(self, include_deleted=False):
        with self.db.connect() as conn:
            return [s.to_dict() for s in SchoolRepository(conn).list(include_deleted)]

    def get(self, school_id, include_deleted=False):
        with self.db.connect() as conn:
            s = SchoolRepository(conn).find(school_id)
        if not s or (s.deleted_at is not None and not include_deleted):
            raise NotFound(f"Sekolah dengan id {school_id} tidak ditemukan.")
        return s.to_dict()

    def create(self, name):
        name = NameUtil.clean(name, "Nama sekolah", 150)
        with self.db.begin() as conn:
            schools = SchoolRepository(conn)
            row = schools.find_by_name(name)
            if row:
                if row.deleted_at is None:
                    raise Conflict(f"Sekolah '{row.name}' sudah ada (id {row.id}).")
                schools.restore(row.id)
                return {"id": row.id, "name": row.name, "restored": True}
            new_id = schools.insert(name)
        return {"id": new_id, "name": name, "restored": False}

    def rename(self, school_id, name):
        name = NameUtil.clean(name, "Nama sekolah", 150)
        with self.db.begin() as conn:
            schools = SchoolRepository(conn)
            if not schools.is_active(school_id):
                raise NotFound(f"Sekolah dengan id {school_id} tidak ditemukan.")
            other = schools.find_other_by_name(name, school_id)
            if other:
                if other.deleted_at is None:
                    raise Conflict(f"Nama '{name}' sudah dipakai sekolah lain (id {other.id}).")
                raise Conflict(f"Nama '{name}' dipakai sekolah yang sudah dihapus (id {other.id}). "
                               f"Pulihkan lewat POST /api/schools.")
            schools.rename(school_id, name)
        return {"id": school_id, "name": name}

    def delete(self, school_id, force=False):
        """Soft delete. Jika sekolah punya sesi -> 409, kecuali force=True (sesinya dihapus)."""
        with self.db.begin() as conn:
            schools = SchoolRepository(conn)
            sessions = SessionRepository(conn)
            if not schools.is_active(school_id):
                raise NotFound(f"Sekolah dengan id {school_id} tidak ditemukan.")
            rows = sessions.sessions_of_school(school_id)
            if rows and not force:
                raise Conflict(f"Sekolah masih punya {len(rows)} sesi jadwal. "
                               f"Hapus dengan ?force=true untuk ikut menghapus sesinya.",
                               extra={"sessions": len(rows)})
            sessions.delete_sessions([r[0] for r in rows])
            schools.soft_delete(school_id)
            WorkloadRepository(conn).rebuild({r[1] for r in rows})
        return {"deleted": school_id, "sessions_removed": len(rows)}
