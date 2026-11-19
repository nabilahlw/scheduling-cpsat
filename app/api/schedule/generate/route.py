"""POST /api/schedule/generate"""
from app.core.container import container
from app.core.dependencies import SCHED
from app.core.router_loader import route
from app.schemas.schedule import ScheduleRequest


@route(dependencies=[SCHED])
def POST(payload: ScheduleRequest):
    """Generate satu hari. Penugasan yang sudah tersimpan di hari yang sama ikut diperhitungkan;
    sesi dengan kunci sama (sekolah+kelas+jam) ditimpa. replace_day=true mengosongkan hari itu dulu."""
    return container.generation.generate([(payload.day, payload.schools)], payload)
