"""POST /api/schedule/manual"""
from app.core.container import container
from app.core.dependencies import SCHED
from app.core.router_loader import route
from app.lib.timeutil import TimeUtil
from app.schemas.schedule import ManualScheduleRequest


@route(status_code=201, dependencies=[SCHED])
def POST(body: ManualScheduleRequest):
    """Simpan pilihan admin untuk satu sesi (guru dipilih dari GET /api/teachers/available)."""
    day = TimeUtil.normalize_day(body.day)
    s, e = TimeUtil.parse_slot(body.time_slot)
    return container.schedule.save_manual(day, body.school_name, body.class_name, s, e,
                                          body.teachers, body.required_teachers_count)
