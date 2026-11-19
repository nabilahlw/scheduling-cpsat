# from typing import List, Optional

# from app.repositories.base import BaseRepository


# class InvoiceRepository(BaseRepository):
#     _SELECT = ("SELECT i.id, i.invoice_number, i.school_id, s.name, i.issue_date, i.due_date, i.notes, "
#                "i.status, i.total_amount, i.paid_at, i.created_at FROM invoices i "
#                "JOIN schools s ON s.id = i.school_id")

#     @staticmethod
#     def _to_dict(r) -> dict:
#         iso = lambda v: v.isoformat() if v else None  # noqa: E731
#         return {"id": r[0], "invoice_number": r[1], "school_id": r[2], "school": r[3],
#                 "issue_date": iso(r[4]), "due_date": iso(r[5]), "notes": r[6], "status": r[7],
#                 "total_amount": int(r[8]), "paid_at": iso(r[9]), "created_at": iso(r[10])}

#     def last_number(self, prefix: str) -> Optional[str]:
#         return self.execute(
#             "SELECT invoice_number FROM invoices WHERE invoice_number LIKE :p "
#             "ORDER BY LENGTH(invoice_number) DESC, invoice_number DESC LIMIT 1",
#             {"p": prefix + "%"}).scalar()

#     def insert(self, number, school_id, issue_date, due_date, notes, total, created_by) -> int:
#         return self.execute("""
#             INSERT INTO invoices (invoice_number, school_id, issue_date, due_date, notes,
#                                   total_amount, created_by)
#             VALUES (:n, :s, :i, :d, :o, :t, :u)""",
#                             {"n": number, "s": school_id, "i": issue_date, "d": due_date, "o": notes,
#                              "t": total, "u": created_by}).lastrowid

#     def insert_items(self, invoice_id: int, items) -> None:
#         for desc, qty, price, sub in items:
#             self.execute("INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, subtotal) "
#                          "VALUES (:i, :d, :q, :p, :s)",
#                          {"i": invoice_id, "d": desc, "q": qty, "p": price, "s": sub})

#     def delete_items(self, invoice_id: int) -> None:
#         self.execute("DELETE FROM invoice_items WHERE invoice_id = :i", {"i": invoice_id})

#     def get(self, invoice_id: int) -> Optional[dict]:
#         r = self.execute(self._SELECT + " WHERE i.id = :i AND i.deleted_at IS NULL", {"i": invoice_id}).first()
#         if not r:
#             return None
#         items = self.execute("SELECT description, quantity, unit_price, subtotal FROM invoice_items "
#                              "WHERE invoice_id = :i ORDER BY id", {"i": invoice_id}).all()
#         inv = self._to_dict(r)
#         inv["items"] = [{"description": x[0], "quantity": x[1], "unit_price": int(x[2]), "subtotal": int(x[3])}
#                         for x in items]
#         return inv

#     def search(self, school_id, status, date_from, date_to, limit, offset):
#         where, params = ["i.deleted_at IS NULL"], {"lim": limit, "off": offset}
#         if school_id is not None:
#             where.append("i.school_id = :sid"); params["sid"] = school_id
#         if status is not None:
#             where.append("i.status = :st"); params["st"] = status
#         if date_from is not None:
#             where.append("i.issue_date >= :df"); params["df"] = date_from
#         if date_to is not None:
#             where.append("i.issue_date <= :dt"); params["dt"] = date_to
#         clause = " WHERE " + " AND ".join(where)
#         total = self.execute("SELECT COUNT(*) FROM invoices i" + clause, params).scalar()
#         rows = self.execute(self._SELECT + clause + " ORDER BY i.id DESC LIMIT :lim OFFSET :off", params).all()
#         return total, [self._to_dict(r) for r in rows]

#     def header(self, invoice_id: int):
#         """(status, issue_date, due_date, school_id) atau None."""
#         return self.execute("SELECT status, issue_date, due_date, school_id FROM invoices "
#                             "WHERE id = :i AND deleted_at IS NULL", {"i": invoice_id}).first()

#     def status_of(self, invoice_id: int) -> Optional[str]:
#         r = self.execute("SELECT status FROM invoices WHERE id = :i AND deleted_at IS NULL",
#                          {"i": invoice_id}).first()
#         return r[0] if r else None

#     def update_fields(self, invoice_id: int, sets: List[str], params: dict) -> None:
#         self.execute(f"UPDATE invoices SET {', '.join(sets)} WHERE id = :i", {**params, "i": invoice_id})

#     def set_status(self, invoice_id: int, status: str, mark_paid: bool) -> None:
#         self.execute("UPDATE invoices SET status = :s, paid_at = " +
#                      ("NOW()" if mark_paid else "paid_at") + " WHERE id = :i",
#                      {"s": status, "i": invoice_id})

#     def soft_delete(self, invoice_id: int) -> None:
#         self.execute("UPDATE invoices SET deleted_at = NOW() WHERE id = :i", {"i": invoice_id})
