# School Scheduling API

API penjadwalan guru untuk lembaga les/sekolah. Admin memasukkan jam tersedia tiap guru, lalu sistem menyusun jadwal otomatis (OR-Tools CP-SAT) atau admin memilih guru secara manual.

**Teknologi:** Python, FastAPI, OR-Tools CP-SAT, SQLAlchemy + PyMySQL, MySQL (XAMPP), JWT.
**Code Style:** berorientasi objek (class), rute berbasis folder seperti Next.js App Router.

---

## 1. Struktur Folder

```
scheduling-cpsat/
├── app/
│   ├── main.py            create_app(): pasang error handler + muat semua route.py
│   ├── route.py           GET /
│   │
│   ├── api/               RUTE (folder = URL, lihat bagian 2)
│   │   ├── auth/          login · me · change-password
│   │   ├── users/         daftar/buat user · [user_id]
│   │   ├── teachers/      daftar/buat guru · [teacher_id] · availability · available · remaining
│   │   ├── schools/       daftar/buat sekolah · [school_id]
│   │   ├── schedule/      generate · generate-multi · manual · [day]
│   │   ├── sessions/      [session_id]
│   │   ├── workload/      [day]
│   │   ├── invoices/      daftar/buat invoice · [invoice_id] · [invoice_id]/status
│   │   └── db-test/       cek koneksi database
│   │
│   ├── core/              INFRASTRUKTUR
│   │   ├── config.py          Settings, membaca .env
│   │   ├── database.py        Database (engine + transaksi)
│   │   ├── security.py        PasswordHasher, TokenService (JWT)
│   │   ├── container.py       Container, merakit semua service & repository
│   │   ├── dependencies.py    get_current_user, READ / SCHED / FIN / ADMIN_ONLY
│   │   ├── router_loader.py   FileRouter + dekorator @route
│   │   ├── error_handlers.py  error → respons JSON
│   │   └── errors.py          AppError, BadRequest, NotFound, Conflict, ...
│   │
│   ├── schemas/           model request (Pydantic): auth, people, schedule
│   ├── models/            entities.py → User, Teacher, School
│   ├── repositories/      SEMUA SQL, satu class per tabel/agregat
│   ├── services/          ATURAN BISNIS, satu class per fitur
│   ├── solver/            CP-SAT: context · model_builder · diagnostics · scheduler
│   └── lib/               timeutil.py (jam/hari), names.py (nama)
│
├── scripts/create_admin.py    buat admin pertama
├── sql/schema.sql             struktur tabel (instalasi baru)
├── sql/migration.sql          perubahan untuk database lama
├── tests/                     test_routes · test_solver · test_timeutil
├── .env.example               contoh pengaturan
└── requirements.txt
```

---

## 2. Setup

1. Nyalakan MySQL di XAMPP (Apache tidak wajib).
2. Virtual environment dan library** (dari folder proyek):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   python3 -m pip install -r requirements.txt
   ```
3. Database (lihat bagian 4).
4. Pengaturan: salin `.env.example` menjadi `.env`
5. Buat admin pertama:
   ```bash
   python3 -m scripts.create_admin admin
   ```
6. Jalankan server (dari root proyek):
   ```bash
   python3 -m uvicorn app.main:app --reload --port 8000
   ```
7. Buka http://127.0.0.1:8000/docs → `POST /api/auth/login` → salin `access_token` → klik Authorize → tempel token.
8. Test dgn Postman: `POST /api/auth/login` (Auth: No Auth, Body: raw JSON `{"username":"admin","password":"..."}`) → salin `access_token` → di request lain pilih Authorization → Bearer Token → tempel token.
9. Tes otomatis: `python3 -m pytest tests -q` (tes waktu, solver, dan daftar rute tidak butuh database).

---

## 3. Database

| Tabel | Isi | Catatan |
|---|---|---|
| `teachers` | daftar guru resmi | soft delete (`deleted_at`) |
| `schools` | daftar sekolah | soft delete (`deleted_at`) |
| `classes` | kelas milik sekolah | unik per (sekolah, nama kelas) |
| `sessions` | sesi mengajar: hari, jam mulai/selesai, durasi, jumlah guru dibutuhkan | |
| `assignments` | guru mana mengajar sesi mana | sumber kebenaran jadwal |
| `teacher_schedules` | ATURAN: jam guru bisa mengajar per hari (JSON rentang jam, jumlah rentang, total jam) | tidak berubah saat guru ditugaskan |
| `teacher_workload` | HASIL: jam guru yang sudah ditugaskan per hari | dibangun ulang otomatis dari `assignments` |
| `users` | akun login | password disimpan sebagai hash |
| `invoices`, `invoice_items` | invoice dan item-itemnya | soft delete (`deleted_at`) |

---

## 4. Daftar Endpoint

| Kelompok | Endpoint |
|---|---|
| **Auth & User** | `POST /api/auth/login` · `GET /api/auth/me` · `POST /api/auth/change-password` · `GET, POST /api/users` · `PATCH /api/users/{id}` |
| **Guru** | `GET, POST /api/teachers` · `GET, PUT, DELETE /api/teachers/{id}` |
| **Ketersediaan** | `POST /api/teachers/availability` · `GET /api/teachers/availability/{hari}` · `DELETE /api/teachers/{id}/availability?day=` |
| **Cari & sisa jam** | `GET /api/teachers/available?day&start&end&school` · `GET /api/teachers/remaining/{hari}?school=` |
| **Sekolah** | `GET, POST /api/schools` · `GET, PUT, DELETE /api/schools/{id}` |
| **Jadwal** | `POST /api/schedule/generate` · `POST /api/schedule/generate-multi` · `POST /api/schedule/manual` · `GET, DELETE /api/schedule/{hari}` |
| **Sesi & beban** | `GET, PATCH, DELETE /api/sessions/{id}` · `GET /api/workload/{hari}` |
| **Invoice** | `GET, POST /api/invoices` · `GET, PATCH, DELETE /api/invoices/{id}` · `POST /api/invoices/{id}/status` |
| **Lainnya** | `GET /` · `GET /api/db-test` |
