# """Manajemen invoice / kuitansi manual.

# Alur status:  DRAFT -> SENT -> PAID ;  DRAFT/SENT -> CANCELLED.
# Hanya DRAFT yang boleh diubah isinya. Hapus (soft delete) hanya untuk DRAFT/CANCELLED.
# Nominal = Rupiah bulat (BIGINT); total dihitung server dari item, bukan dari klien.
# """
# import re

# from sqlalchemy.exc import IntegrityError

# from app.core.database import Database
# from app.core.errors import BadRequest, Conflict, NotFound
# from app.lib.names import NameUtil
# from app.repositories.invoice_repository import InvoiceRepository
# from app.repositories.school_repository import SchoolRepository


# class InvoiceService:
#     STATUSES = ("DRAFT", "SENT", "PAID", "CANCELLED")
#     TRANSITIONS = {"DRAFT": {"SENT", "CANCELLED"}, "SENT": {"PAID", "CANCELLED"},
#                    "PAID": set(), "CANCELLED": set()}
#     _NUMBER_RE = re.compile(r"^[A-Za-z0-9/_.-]{1,30}$")
#     MAX_ITEMS = 100

#     def __init__(self, db: Database):
#         self.db = db

#     # ---- validasi ----

#     @classmethod
#     def _clean_items(cls, items):
#         if not items or len(items) > cls.MAX_ITEMS:
#             raise BadRequest(f"Invoice harus punya 1-{cls.MAX_ITEMS} item.")
#         out, total = [], 0
#         for it in items:
#             desc = NameUtil.clean(it["description"], "Deskripsi item", 255)
#             qty, price = it["quantity"], it["unit_price"]
#             if not isinstance(qty, int) or isinstance(qty, bool) or not (1 <= qty <= 1_000_000):
#                 raise BadRequest("quantity harus bilangan bulat 1 - 1.000.000.")
#             if not isinstance(price, int) or isinstance(price, bool) or not (0 <= price <= 10**12):
#                 raise BadRequest("unit_price harus bilangan bulat Rupiah 0 - 1.000.000.000.000.")
#             out.append((desc, qty, price, qty * price))
#             total += qty * price
#         return out, total

#     @staticmethod
#     def _check_dates(issue, due):
#         if due is not None and due < issue:
#             raise BadRequest("due_date tidak boleh sebelum issue_date.")

#     @staticmethod
#     def _active_school(conn, school_id):
#         if not SchoolRepository(conn).is_active(school_id):
#             raise BadRequest(f"Sekolah dengan id {school_id} tidak ditemukan.")

#     @staticmethod
#     def _next_number(invoices: InvoiceRepository, issue):
#         prefix = f"INV-{issue:%Y%m}-"
#         last = invoices.last_number(prefix)
#         seq = int(last[len(prefix):]) + 1 if last and last[len(prefix):].isdigit() else 1
#         return f"{prefix}{seq:04d}"

#     # ---- operasi ----

#     def create(self, school_id, issue_date, due_date, notes, items, invoice_number=None, created_by=None):
#         self._check_dates(issue_date, due_date)
#         clean, total = self._clean_items(items)
#         if invoice_number is not None and not self._NUMBER_RE.match(invoice_number):
#             raise BadRequest("invoice_number maksimal 30 karakter: huruf, angka, / _ . -")
#         notes = notes.strip() if notes else None
#         if notes and len(notes) > 500:
#             raise BadRequest("notes maksimal 500 karakter.")

#         for _ in range(5):  # nomor otomatis bisa bentrok bila dua admin membuat bersamaan -> ulangi
#             try:
#                 with self.db.begin() as conn:
#                     invoices = InvoiceRepository(conn)
#                     self._active_school(conn, school_id)
#                     number = invoice_number or self._next_number(invoices, issue_date)
#                     iid = invoices.insert(number, school_id, issue_date, due_date, notes, total, created_by)
#                     invoices.insert_items(iid, clean)
#                 return self.get(iid)
#             except IntegrityError:
#                 if invoice_number is not None:
#                     raise Conflict(f"Nomor invoice '{invoice_number}' sudah dipakai.")
#         raise Conflict("Gagal membuat nomor invoice otomatis, coba lagi.")

#     def get(self, invoice_id):
#         with self.db.connect() as conn:
#             inv = InvoiceRepository(conn).get(invoice_id)
#         if not inv:
#             raise NotFound(f"Invoice dengan id {invoice_id} tidak ditemukan.")
#         return inv

#     def list(self, school_id=None, status=None, date_from=None, date_to=None, limit=50, offset=0):
#         if status is not None and status not in self.STATUSES:
#             raise BadRequest(f"status tidak valid. Pilihan: {', '.join(self.STATUSES)}.")
#         with self.db.connect() as conn:
#             total, rows = InvoiceRepository(conn).search(school_id, status, date_from, date_to, limit, offset)
#         return {"total": total, "limit": limit, "offset": offset, "invoices": rows}

#     def update(self, invoice_id, changes):
#         """Ubah invoice DRAFT. changes (hanya yang dikirim): school_id, issue_date, due_date, notes, items."""
#         with self.db.begin() as conn:
#             invoices = InvoiceRepository(conn)
#             cur = invoices.header(invoice_id)
#             if not cur:
#                 raise NotFound(f"Invoice dengan id {invoice_id} tidak ditemukan.")
#             if cur[0] != "DRAFT":
#                 raise Conflict(f"Invoice berstatus {cur[0]}; hanya DRAFT yang boleh diubah.")
#             self._check_dates(changes.get("issue_date", cur[1]), changes.get("due_date", cur[2]))
#             sets, params = [], {}
#             if "school_id" in changes:
#                 self._active_school(conn, changes["school_id"])
#                 sets.append("school_id = :s"); params["s"] = changes["school_id"]
#             for col in ("issue_date", "due_date"):
#                 if col in changes:
#                     sets.append(f"{col} = :{col}"); params[col] = changes[col]
#             if "notes" in changes:
#                 n = changes["notes"].strip() if changes["notes"] else None
#                 if n and len(n) > 500:
#                     raise BadRequest("notes maksimal 500 karakter.")
#                 sets.append("notes = :notes"); params["notes"] = n
#             if "items" in changes:
#                 clean, total = self._clean_items(changes["items"])
#                 invoices.delete_items(invoice_id)
#                 invoices.insert_items(invoice_id, clean)
#                 sets.append("total_amount = :t"); params["t"] = total
#             if sets:
#                 invoices.update_fields(invoice_id, sets, params)
#         return self.get(invoice_id)

#     def set_status(self, invoice_id, new_status):
#         if new_status not in self.STATUSES:
#             raise BadRequest(f"status tidak valid. Pilihan: {', '.join(self.STATUSES)}.")
#         with self.db.begin() as conn:
#             invoices = InvoiceRepository(conn)
#             cur = invoices.status_of(invoice_id)
#             if cur is None:
#                 raise NotFound(f"Invoice dengan id {invoice_id} tidak ditemukan.")
#             if new_status not in self.TRANSITIONS[cur]:
#                 allowed = ", ".join(sorted(self.TRANSITIONS[cur])) or "tidak ada"
#                 raise Conflict(f"Status {cur} tidak bisa menjadi {new_status}. Yang diizinkan: {allowed}.")
#             invoices.set_status(invoice_id, new_status, mark_paid=(new_status == "PAID"))
#         return self.get(invoice_id)

#     def delete(self, invoice_id):
#         with self.db.begin() as conn:
#             invoices = InvoiceRepository(conn)
#             cur = invoices.status_of(invoice_id)
#             if cur is None:
#                 raise NotFound(f"Invoice dengan id {invoice_id} tidak ditemukan.")
#             if cur not in ("DRAFT", "CANCELLED"):
#                 raise Conflict(f"Invoice berstatus {cur} tidak boleh dihapus. Batalkan dulu (CANCELLED).")
#             invoices.soft_delete(invoice_id)
#         return {"deleted": invoice_id}
