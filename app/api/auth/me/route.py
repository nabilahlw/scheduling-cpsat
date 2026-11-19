"""GET /api/auth/me"""
from app.core.dependencies import READ


def GET(user=READ):
    return user
