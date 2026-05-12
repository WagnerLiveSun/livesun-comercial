-- MIGRACAO 011: Compras NF manual e documentos nao fiscais

-- ============================================
-- 1) Compras NF manual (cabecalho)
-- ============================================
CREATE TABLE IF NOT EXISTS compras_nf_manual (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    filial_id INT NULL,
    fornecedor_id INT NOT NULL,
    lancamento_id INT NULL,
    numero_documento VARCHAR(50) NOT NULL,
    serie VARCHAR(10) NULL,
    data_emissao DATE NOT NULL,
    data_entrada DATE NOT NULL,
    valor_total DECIMAL(15,2) NOT NULL,
    observacoes TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'registrada',
    criado_por_user_id INT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_compra_empresa (empresa_id),
    INDEX idx_compra_fornecedor (fornecedor_id),
    INDEX idx_compra_numero (numero_documento),
    INDEX idx_compra_emissao (data_emissao),
    CONSTRAINT fk_compra_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_compra_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_compra_fornecedor FOREIGN KEY (fornecedor_id) REFERENCES entidades(id),
    CONSTRAINT fk_compra_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_compra_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2) Compras NF manual (itens)
-- ============================================
CREATE TABLE IF NOT EXISTS compras_nf_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    compra_id INT NOT NULL,
    produto_id INT NULL,
    descricao_livre VARCHAR(200) NULL,
    quantidade DECIMAL(15,3) NOT NULL,
    valor_unitario DECIMAL(15,2) NOT NULL,
    total_item DECIMAL(15,2) NOT NULL,
    ncm VARCHAR(10) NULL,
    cfop VARCHAR(10) NULL,
    cst VARCHAR(5) NULL,
    csosn VARCHAR(5) NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_compra_item_empresa (empresa_id),
    INDEX idx_compra_item_compra (compra_id),
    CONSTRAINT fk_compra_item_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_compra_item_compra FOREIGN KEY (compra_id) REFERENCES compras_nf_manual(id) ON DELETE CASCADE,
    CONSTRAINT fk_compra_item_produto FOREIGN KEY (produto_id) REFERENCES produtos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3) Documentos nao fiscais de venda (cabecalho)
-- ============================================
CREATE TABLE IF NOT EXISTS documentos_venda (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    filial_id INT NULL,
    cliente_id INT NOT NULL,
    lancamento_id INT NULL,
    numero_documento VARCHAR(50) NOT NULL,
    data_emissao DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE NULL,
    valor_total DECIMAL(15,2) NOT NULL,
    observacoes TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'emitido',
    criado_por_user_id INT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doc_empresa (empresa_id),
    INDEX idx_doc_cliente (cliente_id),
    INDEX idx_doc_numero (numero_documento),
    INDEX idx_doc_emissao (data_emissao),
    CONSTRAINT fk_doc_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_doc_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_doc_cliente FOREIGN KEY (cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_doc_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_doc_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4) Documentos nao fiscais de venda (itens)
-- ============================================
CREATE TABLE IF NOT EXISTS documentos_venda_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    documento_id INT NOT NULL,
    tipo_item VARCHAR(1) NOT NULL,
    produto_id INT NULL,
    servico_id INT NULL,
    descricao VARCHAR(200) NULL,
    quantidade DECIMAL(15,3) NOT NULL,
    valor_unitario DECIMAL(15,2) NOT NULL,
    total_item DECIMAL(15,2) NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doc_item_empresa (empresa_id),
    INDEX idx_doc_item_documento (documento_id),
    CONSTRAINT fk_doc_item_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_doc_item_documento FOREIGN KEY (documento_id) REFERENCES documentos_venda(id) ON DELETE CASCADE,
    CONSTRAINT fk_doc_item_produto FOREIGN KEY (produto_id) REFERENCES produtos(id),
    CONSTRAINT fk_doc_item_servico FOREIGN KEY (servico_id) REFERENCES servicos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
