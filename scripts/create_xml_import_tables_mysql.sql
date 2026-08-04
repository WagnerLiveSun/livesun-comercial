-- Script para criar tabelas de importação de XML de NF-e (MySQL)
-- Execute este script no banco de dados Hostinger via phpMyAdmin

-- Tabela: compras_nf_xml_import
CREATE TABLE IF NOT EXISTS compras_nf_xml_import (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    fornecedor_id INT,
    xml_original TEXT NOT NULL,
    dados_parseados JSON NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente',
    criado_por_user_id INT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (fornecedor_id) REFERENCES entidades(id),
    FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: compras_nf_xml_itens
CREATE TABLE IF NOT EXISTS compras_nf_xml_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    import_id INT NOT NULL,
    produto_id INT,
    dados_item JSON NOT NULL,
    confirmado TINYINT(1) DEFAULT 0,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (import_id) REFERENCES compras_nf_xml_import(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índices para melhorar performance
CREATE INDEX idx_xml_import_empresa ON compras_nf_xml_import(empresa_id);
CREATE INDEX idx_xml_import_fornecedor ON compras_nf_xml_import(fornecedor_id);
CREATE INDEX idx_xml_import_status ON compras_nf_xml_import(status);
CREATE INDEX idx_xml_import_usuario ON compras_nf_xml_import(criado_por_user_id);
CREATE INDEX idx_xml_item_empresa ON compras_nf_xml_itens(empresa_id);
CREATE INDEX idx_xml_item_import ON compras_nf_xml_itens(import_id);
CREATE INDEX idx_xml_item_produto ON compras_nf_xml_itens(produto_id);
