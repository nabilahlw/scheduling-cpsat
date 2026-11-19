"""GET /api/teachers/available?day&start&end&school"""
from typing import Optional

from app.core.container import container
from app.core.dependencies import READ
from app.core.router_loader import route
from app.lib.timeutil import TimeUtil


@route(dependencies=[READ])
def GET(day: str, start: str, end: str, school: Optional[str] = None):
    """Cari guru yang tersedia di hari + jam tertentu (tidak menyimpan apa pun)."""
    day = TimeUtil.normalize_day(day)
    result = container.availability.find_available(day, start, end, school)
    return {"day": day, "time": f"{start} - {end}", "school": school, **result}
