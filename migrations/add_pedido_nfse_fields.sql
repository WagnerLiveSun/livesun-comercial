-- Migration: Adicionar campos para integração de pedido com NF-e/NFS-e
-- Data: 2026-08-05

-- Adicionar campos em pedidos_venda
ALTER TABLE pedidos_venda 
ADD COLUMN documento_nfse_id INT NULL,
ADD COLUMN documento_nfe_id INT NULL;

-- Adicionar campos em pedidos_venda_itens
ALTER TABLE pedidos_venda_itens 
ADD COLUMN documento_item_id INT NULL,
ADD COLUMN tipo_documento VARCHAR(10) NULL;

-- Adicionar campos em documentos_venda
ALTER TABLE documentos_venda 
ADD COLUMN pedido_id INT NULL,
ADD COLUMN origem_tipo VARCHAR(10) NULL;

-- Adicionar campo em nfse_nacional_emissoes
ALTER TABLE nfse_nacional_emissoes 
ADD COLUMN pedido_id INT NULL;
