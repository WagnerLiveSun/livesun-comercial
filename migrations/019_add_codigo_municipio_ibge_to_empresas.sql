-- Migration: add codigo_municipio_ibge to empresas
ALTER TABLE empresas
ADD COLUMN codigo_municipio_ibge VARCHAR(7) NULL;

CREATE INDEX idx_empresas_codigo_municipio_ibge ON empresas (codigo_municipio_ibge);
