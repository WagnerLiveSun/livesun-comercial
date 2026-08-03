-- MIGRAÇÃO: Adiciona coluna entidade_id à tabela importacao_nfse
ALTER TABLE importacao_nfse
ADD COLUMN entidade_id INT NULL,
ADD INDEX idx_importacao_nfse_entidade_id (entidade_id),
ADD CONSTRAINT fk_importacao_nfse_entidade_id FOREIGN KEY (entidade_id) REFERENCES entidades(id);
