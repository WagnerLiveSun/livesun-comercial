-- ============================================================================
-- LiveSun Comercial - 033 - Adiciona coluna usuarios_maximos (PostgreSQL)
-- ----------------------------------------------------------------------------
-- Cada empresa possui um limite de usuarios ativos definido pelo Backoffice
-- Comercial (coluna `usuarios_maximos`, valor padrao 5 -> espelha o plano
-- intermediate). Esta migration e IDEMPOTENTE (ADD COLUMN IF NOT EXISTS).
--
-- A tabela vive no schema `app` e se chama `empresas` (plural), conforme
-- src/models/__init__.py :: class Empresa.
--
-- EXECUCAO: conectar no database comercial como comercial_db_owner (ou
-- postgres). A role livesun_api nao pode executar este DDL.
-- ============================================================================

BEGIN;

ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS usuarios_maximos INTEGER DEFAULT 5 NOT NULL;

-- Garantir valores definidos em linhas pre-existentes
UPDATE app.empresas SET usuarios_maximos = 5 WHERE usuarios_maximos IS NULL OR usuarios_maximos < 1;

COMMENT ON COLUMN app.empresas.usuarios_maximos IS 'Limite de usuarios ativos definido pelo backoffice comercial';

COMMIT;

-- Verificar resultado
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'app'
  AND table_name = 'empresas'
  AND column_name = 'usuarios_maximos';
