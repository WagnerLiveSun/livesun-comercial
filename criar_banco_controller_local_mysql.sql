-- =====================================================================
-- LiveSun Controller - Setup local MySQL (DBeaver, sem Docker)
-- =====================================================================
-- Uso:
-- 1) Conecte no MySQL local pelo DBeaver com usuário administrador (ex: root)
-- 2) Execute este script completo
-- 3) Configure o .env para usar DB_NAME=controller e DB_USER=controller_owner
--
-- Compatível com MySQL 8+
-- =====================================================================

-- DATABASE / SCHEMA
CREATE DATABASE IF NOT EXISTS controller
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- OWNER (usuário dono do schema, local)
CREATE USER IF NOT EXISTS 'controller_owner'@'localhost' IDENTIFIED BY 'Controller@2026!';
GRANT ALL PRIVILEGES ON controller.* TO 'controller_owner'@'localhost';
FLUSH PRIVILEGES;

USE controller;

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- =====================================================================
-- TABELAS BASE DO CONTROLLER
-- =====================================================================

CREATE TABLE IF NOT EXISTS empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    cnpj VARCHAR(18) UNIQUE,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    username VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    dashboard_chart_days INT NOT NULL DEFAULT 30,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_users_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_users_empresa_username UNIQUE (empresa_id, username),
    CONSTRAINT uq_users_email UNIQUE (email),

    INDEX idx_users_empresa_id (empresa_id),
    INDEX idx_users_username (username),
    INDEX idx_users_role (role),
    INDEX idx_users_empresa_active (empresa_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fluxo_contas_modelo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    descricao VARCHAR(200) NOT NULL,
    tipo VARCHAR(1) NOT NULL,
    mascara VARCHAR(50) NULL,
    nivel_sintetico INT NULL,
    nivel_analitico INT NULL,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_fluxo_contas_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_fluxo_empresa_codigo UNIQUE (empresa_id, codigo),

    INDEX idx_fluxo_empresa_id (empresa_id),
    INDEX idx_fluxo_codigo (codigo),
    INDEX idx_fluxo_tipo (tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS entidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nome VARCHAR(150) NOT NULL,
    cnpj_cpf VARCHAR(18) NOT NULL,
    tipo VARCHAR(1) NULL,
    fluxo_conta_id INT NULL,
    aliquota_comissao_especifica DECIMAL(5,2) NULL,
    valor_repasse DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    vendedor_id INT NULL,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_entidades_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_entidades_fluxo_conta FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    CONSTRAINT fk_entidades_vendedor FOREIGN KEY (vendedor_id) REFERENCES entidades(id),
    CONSTRAINT uq_entidades_empresa_cnpj UNIQUE (empresa_id, cnpj_cpf),

    INDEX idx_entidades_empresa_id (empresa_id),
    INDEX idx_entidades_cnpj_cpf (cnpj_cpf),
    INDEX idx_entidades_tipo (tipo),
    INDEX idx_entidades_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS contas_banco (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nome VARCHAR(150) NOT NULL,
    banco VARCHAR(50) NOT NULL,
    agencia VARCHAR(10) NOT NULL,
    numero_conta VARCHAR(20) NOT NULL,
    dv VARCHAR(2) NULL,
    tipo VARCHAR(20) NULL,
    fluxo_conta_id INT NULL,
    saldo_inicial DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    is_principal TINYINT(1) NOT NULL DEFAULT 0,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_contas_banco_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_contas_banco_fluxo_conta FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),

    INDEX idx_contas_banco_empresa_id (empresa_id),
    INDEX idx_contas_banco_nome (nome),
    INDEX idx_contas_banco_principal (is_principal)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS lancamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    data_evento DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'aberto',

    entidade_id INT NOT NULL,
    fluxo_conta_id INT NOT NULL,
    conta_banco_id INT NOT NULL,

    valor_real DECIMAL(15,2) NOT NULL,
    valor_pago DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    valor_imposto DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    valor_outros_custos DECIMAL(15,2) NOT NULL DEFAULT 0.00,

    numero_documento VARCHAR(50) NULL,
    observacoes TEXT NULL,

    referencia_banco VARCHAR(100) NULL,
    fonte VARCHAR(50) NOT NULL DEFAULT 'manual',

    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_lancamentos_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_lancamentos_entidade FOREIGN KEY (entidade_id) REFERENCES entidades(id),
    CONSTRAINT fk_lancamentos_fluxo_conta FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    CONSTRAINT fk_lancamentos_conta_banco FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),

    INDEX idx_lancamentos_empresa_id (empresa_id),
    INDEX idx_lancamentos_status (status),
    INDEX idx_lancamentos_data_evento (data_evento),
    INDEX idx_lancamentos_data_vencimento (data_vencimento),
    INDEX idx_lancamentos_data_pagamento (data_pagamento),
    INDEX idx_lancamentos_numero_documento (numero_documento),
    INDEX idx_lancamentos_referencia_banco (referencia_banco),
    INDEX idx_lancamentos_empresa_datas (empresa_id, data_evento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fluxo_caixa_realizado (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    data DATE NOT NULL,
    fluxo_conta_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    saldo_anterior DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    valor_pago DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    valor_recebido DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    saldo_atual DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_fluxo_realizado_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_fluxo_realizado_fluxo_conta FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    CONSTRAINT fk_fluxo_realizado_conta_banco FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),

    INDEX idx_fluxo_realizado_empresa (empresa_id),
    INDEX idx_fluxo_realizado_data (data)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fluxo_caixa_previsto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    data DATE NOT NULL,
    fluxo_conta_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    saldo_anterior DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    valor_previsto_pago DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    valor_previsto_recebido DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    saldo_previsto DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_fluxo_previsto_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_fluxo_previsto_fluxo_conta FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    CONSTRAINT fk_fluxo_previsto_conta_banco FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),

    INDEX idx_fluxo_previsto_empresa (empresa_id),
    INDEX idx_fluxo_previsto_data (data)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS parametros_sistema (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    chave VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'string',
    descricao VARCHAR(255) NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_parametros_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_parametro_chave UNIQUE (empresa_id, chave),

    INDEX idx_parametro_empresa_chave (empresa_id, chave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS comissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    id_apuracao INT NOT NULL,
    lancamento_id INT NOT NULL,
    entidade_cliente_id INT NOT NULL,
    entidade_vendedor_id INT NOT NULL,

    dt_lancamento DATE NOT NULL,
    dt_vencimento DATE NOT NULL,
    dt_pagamento_recebimento DATE NOT NULL,

    vl_nota DECIMAL(15,2) NOT NULL,
    vl_imposto DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    vl_outros_custos DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    vl_repasse DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    vl_liquido DECIMAL(15,2) NOT NULL,
    aliquota_aplicada DECIMAL(5,2) NOT NULL,
    vl_comissao DECIMAL(15,2) NOT NULL,

    situacao VARCHAR(20) NOT NULL DEFAULT 'ativo',
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_comissoes_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_comissoes_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_comissoes_cliente FOREIGN KEY (entidade_cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_comissoes_vendedor FOREIGN KEY (entidade_vendedor_id) REFERENCES entidades(id),

    INDEX idx_comissoes_empresa (empresa_id),
    INDEX idx_comissoes_apuracao (empresa_id, id_apuracao),
    INDEX idx_comissoes_pagamento (dt_pagamento_recebimento),
    INDEX idx_comissoes_lancamento (lancamento_id),
    INDEX idx_comissoes_cliente (entidade_cliente_id),
    INDEX idx_comissoes_vendedor (entidade_vendedor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS importacao_nfse (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    chave_nota VARCHAR(60) NOT NULL,
    numero_nota VARCHAR(30) NOT NULL,
    data_emissao DATE NOT NULL,
    cnpj_tomador VARCHAR(20) NOT NULL,

    entidade_id INT NULL,
    lancamento_id INT NULL,

    valor_bruto DECIMAL(15,2) NOT NULL,
    valor_impostos DECIMAL(15,2) NULL,
    descricao_servico VARCHAR(255) NULL,

    status_importacao VARCHAR(20) NOT NULL DEFAULT 'sucesso',
    mensagem_erro VARCHAR(255) NULL,
    data_importacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    endereco_rua VARCHAR(150) NULL,
    endereco_numero VARCHAR(10) NULL,
    endereco_bairro VARCHAR(100) NULL,
    endereco_cidade VARCHAR(100) NULL,
    endereco_uf VARCHAR(2) NULL,
    endereco_cep VARCHAR(8) NULL,
    telefone VARCHAR(20) NULL,
    email VARCHAR(120) NULL,
    contrato_produto TEXT NULL,

    aliquota_iss DECIMAL(5,2) NULL,
    aliquota_comissao_especifica DECIMAL(5,2) NULL,
    valor_repasse DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    entidade_vendedor_padrao_id INT NULL,

    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_nfse_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_nfse_entidade FOREIGN KEY (entidade_id) REFERENCES entidades(id),
    CONSTRAINT fk_nfse_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id) ON DELETE CASCADE,
    CONSTRAINT fk_nfse_vendedor_padrao FOREIGN KEY (entidade_vendedor_padrao_id) REFERENCES entidades(id),

    CONSTRAINT uq_nfse_empresa_chave UNIQUE (empresa_id, chave_nota),
    INDEX idx_nfse_empresa (empresa_id),
    INDEX idx_nfse_data_emissao (data_emissao),
    INDEX idx_nfse_entidade (entidade_id),
    INDEX idx_nfse_lancamento (lancamento_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- TABELAS DE CONCILIAÇÃO BANCÁRIA
-- =====================================================================

CREATE TABLE IF NOT EXISTS conciliacao_bancaria (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'aberta',
    observacoes TEXT NULL,
    criado_por_user_id INT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_conciliacao_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_conciliacao_conta FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),
    CONSTRAINT fk_conciliacao_usuario FOREIGN KEY (criado_por_user_id) REFERENCES users(id),

    INDEX idx_conciliacao_empresa (empresa_id),
    INDEX idx_conciliacao_conta (conta_banco_id),
    INDEX idx_conciliacao_periodo (periodo_inicio, periodo_fim),
    INDEX idx_conciliacao_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS conciliacao_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    conciliacao_id BIGINT NOT NULL,
    lancamento_id INT NULL,

    data_movimento DATE NOT NULL,
    descricao_extrato VARCHAR(255) NULL,
    referencia_banco VARCHAR(120) NULL,
    valor_extrato DECIMAL(15,2) NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    motivo_divergencia VARCHAR(255) NULL,

    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_conciliacao_item_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_conciliacao_item_conciliacao FOREIGN KEY (conciliacao_id) REFERENCES conciliacao_bancaria(id) ON DELETE CASCADE,
    CONSTRAINT fk_conciliacao_item_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id) ON DELETE SET NULL,

    INDEX idx_conciliacao_item_empresa (empresa_id),
    INDEX idx_conciliacao_item_conciliacao (conciliacao_id),
    INDEX idx_conciliacao_item_lancamento (lancamento_id),
    INDEX idx_conciliacao_item_status (status),
    INDEX idx_conciliacao_item_referencia (referencia_banco)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- TABELAS DE CONTROLE DE ACESSO (RBAC + AUDITORIA)
-- =====================================================================

CREATE TABLE IF NOT EXISTS rbac_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nome VARCHAR(50) NOT NULL,
    descricao VARCHAR(255) NULL,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_rbac_roles_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_rbac_roles_empresa_nome UNIQUE (empresa_id, nome),

    INDEX idx_rbac_roles_empresa (empresa_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS rbac_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(100) NOT NULL,
    descricao VARCHAR(255) NULL,

    CONSTRAINT uq_rbac_permissions_codigo UNIQUE (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS rbac_user_roles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rbac_user_roles_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_rbac_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rbac_user_roles_role FOREIGN KEY (role_id) REFERENCES rbac_roles(id) ON DELETE CASCADE,

    CONSTRAINT uq_rbac_user_role UNIQUE (user_id, role_id),
    INDEX idx_rbac_user_roles_empresa (empresa_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS rbac_role_permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    permission_id INT NOT NULL,

    CONSTRAINT fk_rbac_role_permissions_role FOREIGN KEY (role_id) REFERENCES rbac_roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_rbac_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES rbac_permissions(id) ON DELETE CASCADE,

    CONSTRAINT uq_rbac_role_permission UNIQUE (role_id, permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS auditoria_eventos (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NULL,
    user_id INT NULL,
    modulo VARCHAR(60) NOT NULL,
    acao VARCHAR(60) NOT NULL,
    entidade VARCHAR(60) NULL,
    entidade_id VARCHAR(60) NULL,
    detalhes JSON NULL,
    ip_origem VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_auditoria_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE SET NULL,
    CONSTRAINT fk_auditoria_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,

    INDEX idx_auditoria_empresa (empresa_id),
    INDEX idx_auditoria_user (user_id),
    INDEX idx_auditoria_modulo_acao (modulo, acao),
    INDEX idx_auditoria_criado_em (criado_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO rbac_permissions (codigo, descricao) VALUES
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
('users.manage', 'Gerenciar usuários e permissões');

SHOW TABLES;
