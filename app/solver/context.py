"""Data penjadwalan yang sudah diolah, dipakai bersama model utama & diagnosis."""
from app.lib.timeutil import TimeUtil


class SchedulingContext:
    def __init__(self, data: dict, travel_buffer: int):
        self.teachers = list(dict.fromkeys(data["teachers"]))
        self.buffer = travel_buffer
        self.max_daily = data.get("max_daily_minutes")
        self.max_weekly = data.get("max_weekly_minutes")
        self.continuity = data.get("continuity", True)
        self.priorities = {k.lower(): v for k, v in (data.get("priorities") or {}).items()}

        self.sessions = []
        for d in data["days"]:
            for school in d["schools"]:
                for sess in school["sessions"]:
                    s, e = TimeUtil.parse_slot(sess["time_slot"])
                    self.sessions.append({
                        "day": d["day"], "school": school["school_name"],
                        "class_name": sess["class_name"], "time_slot": sess["time_slot"],
                        "required": sess["required_teachers_count"], "start": s, "end": e})

        availability = data.get("availability", {})
        self.avail = {day: {n.strip().lower(): r for n, r in m.items()}
                      for day, m in availability.items()}

        # penugasan tersimpan per guru
        self.ex_blocks = {}   # (guru_lower, hari) -> [(school, start, end)]
        self.ex_total = {}    # guru_lower -> menit seminggu
        self.ex_day = {}      # (guru_lower, hari) -> menit
        for r in data.get("existing", []):
            t = r["teacher"].strip().lower()
            self.ex_blocks.setdefault((t, r["day"]), []).append((r["school"], r["start"], r["end"]))
            self.ex_total[t] = self.ex_total.get(t, 0) + (r["end"] - r["start"])
            self.ex_day[(t, r["day"])] = self.ex_day.get((t, r["day"]), 0) + (r["end"] - r["start"])

        # kandidat guru per sesi + alasan tersingkir
        self.allowed, self.excluded = [], []
        for sess in self.sessions:
            cands, exc = [], {"ketersediaan": 0, "bentrok_jadwal_tersimpan": 0}
            for t in self.teachers:
                tl = t.strip().lower()
                ranges = self.avail.get(sess["day"], {}).get(tl)
                if ranges is not None and not any(a <= sess["start"] and sess["end"] <= b for a, b in ranges):
                    exc["ketersediaan"] += 1
                    continue
                if self._conflicts_existing(tl, sess):
                    exc["bentrok_jadwal_tersimpan"] += 1
                    continue
                cands.append(t)
            self.allowed.append(cands)
            self.excluded.append(exc)

    def _conflicts_existing(self, tl, sess):
        for school, st, et in self.ex_blocks.get((tl, sess["day"]), []):
            buf = 0 if school.strip().lower() == sess["school"].strip().lower() else self.buffer
            if TimeUtil.too_close(sess["start"], sess["end"], st, et, buf):
                return True
        return False

    def describe(self, idx):
        s = self.sessions[idx]
        return f"{s['day']} {s['time_slot']} - {s['school']} / {s['class_name']} (butuh {s['required']} guru)"
