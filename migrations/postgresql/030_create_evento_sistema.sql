-- ============================================================================
-- LiveSun Comercial - 030 - Cria tabela de evento de auditoria (backoffice)
-- ============================================================================
-- NOVO:
--   Cria a tabela ``evento_sistema``, usada pelo Log de Eventos do backoffice
--   comercial. Armazena: usuário (id), empresa (id), categoria (info/sucesso/
--   alerta/erro), tipo (EXCLUIR, PURGAR, MUDANCA_PLANO, ATUALIZACAO_USUARIO,
--   EXCLUSAO_DEFINITIVA), descricao, detalhes (JSONB) e origem (tabela/id).
--   O painel ``comercial_panel.html`` exibe os últimos registros e aceita
--   filtros por categoria e tipo via querystring.
-- EXECUÇÃO:
--   Conectar ao database comercial no MontuDB como comercial_db_owner (ou
--   postgres). A role livesun_api NÃO pode executar DDL (sem CREATE no schema
--   comercial) e tem apenas SELECT/UPDATE/DELETE nos registros inseres.
-- ============================================================================

CREATE TABLE IF NOT EXISTS evento_sistema (
    id            SERIAL PRIMARY KEY,
    usuario_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    empresa_id    INTEGER REFERENCES empresas(id) ON DELETE SET NULL,
    categoria     VARCHAR(20) NOT NULL,
    tipo          VARCHAR(60) NOT NULL,
    descricao     VARCHAR(500),
    detalhes      JSONB,
    origem_tabela VARCHAR(60),
    origem_id     INTEGER,
    criado_em     TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_evento_sistema_criado_em ON evento_sistema (criado_em);
CREATE INDEX ix_evento_sistema_empresa_criado ON evento_sistema (empresa_id, criado_em);
CREATE INDEX ix_evento_sistema_tipo_criado ON evento_sistema (tipo, criado_em);
