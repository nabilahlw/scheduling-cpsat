"""File-based routing ala Next.js App Router.

Aturan:
  app/api/teachers/route.py              -> /api/teachers
  app/api/teachers/[teacher_id]/route.py -> /api/teachers/{teacher_id}
  Di dalam route.py, fungsi bernama GET / POST / PUT / PATCH / DELETE
  otomatis menjadi handler HTTP method itu.
  Opsi per handler (status_code, dependencies, dst.) lewat dekorator @route(...).
  Rute statis selalu didaftarkan sebelum rute dinamis ("[x]"), jadi
  /api/teachers/available tidak tertelan oleh /api/teachers/{teacher_id}.
"""
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from fastapi import APIRouter

HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
ROUTE_FILE = "route.py"
_DYNAMIC = re.compile(r"^\[(\w+)\]$")


def route(**options):
    """Dekorator opsional: @route(status_code=201, dependencies=[...])."""
    def decorator(fn):
        fn.route_options = options
        return fn
    return decorator


@dataclass
class RouteFile:
    file: Path
    segments: List[str]

    @property
    def url(self) -> str:
        return "/" + "/".join(self.segments)

    @property
    def sort_key(self):
        # segmen statis (0) mengalahkan segmen dinamis (1) pada posisi yang sama
        return [(1 if s.startswith("{") else 0, s) for s in self.segments]


class FileRouter:
    def __init__(self, root: Path):
        self.root = Path(root)

    def discover(self) -> List[RouteFile]:
        found = []
        for file in self.root.rglob(ROUTE_FILE):
            parts = file.parent.relative_to(self.root).parts
            segments = [f"{{{m.group(1)}}}" if (m := _DYNAMIC.match(p)) else p for p in parts]
            found.append(RouteFile(file, segments))
        return sorted(found, key=lambda r: r.sort_key)

    def build(self) -> APIRouter:
        router = APIRouter()
        for rf in self.discover():
            module = self._import(rf)
            handlers = [(m, getattr(module, m)) for m in HTTP_METHODS if callable(getattr(module, m, None))]
            if not handlers:
                raise RuntimeError(f"{rf.file} tidak punya handler (GET/POST/PUT/PATCH/DELETE).")
            for method, fn in handlers:
                options = dict(getattr(fn, "route_options", {}))
                options.setdefault("name", f"{method} {rf.url}")
                router.add_api_route(rf.url, fn, methods=[method], **options)
        return router

    def _import(self, rf: RouteFile):
        rel = rf.file.relative_to(self.root).with_suffix("")
        name = "app_routes_" + re.sub(r"\W", "_", "_".join(rel.parts))
        spec = importlib.util.spec_from_file_location(name, rf.file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module  # perlu agar anotasi tipe FastAPI/Pydantic bisa di-resolve
        spec.loader.exec_module(module)
        return module
