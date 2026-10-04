-- ============================================================
-- SalitAACo - Filipino AAC
-- Import this file in phpMyAdmin: Import tab -> choose file -> Go
-- Or run: mysql -u root -p < database.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS salitaaco_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE salitaaco_db;

-- ---------- Users (accounts) ----------
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  age INT NULL,
  avatar_data LONGBLOB NULL,
  avatar_mime VARCHAR(50) NULL,
  is_admin TINYINT(1) NOT NULL DEFAULT 0,
  last_login TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------- Per-user customizations (editable images + recorded sounds) ----------
CREATE TABLE IF NOT EXISTS customizations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  word VARCHAR(100) NOT NULL,
  image_data LONGBLOB NULL,
  image_mime VARCHAR(50) NULL,
  sound_data LONGBLOB NULL,
  sound_mime VARCHAR(50) NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_user_word (user_id, word),
  CONSTRAINT fk_customizations_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------- Per-user word usage counts (powers the "Madalas Gamitin" tab) ----------
CREATE TABLE IF NOT EXISTS word_usage (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  word VARCHAR(100) NOT NULL,
  use_count INT NOT NULL DEFAULT 0,
  last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_user_word_usage (user_id, word),
  CONSTRAINT fk_word_usage_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------- One rating per user (app rating + optional comment) ----------
CREATE TABLE IF NOT EXISTS ratings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  rating TINYINT NOT NULL,
  comment TEXT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_user_rating (user_id),
  CONSTRAINT fk_ratings_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT chk_rating_range CHECK (rating BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Upgrading an existing database created by an earlier version?
-- Run the statements below instead of the CREATE TABLE statements above.
--
-- ALTER TABLE users ADD COLUMN age INT NULL;
-- ALTER TABLE users ADD COLUMN avatar_data LONGBLOB NULL;
-- ALTER TABLE users ADD COLUMN avatar_mime VARCHAR(50) NULL;
-- ALTER TABLE users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0;
-- ALTER TABLE users ADD COLUMN last_login TIMESTAMP NULL;
--
-- CREATE TABLE IF NOT EXISTS ratings (
--   id INT AUTO_INCREMENT PRIMARY KEY,
--   user_id INT NOT NULL,
--   rating TINYINT NOT NULL,
--   comment TEXT NULL,
--   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--   UNIQUE KEY unique_user_rating (user_id),
--   CONSTRAINT fk_ratings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--   CONSTRAINT chk_rating_range CHECK (rating BETWEEN 1 AND 5)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
-- ============================================================

-- ============================================================
-- Make yourself a developer/admin after signing up through the app:
--
-- UPDATE users SET is_admin = 1 WHERE username = 'your_username_here';
--
-- Admins can open admin.php to view the analytics dashboard. This flag
-- cannot be set from inside the app itself, on purpose - only someone
-- with direct database access can grant it.
-- ============================================================
