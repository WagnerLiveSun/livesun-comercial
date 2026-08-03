-- Migration: add removed_by_id, removed_by, removed_at to nfse_nacional_certificados
ALTER TABLE nfse_nacional_certificados
    ADD COLUMN removed_by_id INT NULL,
    ADD COLUMN removed_by VARCHAR(120) NULL,
    ADD COLUMN removed_at DATETIME NULL;
