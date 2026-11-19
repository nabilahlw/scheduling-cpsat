"""GET, POST /api/users"""
from app.core.container import container
from app.core.dependencies import ADMIN_ONLY
from app.core.router_loader import route
from app.schemas.auth import UserCreate


@route(dependencies=[ADMIN_ONLY])
def GET():
    return {"users": container.users.list()}


@route(status_code=201, dependencies=[ADMIN_ONLY])
def POST(body: UserCreate):
    return container.users.create(body.username, body.password, body.role)
