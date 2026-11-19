"""Repository dasar: membungkus satu koneksi/transaksi yang dipinjam dari service."""
from sqlalchemy import bindparam, text


class BaseRepository:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        return self.conn.execute(text(sql), params or {})

    @staticmethod
    def in_stmt(sql, ids):
        """Statement dengan klausa `IN :ids`."""
        return text(sql).bindparams(bindparam("ids", expanding=True)), {"ids": list(ids)}
