"""POST /api/schedule/generate-multi"""
from app.core.container import container
from app.core.dependencies import SCHED
from app.core.router_loader import route
from app.schemas.schedule import MultiDayRequest


@route(dependencies=[SCHED])
def POST(payload: MultiDayRequest):
    """Generate beberapa hari sekaligus, dengan opsi max_daily_minutes / max_weekly_minutes."""
    return container.generation.generate([(d.day, d.schools) for d in payload.days], payload)
