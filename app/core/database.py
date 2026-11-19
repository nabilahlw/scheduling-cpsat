"""Pembungkus koneksi database (SQLAlchemy engine)."""
from contextlib import contextmanager

from sqlalchemy import create_engine


class Database:
    def __init__(self, url: str):
        self.engine = create_engine(url, pool_pre_ping=True)

    @contextmanager
    def begin(self):
        """Transaksi: commit bila sukses, rollback bila error."""
        with self.engine.begin() as conn:
            yield conn

    @contextmanager
    def connect(self):
        """Koneksi baca saja (tanpa commit)."""
        with self.engine.connect() as conn:
            yield conn
