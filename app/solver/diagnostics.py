"""Diagnosis bila tidak ada solusi (unsat core)."""
from ortools.sat.python import cp_model

from app.solver.context import SchedulingContext
from app.solver.model_builder import ModelBuilder


class InfeasibilityDiagnoser:
    MAX_CORE_FOR_TRIMMING = 25

    def __init__(self, ctx: SchedulingContext, builder: ModelBuilder):
        self.ctx = ctx
        self.builder = builder

    def diagnose(self) -> dict:
        ctx = self.ctx
        n = len(ctx.sessions)
        short = [i for i in range(n) if len(ctx.allowed[i]) < ctx.sessions[i]["required"]]

        if short:
            return {
                "reason": "TOO_FEW_CANDIDATES",
                "message": "Ada sesi yang kekurangan guru kandidat (setelah ketersediaan dan jadwal "
                           "tersimpan diperhitungkan): " + "; ".join(
                               ctx.describe(i) + f" -> hanya {len(ctx.allowed[i])} guru yang memenuhi"
                               for i in short),
                "sessions": [self._entry(i) for i in short]}

        core = self._find_core()
        if core:
            limits = ctx.max_daily is not None or ctx.max_weekly is not None
            if len(core) == 1:
                head = "Sesi berikut tidak bisa dipenuhi: " + ctx.describe(core[0]) + ". "
                hint = ("Guru kandidat yang ada terhalang batas beban harian/mingguan. Naikkan batas, "
                        "tambah guru, atau kurangi kuota." if limits else
                        "Tambah guru atau kurangi kuota.")
            else:
                head = ("Sesi-sesi berikut tidak bisa dipenuhi bersamaan: " +
                        "; ".join(ctx.describe(i) for i in core) + ". ")
                hint = ("Sesi-sesi ini berebut guru yang sama (jamnya berimpitan atau jeda pindah "
                        f"sekolah {ctx.buffer} menit tidak cukup)")
                if limits:
                    hint += ", dan batas beban harian/mingguan ikut membatasi"
                hint += ". Tambah guru, geser jam, atau kurangi kuota salah satunya."
            return {"reason": "CONFLICTING_SESSIONS", "message": head + hint,
                    "sessions": [self._entry(i) for i in core]}

        return {"reason": "UNKNOWN",
                "message": "Tidak ada solusi, tetapi penyebab spesifik tidak bisa ditentukan. "
                           "Periksa kuota, jumlah guru, ketersediaan, dan batas beban.",
                "sessions": []}

    def _entry(self, i) -> dict:
        s = self.ctx.sessions[i]
        return {"day": s["day"], "school": s["school"], "class_name": s["class_name"],
                "time_slot": s["time_slot"], "required_teachers": s["required"],
                "candidate_teachers": len(self.ctx.allowed[i]),
                "excluded_by_availability": self.ctx.excluded[i]["ketersediaan"],
                "excluded_by_saved_schedule": self.ctx.excluded[i]["bentrok_jadwal_tersimpan"]}

    def _find_core(self):
        """Unsat core via assumptions, lalu dipangkas (deletion filter) bila kecil."""
        model, _, lits = self.builder.build(with_assumptions=True)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 5
        if solver.Solve(model) != cp_model.INFEASIBLE:
            return []
        by_lit = {lit.Index(): idx for idx, lit in lits.items()}
        core = sorted(by_lit[i] for i in solver.SufficientAssumptionsForInfeasibility() if i in by_lit)
        if not core or len(core) > self.MAX_CORE_FOR_TRIMMING:
            return core

        for idx in list(core):
            trial = [c for c in core if c != idx]
            if not trial:
                break
            m, _, _ = self.builder.build(with_assumptions=False, subset=trial)
            s2 = cp_model.CpSolver()
            s2.parameters.max_time_in_seconds = 2
            if s2.Solve(m) == cp_model.INFEASIBLE:
                core = trial
        return core
