-- =====================================================================
-- LiveSun Comercial - Script completo de criação de banco (PostgreSQL 14+)
-- =====================================================================
-- Objetivo:
-- 1) Criar database/schema do projeto Comercial
-- 2) Criar owner do schema (usuário PostgreSQL dono lógico do banco)
-- 3) Criar TODAS as tabelas necessárias para operação do sistema
-- 4) Incluir tabelas de conciliação bancária e controle de acesso
--
-- IMPORTANTE:
-- - Este script NÃO cria usuário funcional da aplicação na tabela `users`.
-- - Ajuste os placeholders antes de executar.
-- - PostgreSQL usa SERIAL/IDENTITY em vez de AUTO_INCREMENT
-- - PostgreSQL usa BOOLEAN em vez de TINYINT(1)
-- - PostgreSQL usa TIMESTAMP em vez de DATETIME
-- =====================================================================

-- =========================
-- 1) DATABASE + OWNER
-- =========================
-- Criar database e owner
CREATE DATABASE comercial
  WITH OWNER = postgres
       ENCODING = 'UTF8'
       LC_COLLATE = 'en_US.UTF-8'
       LC_CTYPE = 'en_US.UTF-8'
       TEMPLATE = template0;

-- Conectar ao database comercial
\c comercial

--Criar usuário owner do banco
CREATE USER comercial_db_owner WITH PASSWORD 'Troque_Essa_Senha_Forte_2026!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE comercial TO comercial_db_owner;
GRANT ALL PRIVILEGES ON SCHEMA public TO comercial_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO comercial_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO comercial_db_owner;

-- Configurar timezone
SET timezone = 'UTC';

-- =========================
-- 2) FUNÇÃO PARA AUTO-UPDATE DE TIMESTAMP
-- =========================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =========================
-- 3) TABELAS CORE (TENANT)
-- =========================

CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    cnpj VARCHAR(18) UNIQUE,
    plano VARCHAR(20) NOT NULL DEFAULT 'premium',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_empresas_atualizado_em
    BEFORE UPDATE ON empresas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER,
    username VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_admin BOOLEAN NOT NULL DEFAULT false,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    dashboard_chart_days INTEGER NOT NULL DEFAULT 30,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_users_empresa
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_users_empresa_username UNIQUE (empresa_id, username),
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE INDEX idx_users_empresa_id ON users(empresa_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_empresa_active ON users(empresa_id, is_active);

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,
    permission_key VARCHAR(80) NOT NULL,
    allowed BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_role_permissions_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_role_permission_empresa_role_key UNIQUE (empresa_id, role, permission_key)
);

CREATE INDEX idx_role_permissions_empresa ON role_permissions(empresa_id);
CREATE INDEX idx_role_permissions_role ON role_permissions(role);
CREATE INDEX idx_role_permissions_key ON role_permissions(permission_key);

CREATE TRIGGER update_role_permissions_updated_at
    BEFORE UPDATE ON role_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS user_permission_overrides (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    permission_key VARCHAR(80) NOT NULL,
    allowed BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user_permission_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_user_permission_user 
      FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT uq_user_permission_override UNIQUE (empresa_id, user_id, permission_key)
);

CREATE INDEX idx_user_permission_empresa ON user_permission_overrides(empresa_id);
CREATE INDEX idx_user_permission_user ON user_permission_overrides(user_id);
CREATE INDEX idx_user_permission_key ON user_permission_overrides(permission_key);

CREATE TRIGGER update_user_permission_overrides_updated_at
    BEFORE UPDATE ON user_permission_overrides
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS fluxo_contas_modelo (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    descricao VARCHAR(200) NOT NULL,
    tipo VARCHAR(1) NOT NULL,
    mascara VARCHAR(50),
    nivel_sintetico INTEGER,
    nivel_analitico INTEGER,
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_fluxo_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_fluxo_empresa_codigo UNIQUE (empresa_id, codigo)
);

CREATE INDEX idx_fluxo_empresa ON fluxo_contas_modelo(empresa_id);
CREATE INDEX idx_fluxo_codigo ON fluxo_contas_modelo(codigo);
CREATE INDEX idx_fluxo_tipo ON fluxo_contas_modelo(tipo);

CREATE TRIGGER update_fluxo_contas_atualizado_em
    BEFORE UPDATE ON fluxo_contas_modelo
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Plano de contas padrão (será inserido após criar a empresa)
-- Verificar se empresa_id=1 existe antes de inserir
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM empresas WHERE id = 1) THEN
        INSERT INTO fluxo_contas_modelo (
            empresa_id, codigo, descricao, tipo, mascara, nivel_sintetico, nivel_analitico, ativo, criado_em, atualizado_em
        ) VALUES
        (1, '1', 'Entradas de Caixa', 'R', NULL, 1, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.1', 'Receitas Operacionais', 'R', NULL, 2, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.1.1', 'Vendas a vista', 'R', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.1.2', 'Vendas cartao credito', 'R', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.1.3', 'Vendas cartao debito', 'R', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.1.4', 'Recebimento mensalidades/servicos', 'R', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.2', 'Receitas Financeiras', 'R', NULL, 2, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.2.1', 'Juros recebidos', 'R', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.2.2', 'Descontos obtidos', 'R', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.3', 'Outras Entradas', 'R', NULL, 2, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.3.1', 'Emprestimos recebidos', 'R', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.3.2', 'Aporte de socios', 'R', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '1.3.3', 'Reembolsos diversos', 'R', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2', 'Saidas de Caixa', 'P', NULL, 1, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.1', 'Custos Operacionais', 'P', NULL, 2, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.1.1', 'Compra de mercadorias', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.1.2', 'Materia-prima/insumos', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.1.3', 'Fretes sobre compras', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.2', 'Despesas Fixas', 'P', NULL, 2, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.2.1', 'Aluguel', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.2.2', 'Energia eletrica', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.2.3', 'Agua', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.2.4', 'Internet e telefone', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.3', 'Despesas com Pessoal', 'P', NULL, 2, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.3.1', 'Salarios', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.3.2', 'Encargos (INSS, FGTS)', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.3.3', 'Pro-labore', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.4', 'Despesas Variaveis', 'P', NULL, 2, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.4.1', 'Comissoes sobre vendas', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.4.2', 'Taxas de cartao/maquininha', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.4.3', 'Impostos sobre vendas', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.5', 'Despesas Financeiras', 'P', NULL, 2, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.5.1', 'Juros e multas pagas', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.5.2', 'Tarifas bancarias', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.6', 'Outras Saidas', 'P', NULL, 2, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.6.1', 'Distribuicao de lucros', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, '2.6.2', 'Adiantamentos a socios', 'P', NULL, 3, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (empresa_id, codigo) DO NOTHING;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS contas_banco (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    nome VARCHAR(150) NOT NULL,
    banco VARCHAR(50) NOT NULL,
    agencia VARCHAR(10) NOT NULL,
    numero_conta VARCHAR(20) NOT NULL,
    dv VARCHAR(2),
    tipo VARCHAR(20),
    fluxo_conta_id INTEGER,
    saldo_inicial NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    is_principal BOOLEAN NOT NULL DEFAULT false,
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_conta_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_conta_fluxo 
      FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id)
);

CREATE INDEX idx_conta_empresa ON contas_banco(empresa_id);
CREATE INDEX idx_conta_nome ON contas_banco(nome);
CREATE INDEX idx_conta_principal ON contas_banco(is_principal);

CREATE TRIGGER update_contas_banco_atualizado_em
    BEFORE UPDATE ON contas_banco
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS entidades (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    nome VARCHAR(150) NOT NULL,
    nome_fantasia VARCHAR(150),
    cnpj_cpf VARCHAR(18) NOT NULL,
    inscricao_estadual VARCHAR(50),
    inscricao_municipal VARCHAR(50),
    tipo VARCHAR(1),
    fluxo_conta_id INTEGER,
    
    endereco_rua VARCHAR(150),
    endereco_numero VARCHAR(10),
    endereco_bairro VARCHAR(100),
    endereco_cidade VARCHAR(100),
    endereco_uf VARCHAR(2),
    endereco_cep VARCHAR(8),
    telefone VARCHAR(20),
    email VARCHAR(120),
    contrato_produto TEXT,
    
    aliquota_comissao_especifica NUMERIC(5,2),
    valor_repasse NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    vendedor_id INTEGER,
    
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_entidades_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_entidades_fluxo_conta 
      FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    CONSTRAINT fk_entidades_vendedor 
      FOREIGN KEY (vendedor_id) REFERENCES entidades(id),
    CONSTRAINT uq_entidades_empresa_cnpj UNIQUE (empresa_id, cnpj_cpf)
);

CREATE INDEX idx_entidades_empresa ON entidades(empresa_id);
CREATE INDEX idx_entidades_cnpj ON entidades(cnpj_cpf);
CREATE INDEX idx_entidades_tipo ON entidades(tipo);
CREATE INDEX idx_entidades_nome ON entidades(nome);

CREATE TRIGGER update_entidades_atualizado_em
    BEFORE UPDATE ON entidades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS lancamentos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    data_evento DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'aberto',
    
    entidade_id INTEGER NOT NULL,
    fluxo_conta_id INTEGER NOT NULL,
    conta_banco_id INTEGER NOT NULL,
    
    valor_real NUMERIC(15,2) NOT NULL,
    valor_pago NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    valor_imposto NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    valor_outros_custos NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    
    numero_documento VARCHAR(50),
    observacoes TEXT,
    
    referencia_banco VARCHAR(100),
    fonte VARCHAR(50) NOT NULL DEFAULT 'manual',
    
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_lanc_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_lanc_entidade 
      FOREIGN KEY (entidade_id) REFERENCES entidades(id),
    CONSTRAINT fk_lanc_fluxo 
      FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    CONSTRAINT fk_lanc_conta 
      FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id)
);

CREATE INDEX idx_lanc_empresa ON lancamentos(empresa_id);
CREATE INDEX idx_lanc_evento ON lancamentos(data_evento);
CREATE INDEX idx_lanc_vencimento ON lancamentos(data_vencimento);
CREATE INDEX idx_lanc_pagamento ON lancamentos(data_pagamento);
CREATE INDEX idx_lanc_documento ON lancamentos(numero_documento);
CREATE INDEX idx_lanc_referencia ON lancamentos(referencia_banco);
CREATE INDEX idx_lanc_empresa_datas ON lancamentos(empresa_id, data_evento);

CREATE TRIGGER update_lancamentos_atualizado_em
    BEFORE UPDATE ON lancamentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS fluxo_caixa_realizado (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    data DATE NOT NULL,
    fluxo_conta_id INTEGER NOT NULL,
    conta_banco_id INTEGER NOT NULL,
    saldo_anterior NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    valor_pago NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    valor_recebido NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    saldo_atual NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_fluxo_realizado_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_fluxo_realizado_fluxo 
      FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    CONSTRAINT fk_fluxo_realizado_conta 
      FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id)
);

CREATE INDEX idx_fluxo_realizado_empresa ON fluxo_caixa_realizado(empresa_id);
CREATE INDEX idx_fluxo_realizado_data ON fluxo_caixa_realizado(data);

CREATE TRIGGER update_fluxo_caixa_realizado_atualizado_em
    BEFORE UPDATE ON fluxo_caixa_realizado
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS fluxo_caixa_previsto (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    data DATE NOT NULL,
    fluxo_conta_id INTEGER NOT NULL,
    conta_banco_id INTEGER NOT NULL,
    saldo_anterior NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    valor_previsto_pago NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    valor_previsto_recebido NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    saldo_previsto NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_fluxo_previsto_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_fluxo_previsto_fluxo 
      FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    CONSTRAINT fk_fluxo_previsto_conta 
      FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id)
);

CREATE INDEX idx_fluxo_previsto_empresa ON fluxo_caixa_previsto(empresa_id);
CREATE INDEX idx_fluxo_previsto_data ON fluxo_caixa_previsto(data);

CREATE TRIGGER update_fluxo_caixa_previsto_atualizado_em
    BEFORE UPDATE ON fluxo_caixa_previsto
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS parametros_sistema (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    chave VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'string',
    descricao VARCHAR(255),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_parametros_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_parametro_chave UNIQUE (empresa_id, chave)
);

CREATE INDEX idx_parametro_empresa_chave ON parametros_sistema(empresa_id, chave);

CREATE TRIGGER update_parametros_sistema_atualizado_em
    BEFORE UPDATE ON parametros_sistema
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS comissoes (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    id_apuracao INTEGER NOT NULL,
    lancamento_id INTEGER NOT NULL,
    entidade_cliente_id INTEGER NOT NULL,
    entidade_vendedor_id INTEGER NOT NULL,
    
    dt_lancamento DATE NOT NULL,
    dt_vencimento DATE NOT NULL,
    dt_pagamento_recebimento DATE NOT NULL,
    
    vl_nota NUMERIC(15,2) NOT NULL,
    vl_imposto NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    vl_outros_custos NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    vl_repasse NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    vl_liquido NUMERIC(15,2) NOT NULL,
    aliquota_aplicada NUMERIC(5,2) NOT NULL,
    vl_comissao NUMERIC(15,2) NOT NULL,
    
    situacao VARCHAR(20) NOT NULL DEFAULT 'ativo',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_comissoes_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_comissoes_lancamento 
      FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_comissoes_cliente 
      FOREIGN KEY (entidade_cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_comissoes_vendedor 
      FOREIGN KEY (entidade_vendedor_id) REFERENCES entidades(id),
    CONSTRAINT uq_comissao_unica UNIQUE (lancamento_id, entidade_cliente_id, entidade_vendedor_id, situacao)
);

CREATE INDEX idx_comissoes_empresa ON comissoes(empresa_id);
CREATE INDEX idx_comissoes_lancamento_data ON comissoes(dt_lancamento);
CREATE INDEX idx_comissoes_vencimento ON comissoes(dt_vencimento);
CREATE INDEX idx_comissoes_pagamento ON comissoes(dt_pagamento_recebimento);
CREATE INDEX idx_comissoes_lancamento ON comissoes(lancamento_id);
CREATE INDEX idx_comissoes_cliente ON comissoes(entidade_cliente_id);
CREATE INDEX idx_comissoes_vendedor ON comissoes(entidade_vendedor_id);
CREATE INDEX idx_comissoes_apuracao ON comissoes(empresa_id, id_apuracao);
CREATE INDEX idx_comissoes_empresa_lancamento ON comissoes(empresa_id, lancamento_id, entidade_cliente_id, entidade_vendedor_id);

CREATE TRIGGER update_comissoes_atualizado_em
    BEFORE UPDATE ON comissoes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS importacao_nfse (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    chave_nota VARCHAR(60) NOT NULL,
    numero_nota VARCHAR(30) NOT NULL,
    data_emissao DATE NOT NULL,
    cnpj_tomador VARCHAR(20) NOT NULL,
    
    entidade_id INTEGER,
    lancamento_id INTEGER,
    
    valor_bruto NUMERIC(15,2) NOT NULL,
    valor_impostos NUMERIC(15,2),
    descricao_servico TEXT,
    
    status_importacao VARCHAR(20) NOT NULL DEFAULT 'sucesso',
    mensagem_erro VARCHAR(255),
    data_importacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    endereco_rua VARCHAR(150),
    endereco_numero VARCHAR(10),
    endereco_bairro VARCHAR(100),
    endereco_cidade VARCHAR(100),
    endereco_uf VARCHAR(2),
    endereco_cep VARCHAR(8),
    telefone VARCHAR(20),
    email VARCHAR(120),
    contrato_produto TEXT,
    
    aliquota_iss NUMERIC(5,2),
    aliquota_comissao_especifica NUMERIC(5,2),
    valor_repasse NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    entidade_vendedor_padrao_id INTEGER,
    
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_nfse_grupo_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_nfse_entidade 
      FOREIGN KEY (entidade_id) REFERENCES entidades(id),
    CONSTRAINT fk_nfse_lancamento 
      FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id) ON DELETE CASCADE,
    CONSTRAINT fk_nfse_vendedor_padrao 
      FOREIGN KEY (entidade_vendedor_padrao_id) REFERENCES entidades(id),
    CONSTRAINT uq_nfse_empresa_chave UNIQUE (empresa_id, chave_nota)
);

CREATE INDEX idx_nfse_empresa ON importacao_nfse(empresa_id);
CREATE INDEX idx_nfse_chave ON importacao_nfse(chave_nota);
CREATE INDEX idx_nfse_data_emissao ON importacao_nfse(data_emissao);
CREATE INDEX idx_nfse_entidade ON importacao_nfse(entidade_id);
CREATE INDEX idx_nfse_lancamento ON importacao_nfse(lancamento_id);

CREATE TRIGGER update_importacao_nfse_atualizado_em
    BEFORE UPDATE ON importacao_nfse
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Continua no próximo arquivo devido ao tamanho
-- Verificar: criar_banco_comercial_postgresql_part2.sql
