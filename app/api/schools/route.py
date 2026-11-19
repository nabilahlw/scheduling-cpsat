"""GET, POST /api/schools"""
from app.core.container import container
from app.core.dependencies import READ, SCHED
from app.core.router_loader import route
from app.schemas.people import NameBody


@route(dependencies=[READ])
def GET(include_deleted: bool = False):
    return {"schools": container.schools.list(include_deleted)}


@route(status_code=201, dependencies=[SCHED])
def POST(body: NameBody):
    return container.schools.create(body.name)
