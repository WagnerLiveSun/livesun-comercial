-- ============================================================================
-- LiveSun Comercial - 031 - Adiciona atividade_relatorios (PostgreSQL)
-- Data: 2026-10-21
-- Motivo: Adicionar controle de acesso ao modulo de relatorios
--
-- A tabela vive no schema `app` e se chama `empresas` (plural), igual ao
-- __tablename__ do model src/models/__init__.py :: class Empresa.
-- A versao anterior usava `app.empresa` (singular), que nao existe.
--
-- PostgreSQL suporta `ADD COLUMN IF NOT EXISTS` nativamente, portanto esta
-- migration e IDEMPOTENTE.
--
-- EXECUCAO: conectar no database comercial como comercial_db_owner (ou
-- postgres). A role livesun_api nao pode executar este DDL.
-- ============================================================================

ALTER TABLE app.empresas
    ADD COLUMN IF NOT EXISTS atividade_relatorios BOOLEAN DEFAULT FALSE;

-- Adicionar comentario
COMMENT ON COLUMN app.empresas.atividade_relatorios IS 'Controla acesso ao modulo de relatorios gerenciais e fiscais';

-- Normalizar valores pre-existentes (evita NULL em coluna booleana)
UPDATE app.empresas
SET atividade_relatorios = FALSE
WHERE atividade_relatorios IS NULL;
