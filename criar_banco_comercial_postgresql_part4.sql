-- =====================================================================
-- LiveSun Comercial - Parte 4: PDV / CAIXA (PostgreSQL)
-- =====================================================================
-- Este arquivo deve ser executado após criar_banco_comercial_postgresql_part3.sql
-- =====================================================================

-- =========================
-- 9) PDV / CAIXA
-- =========================
CREATE TABLE IF NOT EXISTS pdv_sessoes (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    filial_id INTEGER,
    user_id INTEGER NOT NULL,
    numero VARCHAR(20) NOT NULL,
    pdv_nome VARCHAR(50) DEFAULT 'PDV Principal',
    data_abertura TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_fechamento TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'aberto',
    valor_abertura NUMERIC(15,2) DEFAULT 0.00,
    valor_vendas NUMERIC(15,2) DEFAULT 0.00,
    valor_sangria NUMERIC(15,2) DEFAULT 0.00,
    valor_suprimento NUMERIC(15,2) DEFAULT 0.00,
    valor_fechamento NUMERIC(15,2),
    observacoes TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pdv_sessao_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_pdv_sessao_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_pdv_sessao_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_pdv_empresa_status ON pdv_sessoes(empresa_id, status);
CREATE INDEX idx_pdv_usuario ON pdv_sessoes(user_id);
CREATE INDEX idx_pdv_data_abertura ON pdv_sessoes(data_abertura);

CREATE TRIGGER update_pdv_sessoes_atualizado_em
    BEFORE UPDATE ON pdv_sessoes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS pdv_vendas (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    filial_id INTEGER,
    sessao_id INTEGER NOT NULL,
    numero VARCHAR(30) NOT NULL,
    cliente_id INTEGER,
    data_venda TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'em_andamento',
    subtotal NUMERIC(15,2) DEFAULT 0.00,
    valor_desconto NUMERIC(15,2) DEFAULT 0.00,
    valor_total NUMERIC(15,2) NOT NULL,
    valor_dinheiro NUMERIC(15,2) DEFAULT 0.00,
    valor_cartao_credito NUMERIC(15,2) DEFAULT 0.00,
    valor_cartao_debito NUMERIC(15,2) DEFAULT 0.00,
    valor_pix NUMERIC(15,2) DEFAULT 0.00,
    valor_boleto NUMERIC(15,2) DEFAULT 0.00,
    valor_outros NUMERIC(15,2) DEFAULT 0.00,
    valor_recebido NUMERIC(15,2) DEFAULT 0.00,
    valor_troco NUMERIC(15,2) DEFAULT 0.00,
    chave_cupom VARCHAR(50),
    numero_cupom VARCHAR(20),
    situacao_cupom VARCHAR(20) DEFAULT 'pendente',
    observacoes TEXT,
    documento_venda_id INTEGER,
    criado_por_user_id INTEGER,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pdv_venda_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_pdv_venda_filial FOREIGN KEY (filial_id) REFERENCES filiais(id),
    CONSTRAINT fk_pdv_venda_sessao FOREIGN KEY (sessao_id) REFERENCES pdv_sessoes(id),
    CONSTRAINT fk_pdv_venda_cliente FOREIGN KEY (cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_pdv_venda_documento FOREIGN KEY (documento_venda_id) REFERENCES documentos_venda(id),
    CONSTRAINT fk_pdv_venda_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_pdv_venda_empresa_data ON pdv_vendas(empresa_id, data_venda);
CREATE INDEX idx_pdv_venda_sessao ON pdv_vendas(sessao_id);
CREATE INDEX idx_pdv_venda_cliente ON pdv_vendas(cliente_id);
CREATE INDEX idx_pdv_venda_numero ON pdv_vendas(numero);
CREATE INDEX idx_pdv_venda_status ON pdv_vendas(status);

CREATE TRIGGER update_pdv_vendas_atualizado_em
    BEFORE UPDATE ON pdv_vendas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS pdv_itens (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    venda_id INTEGER NOT NULL,
    sequencia INTEGER NOT NULL DEFAULT 1,
    tipo_item VARCHAR(1) NOT NULL,
    produto_id INTEGER,
    servico_id INTEGER,
    codigo VARCHAR(50),
    descricao VARCHAR(200) NOT NULL,
    quantidade NUMERIC(15,3) NOT NULL,
    valor_unitario NUMERIC(15,4) NOT NULL,
    valor_desconto NUMERIC(15,4) DEFAULT 0.0000,
    percentual_desconto NUMERIC(5,2) DEFAULT 0.00,
    valor_total NUMERIC(15,2) NOT NULL,
    codigo_barras VARCHAR(60),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pdv_item_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_pdv_item_venda FOREIGN KEY (venda_id) REFERENCES pdv_vendas(id) ON DELETE CASCADE,
    CONSTRAINT fk_pdv_item_produto FOREIGN KEY (produto_id) REFERENCES produtos(id),
    CONSTRAINT fk_pdv_item_servico FOREIGN KEY (servico_id) REFERENCES servicos(id)
);

CREATE INDEX idx_pdv_item_empresa ON pdv_itens(empresa_id);
CREATE INDEX idx_pdv_item_venda ON pdv_itens(venda_id);
CREATE INDEX idx_pdv_item_produto ON pdv_itens(produto_id);
CREATE INDEX idx_pdv_item_servico ON pdv_itens(servico_id);

CREATE TRIGGER update_pdv_itens_atualizado_em
    BEFORE UPDATE ON pdv_itens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Continua no próximo arquivo
