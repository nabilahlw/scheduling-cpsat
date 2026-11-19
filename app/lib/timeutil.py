"""Parsing & validasi jam dan hari. Semua error -> BadRequest (HTTP 400)."""
import re

from app.core.errors import BadRequest


class TimeUtil:
    DAYS = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    _DAY_ALIASES = {
        "MONDAY": "SENIN", "TUESDAY": "SELASA", "WEDNESDAY": "RABU",
        "THURSDAY": "KAMIS", "FRIDAY": "JUMAT", "SATURDAY": "SABTU",
        "SUNDAY": "MINGGU", "JUM'AT": "JUMAT", "JUMAT": "JUMAT",
    }
    _TIME_RE = re.compile(r"^(\d{1,2})[:.](\d{2})$")

    @classmethod
    def normalize_day(cls, day):
        """'senin' -> 'SENIN'. Nama Inggris dipetakan ke Indonesia."""
        if not isinstance(day, str) or not day.strip():
            raise BadRequest("Hari wajib diisi.")
        d = day.strip().upper()
        d = cls._DAY_ALIASES.get(d, d)
        if d not in cls.DAYS:
            raise BadRequest(f"Hari '{day}' tidak dikenali. Gunakan: {', '.join(cls.DAYS)}.")
        return d

    @classmethod
    def to_minutes(cls, value):
        """'07.45' / '07:45' / '7:45' -> 465. Menolak format lain & jam tidak valid."""
        if not isinstance(value, str):
            raise BadRequest(f"Format jam tidak valid: {value!r}. Gunakan HH:MM.")
        m = cls._TIME_RE.match(value.strip())
        if not m:
            raise BadRequest(f"Format jam tidak valid: '{value}'. Gunakan HH:MM, contoh 07:45.")
        h, mi = int(m.group(1)), int(m.group(2))
        if h > 23 or mi > 59:
            raise BadRequest(f"Jam tidak valid: '{value}' (jam 00-23, menit 00-59).")
        return h * 60 + mi

    @staticmethod
    def hhmm(minutes):
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    @classmethod
    def to_sql_time(cls, minutes):
        return cls.hhmm(minutes) + ":00"

    @staticmethod
    def fmt(minutes):
        """150 -> '2 jam 30 menit'"""
        return f"{minutes // 60} jam {minutes % 60} menit"

    @classmethod
    def parse_range(cls, a, b):
        s, e = cls.to_minutes(a), cls.to_minutes(b)
        if s >= e:
            raise BadRequest(f"Rentang tidak valid: {a} - {b} (jam mulai harus lebih kecil).")
        return s, e

    @classmethod
    def parse_slot(cls, time_slot):
        """'07.45-09.00' -> (465, 540)."""
        if not isinstance(time_slot, str) or time_slot.count("-") != 1:
            raise BadRequest(f"time_slot tidak valid: {time_slot!r}. Gunakan 'HH:MM-HH:MM'.")
        a, b = time_slot.split("-")
        return cls.parse_range(a, b)

    @classmethod
    def slot_label(cls, start, end):
        return f"{cls.hhmm(start)}-{cls.hhmm(end)}"

    @staticmethod
    def merge_ranges(ranges):
        """Gabungkan rentang yang menempel/beririsan: [(a,b)...] -> terurut & ringkas."""
        out = []
        for a, b in sorted(ranges):
            if out and a <= out[-1][1]:
                out[-1] = (out[-1][0], max(out[-1][1], b))
            else:
                out.append((a, b))
        return out

    @staticmethod
    def subtract(ranges, blocks):
        """Kurangi rentang `ranges` dengan `blocks` -> sisa rentang kosong."""
        result = []
        blocks = sorted(blocks)
        for a, b in ranges:
            cur = a
            for s, e in blocks:
                if e <= cur or s >= b:
                    continue
                if s > cur:
                    result.append((cur, s))
                cur = max(cur, e)
                if cur >= b:
                    break
            if cur < b:
                result.append((cur, b))
        return result

    @staticmethod
    def too_close(a_start, a_end, b_start, b_end, buffer):
        """True bila dua rentang beririsan atau jaraknya kurang dari `buffer` menit."""
        return a_start < b_end + buffer and b_start < a_end + buffer
