"""GET, PATCH, DELETE /api/sessions/{session_id}"""
from app.core.container import container
from app.core.dependencies import READ, SCHED
from app.core.errors import BadRequest
from app.core.router_loader import route
from app.lib.names import NameUtil
from app.lib.timeutil import TimeUtil
from app.schemas.base import dump
from app.schemas.schedule import SessionUpdate


@route(dependencies=[READ])
def GET(session_id: int):
    return container.schedule.get_session(session_id)


@route(dependencies=[SCHED])
def PATCH(session_id: int, body: SessionUpdate):
    raw = {k: v for k, v in dump(body, exclude_unset=True).items() if v is not None}
    if not raw:
        raise BadRequest("Tidak ada field yang diubah.")
    changes = {}
    if "day" in raw:
        changes["day"] = TimeUtil.normalize_day(raw["day"])
    if "school_name" in raw:
        changes["school"] = NameUtil.clean(raw["school_name"], "Nama sekolah", 150)
    if "class_name" in raw:
        changes["class_name"] = NameUtil.clean(raw["class_name"], "Nama kelas", 50)
    if "time_slot" in raw:
        changes["slot"] = TimeUtil.parse_slot(raw["time_slot"])
    if "teachers" in raw:
        changes["teachers"] = raw["teachers"]
    if "required_teachers_count" in raw:
        changes["required"] = raw["required_teachers_count"]
    return container.schedule.update_session(session_id, changes)


@route(dependencies=[SCHED])
def DELETE(session_id: int):
    return container.schedule.delete_session(session_id)
