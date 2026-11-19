"""Konfigurasi aplikasi. Dibaca dari environment / file .env (bukan ditulis di kode)."""
import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret_key: str
    token_expire_minutes: int = 480
    travel_buffer: int = 30          # jeda minimal (menit) saat guru pindah ke SEKOLAH BERBEDA
    max_solve_seconds: int = 10      # batas waktu pencarian solver (detik)
    pbkdf2_iterations: int = 600000  # turunkan hanya untuk tes

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        secret = cls._required("SECRET_KEY")
        if len(secret) < 32:
            raise ConfigError("SECRET_KEY minimal 32 karakter.")
        return cls(
            database_url=cls._required("DATABASE_URL"),
            secret_key=secret,
            token_expire_minutes=int(os.getenv("TOKEN_EXPIRE_MINUTES", "480")),
            travel_buffer=int(os.getenv("TRAVEL_BUFFER", "30")),
            max_solve_seconds=int(os.getenv("MAX_SOLVE_SECONDS", "10")),
            pbkdf2_iterations=int(os.getenv("PBKDF2_ITERATIONS", "600000")),
        )

    @staticmethod
    def _required(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ConfigError(
                f"Environment variable {name} belum diisi. "
                f"Salin .env.example menjadi .env lalu isi nilainya.")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
