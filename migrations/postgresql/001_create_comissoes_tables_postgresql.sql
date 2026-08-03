-- Script de migração para tabelas de comissão - PostgreSQL
-- Execute este script no seu banco de dados PostgreSQL para criar as estruturas necessárias

-- ============================================
-- 1. Criar função para atualização automática de timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- 2. Criar tabela de parâmetros de sistema
-- ============================================

CREATE TABLE IF NOT EXISTS parametros_sistema (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    chave VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    tipo VARCHAR(20) DEFAULT 'string',
    descricao VARCHAR(255),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_parametro_chave UNIQUE (empresa_id, chave),
    CONSTRAINT fk_parametros_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

CREATE INDEX idx_parametro_chave ON parametros_sistema(empresa_id, chave);

CREATE TRIGGER update_parametros_sistema_atualizado_em
    BEFORE UPDATE ON parametros_sistema
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 3. Criar tabela de comissões
-- ============================================

CREATE TABLE IF NOT EXISTS comissoes (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    id_apuracao INTEGER NOT NULL,
    lancamento_id INTEGER NOT NULL,
    entidade_cliente_id INTEGER NOT NULL,
    entidade_vendedor_id INTEGER NOT NULL,
    
    -- Datas
    dt_lancamento DATE NOT NULL,
    dt_vencimento DATE NOT NULL,
    dt_pagamento_recebimento DATE NOT NULL,
    
    -- Valores
    vl_nota NUMERIC(15, 2) NOT NULL,
    vl_imposto NUMERIC(15, 2) DEFAULT 0.00,
    vl_outros_custos NUMERIC(15, 2) DEFAULT 0.00,
    vl_repasse NUMERIC(15, 2) DEFAULT 0.00,
    vl_liquido NUMERIC(15, 2) NOT NULL,
    aliquota_aplicada NUMERIC(5, 2) NOT NULL,
    vl_comissao NUMERIC(15, 2) NOT NULL,
    
    -- Situação
    situacao VARCHAR(20) DEFAULT 'ativo',
    
    -- Metadados
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT fk_comissoes_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_comissoes_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_comissoes_cliente FOREIGN KEY (entidade_cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_comissoes_vendedor FOREIGN KEY (entidade_vendedor_id) REFERENCES entidades(id),
    CONSTRAINT uq_comissao_unica UNIQUE (lancamento_id, entidade_cliente_id, entidade_vendedor_id, situacao)
);

-- Índices
CREATE INDEX idx_comissao_empresa ON comissoes(empresa_id);
CREATE INDEX idx_comissao_apuracao ON comissoes(empresa_id, id_apuracao);
CREATE INDEX idx_comissao_datas ON comissoes(dt_pagamento_recebimento);
CREATE INDEX idx_comissao_lancamento ON comissoes(lancamento_id);
CREATE INDEX idx_comissao_cliente ON comissoes(entidade_cliente_id);
CREATE INDEX idx_comissao_vendedor ON comissoes(entidade_vendedor_id);

CREATE TRIGGER update_comissoes_atualizado_em
    BEFORE UPDATE ON comissoes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. Verificação de estrutura
-- ============================================

-- Consultar estrutura da tabela comissões
-- \d comissoes

-- Consultar parâmetros criados
-- SELECT * FROM parametros_sistema WHERE chave = 'aliquota_comissao_padrao';

-- ============================================
-- 5. Query de teste (após inserir dados)
-- ============================================

-- Listar comissões de um período
-- SELECT 
--     c.id,
--     c.id_apuracao,
--     c.dt_pagamento_recebimento,
--     ec.nome AS cliente,
--     ev.nome AS vendedor,
--     c.vl_nota,
--     c.vl_repasse,
--     c.vl_liquido,
--     c.aliquota_aplicada,
--     c.vl_comissao
-- FROM comissoes c
-- JOIN entidades ec ON c.entidade_cliente_id = ec.id
-- JOIN entidades ev ON c.entidade_vendedor_id = ev.id
-- WHERE c.empresa_id = 1
--   AND c.dt_pagamento_recebimento BETWEEN '2026-01-01' AND '2026-02-28'
-- ORDER BY c.dt_pagamento_recebimento DESC;

-- Resumo por vendedor
-- SELECT 
--     ev.nome AS vendedor,
--     COUNT(*) AS quantidade_notas,
--     SUM(c.vl_nota) AS total_notas,
--     SUM(c.vl_liquido) AS total_liquido,
--     SUM(c.vl_comissao) AS total_comissao
-- FROM comissoes c
-- JOIN entidades ev ON c.entidade_vendedor_id = ev.id
-- WHERE c.empresa_id = 1
--   AND c.dt_pagamento_recebimento BETWEEN '2026-01-01' AND '2026-02-28'
-- GROUP BY ev.id, ev.nome
-- ORDER BY total_comissao DESC;
