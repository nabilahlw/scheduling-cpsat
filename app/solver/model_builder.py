"""Membangun model CP-SAT: aturan keras + fungsi tujuan.

Aturan keras:
  1. Kuota guru tiap sesi tepat sesuai required_teachers_count.
  2. Anti-bentrok + jeda pindah sekolah - juga terhadap penugasan tersimpan.
  3. Ketersediaan guru per hari (guru tanpa data dianggap bisa kapan saja).
  4. Batas beban harian / mingguan (jika diisi; beban tersimpan ikut dihitung).
Tujuan (urut prioritas, leksikografis):
  a. Minimalkan beban total guru yang paling sibuk (pemerataan).
  b. Minimalkan jumlah pasangan (guru, sekolah) -> kontinuitas guru per sekolah.
  c. Minimalkan "biaya prioritas" (guru berprioritas tinggi lebih dulu dipakai).
"""
from ortools.sat.python import cp_model

from app.lib.timeutil import TimeUtil
from app.solver.context import SchedulingContext


class ModelBuilder:
    PRIORITY_DEFAULT = 3
    PRIORITY_MAX = 5

    def __init__(self, ctx: SchedulingContext):
        self.ctx = ctx

    def build(self, with_assumptions=False, subset=None):
        """Return (model, x, lits). x[(guru, idx_sesi)] = variabel boolean."""
        ctx = self.ctx
        model = cp_model.CpModel()
        x = {}
        for s_idx, cands in enumerate(ctx.allowed):
            for t in cands:
                x[(t, s_idx)] = model.NewBoolVar(f"x_{t}_{s_idx}")

        lits = self._add_quota(model, x, with_assumptions, subset)
        self._add_no_overlap(model, x)
        self._add_load_limits(model, x)
        return model, x, lits

    # ---- aturan keras ----

    def _add_quota(self, model, x, with_assumptions, subset):
        ctx = self.ctx
        n = len(ctx.sessions)
        lits = {}
        for s_idx in (range(n) if subset is None else subset):
            expr = sum(x[(t, s_idx)] for t in ctx.allowed[s_idx])
            if with_assumptions:
                lit = model.NewBoolVar(f"on_{s_idx}")
                model.Add(expr == ctx.sessions[s_idx]["required"]).OnlyEnforceIf(lit)
                lits[s_idx] = lit
            else:
                model.Add(expr == ctx.sessions[s_idx]["required"])
        if with_assumptions:
            model.AddAssumptions(list(lits.values()))
        return lits

    def _add_no_overlap(self, model, x):
        ctx = self.ctx
        n = len(ctx.sessions)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = ctx.sessions[i], ctx.sessions[j]
                if a["day"] != b["day"]:
                    continue
                buf = 0 if a["school"].strip().lower() == b["school"].strip().lower() else ctx.buffer
                if TimeUtil.too_close(a["start"], a["end"], b["start"], b["end"], buf):
                    for t in set(ctx.allowed[i]) & set(ctx.allowed[j]):
                        model.Add(x[(t, i)] + x[(t, j)] <= 1)

    def _add_load_limits(self, model, x):
        ctx = self.ctx
        n = len(ctx.sessions)
        for t in ctx.teachers:
            tl = t.strip().lower()
            if ctx.max_weekly is not None:
                new = sum(x[(t, s)] * (ctx.sessions[s]["end"] - ctx.sessions[s]["start"])
                          for s in range(n) if (t, s) in x)
                model.Add(new + ctx.ex_total.get(tl, 0) <= ctx.max_weekly)
            if ctx.max_daily is not None:
                for day in {s["day"] for s in ctx.sessions}:
                    new = sum(x[(t, s)] * (ctx.sessions[s]["end"] - ctx.sessions[s]["start"])
                              for s in range(n) if (t, s) in x and ctx.sessions[s]["day"] == day)
                    model.Add(new + ctx.ex_day.get((tl, day), 0) <= ctx.max_daily)

    # ---- tujuan ----

    def add_objective(self, model, x):
        """Pasang fungsi tujuan; return variabel max_load."""
        ctx = self.ctx
        n = len(ctx.sessions)
        total_new = sum(s["end"] - s["start"] for s in ctx.sessions)
        ub = total_new + max([ctx.ex_total.get(t.strip().lower(), 0) for t in ctx.teachers] or [0]) + 1
        max_load = model.NewIntVar(0, ub, "max_load")
        for t in ctx.teachers:
            load = sum(x[(t, s)] * (ctx.sessions[s]["end"] - ctx.sessions[s]["start"])
                       for s in range(n) if (t, s) in x)
            model.Add(load + ctx.ex_total.get(t.strip().lower(), 0) <= max_load)

        secondary = []
        bound = 0
        if ctx.continuity:
            pairs = {}
            for (t, s), var in x.items():
                key = (t, ctx.sessions[s]["school"].strip().lower())
                if key not in pairs:
                    pairs[key] = model.NewBoolVar(f"y_{t}_{len(pairs)}")
                model.Add(var <= pairs[key])
            secondary.extend(pairs.values())
            bound += len(pairs)

        for (t, s), var in x.items():
            p = ctx.priorities.get(t.strip().lower(), self.PRIORITY_DEFAULT)
            cost = self.PRIORITY_MAX - p
            if cost:
                secondary.append(cost * var)
                bound += cost

        # bobot beban > batas atas semua suku sekunder -> pemerataan tetap prioritas utama
        model.Minimize((bound + 1) * max_load + sum(secondary))
        return max_load
