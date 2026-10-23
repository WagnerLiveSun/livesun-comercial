-- ============================================================================
-- LiveSun Comercial - 032 - Adiciona TODAS as colunas atividade_* (PostgreSQL)
-- ----------------------------------------------------------------------------
-- Consolida as colunas de controle de acesso por modulo (multi-tenant).
-- A tabela vive no schema `app` e se chama `empresas` (plural), igual ao
-- __tablename__ do model src/models/__init__.py :: class Empresa.
--
-- COLUNAS (alinhadas com src/models/__init__.py :: class Empresa):
--   atividade_comercial   BOOLEAN DEFAULT TRUE
--   atividade_servicos    BOOLEAN DEFAULT TRUE
--   atividade_financeiro  BOOLEAN DEFAULT TRUE
--   atividade_locacao     BOOLEAN DEFAULT FALSE
--   atividade_contratos   BOOLEAN DEFAULT FALSE
--   atividade_propostas   BOOLEAN DEFAULT FALSE
--   atividade_dashboard   BOOLEAN DEFAULT TRUE
--   atividade_relatorios  BOOLEAN DEFAULT FALSE
--
-- PostgreSQL suporta `ADD COLUMN IF NOT EXISTS` nativamente, portanto esta
-- migration e IDEMPOTENTE e pode ser executada quantas vezes for necessario.
-- A migration 022 (atividade_contratos) e a 031 (atividade_relatorios) sao
-- covered por esta e podem ser mantidas no historico.
--
-- EXECUCAO: conectar no database comercial como comercial_db_owner (ou
-- postgres). A role livesun_api nao pode executar este DDL.
-- ============================================================================

BEGIN;

ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_comercial  BOOLEAN DEFAULT TRUE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_servicos   BOOLEAN DEFAULT TRUE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_financeiro BOOLEAN DEFAULT TRUE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_locacao    BOOLEAN DEFAULT FALSE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_contratos  BOOLEAN DEFAULT FALSE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_propostas  BOOLEAN DEFAULT FALSE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_dashboard  BOOLEAN DEFAULT TRUE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_relatorios BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN app.empresas.atividade_comercial  IS 'Controla acesso ao modulo comercial';
COMMENT ON COLUMN app.empresas.atividade_servicos   IS 'Controla acesso ao modulo de servicos';
COMMENT ON COLUMN app.empresas.atividade_financeiro IS 'Controla acesso ao modulo financeiro';
COMMENT ON COLUMN app.empresas.atividade_locacao    IS 'Controla acesso ao modulo de locacao';
COMMENT ON COLUMN app.empresas.atividade_contratos  IS 'Controla acesso ao modulo de contratos';
COMMENT ON COLUMN app.empresas.atividade_propostas  IS 'Controla acesso ao modulo de propostas';
COMMENT ON COLUMN app.empresas.atividade_dashboard  IS 'Controla acesso ao dashboard';
COMMENT ON COLUMN app.empresas.atividade_relatorios IS 'Controla acesso ao modulo de relatorios gerenciais e fiscais';

-- Normalizar valores pre-existentes (evita NULL em colunas booleanas)
UPDATE app.empresas
SET
    atividade_comercial  = COALESCE(atividade_comercial, TRUE),
    atividade_servicos   = COALESCE(atividade_servicos, TRUE),
    atividade_financeiro = COALESCE(atividade_financeiro, TRUE),
    atividade_locacao    = COALESCE(atividade_locacao, FALSE),
    atividade_contratos  = COALESCE(atividade_contratos, FALSE),
    atividade_propostas  = COALESCE(atividade_propostas, FALSE),
    atividade_dashboard  = COALESCE(atividade_dashboard, TRUE),
    atividade_relatorios = COALESCE(atividade_relatorios, FALSE);

COMMIT;

-- Verificar resultado
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'app'
  AND table_name = 'empresas'
  AND column_name LIKE 'atividade%'
ORDER BY column_name;