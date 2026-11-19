"""GET /api/db-test"""
from app.core.container import container
from app.core.dependencies import READ
from app.core.router_loader import route


@route(dependencies=[READ])
def GET():
    return {"total_teachers": container.teachers.count_active()}
