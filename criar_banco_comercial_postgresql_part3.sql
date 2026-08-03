-- =====================================================================
-- LiveSun Comercial - Parte 3: Tabelas de Preço, Orçamentos e Pedidos (PostgreSQL)
-- =====================================================================
-- Este arquivo deve ser executado após criar_banco_comercial_postgresql_part2.sql
-- =====================================================================

-- =========================
-- 6) TABELAS DE PREÇO
-- =========================
CREATE TABLE IF NOT EXISTS tabelas_preco (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_inicio DATE NOT NULL,
    data_fim DATE,
    tipo VARCHAR(20) NOT NULL DEFAULT 'venda',
    markup_padrao NUMERIC(5,2) DEFAULT 0.00,
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_tabela_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_tabela_empresa_codigo UNIQUE (empresa_id, codigo)
);

CREATE INDEX idx_tabela_empresa ON tabelas_preco(empresa_id);
CREATE INDEX idx_tabela_codigo ON tabelas_preco(codigo);
CREATE INDEX idx_tabela_tipo ON tabelas_preco(tipo);
CREATE INDEX idx_tabela_ativo ON tabelas_preco(ativo);

CREATE TRIGGER update_tabelas_preco_atualizado_em
    BEFORE UPDATE ON tabelas_preco
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS tabelas_preco_itens (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    tabela_preco_id INTEGER NOT NULL,
    produto_id INTEGER,
    servico_id INTEGER,
    preco_custo NUMERIC(15,4) DEFAULT 0.0000,
    preco_venda NUMERIC(15,4) NOT NULL,
    markup NUMERIC(5,2) DEFAULT 0.00,
    desconto_maximo NUMERIC(5,2) DEFAULT 0.00,
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_tabela_item_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_tabela_item_tabela FOREIGN KEY (tabela_preco_id) REFERENCES tabelas_preco(id) ON DELETE CASCADE,
    CONSTRAINT fk_tabela_item_produto FOREIGN KEY (produto_id) REFERENCES produtos(id),
    CONSTRAINT fk_tabela_item_servico FOREIGN KEY (servico_id) REFERENCES servicos(id),
    CONSTRAINT uq_tabela_item_produto_servico UNIQUE (tabela_preco_id, produto_id, servico_id)
);

CREATE INDEX idx_tabela_item_empresa ON tabelas_preco_itens(empresa_id);
CREATE INDEX idx_tabela_item_tabela ON tabelas_preco_itens(tabela_preco_id);
CREATE INDEX idx_tabela_item_produto ON tabelas_preco_itens(produto_id);
CREATE INDEX idx_tabela_item_servico ON tabelas_preco_itens(servico_id);

CREATE TRIGGER update_tabelas_preco_itens_atualizado_em
    BEFORE UPDATE ON tabelas_preco_itens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================
-- 7) ORÇAMENTOS
-- =========================
CREATE TABLE IF NOT EXISTS orcamentos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    filial_id INTEGER,
    numero VARCHAR(30) NOT NULL,
    serie VARCHAR(10) DEFAULT '1',
    cliente_id INTEGER NOT NULL,
    vendedor_id INTEGER,
    data_emissao DATE NOT NULL,
    data_validade DATE NOT NULL,
    data_aprovacao DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'emitido',
    tabela_preco_id INTEGER,
    valor_produtos NUMERIC(15,2) DEFAULT 0.00,
    valor_servicos NUMERIC(15,2) DEFAULT 0.00,
    valor_desconto NUMERIC(15,2) DEFAULT 0.00,
    valor_total NUMERIC(15,2) NOT NULL,
    observacoes TEXT,
    observacoes_internas TEXT,
    pedido_id INTEGER,
    criado_por_user_id INTEGER,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_orcamento_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_orcamento_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_orcamento_cliente FOREIGN KEY (cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_orcamento_vendedor FOREIGN KEY (vendedor_id) REFERENCES entidades(id),
    CONSTRAINT fk_orcamento_tabela FOREIGN KEY (tabela_preco_id) REFERENCES tabelas_preco(id),
    CONSTRAINT fk_orcamento_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_orcamento_empresa_status ON orcamentos(empresa_id, status);
CREATE INDEX idx_orcamento_cliente ON orcamentos(cliente_id);
CREATE INDEX idx_orcamento_data ON orcamentos(data_emissao);
CREATE INDEX idx_orcamento_numero ON orcamentos(numero);

CREATE TRIGGER update_orcamentos_atualizado_em
    BEFORE UPDATE ON orcamentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS orcamentos_itens (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    orcamento_id INTEGER NOT NULL,
    tipo_item VARCHAR(1) NOT NULL,
    produto_id INTEGER,
    servico_id INTEGER,
    descricao VARCHAR(200) NOT NULL,
    quantidade NUMERIC(15,3) NOT NULL,
    valor_unitario NUMERIC(15,4) NOT NULL,
    valor_desconto NUMERIC(15,4) DEFAULT 0.0000,
    percentual_desconto NUMERIC(5,2) DEFAULT 0.00,
    valor_total NUMERIC(15,2) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_orcamento_item_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_orcamento_item_orcamento FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE,
    CONSTRAINT fk_orcamento_item_produto FOREIGN KEY (produto_id) REFERENCES produtos(id),
    CONSTRAINT fk_orcamento_item_servico FOREIGN KEY (servico_id) REFERENCES servicos(id)
);

CREATE INDEX idx_orcamento_item_empresa ON orcamentos_itens(empresa_id);
CREATE INDEX idx_orcamento_item_orcamento ON orcamentos_itens(orcamento_id);
CREATE INDEX idx_orcamento_item_produto ON orcamentos_itens(produto_id);
CREATE INDEX idx_orcamento_item_servico ON orcamentos_itens(servico_id);

CREATE TRIGGER update_orcamentos_itens_atualizado_em
    BEFORE UPDATE ON orcamentos_itens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================
-- 8) PEDIDOS DE VENDA
-- =========================
CREATE TABLE IF NOT EXISTS pedidos_venda (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    filial_id INTEGER,
    numero VARCHAR(30) NOT NULL,
    serie VARCHAR(10) DEFAULT '1',
    orcamento_id INTEGER,
    cliente_id INTEGER NOT NULL,
    vendedor_id INTEGER,
    data_emissao DATE NOT NULL,
    data_entrega DATE,
    data_faturamento DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'aprovado',
    valor_produtos NUMERIC(15,2) DEFAULT 0.00,
    valor_servicos NUMERIC(15,2) DEFAULT 0.00,
    valor_desconto NUMERIC(15,2) DEFAULT 0.00,
    valor_frete NUMERIC(15,2) DEFAULT 0.00,
    valor_total NUMERIC(15,2) NOT NULL,
    observacoes TEXT,
    observacoes_faturamento TEXT,
    documento_venda_id INTEGER,
    criado_por_user_id INTEGER,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pedido_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_pedido_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_pedido_orcamento FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id),
    CONSTRAINT fk_pedido_cliente FOREIGN KEY (cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_pedido_vendedor FOREIGN KEY (vendedor_id) REFERENCES entidades(id),
    CONSTRAINT fk_pedido_documento FOREIGN KEY (documento_venda_id) REFERENCES documentos_venda(id),
    CONSTRAINT fk_pedido_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_pedido_empresa_status ON pedidos_venda(empresa_id, status);
CREATE INDEX idx_pedido_cliente ON pedidos_venda(cliente_id);
CREATE INDEX idx_pedido_orcamento ON pedidos_venda(orcamento_id);
CREATE INDEX idx_pedido_data ON pedidos_venda(data_emissao);
CREATE INDEX idx_pedido_numero ON pedidos_venda(numero);

CREATE TRIGGER update_pedidos_venda_atualizado_em
    BEFORE UPDATE ON pedidos_venda
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS pedidos_venda_itens (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    pedido_id INTEGER NOT NULL,
    orcamento_item_id INTEGER,
    tipo_item VARCHAR(1) NOT NULL,
    produto_id INTEGER,
    servico_id INTEGER,
    descricao VARCHAR(200) NOT NULL,
    quantidade NUMERIC(15,3) NOT NULL,
    quantidade_atendida NUMERIC(15,3) DEFAULT 0.000,
    valor_unitario NUMERIC(15,4) NOT NULL,
    valor_desconto NUMERIC(15,4) DEFAULT 0.0000,
    percentual_desconto NUMERIC(5,2) DEFAULT 0.00,
    valor_total NUMERIC(15,2) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pedido_item_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_pedido_item_pedido FOREIGN KEY (pedido_id) REFERENCES pedidos_venda(id) ON DELETE CASCADE,
    CONSTRAINT fk_pedido_item_produto FOREIGN KEY (produto_id) REFERENCES produtos(id),
    CONSTRAINT fk_pedido_item_servico FOREIGN KEY (servico_id) REFERENCES servicos(id)
);

CREATE INDEX idx_pedido_item_empresa ON pedidos_venda_itens(empresa_id);
CREATE INDEX idx_pedido_item_pedido ON pedidos_venda_itens(pedido_id);
CREATE INDEX idx_pedido_item_produto ON pedidos_venda_itens(produto_id);
CREATE INDEX idx_pedido_item_servico ON pedidos_venda_itens(servico_id);

CREATE TRIGGER update_pedidos_venda_itens_atualizado_em
    BEFORE UPDATE ON pedidos_venda_itens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Continua no próximo arquivo
