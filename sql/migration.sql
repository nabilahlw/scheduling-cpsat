-- Migrasi untuk database teacher_scheduling yang SUDAH ada (dibuat lewat phpMyAdmin).
-- Aman dijalankan ulang (MariaDB/XAMPP mendukung IF NOT EXISTS pada ALTER).
-- BACKUP dulu: phpMyAdmin > Export.
-- Jalankan: phpMyAdmin > pilih database teacher_scheduling > tab SQL > tempel > Go.

-- 1. Soft delete
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL;
ALTER TABLE schools  ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL;

-- 2. RBAC
CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Invoice / kuitansi
CREATE TABLE IF NOT EXISTS invoices (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  invoice_number VARCHAR(30) NOT NULL,
  school_id INT NOT NULL,
  issue_date DATE NOT NULL,
  due_date DATE NULL,
  notes VARCHAR(500) NULL,
  status VARCHAR(15) NOT NULL DEFAULT 'DRAFT',
  total_amount BIGINT NOT NULL DEFAULT 0,
  paid_at DATETIME NULL,
  created_by INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  UNIQUE KEY uq_invoice_number (invoice_number),
  KEY idx_invoices_school (school_id),
  CONSTRAINT fk_invoice_school FOREIGN KEY (school_id) REFERENCES schools(id),
  CONSTRAINT fk_invoice_user FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS invoice_items (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  invoice_id INT NOT NULL,
  description VARCHAR(255) NOT NULL,
  quantity INT NOT NULL,
  unit_price BIGINT NOT NULL,
  subtotal BIGINT NOT NULL,
  CONSTRAINT fk_item_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Kode versi baru memakai nama hari Indonesia (SENIN..MINGGU).
--    Jika data lama kamu memakai nama Inggris, normalkan dengan (hapus tanda -- jika perlu):
-- UPDATE teacher_schedules SET day='SENIN'  WHERE day='MONDAY';
-- UPDATE teacher_schedules SET day='SELASA' WHERE day='TUESDAY';
-- UPDATE teacher_schedules SET day='RABU'   WHERE day='WEDNESDAY';
-- UPDATE teacher_schedules SET day='KAMIS'  WHERE day='THURSDAY';
-- UPDATE teacher_schedules SET day='JUMAT'  WHERE day='FRIDAY';
-- UPDATE teacher_schedules SET day='SABTU'  WHERE day='SATURDAY';
-- UPDATE teacher_schedules SET day='MINGGU' WHERE day='SUNDAY';
-- (ulangi untuk tabel sessions dan teacher_workload)

-- 5. Cek unique key yang dipakai kode (INSERT IGNORE / ON DUPLICATE KEY). Jalankan SHOW INDEX;
--    kalau belum ada, buka komentar di bawah:
-- ALTER TABLE teachers ADD UNIQUE KEY uq_teachers_name (name);
-- ALTER TABLE schools  ADD UNIQUE KEY uq_schools_name (name);
-- ALTER TABLE classes  ADD UNIQUE KEY uq_classes_school_name (school_id, name);
-- ALTER TABLE teacher_schedules ADD UNIQUE KEY uq_schedules_teacher_day (teacher_id, day);
-- ALTER TABLE teacher_workload  ADD UNIQUE KEY uq_workload_teacher_day (teacher_id, day);
