from typing import List, Optional, Tuple

from app.models.entities import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def username_exists(self, username: str) -> bool:
        return bool(self.execute("SELECT 1 FROM users WHERE username = :u", {"u": username}).first())

    def insert(self, username: str, password_hash: str, role: str) -> int:
        return self.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (:u, :p, :r)",
            {"u": username, "p": password_hash, "r": role}).lastrowid

    def list_all(self) -> List[User]:
        rows = self.execute("SELECT id, username, role, is_active FROM users ORDER BY username").all()
        return [User.from_row(r) for r in rows]

    def find(self, user_id: int) -> Optional[User]:
        r = self.execute("SELECT id, username, role, is_active FROM users WHERE id = :i",
                         {"i": user_id}).first()
        return User.from_row(r) if r else None

    def find_with_hash(self, username: str) -> Optional[Tuple[User, str]]:
        r = self.execute(
            "SELECT id, username, role, is_active, password_hash FROM users WHERE username = :u",
            {"u": username}).first()
        return (User.from_row(r), r[4]) if r else None

    def count_other_active_admins(self, user_id: int) -> int:
        return self.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1 AND id <> :i",
            {"i": user_id}).scalar()

    def update(self, user_id: int, role: str, is_active: bool, password_hash: Optional[str] = None) -> None:
        sets, params = ["role = :r", "is_active = :a"], {"r": role, "a": int(is_active), "i": user_id}
        if password_hash is not None:
            sets.append("password_hash = :p")
            params["p"] = password_hash
        self.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = :i", params)

    def password_hash(self, user_id: int) -> str:
        return self.execute("SELECT password_hash FROM users WHERE id = :i", {"i": user_id}).scalar()

    def set_password_hash(self, user_id: int, password_hash: str) -> None:
        self.execute("UPDATE users SET password_hash = :p WHERE id = :i",
                     {"p": password_hash, "i": user_id})
