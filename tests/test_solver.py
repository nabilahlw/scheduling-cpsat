from app.solver.scheduler import ScheduleSolver


def solver():
    return ScheduleSolver(travel_buffer=30, max_solve_seconds=5)


def session(slot, cls="1A", req=1):
    return {"time_slot": slot, "class_name": cls, "required_teachers_count": req}


def data(days, teachers, **extra):
    return {"teachers": teachers, "days": days, **extra}


def day(name, *schools):
    return {"day": name, "schools": [{"school_name": n, "sessions": s} for n, s in schools]}


def test_basic_success_and_quota():
    d = data([day("SENIN", ("SD A", [session("07:00-08:00", req=2)]))], ["Ani", "Budi", "Citra"])
    r = solver().solve(d)
    assert r["status"] == "SUCCESS"
    assert len(r["assigned_schedule"][0]["assigned_teachers"]) == 2


def test_balances_load():
    d = data([day("SENIN", ("SD A", [session("07:00-08:00", "1A"), session("09:00-10:00", "1B")]))],
             ["Ani", "Budi"], continuity=False)
    r = solver().solve(d)
    teachers = [s["assigned_teachers"][0] for s in r["assigned_schedule"]]
    assert sorted(teachers) == ["Ani", "Budi"]
    assert r["max_load_minutes"] == 60


def test_travel_buffer_between_schools_forces_other_teacher():
    # jarak antar sesi 10 menit, sekolah berbeda (butuh 30) -> tidak boleh guru yang sama
    d = data([day("SENIN",
                  ("SD A", [session("07:00-08:00")]),
                  ("SD B", [session("08:10-09:00")]))], ["Ani", "Budi"])
    r = solver().solve(d)
    a, b = (s["assigned_teachers"][0] for s in r["assigned_schedule"])
    assert a != b


def test_same_school_back_to_back_allowed_for_continuity():
    d = data([day("SENIN", ("SD A", [session("07:00-08:00", "1A"), session("08:00-09:00", "1B")]))],
             ["Ani", "Budi"], continuity=True, max_daily_minutes=120)
    r = solver().solve(d)
    assert r["status"] == "SUCCESS"


def test_availability_excludes_teacher():
    d = data([day("SENIN", ("SD A", [session("07:00-08:00")]))], ["Ani", "Budi"],
             availability={"SENIN": {"Ani": [(600, 700)]}})
    r = solver().solve(d)
    assert r["assigned_schedule"][0]["assigned_teachers"] == ["Budi"]


def test_existing_assignment_blocks_teacher():
    d = data([day("SENIN", ("SD A", [session("07:00-08:00")]))], ["Ani", "Budi"],
             existing=[{"teacher": "Budi", "day": "SENIN", "school": "SD A", "start": 420, "end": 480}])
    r = solver().solve(d)
    assert r["assigned_schedule"][0]["assigned_teachers"] == ["Ani"]


def test_too_few_candidates_diagnostics():
    d = data([day("SENIN", ("SD A", [session("07:00-08:00", req=2)]))], ["Ani", "Budi"],
             availability={"SENIN": {"Ani": [(0, 60)]}})
    r = solver().solve(d)
    assert r["status"] == "NO_SOLUTION_FOUND"
    assert r["diagnostics"]["reason"] == "TOO_FEW_CANDIDATES"


def test_conflicting_sessions_core():
    d = data([day("SENIN", ("SD A", [session("07:00-08:00", "1A"), session("07:30-08:30", "1B")]))],
             ["Ani"])
    r = solver().solve(d)
    assert r["status"] == "NO_SOLUTION_FOUND"
    assert r["diagnostics"]["reason"] == "CONFLICTING_SESSIONS"
    assert len(r["diagnostics"]["sessions"]) == 2


def test_weekly_limit_infeasible():
    d = data([day("SENIN", ("SD A", [session("07:00-09:00")]))], ["Ani"], max_weekly_minutes=60)
    r = solver().solve(d)
    assert r["status"] == "NO_SOLUTION_FOUND"


def test_priority_prefers_high_priority_when_load_equal():
    d = data([day("SENIN", ("SD A", [session("07:00-08:00")]))], ["Ani", "Budi"],
             priorities={"Budi": 5, "Ani": 1})
    r = solver().solve(d)
    assert r["assigned_schedule"][0]["assigned_teachers"] == ["Budi"]


def test_empty_input():
    assert solver().solve(data([], ["Ani"]))["status"] == "SUCCESS"
