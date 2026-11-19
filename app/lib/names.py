"""Pembersihan & pencocokan nama (pagar guru ganda)."""
import difflib
import re

from app.core.errors import BadRequest


class NameUtil:
    HONORIFICS = {"mr", "mrs", "ms", "miss", "mister", "pak", "bu", "ibu", "bapak",
                  "kak", "sir", "mam", "teacher"}

    @staticmethod
    def clean(name, field="Nama", max_len=100):
        """Rapikan spasi; tolak kosong / terlalu panjang."""
        if not isinstance(name, str):
            raise BadRequest(f"{field} wajib diisi.")
        n = " ".join(name.split())
        if not n:
            raise BadRequest(f"{field} tidak boleh kosong.")
        if len(n) > max_len:
            raise BadRequest(f"{field} maksimal {max_len} karakter.")
        return n

    @staticmethod
    def same(a, b):
        return a.strip().lower() == b.strip().lower()

    @classmethod
    def base_name(cls, name):
        parts = re.sub(r"[.\-_,]", " ", name.lower()).split()
        while parts and parts[0] in cls.HONORIFICS:
            parts.pop(0)
        return " ".join(parts)

    @classmethod
    def similar(cls, name, candidates, cutoff=0.8):
        """Nama yang mirip (beda sapaan 'Mr/Ms', atau beda 1-2 huruf), selain yang persis sama."""
        base = cls.base_name(name)
        if not base:
            return []
        found = []
        for c in candidates:
            if cls.same(c, name):
                continue
            cb = cls.base_name(c)
            if cb and (cb == base or difflib.SequenceMatcher(None, base, cb).ratio() >= cutoff):
                found.append(c)
        return found
