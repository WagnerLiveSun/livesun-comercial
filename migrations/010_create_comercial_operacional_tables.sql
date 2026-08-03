-- MIGRACAO 010: Estruturas do modulo comercial operacional

-- ============================================
-- 1) Filiais
-- ============================================
CREATE TABLE IF NOT EXISTS filiais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    nome VARCHAR(150) NOT NULL,
    cnpj VARCHAR(18) NULL,
    endereco_rua VARCHAR(150) NULL,
    endereco_numero VARCHAR(10) NULL,
    endereco_bairro VARCHAR(100) NULL,
    endereco_cidade VARCHAR(100) NULL,
    endereco_uf VARCHAR(2) NULL,
    endereco_cep VARCHAR(8) NULL,
    ativo BOOLEAN NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_filial_empresa_codigo (empresa_id, codigo),
    INDEX idx_filial_empresa (empresa_id),
    INDEX idx_filial_codigo (codigo),
    CONSTRAINT fk_filial_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2) Produtos
-- ============================================
CREATE TABLE IF NOT EXISTS produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    filial_id INT NULL,
    codigo_interno VARCHAR(50) NOT NULL,
    descricao_resumida VARCHAR(200) NOT NULL,
    descricao_completa TEXT NULL,
    unidade_medida VARCHAR(10) NULL,
    codigo_barras VARCHAR(60) NULL,
    gtin VARCHAR(60) NULL,
    ncm VARCHAR(10) NULL,
    ex_tipi VARCHAR(5) NULL,
    cest VARCHAR(10) NULL,
    ipi_classe VARCHAR(10) NULL,
    origem_mercadoria VARCHAR(20) NULL,
    tipo_item VARCHAR(20) NULL,
    controla_estoque BOOLEAN NOT NULL DEFAULT 0,
    estoque_atual DECIMAL(15,3) NOT NULL DEFAULT 0.000,
    estoque_minimo DECIMAL(15,3) NOT NULL DEFAULT 0.000,
    ativo BOOLEAN NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_produto_empresa_codigo (empresa_id, codigo_interno),
    INDEX idx_produto_empresa (empresa_id),
    INDEX idx_produto_filial (filial_id),
    INDEX idx_produto_ncm (empresa_id, ncm),
    CONSTRAINT fk_produto_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_produto_filial FOREIGN KEY (filial_id) REFERENCES filiais(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3) Servicos
-- ============================================
CREATE TABLE IF NOT EXISTS servicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    filial_id INT NULL,
    codigo_interno VARCHAR(50) NOT NULL,
    descricao VARCHAR(200) NOT NULL,
    codigo_servico VARCHAR(20) NULL,
    nbs VARCHAR(20) NULL,
    natureza_servico VARCHAR(120) NULL,
    indicador_incidencia VARCHAR(30) NULL,
    ativo BOOLEAN NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_servico_empresa_codigo (empresa_id, codigo_interno),
    INDEX idx_servico_empresa (empresa_id),
    INDEX idx_servico_filial (filial_id),
    CONSTRAINT fk_servico_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_servico_filial FOREIGN KEY (filial_id) REFERENCES filiais(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4) Movimentos de estoque
-- ============================================
CREATE TABLE IF NOT EXISTS estoque_movimentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    filial_id INT NULL,
    produto_id INT NOT NULL,
    tipo_movimento VARCHAR(10) NOT NULL,
    quantidade DECIMAL(15,3) NOT NULL,
    valor_unitario DECIMAL(15,2) NULL,
    origem VARCHAR(20) NOT NULL DEFAULT 'manual',
    documento_ref VARCHAR(80) NULL,
    data_movimento DATE NOT NULL,
    criado_por_user_id INT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_estoque_empresa (empresa_id),
    INDEX idx_estoque_produto (produto_id),
    INDEX idx_estoque_data (data_movimento),
    INDEX idx_estoque_empresa_produto_data (empresa_id, produto_id, data_movimento),
    CONSTRAINT fk_estoque_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_estoque_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_estoque_produto FOREIGN KEY (produto_id) REFERENCES produtos(id),
    CONSTRAINT fk_estoque_user FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
