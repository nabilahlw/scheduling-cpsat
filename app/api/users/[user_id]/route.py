"""PATCH /api/users/{user_id}"""
from app.core.container import container
from app.core.dependencies import ADMIN_ONLY
from app.core.router_loader import route
from app.schemas.auth import UserUpdate


@route(dependencies=[ADMIN_ONLY])
def PATCH(user_id: int, body: UserUpdate):
    return container.users.update(user_id, body.role, body.is_active, body.password)
