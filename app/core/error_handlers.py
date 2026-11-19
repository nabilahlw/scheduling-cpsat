"""Penanganan error global (AppError & error database)."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.core.errors import AppError

log = logging.getLogger("scheduling")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse({"detail": exc.detail, **exc.extra},
                            status_code=exc.status_code, headers=headers)

    @app.exception_handler(SQLAlchemyError)
    async def db_error_handler(request: Request, exc: SQLAlchemyError):
        log.exception("Database error pada %s %s", request.method, request.url.path)
        if isinstance(exc, OperationalError):
            return JSONResponse(
                {"detail": "Database tidak dapat dihubungi. Pastikan MySQL/XAMPP menyala."},
                status_code=503)
        return JSONResponse(
            {"detail": "Terjadi kesalahan database. Data tidak berubah; coba lagi atau "
                       "hubungi admin (detail ada di log server)."}, status_code=500)
