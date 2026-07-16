-- Add missing fields to categories table
ALTER TABLE categories ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE categories ADD COLUMN updated_at TEXT;