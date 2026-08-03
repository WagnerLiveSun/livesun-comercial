-- Criar tabela de referência de municípios para NFS-e
CREATE TABLE IF NOT EXISTS nfse_municipios_referencia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_ibge VARCHAR(7) NOT NULL,
    uf_sigla VARCHAR(2) NOT NULL,
    nome_municipio VARCHAR(120) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    UNIQUE KEY uq_nfse_municipio_codigo_ibge (codigo_ibge),
    KEY idx_nfse_municipio_uf_nome (uf_sigla, nome_municipio),
    KEY idx_nfse_municipio_codigo_ibge (codigo_ibge)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
