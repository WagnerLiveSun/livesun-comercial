-- Migration: Corrigir tamanho da coluna status em contratos
-- Data: 2026-08-05

ALTER TABLE contratos 
MODIFY COLUMN status VARCHAR(30) NOT NULL DEFAULT 'rascunho';
