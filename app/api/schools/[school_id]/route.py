"""GET, PUT, DELETE /api/schools/{school_id}"""
from app.core.container import container
from app.core.dependencies import ADMIN_ONLY, READ, SCHED
from app.core.router_loader import route
from app.schemas.people import NameBody


@route(dependencies=[READ])
def GET(school_id: int):
    return container.schools.get(school_id)


@route(dependencies=[SCHED])
def PUT(school_id: int, body: NameBody):
    return container.schools.rename(school_id, body.name)


@route(dependencies=[ADMIN_ONLY])
def DELETE(school_id: int, force: bool = False):
    return container.schools.delete(school_id, force)
