"""Solver penjadwalan guru (Google OR-Tools CP-SAT).

Input `data`:
  teachers     : [nama guru]                      (nama kanonik dari daftar guru resmi)
  days         : [{day, schools:[{school_name, sessions:[{time_slot, class_name,
                                   required_teachers_count, ...}]}]}]
  availability : {hari: {nama_guru: [(start_menit, end_menit)]}}
  existing     : [{teacher, day, school, start, end}]   penugasan yang SUDAH tersimpan
  max_daily_minutes / max_weekly_minutes : batas beban (opsional)
  continuity   : True -> sedikit mungkin guru berbeda per sekolah
  priorities   : {nama_guru: 1..5}  (5 = paling diutamakan, default 3)
"""
from ortools.sat.python import cp_model

from app.solver.context import SchedulingContext
from app.solver.diagnostics import InfeasibilityDiagnoser
from app.solver.model_builder import ModelBuilder


class ScheduleSolver:
    PRIORITY_MAX = ModelBuilder.PRIORITY_MAX

    def __init__(self, travel_buffer: int, max_solve_seconds: int):
        self.travel_buffer = travel_buffer
        self.max_solve_seconds = max_solve_seconds

    def solve(self, data: dict) -> dict:
        ctx = SchedulingContext(data, self.travel_buffer)
        builder = ModelBuilder(ctx)
        diagnoser = InfeasibilityDiagnoser(ctx, builder)

        if not ctx.sessions:
            return {"status": "SUCCESS", "max_load_minutes": 0, "assigned_schedule": []}

        if any(len(c) < s["required"] for c, s in zip(ctx.allowed, ctx.sessions)):
            return self._no_solution(diagnoser.diagnose())

        model, x, _ = builder.build()
        max_load = builder.add_objective(model, x)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_solve_seconds
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            schedule = []
            for s_idx, sess in enumerate(ctx.sessions):
                assigned = [t for t in ctx.allowed[s_idx] if solver.Value(x[(t, s_idx)]) == 1]
                schedule.append({"day": sess["day"], "school": sess["school"],
                                 "time_slot": sess["time_slot"], "class_name": sess["class_name"],
                                 "assigned_teachers": assigned})
            return {"status": "SUCCESS",
                    "solver_status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                    "max_load_minutes": solver.Value(max_load),
                    "assigned_schedule": schedule}

        if status == cp_model.INFEASIBLE:
            return self._no_solution(diagnoser.diagnose())

        return self._no_solution({
            "reason": "TIMEOUT",
            "message": f"Solver tidak menemukan solusi dalam {self.max_solve_seconds} detik. "
                       f"Naikkan MAX_SOLVE_SECONDS atau kurangi ukuran masalah.",
            "sessions": []})

    @staticmethod
    def _no_solution(diagnostics: dict) -> dict:
        return {"status": "NO_SOLUTION_FOUND", "assigned_schedule": [], "diagnostics": diagnostics}
