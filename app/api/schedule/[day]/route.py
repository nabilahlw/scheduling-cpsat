"""GET, DELETE /api/schedule/{day}"""
from typing import Optional

from app.core.container import container
from app.core.dependencies import READ, SCHED
from app.core.router_loader import route
from app.lib.timeutil import TimeUtil


@route(dependencies=[READ])
def GET(day: str):
    day = TimeUtil.normalize_day(day)
    return {"day": day, "schedule": container.schedule.get_schedule(day)}


@route(dependencies=[SCHED])
def DELETE(day: str, school: Optional[str] = None):
    """Hapus seluruh jadwal hari itu (atau hanya satu sekolah bila `school` diisi)."""
    return container.schedule.delete_schedule(TimeUtil.normalize_day(day), school)
