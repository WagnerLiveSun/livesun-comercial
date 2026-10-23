-- ============================================================================
-- LiveSun Comercial - 034 - Adiciona colunas atividade_* do painel comercial (PostgreSQL)
-- ----------------------------------------------------------------------------
-- Adiciona as novas colunas booleanas que controlam o acesso aos módulos
-- liberados pelo Backoffice Comercial no painel de módulos:
--   entidades, estoque, compras, pedidos, pdv, aprovacao, fluxo,
--   contas_banco, usuarios, controle_acesso.
--
-- COLUNAS (alinhadas com src/models/__init__.py :: class Empresa):
--   atividade_entidades        BOOLEAN DEFAULT TRUE
--   atividade_estoque          BOOLEAN DEFAULT FALSE
--   atividade_compras          BOOLEAN DEFAULT FALSE
--   atividade_pedidos          BOOLEAN DEFAULT FALSE
--   atividade_pdv              BOOLEAN DEFAULT FALSE
--   atividade_aprovacao        BOOLEAN DEFAULT FALSE
--   atividade_fluxo            BOOLEAN DEFAULT TRUE
--   atividade_contas_banco     BOOLEAN DEFAULT TRUE
--   atividade_usuarios         BOOLEAN DEFAULT FALSE
--   atividade_controle_acesso  BOOLEAN DEFAULT FALSE
--
-- PostgreSQL suporta `ADD COLUMN IF NOT EXISTS` nativamente, portanto esta
-- migration e IDEMPOTENTE e pode ser executada quantas vezes for necessario.
-- A migration 032 (atividade_* originais) e a 031 (atividade_relatorios)
-- sao covered por esta e podem ser mantidas no historico.
--
-- EXECUCAO: conectar no database comercial como comercial_db_owner (ou
-- postgres). A role livesun_api nao pode executar este DDL.
-- ============================================================================

BEGIN;

ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_entidades        BOOLEAN DEFAULT TRUE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_estoque          BOOLEAN DEFAULT FALSE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_compras          BOOLEAN DEFAULT FALSE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_pedidos          BOOLEAN DEFAULT FALSE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_pdv              BOOLEAN DEFAULT FALSE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_aprovacao        BOOLEAN DEFAULT FALSE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_fluxo            BOOLEAN DEFAULT TRUE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_contas_banco     BOOLEAN DEFAULT TRUE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_usuarios         BOOLEAN DEFAULT FALSE;
ALTER TABLE app.empresas ADD COLUMN IF NOT EXISTS atividade_controle_acesso  BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN app.empresas.atividade_entidades        IS 'Controla acesso ao modulo de Entidades (clientes/fornecedores)';
COMMENT ON COLUMN app.empresas.atividade_estoque          IS 'Controla acesso ao modulo de Estoque';
COMMENT ON COLUMN app.empresas.atividade_compras          IS 'Controla acesso ao modulo de Compras';
COMMENT ON COLUMN app.empresas.atividade_pedidos          IS 'Controla acesso ao modulo de Pedidos de venda';
COMMENT ON COLUMN app.empresas.atividade_pdv              IS 'Controla acesso ao modulo PDV';
COMMENT ON COLUMN app.empresas.atividade_aprovacao        IS 'Controla acesso ao modulo de Aprovacao de propostas';
COMMENT ON COLUMN app.empresas.atividade_fluxo            IS 'Controla acesso ao modulo de Fluxo de caixa';
COMMENT ON COLUMN app.empresas.atividade_contas_banco     IS 'Controla acesso ao modulo de Contas Banco';
COMMENT ON COLUMN app.empresas.atividade_usuarios         IS 'Controla acesso ao modulo de Usuarios';
COMMENT ON COLUMN app.empresas.atividade_controle_acesso  IS 'Controla acesso ao modulo de Controle de acesso';

-- Normalizar valores pre-existentes (evita NULL em colunas booleanas)
UPDATE app.empresas
SET
    atividade_entidades        = COALESCE(atividade_entidades, TRUE),
    atividade_estoque          = COALESCE(atividade_estoque, FALSE),
    atividade_compras          = COALESCE(atividade_compras, FALSE),
    atividade_pedidos          = COALESCE(atividade_pedidos, FALSE),
    atividade_pdv              = COALESCE(atividade_pdv, FALSE),
    atividade_aprovacao        = COALESCE(atividade_aprovacao, FALSE),
    atividade_fluxo            = COALESCE(atividade_fluxo, TRUE),
    atividade_contas_banco     = COALESCE(atividade_contas_banco, TRUE),
    atividade_usuarios         = COALESCE(atividade_usuarios, FALSE),
    atividade_controle_acesso  = COALESCE(atividade_controle_acesso, FALSE);

COMMIT;

-- Verificar resultado
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'app'
  AND table_name = 'empresas'
  AND column_name LIKE 'atividade%'
ORDER BY column_name;