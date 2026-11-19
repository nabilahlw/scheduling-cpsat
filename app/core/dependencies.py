"""Dependency FastAPI untuk autentikasi.

Saat ini hanya ada satu peran (admin), jadi semua endpoint cukup login.
Alias READ/SCHED/FIN/ADMIN_ONLY dipertahankan supaya nanti mudah dipecah lagi per peran.
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.container import container
from app.core.errors import Unauthorized

_bearer = HTTPBearer(auto_error=False)


def get_current_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)):
    if cred is None:
        raise Unauthorized("Belum login. Kirim header 'Authorization: Bearer <token>'.")
    return container.auth.user_from_token(cred.credentials)


READ = Depends(get_current_user)
SCHED = FIN = ADMIN_ONLY = READ
