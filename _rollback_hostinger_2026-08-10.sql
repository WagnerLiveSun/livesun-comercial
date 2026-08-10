ALTER TABLE `documentos_venda` DROP COLUMN `origem_tipo`;
ALTER TABLE `documentos_venda` DROP COLUMN `pedido_id`;
ALTER TABLE `nfse_nacional_emissoes` DROP COLUMN `pedido_id`;
ALTER TABLE `pedidos_venda` DROP COLUMN `documento_nfe_id`;
ALTER TABLE `pedidos_venda` DROP COLUMN `documento_nfse_id`;
ALTER TABLE `pedidos_venda_itens` DROP COLUMN `documento_item_id`;
ALTER TABLE `pedidos_venda_itens` DROP COLUMN `tipo_documento`;
