from typing import List, Optional, Tuple

from app.core.errors import Conflict
from app.lib.names import NameUtil
from app.models.entities import School
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository):
    def list(self, include_deleted=False) -> List[School]:
        sql = "SELECT id, name, deleted_at FROM schools"
        if not include_deleted:
            sql += " WHERE deleted_at IS NULL"
        return [School.from_row(r) for r in self.execute(sql + " ORDER BY name").all()]

    def find(self, school_id: int) -> Optional[School]:
        r = self.execute("SELECT id, name, deleted_at FROM schools WHERE id = :i", {"i": school_id}).first()
        return School.from_row(r) if r else None

    def is_active(self, school_id: int) -> bool:
        return bool(self.execute("SELECT 1 FROM schools WHERE id = :i AND deleted_at IS NULL",
                                 {"i": school_id}).first())

    def find_by_name(self, name: str) -> Optional[School]:
        r = self.execute("SELECT id, name, deleted_at FROM schools WHERE name = :n", {"n": name}).first()
        return School.from_row(r) if r else None

    def find_other_by_name(self, name: str, exclude_id: int) -> Optional[School]:
        r = self.execute("SELECT id, name, deleted_at FROM schools WHERE name = :n AND id <> :i",
                         {"n": name, "i": exclude_id}).first()
        return School.from_row(r) if r else None

    def name_of(self, school_id: int) -> str:
        return self.execute("SELECT name FROM schools WHERE id = :i", {"i": school_id}).scalar()

    def insert(self, name: str) -> int:
        return self.execute("INSERT INTO schools (name) VALUES (:n)", {"n": name}).lastrowid

    def restore(self, school_id: int) -> None:
        self.execute("UPDATE schools SET deleted_at = NULL WHERE id = :i", {"i": school_id})

    def rename(self, school_id: int, name: str) -> None:
        self.execute("UPDATE schools SET name = :n WHERE id = :i", {"n": name, "i": school_id})

    def soft_delete(self, school_id: int) -> None:
        self.execute("UPDATE schools SET deleted_at = NOW() WHERE id = :i", {"i": school_id})

    def find_or_create(self, name: str) -> Tuple[int, bool]:
        """Cari/buat sekolah. Sekolah yang sudah dihapus -> 409. Return (id, baru_dibuat)."""
        name = NameUtil.clean(name, "Nama sekolah", 150)
        row = self.find_by_name(name)
        if row:
            if row.deleted_at is not None:
                raise Conflict(f"Sekolah '{name}' sudah dihapus. Pulihkan lewat POST /api/schools.")
            return row.id, False
        return self.insert(name), True
