-- =====================================================================
-- LiveSun Comercial - Parte 2: Tabelas Operacionais e PDV (PostgreSQL)
-- =====================================================================
-- Este arquivo deve ser executado após criar_banco_comercial_postgresql.sql
-- =====================================================================

-- =========================
-- 4) CONCILIAÇÃO BANCÁRIA
-- =========================
CREATE TABLE IF NOT EXISTS conciliacao_bancaria (
    id BIGSERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    conta_banco_id INTEGER NOT NULL,
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'aberta',
    observacoes TEXT,
    criado_por_user_id INTEGER,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_conciliacao_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_conciliacao_conta 
      FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),
    CONSTRAINT fk_conciliacao_usuario 
      FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_conciliacao_empresa ON conciliacao_bancaria(empresa_id);
CREATE INDEX idx_conciliacao_conta ON conciliacao_bancaria(conta_banco_id);
CREATE INDEX idx_conciliacao_periodo ON conciliacao_bancaria(periodo_inicio, periodo_fim);
CREATE INDEX idx_conciliacao_status ON conciliacao_bancaria(status);

CREATE TRIGGER update_conciliacao_bancaria_atualizado_em
    BEFORE UPDATE ON conciliacao_bancaria
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS conciliacao_item (
    id BIGSERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    conciliacao_id BIGINT NOT NULL,
    lancamento_id INTEGER,
    
    data_movimento DATE NOT NULL,
    descricao_extrato VARCHAR(255),
    referencia_banco VARCHAR(120),
    valor_extrato NUMERIC(15,2) NOT NULL,
    
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    motivo_divergencia VARCHAR(255),
    
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_conciliacao_item_empresa 
      FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_conciliacao_item_conciliacao 
      FOREIGN KEY (conciliacao_id) REFERENCES conciliacao_bancaria(id) ON DELETE CASCADE,
    CONSTRAINT fk_conciliacao_item_lancamento 
      FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id) ON DELETE SET NULL
);

CREATE INDEX idx_conciliacao_item_empresa ON conciliacao_item(empresa_id);
CREATE INDEX idx_conciliacao_item_conciliacao ON conciliacao_item(conciliacao_id);
CREATE INDEX idx_conciliacao_item_lancamento ON conciliacao_item(lancamento_id);
CREATE INDEX idx_conciliacao_item_data ON conciliacao_item(data_movimento);
CREATE INDEX idx_conciliacao_item_status ON conciliacao_item(status);
CREATE INDEX idx_conciliacao_item_referencia ON conciliacao_item(referencia_banco);

CREATE TRIGGER update_conciliacao_item_atualizado_em
    BEFORE UPDATE ON conciliacao_item
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================
-- 5) COMERCIAL OPERACIONAL
-- =========================
CREATE TABLE IF NOT EXISTS filiais (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    nome VARCHAR(150) NOT NULL,
    cnpj VARCHAR(18),
    endereco_rua VARCHAR(150),
    endereco_numero VARCHAR(10),
    endereco_bairro VARCHAR(100),
    endereco_cidade VARCHAR(100),
    endereco_uf VARCHAR(2),
    endereco_cep VARCHAR(8),
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_filial_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_filial_empresa_codigo UNIQUE (empresa_id, codigo)
);

CREATE INDEX idx_filial_empresa ON filiais(empresa_id);
CREATE INDEX idx_filial_codigo ON filiais(codigo);

CREATE TRIGGER update_filiais_atualizado_em
    BEFORE UPDATE ON filiais
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS produtos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    filial_id INTEGER,
    codigo_interno VARCHAR(50) NOT NULL,
    descricao_resumida VARCHAR(200) NOT NULL,
    descricao_completa TEXT,
    unidade_medida VARCHAR(10),
    codigo_barras VARCHAR(60),
    gtin VARCHAR(60),
    ncm VARCHAR(10),
    ex_tipi VARCHAR(5),
    cest VARCHAR(10),
    ipi_classe VARCHAR(10),
    origem_mercadoria VARCHAR(20),
    tipo_item VARCHAR(20),
    controla_estoque BOOLEAN NOT NULL DEFAULT false,
    estoque_atual NUMERIC(15,3) NOT NULL DEFAULT 0.000,
    estoque_minimo NUMERIC(15,3) NOT NULL DEFAULT 0.000,
    valor_venda_padrao NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    valor_custo NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_produto_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_produto_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT uq_produto_empresa_codigo UNIQUE (empresa_id, codigo_interno)
);

CREATE INDEX idx_produto_empresa ON produtos(empresa_id);
CREATE INDEX idx_produto_filial ON produtos(filial_id);
CREATE INDEX idx_produto_ncm ON produtos(empresa_id, ncm);

CREATE TRIGGER update_produtos_atualizado_em
    BEFORE UPDATE ON produtos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS servicos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    filial_id INTEGER,
    codigo_interno VARCHAR(50) NOT NULL,
    descricao VARCHAR(200) NOT NULL,
    codigo_servico VARCHAR(20),
    nbs VARCHAR(20),
    natureza_servico VARCHAR(120),
    indicador_incidencia VARCHAR(30),
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_servico_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_servico_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT uq_servico_empresa_codigo UNIQUE (empresa_id, codigo_interno)
);

CREATE INDEX idx_servico_empresa ON servicos(empresa_id);
CREATE INDEX idx_servico_filial ON servicos(filial_id);

CREATE TRIGGER update_servicos_atualizado_em
    BEFORE UPDATE ON servicos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS estoque_movimentos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    filial_id INTEGER,
    produto_id INTEGER NOT NULL,
    tipo_movimento VARCHAR(10) NOT NULL,
    quantidade NUMERIC(15,3) NOT NULL,
    valor_unitario NUMERIC(15,2),
    origem VARCHAR(20) NOT NULL DEFAULT 'manual',
    documento_ref VARCHAR(80),
    data_movimento DATE NOT NULL,
    criado_por_user_id INTEGER,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_estoque_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_estoque_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_estoque_produto FOREIGN KEY (produto_id) REFERENCES produtos(id),
    CONSTRAINT fk_estoque_user FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_estoque_empresa ON estoque_movimentos(empresa_id);
CREATE INDEX idx_estoque_filial ON estoque_movimentos(filial_id);
CREATE INDEX idx_estoque_produto ON estoque_movimentos(produto_id);
CREATE INDEX idx_estoque_data ON estoque_movimentos(data_movimento);
CREATE INDEX idx_estoque_empresa_produto_data ON estoque_movimentos(empresa_id, produto_id, data_movimento);

CREATE TRIGGER update_estoque_movimentos_atualizado_em
    BEFORE UPDATE ON estoque_movimentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS compras_nf_manual (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    filial_id INTEGER,
    fornecedor_id INTEGER NOT NULL,
    lancamento_id INTEGER,
    numero_documento VARCHAR(50) NOT NULL,
    serie VARCHAR(10),
    data_emissao DATE NOT NULL,
    data_entrada DATE NOT NULL,
    valor_total NUMERIC(15,2) NOT NULL,
    observacoes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'registrada',
    criado_por_user_id INTEGER,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_compra_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_compra_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_compra_fornecedor FOREIGN KEY (fornecedor_id) REFERENCES entidades(id),
    CONSTRAINT fk_compra_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_compra_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_compra_empresa ON compras_nf_manual(empresa_id);
CREATE INDEX idx_compra_filial ON compras_nf_manual(filial_id);
CREATE INDEX idx_compra_fornecedor ON compras_nf_manual(fornecedor_id);
CREATE INDEX idx_compra_lancamento ON compras_nf_manual(lancamento_id);
CREATE INDEX idx_compra_numero ON compras_nf_manual(numero_documento);
CREATE INDEX idx_compra_emissao ON compras_nf_manual(data_emissao);
CREATE INDEX idx_compra_entrada ON compras_nf_manual(data_entrada);

CREATE TRIGGER update_compras_nf_manual_atualizado_em
    BEFORE UPDATE ON compras_nf_manual
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS compras_nf_itens (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    compra_id INTEGER NOT NULL,
    produto_id INTEGER,
    descricao_livre VARCHAR(200),
    quantidade NUMERIC(15,3) NOT NULL,
    valor_unitario NUMERIC(15,2) NOT NULL,
    total_item NUMERIC(15,2) NOT NULL,
    ncm VARCHAR(10),
    cfop VARCHAR(10),
    cst VARCHAR(5),
    csosn VARCHAR(5),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_compra_item_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_compra_item_compra FOREIGN KEY (compra_id) REFERENCES compras_nf_manual(id) ON DELETE CASCADE,
    CONSTRAINT fk_compra_item_produto FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

CREATE INDEX idx_compra_item_empresa ON compras_nf_itens(empresa_id);
CREATE INDEX idx_compra_item_compra ON compras_nf_itens(compra_id);
CREATE INDEX idx_compra_item_produto ON compras_nf_itens(produto_id);

CREATE TRIGGER update_compras_nf_itens_atualizado_em
    BEFORE UPDATE ON compras_nf_itens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS compras_nf_lancamentos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    compra_id INTEGER NOT NULL,
    lancamento_id INTEGER NOT NULL,
    parcela_numero INTEGER NOT NULL,
    parcela_total INTEGER NOT NULL,
    valor_parcela NUMERIC(15,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_compra_lanc_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_compra_lanc_compra FOREIGN KEY (compra_id) REFERENCES compras_nf_manual(id) ON DELETE CASCADE,
    CONSTRAINT fk_compra_lanc_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT uq_compra_parcela UNIQUE (compra_id, parcela_numero)
);

CREATE INDEX idx_compra_lanc_empresa ON compras_nf_lancamentos(empresa_id);
CREATE INDEX idx_compra_lanc_compra ON compras_nf_lancamentos(compra_id);
CREATE INDEX idx_compra_lanc_venc ON compras_nf_lancamentos(data_vencimento);

CREATE TRIGGER update_compras_nf_lancamentos_atualizado_em
    BEFORE UPDATE ON compras_nf_lancamentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS documentos_venda (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    filial_id INTEGER,
    cliente_id INTEGER NOT NULL,
    lancamento_id INTEGER,
    numero_documento VARCHAR(50) NOT NULL,
    data_emissao DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    valor_total NUMERIC(15,2) NOT NULL,
    observacoes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'emitido',
    criado_por_user_id INTEGER,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_doc_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_doc_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_doc_cliente FOREIGN KEY (cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_doc_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_doc_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_doc_empresa ON documentos_venda(empresa_id);
CREATE INDEX idx_doc_filial ON documentos_venda(filial_id);
CREATE INDEX idx_doc_cliente ON documentos_venda(cliente_id);
CREATE INDEX idx_doc_lancamento ON documentos_venda(lancamento_id);
CREATE INDEX idx_doc_numero ON documentos_venda(numero_documento);
CREATE INDEX idx_doc_emissao ON documentos_venda(data_emissao);
CREATE INDEX idx_doc_vencimento ON documentos_venda(data_vencimento);

CREATE TRIGGER update_documentos_venda_atualizado_em
    BEFORE UPDATE ON documentos_venda
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS documentos_venda_itens (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    documento_id INTEGER NOT NULL,
    tipo_item VARCHAR(1) NOT NULL,
    produto_id INTEGER,
    servico_id INTEGER,
    descricao VARCHAR(200),
    quantidade NUMERIC(15,3) NOT NULL,
    valor_unitario NUMERIC(15,2) NOT NULL,
    total_item NUMERIC(15,2) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_doc_item_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_doc_item_documento FOREIGN KEY (documento_id) REFERENCES documentos_venda(id) ON DELETE CASCADE,
    CONSTRAINT fk_doc_item_produto FOREIGN KEY (produto_id) REFERENCES produtos(id),
    CONSTRAINT fk_doc_item_servico FOREIGN KEY (servico_id) REFERENCES servicos(id)
);

CREATE INDEX idx_doc_item_empresa ON documentos_venda_itens(empresa_id);
CREATE INDEX idx_doc_item_documento ON documentos_venda_itens(documento_id);
CREATE INDEX idx_doc_item_produto ON documentos_venda_itens(produto_id);
CREATE INDEX idx_doc_item_servico ON documentos_venda_itens(servico_id);

CREATE TRIGGER update_documentos_venda_itens_atualizado_em
    BEFORE UPDATE ON documentos_venda_itens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Continua no próximo arquivo
