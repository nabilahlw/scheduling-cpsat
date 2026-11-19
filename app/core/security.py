"""Password hashing + token JWT."""
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from functools import cached_property

import jwt

from app.core.errors import BadRequest, Unauthorized


class PasswordPolicy:
    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password) -> None:
        if not isinstance(password, str) or not (cls.MIN_LENGTH <= len(password) <= cls.MAX_LENGTH):
            raise BadRequest("Password harus 8-128 karakter.")


class PasswordHasher:
    ALGORITHM = "pbkdf2_sha256"

    def __init__(self, iterations: int):
        self.iterations = iterations

    def hash(self, password: str, iterations: int = None) -> str:
        iterations = iterations or self.iterations
        salt = secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
        return "{}${}${}${}".format(
            self.ALGORITHM, iterations,
            base64.b64encode(salt).decode(), base64.b64encode(dk).decode())

    def verify(self, password: str, stored: str) -> bool:
        try:
            algo, iters, salt, dk = stored.split("$")
            if algo != self.ALGORITHM:
                return False
            calc = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(iters))
            return hmac.compare_digest(calc, base64.b64decode(dk))
        except (ValueError, TypeError):
            return False

    @cached_property
    def dummy_hash(self) -> str:
        """Dipakai agar waktu login sama walau username tidak ada (anti user-enumeration)."""
        return self.hash("dummy-password-for-timing")


class TokenService:
    ALGORITHM = "HS256"

    def __init__(self, secret_key: str, expire_minutes: int):
        self.secret_key = secret_key
        self.expire_minutes = expire_minutes

    def create(self, user_id: int) -> str:
        exp = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        return jwt.encode({"sub": str(user_id), "exp": exp}, self.secret_key, algorithm=self.ALGORITHM)

    def decode_user_id(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.ALGORITHM])
            return int(payload["sub"])
        except (jwt.PyJWTError, KeyError, ValueError):
            raise Unauthorized("Token tidak valid atau sudah kedaluwarsa.")
