"""GET /api/teachers/remaining/{day}?school="""
from typing import Optional

from app.core.container import container
from app.core.dependencies import READ
from app.core.router_loader import route
from app.lib.timeutil import TimeUtil


@route(dependencies=[READ])
def GET(day: str, school: Optional[str] = None):
    """Sisa jam kosong per guru = jam tersedia - jam sudah ditugaskan.
    Isi `school` agar tugas di sekolah lain diperlebar dengan jeda pindah."""
    day = TimeUtil.normalize_day(day)
    return {"day": day, "school": school, **container.availability.remaining_hours(day, school)}
