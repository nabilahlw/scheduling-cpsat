"""Login & verifikasi token."""
from app.core.database import Database
from app.core.errors import Forbidden, Unauthorized
from app.core.security import PasswordHasher, TokenService
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Database, hasher: PasswordHasher, tokens: TokenService):
        self.db = db
        self.hasher = hasher
        self.tokens = tokens

    def login(self, username, password) -> dict:
        user = self.authenticate(username, password)
        return {"access_token": self.tokens.create(user["id"]), "token_type": "bearer", "user": user}

    def authenticate(self, username, password) -> dict:
        with self.db.connect() as conn:
            found = UserRepository(conn).find_with_hash(username)
        # verifikasi tetap dijalankan walau user tak ada -> waktu respons sama
        ok = self.hasher.verify(password, found[1] if found else self.hasher.dummy_hash)
        if not found or not ok:
            raise Unauthorized("Username atau password salah.")
        user = found[0]
        if not user.is_active:
            raise Forbidden("Akun dinonaktifkan.")
        return user.to_dict()

    def user_from_token(self, token: str) -> dict:
        uid = self.tokens.decode_user_id(token)
        with self.db.connect() as conn:
            user = UserRepository(conn).find(uid)
        if not user or not user.is_active:
            raise Unauthorized("Akun tidak ditemukan atau dinonaktifkan.")
        return user.to_dict()
