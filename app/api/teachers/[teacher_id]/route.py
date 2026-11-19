"""GET, PUT, DELETE /api/teachers/{teacher_id}"""
from app.core.container import container
from app.core.dependencies import ADMIN_ONLY, READ, SCHED
from app.core.router_loader import route
from app.schemas.people import NameBody


@route(dependencies=[READ])
def GET(teacher_id: int):
    return container.teachers.get(teacher_id)


@route(dependencies=[SCHED])
def PUT(teacher_id: int, body: NameBody):
    return container.teachers.rename(teacher_id, body.name, body.confirm_new)


@route(dependencies=[ADMIN_ONLY])
def DELETE(teacher_id: int, force: bool = False):
    """Soft delete. Jika guru punya penugasan: 409, kecuali ?force=true."""
    return container.teachers.delete(teacher_id, force)
