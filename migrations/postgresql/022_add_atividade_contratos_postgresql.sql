-- ============================================================================
-- LiveSun Comercial - 022 - Adiciona atividade_contratos (PostgreSQL)
-- ----------------------------------------------------------------------------
-- A tabela vive no schema `app` (ver CriaPostgreeSQL_MontuDB/02_criar_estrutura
-- _livesun_comercial.sql, que usa `SET search_path = app, security, pg_catalog`).
-- O nome da tabela e `empresas` (plural), igual ao __tablename__ do model
-- src/models/__init__.py :: class Empresa.
--
-- PostgreSQL suporta `ADD COLUMN IF NOT EXISTS` nativamente, portanto esta
-- migration e IDEMPOTENTE.
--
-- EXECUCAO: conectar no database comercial como comercial_db_owner (ou
-- postgres). A role livesun_api nao pode executar este DDL.
-- ============================================================================

ALTER TABLE app.empresas
    ADD COLUMN IF NOT EXISTS atividade_contratos BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN app.empresas.atividade_contratos IS
    'Controla acesso ao modulo de contratos';

-- Normalizar valores pre-existentes (evita NULL em coluna booleana)
UPDATE app.empresas
SET atividade_contratos = FALSE
WHERE atividade_contratos IS NULL;
