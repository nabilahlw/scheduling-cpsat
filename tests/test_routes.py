"""Pastikan file-based routing menghasilkan persis endpoint yang sama dengan main.py lama."""
from app.main import app

EXPECTED = {
    ("GET", "/"),
    ("GET", "/api/db-test"),
    ("POST", "/api/auth/login"), ("GET", "/api/auth/me"), ("POST", "/api/auth/change-password"),
    ("GET", "/api/users"), ("POST", "/api/users"), ("PATCH", "/api/users/{user_id}"),
    ("GET", "/api/teachers"), ("POST", "/api/teachers"),
    ("POST", "/api/teachers/availability"), ("GET", "/api/teachers/available"),
    ("GET", "/api/teachers/availability/{day}"), ("GET", "/api/teachers/remaining/{day}"),
    ("DELETE", "/api/teachers/{teacher_id}/availability"),
    ("GET", "/api/teachers/{teacher_id}"), ("PUT", "/api/teachers/{teacher_id}"),
    ("DELETE", "/api/teachers/{teacher_id}"),
    ("GET", "/api/schools"), ("POST", "/api/schools"),
    ("GET", "/api/schools/{school_id}"), ("PUT", "/api/schools/{school_id}"),
    ("DELETE", "/api/schools/{school_id}"),
    ("POST", "/api/schedule/generate"), ("POST", "/api/schedule/generate-multi"),
    ("POST", "/api/schedule/manual"),
    ("GET", "/api/schedule/{day}"), ("DELETE", "/api/schedule/{day}"),
    ("GET", "/api/sessions/{session_id}"), ("PATCH", "/api/sessions/{session_id}"),
    ("DELETE", "/api/sessions/{session_id}"),
    ("GET", "/api/workload/{day}"),
    ("POST", "/api/invoices"), ("GET", "/api/invoices"),
    ("GET", "/api/invoices/{invoice_id}"), ("PATCH", "/api/invoices/{invoice_id}"),
    ("DELETE", "/api/invoices/{invoice_id}"), ("POST", "/api/invoices/{invoice_id}/status"),
}


def registered():
    out = set()
    for path, ops in app.openapi()["paths"].items():
        for method in ops:
            out.add((method.upper(), path))
    return out


def test_all_endpoints_registered():
    assert registered() == EXPECTED


def test_static_routes_before_dynamic():
    paths = list(app.openapi()["paths"].keys())
    assert paths.index("/api/teachers/available") < paths.index("/api/teachers/{teacher_id}")
    assert paths.index("/api/schedule/generate") < paths.index("/api/schedule/{day}")


def test_protected_endpoint_needs_token():
    from fastapi.testclient import TestClient
    client = TestClient(app)
    r = client.get("/api/teachers")
    assert r.status_code == 401
    assert client.get("/").status_code == 200
