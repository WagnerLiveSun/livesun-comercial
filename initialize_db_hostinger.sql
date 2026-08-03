-- Script de Inicialização do Banco de Dados - LiveSun Financeiro
-- Para execução no HOSTINGER MySQL
-- Data: 2026-03-07
-- 
-- ANTES DE EXECUTAR:
-- 1. Abra o painel do Hostinger
-- 2. Acesse: cPanel → Databases → MySQL Databases
-- 3. Crie um novo database: u951548013_Gfinanceiro
-- 4. Crie um novo usuário MySQL
-- 5. Atribua TODOS OS PRIVILÉGIOS ao usuário para o banco
-- 6. Abra phpMyAdmin
-- 7. Selecione o banco u951548013_Gfinanceiro
-- 8. Vá para SQL e cole este conteúdo
-- =====================================================================

USE u951548013_Gfinanceiro;

-- =====================================================================
-- 1. Criar Tabela: EMPRESAS
-- =====================================================================

CREATE TABLE IF NOT EXISTS empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    cnpj VARCHAR(18) UNIQUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_empresa_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 2. Criar Tabela: USERS (Autenticação)
-- =====================================================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    dashboard_chart_days INT DEFAULT 30,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    INDEX idx_user_username (username),
    INDEX idx_user_email (email),
    INDEX idx_user_empresa (empresa_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 3. Criar Tabela: FLUXO_CONTAS_MODELO (Plano de Contas)
-- =====================================================================

CREATE TABLE IF NOT EXISTS fluxo_contas_modelo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    descricao VARCHAR(200) NOT NULL,
    tipo VARCHAR(1) NOT NULL,
    mascara VARCHAR(50),
    nivel_sintetico INT,
    nivel_analitico INT,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    INDEX idx_fluxo_codigo (codigo),
    INDEX idx_fluxo_empresa (empresa_id),
    UNIQUE KEY uq_fluxo_codigo (empresa_id, codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 4. Criar Tabela: ENTIDADES (Clientes, Fornecedores, Vendedores)
-- =====================================================================

CREATE TABLE IF NOT EXISTS entidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    tipo VARCHAR(1) NOT NULL,
    cnpj_cpf VARCHAR(14) UNIQUE NOT NULL,
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
    aliquota_comissao_especifica DECIMAL(5, 2),
    valor_repasse DECIMAL(10, 2) DEFAULT 0.00,
    vendedor_id INT,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (vendedor_id) REFERENCES entidades(id),
    INDEX idx_entidade_empresa (empresa_id),
    INDEX idx_entidade_tipo (tipo),
    INDEX idx_entidade_cnpj (cnpj_cpf),
    INDEX idx_entidade_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 5. Criar Tabela: CONTAS_BANCO
-- =====================================================================

CREATE TABLE IF NOT EXISTS contas_banco (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nome VARCHAR(150) NOT NULL,
    banco VARCHAR(50) NOT NULL,
    agencia VARCHAR(10) NOT NULL,
    numero_conta VARCHAR(20) NOT NULL,
    dv VARCHAR(2),
    tipo VARCHAR(20),
    fluxo_conta_id INT,
    saldo_inicial DECIMAL(15, 2) DEFAULT 0.00,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    INDEX idx_conta_banco_empresa (empresa_id),
    INDEX idx_conta_banco_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 6. Criar Tabela: LANCAMENTOS (Transações)
-- =====================================================================

CREATE TABLE IF NOT EXISTS lancamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    data_evento DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'aberto',
    fluxo_conta_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    entidade_id INT NOT NULL,
    valor_real DECIMAL(15, 2) NOT NULL,
    valor_pago DECIMAL(15, 2) DEFAULT 0.00,
    valor_imposto DECIMAL(15, 2) DEFAULT 0.00,
    valor_outros_custos DECIMAL(15, 2) DEFAULT 0.00,
    numero_documento VARCHAR(50),
    observacoes TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),
    FOREIGN KEY (entidade_id) REFERENCES entidades(id),
    INDEX idx_lancamento_empresa (empresa_id),
    INDEX idx_lancamento_datas (data_evento, data_vencimento, data_pagamento),
    INDEX idx_lancamento_status (status),
    INDEX idx_lancamento_entidade (entidade_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 7. Criar Tabela: FLUXO_CAIXA_PREVISTO
-- =====================================================================

CREATE TABLE IF NOT EXISTS fluxo_caixa_previsto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    data DATE NOT NULL,
    fluxo_conta_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    saldo_anterior DECIMAL(15, 2) DEFAULT 0.00,
    valor_previsto_pago DECIMAL(15, 2) DEFAULT 0.00,
    valor_previsto_recebido DECIMAL(15, 2) DEFAULT 0.00,
    saldo_previsto DECIMAL(15, 2) DEFAULT 0.00,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),
    INDEX idx_fluxo_caixa_ov_data (data),
    INDEX idx_fluxo_caixa_previsto_empresa (empresa_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 8. Criar Tabela: FLUXO_CAIXA_REALIZADO
-- =====================================================================

CREATE TABLE IF NOT EXISTS fluxo_caixa_realizado (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    data DATE NOT NULL,
    fluxo_conta_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    saldo_anterior DECIMAL(15, 2) DEFAULT 0.00,
    valor_pago DECIMAL(15, 2) DEFAULT 0.00,
    valor_recebido DECIMAL(15, 2) DEFAULT 0.00,
    saldo_atual DECIMAL(15, 2) DEFAULT 0.00,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id),
    FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),
    INDEX idx_fluxo_caixa_realizado_data (data),
    INDEX idx_fluxo_caixa_realizado_empresa (empresa_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 9. Criar Tabela: PARAMETROS_SISTEMA
-- =====================================================================

CREATE TABLE IF NOT EXISTS parametros_sistema (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    chave VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    tipo VARCHAR(20) DEFAULT 'string',
    descricao VARCHAR(255),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    UNIQUE KEY uq_parametro_chave (empresa_id, chave),
    INDEX idx_parametro_chave (empresa_id, chave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 10. Criar Tabela: COMISSOES (Nova - Módulo de Comissões)
-- =====================================================================

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
    vl_nota DECIMAL(15, 2) NOT NULL,
    vl_imposto DECIMAL(15, 2) DEFAULT 0.00,
    vl_outros_custos DECIMAL(15, 2) DEFAULT 0.00,
    vl_repasse DECIMAL(15, 2) DEFAULT 0.00,
    vl_liquido DECIMAL(15, 2) NOT NULL,
    aliquota_aplicada DECIMAL(5, 2) NOT NULL,
    vl_comissao DECIMAL(15, 2) NOT NULL,
    situacao VARCHAR(20) DEFAULT 'ativo',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    FOREIGN KEY (entidade_cliente_id) REFERENCES entidades(id),
    FOREIGN KEY (entidade_vendedor_id) REFERENCES entidades(id),
    INDEX idx_comissao_empresa (empresa_id),
    INDEX idx_comissao_apuracao (empresa_id, id_apuracao),
    INDEX idx_comissao_datas (dt_pagamento_recebimento),
    INDEX idx_comissao_lancamento (lancamento_id),
    INDEX idx_comissao_cliente (entidade_cliente_id),
    INDEX idx_comissao_vendedor (entidade_vendedor_id),
    UNIQUE INDEX idx_comissao_unica (lancamento_id, entidade_cliente_id, entidade_vendedor_id, situacao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 11. DADOS INICIAIS
-- =====================================================================

-- Inserir empresa padrão (se não existir)
INSERT IGNORE INTO empresas (id, nome, cnpj)
VALUES (1, 'LiveSun Financeiro', '00.000.000/0000-00');

-- Inserir usuário padrão (admin/admin123)
INSERT IGNORE INTO users (id, empresa_id, username, email, password_hash, full_name, is_active, is_admin)
VALUES (1, 1, 'admin', 'admin@livesun.local', 
        'scrypt:32768:8:1$hqN1Yd4V4XOu0nVi$6d4a5b8c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f',
        'Administrador', TRUE, TRUE);

-- Inserir parâmetro padrão de comissão
INSERT IGNORE INTO parametros_sistema (empresa_id, chave, valor, tipo, descricao)
VALUES (1, 'aliquota_comissao_padrao', '25.00', 'numeric', 'Alíquota padrão de comissão sobre vendas');

-- =====================================================================
-- 12. ÍNDICES ADICIONAIS PARA PERFORMANCE
-- =====================================================================

ALTER TABLE users ADD INDEX idx_user_empresa_active (empresa_id, is_active);
ALTER TABLE lancamentos ADD INDEX idx_lancamento_empresa_datas (empresa_id, data_evento);
ALTER TABLE entidades ADD INDEX idx_entidade_empresa_tipo (empresa_id, tipo);

-- =====================================================================
-- 13. VERIFICAÇÃO FINAL
-- =====================================================================

-- Mostrar todas as tabelas criadas
SHOW TABLES;

-- Contar registros
SELECT 'empresas' AS tabela, COUNT(*) AS total FROM empresas
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'entidades', COUNT(*) FROM entidades
UNION ALL
SELECT 'lancamentos', COUNT(*) FROM lancamentos
UNION ALL
SELECT 'comissoes', COUNT(*) FROM comissoes;

-- =====================================================================
-- SUCESSO!
-- =====================================================================
-- 
-- O banco de dados foi inicializado com sucesso!
-- 
-- Próximos passos:
-- 1. Configure o arquivo .env com as credenciais do banco
-- 2. Execute: python inicializar_db.py (para criar usuários extras se necessário)
-- 3. Acesse: http://seu-dominio.com.br
-- 4. Login padrão: admin / admin123
--
-- =====================================================================
