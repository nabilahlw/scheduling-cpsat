"""POST /api/teachers/availability"""
from typing import List

from app.core.container import container
from app.core.dependencies import SCHED
from app.core.router_loader import route
from app.schemas.people import AvailabilityItem


@route(dependencies=[SCHED])
def POST(items: List[AvailabilityItem]):
    saved = container.availability.set_bulk([(it.teacher_name, it.day, it.ranges) for it in items])
    return {"saved": saved}
