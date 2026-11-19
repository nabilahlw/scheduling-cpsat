"""DELETE /api/teachers/{teacher_id}/availability"""
from typing import Optional

from app.core.container import container
from app.core.dependencies import SCHED
from app.core.router_loader import route


@route(dependencies=[SCHED])
def DELETE(teacher_id: int, day: Optional[str] = None):
    """Hapus ketersediaan satu guru (satu hari, atau semua hari bila `day` kosong).
    PERHATIAN: guru tanpa data ketersediaan dianggap bisa kapan saja."""
    result = container.availability.delete(teacher_id, day)
    return {**result, "note": "Guru tanpa data ketersediaan dianggap bisa mengajar kapan saja."}
