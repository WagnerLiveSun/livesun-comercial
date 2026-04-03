-- Script de migração para tabelas de comissão
-- Execute este script no seu banco de dados MySQL para criar as estruturas necessárias

-- ============================================
-- 1. Adicionar campos à tabela de lançamentos
-- ============================================

-- Adicionar campos de imposto e outros custos (se não existirem)
-- ALTER TABLE lancamentos 
-- ADD COLUMN valor_imposto DECIMAL(15, 2) DEFAULT 0.00 AFTER valor_pago,
-- ADD COLUMN valor_outros_custos DECIMAL(15, 2) DEFAULT 0.00 AFTER valor_imposto;

-- ============================================
-- 2. Adicionar campos à tabela de entidades
-- ============================================

-- Adicionar campos de comissão (se não existirem)
-- ALTER TABLE entidades 
-- ADD COLUMN aliquota_comissao_especifica DECIMAL(5, 2) AFTER contrato_produto,
-- ADD COLUMN valor_repasse DECIMAL(10, 2) DEFAULT 0.00 AFTER aliquota_comissao_especifica,
-- ADD COLUMN entidade_vendedor_padrao_id INT AFTER valor_repasse;

-- Criar índice e chave estrangeira para vendedor padrão
-- ALTER TABLE entidades 
-- ADD CONSTRAINT fk_entidade_vendedor_padrao 
-- FOREIGN KEY (entidade_vendedor_padrao_id) 
-- REFERENCES entidades(id);

-- ============================================
-- 3. Criar tabela de parâmetros de sistema
-- ============================================

CREATE TABLE IF NOT EXISTS parametros_sistema (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    chave VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    tipo VARCHAR(20) DEFAULT 'string',
    descricao VARCHAR(255),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_parametro_chave (empresa_id, chave),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    INDEX idx_parametro_chave (empresa_id, chave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. Criar tabela de comissões
-- ============================================

CREATE TABLE IF NOT EXISTS comissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    id_apuracao INT NOT NULL,
    lancamento_id INT NOT NULL,
    entidade_cliente_id INT NOT NULL,
    entidade_vendedor_id INT NOT NULL,
    
    -- Datas
    dt_lancamento DATE NOT NULL,
    dt_vencimento DATE NOT NULL,
    dt_pagamento_recebimento DATE NOT NULL,
    
    -- Valores
    vl_nota DECIMAL(15, 2) NOT NULL,
    vl_imposto DECIMAL(15, 2) DEFAULT 0.00,
    vl_outros_custos DECIMAL(15, 2) DEFAULT 0.00,
    vl_repasse DECIMAL(15, 2) DEFAULT 0.00,
    vl_liquido DECIMAL(15, 2) NOT NULL,
    aliquota_aplicada DECIMAL(5, 2) NOT NULL,
    vl_comissao DECIMAL(15, 2) NOT NULL,
    
    -- Situação
    situacao VARCHAR(20) DEFAULT 'ativo',
    
    -- Metadados
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    FOREIGN KEY (entidade_cliente_id) REFERENCES entidades(id),
    FOREIGN KEY (entidade_vendedor_id) REFERENCES entidades(id),
    
    -- Índices
    INDEX idx_comissao_empresa (empresa_id),
    INDEX idx_comissao_apuracao (empresa_id, id_apuracao),
    INDEX idx_comissao_datas (dt_pagamento_recebimento),
    INDEX idx_comissao_lancamento (lancamento_id),
    INDEX idx_comissao_cliente (entidade_cliente_id),
    INDEX idx_comissao_vendedor (entidade_vendedor_id),
    UNIQUE INDEX idx_comissao_unica (lancamento_id, entidade_cliente_id, entidade_vendedor_id, situacao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. Inserir parâmetro padrão de comissão
-- ============================================

-- Inserir ou atualizar alíquota padrão para cada empresa
-- INSERT IGNORE INTO parametros_sistema (empresa_id, chave, valor, tipo, descricao)
-- SELECT id, 'aliquota_comissao_padrao', '5.00', 'numeric', 'Alíquota padrão de comissão sobre vendas'
-- FROM empresas;

-- ============================================
-- 6. Verificação de estrutura
-- ============================================

-- Consultar estrutura da tabela comissões
-- DESCRIBE comissoes;

-- Consultar parâmetros criados
-- SELECT * FROM parametros_sistema WHERE chave = 'aliquota_comissao_padrao';

-- ============================================
-- 7. Query de teste (após inserir dados)
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
