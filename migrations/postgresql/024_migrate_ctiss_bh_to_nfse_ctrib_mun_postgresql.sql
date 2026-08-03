-- Migração de dados da tabela CTISS_BH para nfse_ctrib_mun_referencia
-- Código IBGE de Belo Horizonte: 3106200

INSERT INTO nfse_ctrib_mun_referencia (
    codigo_ibge,
    uf_sigla,
    nome_municipio,
    codigo_tributacao_municipal,
    descricao,
    exige_ctribmun,
    data_inicio_vigencia,
    origem_catalogo,
    ativo,
    criado_em,
    atualizado_em
)
SELECT 
    '3106200' as codigo_ibge,  -- Código IBGE de Belo Horizonte
    'MG' as uf_sigla,
    'Belo Horizonte' as nome_municipio,
    ETM_CDTRIBUTACAO as codigo_tributacao_municipal,
    ETM_DSDESCRICAO as descricao,
    TRUE as exige_ctribmun,
    NULL as data_inicio_vigencia,
    'CTISS_BH' as origem_catalogo,
    TRUE as ativo,
    NOW() as criado_em,
    NOW() as atualizado_em
FROM CTISS_BH
WHERE ETM_CDTRIBUTACAO IS NOT NULL 
  AND ETM_DSDESCRICAO IS NOT NULL
ON CONFLICT (codigo_ibge, codigo_tributacao_municipal) 
DO UPDATE SET 
    descricao = EXCLUDED.descricao,
    exige_ctribmun = EXCLUDED.exige_ctribmun,
    atualizado_em = NOW();
