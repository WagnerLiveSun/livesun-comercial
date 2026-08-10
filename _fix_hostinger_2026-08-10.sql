ALTER TABLE `documentos_venda` ADD COLUMN `origem_tipo` VARCHAR(10) NULL;
ALTER TABLE `documentos_venda` ADD COLUMN `pedido_id` INTEGER NULL;
ALTER TABLE `nfse_nacional_emissoes` ADD COLUMN `pedido_id` INTEGER NULL;
ALTER TABLE `pedidos_venda` ADD COLUMN `documento_nfe_id` INTEGER NULL;
ALTER TABLE `pedidos_venda` ADD COLUMN `documento_nfse_id` INTEGER NULL;
ALTER TABLE `pedidos_venda_itens` ADD COLUMN `documento_item_id` INTEGER NULL;
ALTER TABLE `pedidos_venda_itens` ADD COLUMN `tipo_documento` VARCHAR(10) NULL;
