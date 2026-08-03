-- =====================================================================
-- LiveSun Comercial - Parte 5: Controle de Acesso RBAC e Auditoria (PostgreSQL)
-- =====================================================================
-- Este arquivo deve ser executado após criar_banco_comercial_postgresql_part4.sql
-- =====================================================================

-- =========================
-- 10) CONTROLE DE ACESSO (RBAC)
-- =========================
CREATE TABLE IF NOT EXISTS rbac_roles (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    nome VARCHAR(50) NOT NULL,
    descricao VARCHAR(255),
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_rbac_roles_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_rbac_roles_empresa_nome UNIQUE (empresa_id, nome)
);

CREATE INDEX idx_rbac_roles_empresa ON rbac_roles(empresa_id);

CREATE TRIGGER update_rbac_roles_atualizado_em
    BEFORE UPDATE ON rbac_roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS rbac_permissions (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(100) NOT NULL,
    descricao VARCHAR(255),
    
    CONSTRAINT uq_rbac_permissions_codigo UNIQUE (codigo)
);

CREATE TABLE IF NOT EXISTS rbac_user_roles (
    id BIGSERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_rbac_user_roles_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_rbac_user_roles_user 
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rbac_user_roles_role 
      FOREIGN KEY (role_id) REFERENCES rbac_roles(id) ON DELETE CASCADE,
    CONSTRAINT uq_rbac_user_role UNIQUE (user_id, role_id)
);

CREATE INDEX idx_rbac_user_roles_empresa ON rbac_user_roles(empresa_id);

CREATE TABLE IF NOT EXISTS rbac_role_permissions (
    id BIGSERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    
    CONSTRAINT fk_rbac_role_permissions_role 
      FOREIGN KEY (role_id) REFERENCES rbac_roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_rbac_role_permissions_permission 
      FOREIGN KEY (permission_id) REFERENCES rbac_permissions(id) ON DELETE CASCADE,
    CONSTRAINT uq_rbac_role_permission UNIQUE (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS auditoria_eventos (
    id BIGSERIAL PRIMARY KEY,
    empresa_id INTEGER,
    user_id INTEGER,
    modulo VARCHAR(60) NOT NULL,
    acao VARCHAR(60) NOT NULL,
    entidade VARCHAR(60),
    entidade_id VARCHAR(60),
    detalhes JSONB,
    ip_origem VARCHAR(45),
    user_agent VARCHAR(255),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_auditoria_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE SET NULL,
    CONSTRAINT fk_auditoria_user 
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_auditoria_empresa ON auditoria_eventos(empresa_id);
CREATE INDEX idx_auditoria_user ON auditoria_eventos(user_id);
CREATE INDEX idx_auditoria_modulo_acao ON auditoria_eventos(modulo, acao);
CREATE INDEX idx_auditoria_criado_em ON auditoria_eventos(criado_em);

-- =========================
-- 11) DADOS BASE DE CONTROLE DE ACESSO
-- =========================
INSERT INTO rbac_permissions (codigo, descricao) VALUES
('dashboard.view', 'Visualizar dashboard'),
('entidades.read', 'Consultar entidades'),
('entidades.write', 'Criar/editar entidades'),
('lancamentos.read', 'Consultar lançamentos'),
('lancamentos.write', 'Criar/editar lançamentos'),
('lancamentos.pay', 'Baixar lançamentos'),
('comissoes.read', 'Consultar comissões'),
('comissoes.apurar', 'Executar apuração de comissões'),
('comissoes.parametros', 'Alterar parâmetros de comissão'),
('importacoes.nfse', 'Importar NFSe'),
('importacoes.ofx', 'Importar OFX'),
('conciliacao.read', 'Consultar conciliação bancária'),
('conciliacao.write', 'Executar conciliação bancária'),
('users.manage', 'Gerenciar usuários e permissões')
ON CONFLICT (codigo) DO NOTHING;

-- =========================
-- 12) VERIFICAÇÃO FINAL
-- =========================
-- Listar tabelas criadas
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Contar registros em tabelas principais
SELECT 'empresas' AS tabela, COUNT(*) AS total FROM empresas
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'entidades', COUNT(*) FROM entidades
UNION ALL SELECT 'fluxo_contas_modelo', COUNT(*) FROM fluxo_contas_modelo
UNION ALL SELECT 'contas_banco', COUNT(*) FROM contas_banco
UNION ALL SELECT 'lancamentos', COUNT(*) FROM lancamentos
UNION ALL SELECT 'importacao_nfse', COUNT(*) FROM importacao_nfse
UNION ALL SELECT 'comissoes', COUNT(*) FROM comissoes
UNION ALL SELECT 'conciliacao_bancaria', COUNT(*) FROM conciliacao_bancaria
UNION ALL SELECT 'conciliacao_item', COUNT(*) FROM conciliacao_item
UNION ALL SELECT 'filiais', COUNT(*) FROM filiais
UNION ALL SELECT 'produtos', COUNT(*) FROM produtos
UNION ALL SELECT 'servicos', COUNT(*) FROM servicos
UNION ALL SELECT 'estoque_movimentos', COUNT(*) FROM estoque_movimentos
UNION ALL SELECT 'compras_nf_manual', COUNT(*) FROM compras_nf_manual
UNION ALL SELECT 'documentos_venda', COUNT(*) FROM documentos_venda
UNION ALL SELECT 'tabelas_preco', COUNT(*) FROM tabelas_preco
UNION ALL SELECT 'orcamentos', COUNT(*) FROM orcamentos
UNION ALL SELECT 'pedidos_venda', COUNT(*) FROM pedidos_venda
UNION ALL SELECT 'pdv_sessoes', COUNT(*) FROM pdv_sessoes
UNION ALL SELECT 'pdv_vendas', COUNT(*) FROM pdv_vendas
UNION ALL SELECT 'rbac_permissions', COUNT(*) FROM rbac_permissions;

-- Fim do script PostgreSQL
