from typing import List, Optional, Tuple

from app.models.entities import Teacher
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository):
    def list(self, include_deleted=False) -> List[Teacher]:
        sql = "SELECT id, name, deleted_at FROM teachers"
        if not include_deleted:
            sql += " WHERE deleted_at IS NULL"
        return [Teacher.from_row(r) for r in self.execute(sql + " ORDER BY name").all()]

    def count_active(self) -> int:
        return self.execute("SELECT COUNT(*) FROM teachers WHERE deleted_at IS NULL").scalar()

    def find(self, teacher_id: int) -> Optional[Teacher]:
        """Cari berdasarkan id (termasuk yang sudah dihapus)."""
        r = self.execute("SELECT id, name, deleted_at FROM teachers WHERE id = :i",
                         {"i": teacher_id}).first()
        return Teacher.from_row(r) if r else None

    def find_active(self, teacher_id: int) -> Optional[Teacher]:
        r = self.execute("SELECT id, name, deleted_at FROM teachers WHERE id = :i AND deleted_at IS NULL",
                         {"i": teacher_id}).first()
        return Teacher.from_row(r) if r else None

    def find_by_name(self, name: str) -> Optional[Teacher]:
        r = self.execute("SELECT id, name, deleted_at FROM teachers WHERE name = :n", {"n": name}).first()
        return Teacher.from_row(r) if r else None

    def find_other_by_name(self, name: str, exclude_id: int) -> Optional[Teacher]:
        r = self.execute("SELECT id, name, deleted_at FROM teachers WHERE name = :n AND id <> :i",
                         {"n": name, "i": exclude_id}).first()
        return Teacher.from_row(r) if r else None

    def all(self) -> List[Teacher]:
        """Semua guru termasuk yang dihapus (untuk resolusi nama)."""
        return [Teacher.from_row(r) for r in self.execute("SELECT id, name, deleted_at FROM teachers").all()]

    def active_names(self, exclude_id: Optional[int] = None) -> List[str]:
        if exclude_id is None:
            rows = self.execute("SELECT name FROM teachers WHERE deleted_at IS NULL").all()
        else:
            rows = self.execute("SELECT name FROM teachers WHERE deleted_at IS NULL AND id <> :i",
                                {"i": exclude_id}).all()
        return [r[0] for r in rows]

    def active(self) -> List[Tuple[int, str]]:
        return [(r[0], r[1]) for r in self.execute(
            "SELECT id, name FROM teachers WHERE deleted_at IS NULL ORDER BY name").all()]

    def insert(self, name: str) -> int:
        return self.execute("INSERT INTO teachers (name) VALUES (:n)", {"n": name}).lastrowid

    def restore(self, teacher_id: int) -> None:
        self.execute("UPDATE teachers SET deleted_at = NULL WHERE id = :i", {"i": teacher_id})

    def rename(self, teacher_id: int, name: str) -> None:
        self.execute("UPDATE teachers SET name = :n WHERE id = :i", {"n": name, "i": teacher_id})
        # kolom nama yang didenormalisasi ikut diperbarui
        for table in ("teacher_schedules", "teacher_workload"):
            self.execute(f"UPDATE {table} SET teacher_name = :n WHERE teacher_id = :i",
                         {"n": name, "i": teacher_id})

    def soft_delete(self, teacher_id: int) -> None:
        self.execute("UPDATE teachers SET deleted_at = NOW() WHERE id = :i", {"i": teacher_id})
