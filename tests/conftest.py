import os
import sys
from pathlib import Path

# env dummy agar import app tidak gagal; tes di folder ini tidak butuh database
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://user:pass@localhost/teacher_scheduling_test")
os.environ.setdefault("SECRET_KEY", "x" * 40)
os.environ.setdefault("PBKDF2_ITERATIONS", "1000")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
