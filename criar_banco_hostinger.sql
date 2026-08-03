-- Script para criar estrutura multi-tenant no Hostinger

CREATE TABLE empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    cnpj VARCHAR(18) UNIQUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    dashboard_chart_days INT DEFAULT 30,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

CREATE TABLE entidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    tipo VARCHAR(1) NOT NULL,
    cnpj_cpf VARCHAR(14) NOT NULL UNIQUE,
    inscricao_estadual VARCHAR(20),
    inscricao_municipal VARCHAR(20),
    nome VARCHAR(150) NOT NULL,
    nome_fantasia VARCHAR(150),
    endereco_rua VARCHAR(150),
    endereco_numero VARCHAR(10),
    endereco_bairro VARCHAR(100),
    endereco_cidade VARCHAR(100),
    endereco_uf VARCHAR(2),
    endereco_cep VARCHAR(8),
    telefone VARCHAR(20),
    email VARCHAR(120),
    contrato_produto TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

CREATE TABLE fluxo_contas_modelo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    descricao VARCHAR(200) NOT NULL,
    tipo VARCHAR(1) NOT NULL,
    mascara VARCHAR(50),
    nivel_sintetico INT,
    nivel_analitico INT,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

CREATE TABLE contas_banco (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nome VARCHAR(150) NOT NULL,
    banco VARCHAR(50) NOT NULL,
    agencia VARCHAR(10) NOT NULL,
    numero_conta VARCHAR(20) NOT NULL,
    dv VARCHAR(2),
    tipo VARCHAR(20),
    fluxo_conta_id INT,
    saldo_inicial DECIMAL(15,2) DEFAULT 0.00,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id)
);

CREATE TABLE lancamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    data_evento DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'aberto',
    fluxo_conta_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    entidade_id INT NOT NULL,
    valor_real DECIMAL(15,2) NOT NULL,
    valor_pago DECIMAL(15,2) DEFAULT 0.00,
    numero_documento VARCHAR(50),
    observacoes TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),
    FOREIGN KEY (entidade_id) REFERENCES entidades(id)
);

CREATE TABLE fluxo_caixa_realizado (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    data DATE NOT NULL,
    fluxo_conta_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    saldo_anterior DECIMAL(15,2) DEFAULT 0.00,
    valor_pago DECIMAL(15,2) DEFAULT 0.00,
    valor_recebido DECIMAL(15,2) DEFAULT 0.00,
    saldo_atual DECIMAL(15,2) DEFAULT 0.00,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id)
);

CREATE TABLE fluxo_caixa_previsto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    data DATE NOT NULL,
    fluxo_conta_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    saldo_anterior DECIMAL(15,2) DEFAULT 0.00,
    valor_previsto_pago DECIMAL(15,2) DEFAULT 0.00,
    valor_previsto_recebido DECIMAL(15,2) DEFAULT 0.00,
    saldo_previsto DECIMAL(15,2) DEFAULT 0.00,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id)
);
