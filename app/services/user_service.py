"""Manajemen user. Saat ini hanya satu peran: admin."""
import re

from app.core.database import Database
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.security import PasswordHasher, PasswordPolicy
from app.models.entities import User
from app.repositories.user_repository import UserRepository


class UserService:
    ADMIN = "admin"
    ROLES = (ADMIN,)
    _USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")

    def __init__(self, db: Database, hasher: PasswordHasher):
        self.db = db
        self.hasher = hasher

    def create(self, username, password, role):
        if not self._USERNAME_RE.match(username or ""):
            raise BadRequest("Username 3-50 karakter: huruf, angka, titik, garis bawah, atau strip.")
        PasswordPolicy.validate(password)
        self._check_role(role)
        with self.db.begin() as conn:
            users = UserRepository(conn)
            if users.username_exists(username):
                raise Conflict(f"Username '{username}' sudah dipakai.")
            uid = users.insert(username, self.hasher.hash(password), role)
        return User(uid, username, role, True).to_dict()

    def list(self):
        with self.db.connect() as conn:
            return [u.to_dict() for u in UserRepository(conn).list_all()]

    def update(self, user_id, role=None, is_active=None, password=None):
        with self.db.begin() as conn:
            users = UserRepository(conn)
            cur = users.find(user_id)
            if not cur:
                raise NotFound(f"User dengan id {user_id} tidak ditemukan.")
            if role is not None:
                self._check_role(role)
            new_role = cur.role if role is None else role
            new_active = cur.is_active if is_active is None else is_active
            if cur.role == self.ADMIN and cur.is_active and (new_role != self.ADMIN or not new_active):
                if not users.count_other_active_admins(user_id):
                    raise Conflict("Tidak boleh menghapus/menonaktifkan admin aktif terakhir.")
            new_hash = None
            if password is not None:
                PasswordPolicy.validate(password)
                new_hash = self.hasher.hash(password)
            users.update(user_id, new_role, new_active, new_hash)
        return User(user_id, cur.username, new_role, new_active).to_dict()

    def change_password(self, user: dict, old_password, new_password):
        PasswordPolicy.validate(new_password)
        with self.db.begin() as conn:
            users = UserRepository(conn)
            stored = users.password_hash(user["id"])
            if not self.hasher.verify(old_password, stored):
                raise BadRequest("Password lama salah.")
            users.set_password_hash(user["id"], self.hasher.hash(new_password))

    def _check_role(self, role):
        if role not in self.ROLES:
            raise BadRequest(f"Role tidak valid. Pilihan: {', '.join(self.ROLES)}.")
