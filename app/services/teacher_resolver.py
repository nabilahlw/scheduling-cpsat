from app.core.errors import BadRequest
from app.lib.names import NameUtil
from app.repositories.teacher_repository import TeacherRepository


class TeacherResolver:
    """Nama -> guru resmi. Hanya nama dari daftar guru aktif yang diterima."""

    def __init__(self, teachers: TeacherRepository):
        self.teachers = teachers

    def resolve(self, names, reject_duplicates=False):
        """Return [(id, nama_kanonik)]. Nama asing -> 400 + saran nama mirip.
        Nama guru yang sudah dihapus -> 400."""
        rows = self.teachers.all()
        by_name = {r.name.strip().lower(): r for r in rows}
        active_names = [r.name for r in rows if r.deleted_at is None]

        resolved, seen, unknown, deleted = [], set(), [], []
        for raw in names:
            name = NameUtil.clean(raw, "Nama guru", 100)
            key = name.lower()
            if key in seen:
                if reject_duplicates:
                    raise BadRequest(f"Guru '{name}' ditulis lebih dari sekali.")
                continue
            seen.add(key)
            r = by_name.get(key)
            if r is None:
                unknown.append({"name": name, "suggestions": NameUtil.similar(name, active_names)})
            elif r.deleted_at is not None:
                deleted.append(r.name)
            else:
                resolved.append((r.id, r.name))

        if deleted:
            raise BadRequest(f"Guru sudah dihapus: {', '.join(deleted)}. Pulihkan lewat POST /api/teachers.",
                             extra={"deleted_teachers": deleted})
        if unknown:
            parts = []
            for u in unknown:
                hint = f" (maksud Anda: {', '.join(u['suggestions'])}?)" if u["suggestions"] else ""
                parts.append(f"'{u['name']}'{hint}")
            raise BadRequest("Guru tidak ada di daftar guru resmi: " + "; ".join(parts) +
                             ". Tambahkan dulu lewat POST /api/teachers.",
                             extra={"unknown_teachers": unknown})
        return resolved
