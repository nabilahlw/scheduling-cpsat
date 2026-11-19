"""School Scheduling API (FastAPI + CP-SAT).

Jalankan dari root proyek:  python3 -m uvicorn app.main:app --reload --port 8000
Dokumentasi interaktif: http://127.0.0.1:8000/docs  (klik Authorize, tempel token dari /api/auth/login)

Rute dibaca otomatis dari folder app/ (file-based routing, lihat app/core/router_loader.py).
"""
from pathlib import Path

from fastapi import FastAPI

from app.core.error_handlers import register_error_handlers
from app.core.router_loader import FileRouter


def create_app() -> FastAPI:
    app = FastAPI(title="School Scheduling API with CP-SAT")
    register_error_handlers(app)
    app.include_router(FileRouter(Path(__file__).parent).build())
    return app


app = create_app()
