-- Script para criar tabelas de importação de XML de NF-e
-- Execute este script no banco de dados Hostinger via phpMyAdmin ou pgAdmin

-- Tabela: compra_nf_xml_import
CREATE TABLE IF NOT EXISTS compra_nf_xml_import (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    arquivo_xml TEXT NOT NULL,
    dados_cabecalho JSON NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fornecedor_id INTEGER,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (fornecedor_id) REFERENCES entidades(id)
);

-- Tabela: compra_nf_xml_item
CREATE TABLE IF NOT EXISTS compra_nf_xml_item (
    id SERIAL PRIMARY KEY,
    xml_import_id INTEGER NOT NULL,
    produto_id INTEGER,
    descricao_livre TEXT,
    quantidade NUMERIC(10, 3) NOT NULL,
    valor_unitario NUMERIC(10, 2) NOT NULL,
    total_item NUMERIC(10, 2) NOT NULL,
    ncm VARCHAR(10),
    cfop VARCHAR(4),
    cst VARCHAR(3),
    csosn VARCHAR(3),
    dados_originais JSON NOT NULL,
    FOREIGN KEY (xml_import_id) REFERENCES compra_nf_xml_import(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

-- Índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_xml_import_empresa ON compra_nf_xml_import(empresa_id);
CREATE INDEX IF NOT EXISTS idx_xml_import_usuario ON compra_nf_xml_import(usuario_id);
CREATE INDEX IF NOT EXISTS idx_xml_import_status ON compra_nf_xml_import(status);
CREATE INDEX IF NOT EXISTS idx_xml_import_fornecedor ON compra_nf_xml_import(fornecedor_id);
CREATE INDEX IF NOT EXISTS idx_xml_item_import ON compra_nf_xml_item(xml_import_id);
CREATE INDEX IF NOT EXISTS idx_xml_item_produto ON compra_nf_xml_item(produto_id);

-- Comentários
COMMENT ON TABLE compra_nf_xml_import IS 'Armazena importações de XML de NF-e pendentes de validação';
COMMENT ON TABLE compra_nf_xml_item IS 'Armazena itens de importações de XML de NF-e';
