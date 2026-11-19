"""GET /api/workload/{day}"""
from app.core.container import container
from app.core.dependencies import READ
from app.core.router_loader import route
from app.lib.timeutil import TimeUtil


@route(dependencies=[READ])
def GET(day: str):
    day = TimeUtil.normalize_day(day)
    return {"day": day, "workload": container.schedule.list_workload(day)}
