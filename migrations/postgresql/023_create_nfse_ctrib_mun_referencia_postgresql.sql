-- Tabela de referência para códigos de tributação municipal (cTribMun)
-- Armazena os códigos aceitos por cada município para NFS-e Nacional
CREATE TABLE IF NOT EXISTS nfse_ctrib_mun_referencia (
    id SERIAL PRIMARY KEY,
    codigo_ibge VARCHAR(7) NOT NULL,
    uf_sigla VARCHAR(2) NOT NULL,
    nome_municipio VARCHAR(120) NOT NULL,
    codigo_tributacao_municipal VARCHAR(10) NOT NULL,
    descricao TEXT NOT NULL,
    exige_ctribmun BOOLEAN DEFAULT TRUE,
    data_inicio_vigencia DATE NULL,
    data_fim_vigencia DATE NULL,
    origem_catalogo VARCHAR(40) NULL,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_nfse_ctrib_mun_codigo UNIQUE (codigo_ibge, codigo_tributacao_municipal)
);

CREATE INDEX IF NOT EXISTS idx_nfse_ctrib_mun_municipio ON nfse_ctrib_mun_referencia(codigo_ibge);
CREATE INDEX IF NOT EXISTS idx_nfse_ctrib_mun_codigo ON nfse_ctrib_mun_referencia(codigo_tributacao_municipal);
