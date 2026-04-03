-- Migration: Add role column to users table
-- Purpose: Support role-based access control (RBAC) with admin, operator, viewer roles
-- Compatibility: SQLite and MySQL

-- Add role column if it doesn't exist
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'viewer';

-- Update roles based on is_admin flag for existing users (backfill)
UPDATE users SET role = 'admin' WHERE is_admin = 1;
UPDATE users SET role = 'operator' WHERE is_admin = 0 AND role = 'viewer';
