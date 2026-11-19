"""POST /api/auth/change-password"""
from app.core.container import container
from app.core.dependencies import READ
from app.schemas.auth import PasswordChange


def POST(body: PasswordChange, user=READ):
    container.users.change_password(user, body.old_password, body.new_password)
    return {"changed": True}
