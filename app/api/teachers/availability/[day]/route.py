"""GET /api/teachers/availability/{day}"""
from app.core.container import container
from app.core.dependencies import READ
from app.core.router_loader import route
from app.lib.timeutil import TimeUtil


@route(dependencies=[READ])
def GET(day: str):
    day = TimeUtil.normalize_day(day)
    return {"day": day, "availability": container.availability.list(day)}
