-- Skema lengkap (instalasi baru / database tes). Untuk database yang SUDAH ada, pakai migration.sql.
-- Target: MariaDB (XAMPP) / MySQL 8, InnoDB, utf8mb4.

CREATE TABLE IF NOT EXISTS teachers (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  deleted_at DATETIME NULL,
  UNIQUE KEY uq_teachers_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS schools (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  deleted_at DATETIME NULL,
  UNIQUE KEY uq_schools_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS classes (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  school_id INT NOT NULL,
  name VARCHAR(50) NOT NULL,
  UNIQUE KEY uq_classes_school_name (school_id, name),
  CONSTRAINT fk_classes_school FOREIGN KEY (school_id) REFERENCES schools(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sessions (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  class_id INT NOT NULL,
  day VARCHAR(10) NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  duration_minutes INT NOT NULL,
  required_teachers_count INT NOT NULL,
  KEY idx_sessions_day (day),
  CONSTRAINT fk_sessions_class FOREIGN KEY (class_id) REFERENCES classes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS assignments (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  session_id INT NOT NULL,
  teacher_id INT NOT NULL,
  CONSTRAINT fk_assign_session FOREIGN KEY (session_id) REFERENCES sessions(id),
  CONSTRAINT fk_assign_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS teacher_schedules (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  teacher_name VARCHAR(100) NOT NULL,
  day VARCHAR(10) NOT NULL,
  records LONGTEXT NOT NULL,
  record_count INT NOT NULL,
  total_minutes INT NOT NULL,
  total_hours VARCHAR(20) NOT NULL,
  UNIQUE KEY uq_schedules_teacher_day (teacher_id, day),
  CONSTRAINT fk_tsched_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS teacher_workload (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  teacher_name VARCHAR(100) NOT NULL,
  day VARCHAR(10) NOT NULL,
  records LONGTEXT NOT NULL,
  record_count INT NOT NULL,
  total_minutes INT NOT NULL,
  total_hours VARCHAR(20) NOT NULL,
  UNIQUE KEY uq_workload_teacher_day (teacher_id, day),
  CONSTRAINT fk_twork_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---- RBAC ----
CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL,            -- admin | scheduler | finance | viewer
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---- Invoice / kuitansi ----
CREATE TABLE IF NOT EXISTS invoices (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  invoice_number VARCHAR(30) NOT NULL,
  school_id INT NOT NULL,
  issue_date DATE NOT NULL,
  due_date DATE NULL,
  notes VARCHAR(500) NULL,
  status VARCHAR(15) NOT NULL DEFAULT 'DRAFT',   -- DRAFT | SENT | PAID | CANCELLED
  total_amount BIGINT NOT NULL DEFAULT 0,        -- Rupiah, bilangan bulat
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
