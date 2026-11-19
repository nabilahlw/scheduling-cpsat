"""POST /api/auth/login"""
from app.core.container import container
from app.schemas.auth import LoginRequest


def POST(body: LoginRequest):
    return container.auth.login(body.username, body.password)
