-- SCRIPT DE ATUALIZAÇÃO DO BANCO DE DADOS - LIVESUN COMERCIAL
-- Módulo: Locação de Roupas e Fantasias
-- Compatibilidade: MySQL / MariaDB

-- 1. ADICIONAR CAMPOS DE ATIVIDADES NA TABELA EMPRESA
ALTER TABLE empresa ADD COLUMN IF NOT EXISTS atividade_comercial BOOLEAN DEFAULT FALSE;
ALTER TABLE empresa ADD COLUMN IF NOT EXISTS atividade_servicos BOOLEAN DEFAULT FALSE;
ALTER TABLE empresa ADD COLUMN IF NOT EXISTS atividade_financeiro BOOLEAN DEFAULT FALSE;
ALTER TABLE empresa ADD COLUMN IF NOT EXISTS atividade_locacao BOOLEAN DEFAULT FALSE;

-- 2. CRIAR TABELAS DO MÓDULO DE LOCAÇÃO

-- Tabelas de Acervo
CREATE TABLE IF NOT EXISTS locacao_peca (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    codigo_interno VARCHAR(50) NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    categoria VARCHAR(100),
    tema VARCHAR(100),
    tamanho VARCHAR(20),
    cor VARCHAR(50),
    tecido VARCHAR(100),
    marca VARCHAR(100),
    valor_aquisicao DECIMAL(10, 2),
    valor_reposicao DECIMAL(10, 2),
    preco_aluguel_diario DECIMAL(10, 2),
    preco_venda DECIMAL(10, 2),
    estado_fisico VARCHAR(50),
    observacoes TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_peca_empresa (empresa_id),
    INDEX idx_peca_codigo (codigo_interno)
);

CREATE TABLE IF NOT EXISTS locacao_kit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    codigo_interno VARCHAR(50) NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    preco_aluguel_diario DECIMAL(10, 2),
    ativo BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_kit_empresa (empresa_id)
);

CREATE TABLE IF NOT EXISTS locacao_kit_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kit_id INT NOT NULL,
    peca_id INT NOT NULL,
    quantidade INT DEFAULT 1,
    FOREIGN KEY (kit_id) REFERENCES locacao_kit(id) ON DELETE CASCADE,
    FOREIGN KEY (peca_id) REFERENCES locacao_peca(id)
);

-- Tabelas Comerciais
CREATE TABLE IF NOT EXISTS locacao_orcamento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    numero VARCHAR(20) NOT NULL,
    cliente_id INT NOT NULL,
    data_emissao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_retirada_prevista DATETIME NOT NULL,
    data_devolucao_prevista DATETIME NOT NULL,
    valor_aluguel DECIMAL(10, 2) DEFAULT 0,
    valor_sinal DECIMAL(10, 2) DEFAULT 0,
    valor_caucao DECIMAL(10, 2) DEFAULT 0,
    valor_total DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'rascunho',
    observacoes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_orc_empresa (empresa_id),
    INDEX idx_orc_cliente (cliente_id)
);

CREATE TABLE IF NOT EXISTS locacao_orcamento_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orcamento_id INT NOT NULL,
    tipo_item CHAR(1), -- 'P' para Peça, 'K' para Kit
    peca_id INT,
    kit_id INT,
    descricao VARCHAR(255),
    quantidade INT DEFAULT 1,
    valor_unitario DECIMAL(10, 2),
    valor_total DECIMAL(10, 2),
    FOREIGN KEY (orcamento_id) REFERENCES locacao_orcamento(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS locacao_contrato (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    orcamento_id INT,
    numero VARCHAR(20) NOT NULL,
    cliente_id INT NOT NULL,
    data_contrato DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_retirada DATETIME NOT NULL,
    data_devolucao DATETIME NOT NULL,
    valor_aluguel DECIMAL(10, 2),
    valor_sinal DECIMAL(10, 2),
    valor_caucao DECIMAL(10, 2),
    valor_total DECIMAL(10, 2),
    multa_atraso_diaria DECIMAL(10, 2),
    multa_avaria_percentual DECIMAL(5, 2),
    multa_perda_percentual DECIMAL(5, 2),
    status VARCHAR(50) DEFAULT 'assinado',
    condicoes_gerais TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_cont_empresa (empresa_id),
    INDEX idx_cont_cliente (cliente_id)
);

-- Tabelas Operacionais
CREATE TABLE IF NOT EXISTS locacao_retirada (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    contrato_id INT NOT NULL,
    data_retirada DATETIME DEFAULT CURRENT_TIMESTAMP,
    responsavel_retirada VARCHAR(100),
    modo_retirada VARCHAR(50), -- 'balcao', 'entrega'
    observacoes TEXT,
    status VARCHAR(50) DEFAULT 'concluido',
    FOREIGN KEY (contrato_id) REFERENCES locacao_contrato(id)
);

CREATE TABLE IF NOT EXISTS locacao_devolucao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    contrato_id INT NOT NULL,
    data_devolucao DATETIME DEFAULT CURRENT_TIMESTAMP,
    responsavel_devolucao VARCHAR(100),
    tipo_devolucao VARCHAR(50), -- 'total', 'parcial'
    dias_atraso INT DEFAULT 0,
    multa_atraso DECIMAL(10, 2) DEFAULT 0,
    observacoes TEXT,
    status VARCHAR(50) DEFAULT 'pendente_inspecao',
    FOREIGN KEY (contrato_id) REFERENCES locacao_contrato(id)
);

CREATE TABLE IF NOT EXISTS locacao_inspecao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    devolucao_id INT NOT NULL,
    peca_id INT NOT NULL,
    classificacao VARCHAR(50), -- 'perfeito', 'sujo', 'avariado', 'faltante', 'perdido'
    valor_total_cobranca DECIMAL(10, 2) DEFAULT 0,
    observacoes TEXT,
    FOREIGN KEY (devolucao_id) REFERENCES locacao_devolucao(id)
);

-- Tabelas de Disponibilidade e Parâmetros
CREATE TABLE IF NOT EXISTS locacao_disponibilidade (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    peca_id INT NOT NULL,
    data_inicio DATETIME NOT NULL,
    data_fim DATETIME NOT NULL,
    tipo_bloqueio VARCHAR(50), -- 'reserva', 'locacao', 'manutencao', 'indisponivel'
    referencia_id INT, -- ID do contrato, reserva ou manutenção
    observacoes TEXT,
    INDEX idx_disp_peca_datas (peca_id, data_inicio, data_fim)
);

CREATE TABLE IF NOT EXISTS locacao_parametro (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    percentual_sinal DECIMAL(5, 2) DEFAULT 30.00,
    percentual_caucao DECIMAL(5, 2) DEFAULT 20.00,
    multa_atraso_diaria_valor DECIMAL(10, 2) DEFAULT 50.00,
    multa_atraso_diaria_percentual DECIMAL(5, 2) DEFAULT 10.00,
    multa_avaria_percentual DECIMAL(5, 2) DEFAULT 50.00,
    multa_perda_percentual DECIMAL(5, 2) DEFAULT 100.00,
    valor_limpeza_padrao DECIMAL(10, 2) DEFAULT 25.00,
    valor_reparo_padrao DECIMAL(10, 2) DEFAULT 50.00,
    dias_buffer_retirada INT DEFAULT 1,
    dias_buffer_devolucao INT DEFAULT 1,
    UNIQUE (empresa_id)
);

-- Tabela de Auditoria
CREATE TABLE IF NOT EXISTS locacao_auditoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    user_id INT,
    acao VARCHAR(100) NOT NULL,
    entidade VARCHAR(100),
    entidade_id INT,
    dados_anteriores JSON,
    dados_novos JSON,
    data_acao DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    INDEX idx_auditoria_empresa (empresa_id)
);

-- Tabelas Financeiras Adicionais
CREATE TABLE IF NOT EXISTS locacao_titulo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    contrato_id INT NOT NULL,
    tipo_titulo VARCHAR(50), -- 'sinal', 'caucao', 'saldo', 'multa', 'avaria'
    numero VARCHAR(50),
    valor_original DECIMAL(10, 2),
    data_vencimento DATE,
    status VARCHAR(50) DEFAULT 'aberto',
    lancamento_id INT, -- Referência ao lançamento no módulo financeiro base
    FOREIGN KEY (contrato_id) REFERENCES locacao_contrato(id)
);

CREATE TABLE IF NOT EXISTS locacao_faturamento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    contrato_id INT,
    cliente_id INT,
    data_faturamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    valor_aluguel DECIMAL(10, 2),
    valor_multa DECIMAL(10, 2) DEFAULT 0,
    valor_avaria DECIMAL(10, 2) DEFAULT 0,
    valor_total DECIMAL(10, 2),
    INDEX idx_fat_empresa (empresa_id)
);

-- FINAL DO SCRIPT
