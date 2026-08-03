-- Migration: adiciona o código IBGE do município na tabela entidades

ALTER TABLE entidades
  ADD COLUMN codigo_municipio_ibge VARCHAR(7) NULL AFTER endereco_bairro,
  ADD INDEX idx_entidades_codigo_municipio_ibge (codigo_municipio_ibge);