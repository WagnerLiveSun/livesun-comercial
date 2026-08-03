-- MIGRAÇÃO: adicionar campos de cancelamento à tabela nfse_nacional_emissoes

ALTER TABLE nfse_nacional_emissoes 
ADD COLUMN protocolo_cancelamento VARCHAR(80) NULL AFTER protocolo,
ADD COLUMN motivo_cancelamento TEXT NULL AFTER protocolo_cancelamento,
ADD COLUMN cancelado_em DATETIME NULL AFTER motivo_cancelamento,
ADD COLUMN cancelado_por_id INT NULL AFTER cancelado_em,
ADD COLUMN payload_cancelamento LONGTEXT NULL AFTER cancelado_por_id,
ADD COLUMN tomador_endereco VARCHAR(255) NULL AFTER payload_cancelamento,
ADD COLUMN regime_tributacao VARCHAR(10) NULL AFTER tomador_endereco,
ADD COLUMN codigo_tributacao_nacional VARCHAR(10) NULL AFTER regime_tributacao,
ADD COLUMN codigo_tributacao_municipal VARCHAR(10) NULL AFTER codigo_tributacao_nacional,
ADD COLUMN local_prestacao VARCHAR(10) NULL AFTER codigo_tributacao_municipal,
ADD INDEX idx_nfse_emissao_cancelado_por (cancelado_por_id),
ADD CONSTRAINT fk_nfse_emissao_cancelado_por FOREIGN KEY (cancelado_por_id) REFERENCES users(id);
