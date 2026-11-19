"""Buat user admin pertama:  python3 -m scripts.create_admin <username>"""
import getpass
import sys

from app.core.container import container
from app.core.errors import AppError
from app.services.user_service import UserService

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Pemakaian: python3 -m scripts.create_admin <username>")
    pw = getpass.getpass("Password (min 8 karakter): ")
    if pw != getpass.getpass("Ulangi password: "):
        sys.exit("Password tidak sama.")
    try:
        user = container.users.create(sys.argv[1], pw, UserService.ADMIN)
    except AppError as e:
        sys.exit(f"Gagal: {e.detail}")
    print(f"Admin '{user['username']}' dibuat (id {user['id']}).")

