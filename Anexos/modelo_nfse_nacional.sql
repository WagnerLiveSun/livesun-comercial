-- Modelo interno de apoio à emissão de NFS-e padrão Nacional
-- Objetivo: separar cadastro nacional, vínculo municipal e habilitação por contribuinte
-- Referência funcional: ABRASF / NFS-e Nacional

-- =========================
-- 1) MUNICÍPIOS
-- =========================
CREATE TABLE nfse_municipio (
    id                      BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    codigo_ibge             CHAR(7) NOT NULL UNIQUE,
    uf                      CHAR(2) NOT NULL,
    nome                    VARCHAR(120) NOT NULL,
    aderente_nacional       BOOLEAN NOT NULL DEFAULT TRUE,
    ambiente                VARCHAR(20) NOT NULL DEFAULT 'producao',
    ativo                   BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_nfse_municipio_uf_nome ON nfse_municipio (uf, nome);

-- =========================
-- 2) TABELA NACIONAL DE SERVIÇOS
-- cTribNac = código tributação nacional
-- item_lc116 = item da lista LC 116/2003
-- =========================
CREATE TABLE nfse_servico_nacional (
    id                      BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    ctrib_nac               CHAR(6) NOT NULL UNIQUE,
    item_lc116              VARCHAR(5) NOT NULL,
    descricao               VARCHAR(500) NOT NULL,
    codigo_nbs              VARCHAR(20),
    versao_tabela           VARCHAR(30) NOT NULL,
    vigencia_inicio         DATE,
    vigencia_fim            DATE,
    ativo                   BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_nfse_servico_nacional_ctrib_nac CHECK (ctrib_nac ~ '^[0-9]{6}$')
);

CREATE INDEX ix_nfse_servico_nacional_item ON nfse_servico_nacional (item_lc116);
CREATE INDEX ix_nfse_servico_nacional_nbs ON nfse_servico_nacional (codigo_nbs);

-- =========================
-- 3) RELAÇÃO MUNICÍPIO x SERVIÇO
-- Aqui fica o ponto crítico da crítica “município não possui o código informado”
-- =========================
CREATE TABLE nfse_servico_municipio (
    id                              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    municipio_id                    BIGINT NOT NULL REFERENCES nfse_municipio(id),
    servico_nacional_id             BIGINT NOT NULL REFERENCES nfse_servico_nacional(id),
    codigo_complementar_municipal   VARCHAR(20),
    codigo_tributacao_municipio     VARCHAR(20),
    exige_complemento_municipal     BOOLEAN NOT NULL DEFAULT FALSE,
    permite_retencao_iss            BOOLEAN NOT NULL DEFAULT TRUE,
    permite_fora_municipio          BOOLEAN NOT NULL DEFAULT TRUE,
    exige_cnae                      BOOLEAN NOT NULL DEFAULT FALSE,
    exige_inscricao_tomador         BOOLEAN NOT NULL DEFAULT FALSE,
    ativo                           BOOLEAN NOT NULL DEFAULT TRUE,
    homologado_em                   TIMESTAMP,
    observacao                      VARCHAR(500),
    criado_em                       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em                   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_nfse_servico_municipio UNIQUE (municipio_id, servico_nacional_id, COALESCE(codigo_complementar_municipal, ''))
);

CREATE INDEX ix_nfse_servico_municipio_municipio ON nfse_servico_municipio (municipio_id, ativo);
CREATE INDEX ix_nfse_servico_municipio_servico ON nfse_servico_municipio (servico_nacional_id, ativo);
CREATE INDEX ix_nfse_servico_municipio_cod_mun ON nfse_servico_municipio (codigo_tributacao_municipio);

-- =========================
-- 4) CONTRIBUINTE / INSCRIÇÃO MUNICIPAL
-- =========================
CREATE TABLE nfse_contribuinte_municipio (
    id                          BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    cnpj                        CHAR(14) NOT NULL,
    inscricao_municipal         VARCHAR(20),
    municipio_id                BIGINT NOT NULL REFERENCES nfse_municipio(id),
    razao_social                VARCHAR(200) NOT NULL,
    simples_nacional            BOOLEAN NOT NULL DEFAULT FALSE,
    mei                         BOOLEAN NOT NULL DEFAULT FALSE,
    incentivador_cultural       BOOLEAN NOT NULL DEFAULT FALSE,
    regime_especial             SMALLINT,
    autorizado_emitir_nfse      BOOLEAN NOT NULL DEFAULT TRUE,
    ativo                       BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em                   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_nfse_ctrib_mun UNIQUE (cnpj, municipio_id, COALESCE(inscricao_municipal, '')),
    CONSTRAINT ck_nfse_ctrib_cnpj CHECK (cnpj ~ '^[0-9]{14}$')
);

CREATE INDEX ix_nfse_ctrib_mun_lookup ON nfse_contribuinte_municipio (municipio_id, cnpj, ativo);

-- =========================
-- 5) HABILITAÇÃO DO CONTRIBUINTE POR SERVIÇO
-- Nem todo serviço municipal estará liberado para todo contribuinte
-- =========================
CREATE TABLE nfse_contribuinte_servico (
    id                          BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    contribuinte_municipio_id   BIGINT NOT NULL REFERENCES nfse_contribuinte_municipio(id),
    servico_municipio_id        BIGINT NOT NULL REFERENCES nfse_servico_municipio(id),
    cnae                        VARCHAR(7),
    aliquota                    NUMERIC(7,4),
    retencao_padrao             BOOLEAN NOT NULL DEFAULT FALSE,
    ativo                       BOOLEAN NOT NULL DEFAULT TRUE,
    inicio_vigencia             DATE,
    fim_vigencia                DATE,
    criado_em                   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_nfse_ctrib_serv UNIQUE (contribuinte_municipio_id, servico_municipio_id)
);

CREATE INDEX ix_nfse_ctrib_serv_lookup ON nfse_contribuinte_serv (contribuinte_municipio_id, ativo);

-- =========================
-- 6) CADASTRO INTERNO DE SERVIÇOS DO ERP
-- Faz a ponte com o cadastro operacional da empresa
-- =========================
CREATE TABLE erp_servico (
    id                              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    codigo_interno                  VARCHAR(50) NOT NULL UNIQUE,
    descricao_interna               VARCHAR(255) NOT NULL,
    servico_nacional_id             BIGINT REFERENCES nfse_servico_nacional(id),
    cnae_padrao                     VARCHAR(7),
    item_lc116_padrao               VARCHAR(5),
    gera_nfse                       BOOLEAN NOT NULL DEFAULT TRUE,
    ativo                           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em                       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em                   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 7) PARAMETRIZAÇÃO POR EMPRESA / FILIAL / MUNICÍPIO
-- =========================
CREATE TABLE erp_servico_nfse_param (
    id                              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    empresa_id                      BIGINT NOT NULL,
    filial_id                       BIGINT,
    erp_servico_id                  BIGINT NOT NULL REFERENCES erp_servico(id),
    municipio_id                    BIGINT NOT NULL REFERENCES nfse_municipio(id),
    contribuinte_municipio_id       BIGINT NOT NULL REFERENCES nfse_contribuinte_municipio(id),
    servico_municipio_id            BIGINT NOT NULL REFERENCES nfse_servico_municipio(id),
    natureza_operacao               SMALLINT NOT NULL,
    retem_iss                       BOOLEAN NOT NULL DEFAULT FALSE,
    codigo_cnae_envio               VARCHAR(7),
    enviar_inscricao_tomador        BOOLEAN NOT NULL DEFAULT FALSE,
    ativo                           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em                       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em                   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_erp_servico_nfse_param UNIQUE (empresa_id, COALESCE(filial_id, 0), erp_servico_id, municipio_id)
);

CREATE INDEX ix_erp_servico_nfse_param_lookup ON erp_servico_nfse_param (empresa_id, municipio_id, ativo);

-- =========================
-- 8) LOG DE VALIDAÇÃO / REJEIÇÃO
-- =========================
CREATE TABLE nfse_validacao_log (
    id                              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    empresa_id                      BIGINT NOT NULL,
    referencia_negocio              VARCHAR(80),
    municipio_id                    BIGINT REFERENCES nfse_municipio(id),
    contribuinte_municipio_id       BIGINT REFERENCES nfse_contribuinte_municipio(id),
    erp_servico_id                  BIGINT REFERENCES erp_servico(id),
    codigo_erro                     VARCHAR(20),
    mensagem                        VARCHAR(1000) NOT NULL,
    payload_json                    TEXT,
    criado_em                       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 9) VIEW DE APOIO PARA DIAGNÓSTICO
-- =========================
CREATE VIEW vw_nfse_mapa_servico AS
SELECT
    m.codigo_ibge,
    m.uf,
    m.nome AS municipio,
    sn.ctrib_nac,
    sn.item_lc116,
    sn.descricao AS descricao_nacional,
    sm.codigo_complementar_municipal,
    sm.codigo_tributacao_municipio,
    sm.exige_complemento_municipal,
    sm.ativo AS servico_municipio_ativo
FROM nfse_servico_municipio sm
JOIN nfse_municipio m ON m.id = sm.municipio_id
JOIN nfse_servico_nacional sn ON sn.id = sm.servico_nacional_id;

-- =========================
-- 10) CARGA INICIAL EXEMPLO
-- Ajuste os dados conforme a tabela oficial vigente
-- =========================
INSERT INTO nfse_municipio (codigo_ibge, uf, nome)
VALUES ('3550308', 'SP', 'São Paulo')
ON CONFLICT (codigo_ibge) DO NOTHING;

INSERT INTO nfse_servico_nacional (ctrib_nac, item_lc116, descricao, codigo_nbs, versao_tabela)
VALUES
('010101', '1.01', 'Análise e desenvolvimento de sistemas', '1.0000.00.00', 'v_atual'),
('010102', '1.01', 'Programação', '1.0000.00.00', 'v_atual'),
('170101', '17.01', 'Assessoria ou consultoria de qualquer natureza', '1.0000.00.00', 'v_atual')
ON CONFLICT (ctrib_nac) DO NOTHING;

-- Exemplo de vínculo do município com serviço nacional
INSERT INTO nfse_servico_municipio (
    municipio_id,
    servico_nacional_id,
    codigo_complementar_municipal,
    codigo_tributacao_municipio,
    exige_complemento_municipal,
    ativo
)
SELECT m.id, s.id, NULL, '010101', FALSE, TRUE
FROM nfse_municipio m
JOIN nfse_servico_nacional s ON s.ctrib_nac = '010101'
WHERE m.codigo_ibge = '3550308'
ON CONFLICT DO NOTHING;

-- =========================
-- 11) CONSULTAS DE DIAGNÓSTICO
-- =========================

-- 11.1 Verificar se o município tem o código nacional vinculado
-- :codigo_ibge = município da emissão
-- :ctrib_nac   = código tributação nacional informado
SELECT
    m.codigo_ibge,
    m.nome,
    sn.ctrib_nac,
    sn.descricao,
    sm.ativo,
    sm.codigo_complementar_municipal,
    sm.codigo_tributacao_municipio,
    sm.exige_complemento_municipal
FROM nfse_municipio m
LEFT JOIN nfse_servico_municipio sm ON sm.municipio_id = m.id
LEFT JOIN nfse_servico_nacional sn ON sn.id = sm.servico_nacional_id
WHERE m.codigo_ibge = :codigo_ibge
  AND sn.ctrib_nac = :ctrib_nac;

-- 11.2 Verificar se o contribuinte está habilitado naquele serviço
SELECT
    c.cnpj,
    c.inscricao_municipal,
    c.razao_social,
    c.autorizado_emitir_nfse,
    cs.ativo AS servico_habilitado,
    cs.cnae,
    cs.aliquota
FROM nfse_contribuinte_municipio c
JOIN nfse_contribuinte_servico cs ON cs.contribuinte_municipio_id = c.id
JOIN nfse_servico_municipio sm ON sm.id = cs.servico_municipio_id
JOIN nfse_servico_nacional sn ON sn.id = sm.servico_nacional_id
JOIN nfse_municipio m ON m.id = c.municipio_id
WHERE m.codigo_ibge = :codigo_ibge
  AND c.cnpj = :cnpj
  AND COALESCE(c.inscricao_municipal, '') = COALESCE(:inscricao_municipal, '')
  AND sn.ctrib_nac = :ctrib_nac;

-- 11.3 Localizar parametrização interna do ERP
SELECT
    p.empresa_id,
    p.filial_id,
    es.codigo_interno,
    es.descricao_interna,
    sn.ctrib_nac,
    sm.codigo_complementar_municipal,
    p.natureza_operacao,
    p.retem_iss,
    p.ativo
FROM erp_servico_nfse_param p
JOIN erp_servico es ON es.id = p.erp_servico_id
JOIN nfse_servico_municipio sm ON sm.id = p.servico_municipio_id
JOIN nfse_servico_nacional sn ON sn.id = sm.servico_nacional_id
JOIN nfse_municipio m ON m.id = p.municipio_id
WHERE p.empresa_id = :empresa_id
  AND COALESCE(p.filial_id, 0) = COALESCE(:filial_id, 0)
  AND es.codigo_interno = :codigo_interno
  AND m.codigo_ibge = :codigo_ibge;

-- =========================
-- 12) FUNÇÃO DE VALIDAÇÃO PRÉ-EMISSÃO
-- =========================
CREATE OR REPLACE FUNCTION fn_nfse_validar_servico(
    p_empresa_id             BIGINT,
    p_filial_id              BIGINT,
    p_codigo_interno         VARCHAR,
    p_codigo_ibge            CHAR(7),
    p_cnpj                   CHAR(14),
    p_inscricao_municipal    VARCHAR,
    p_ctrib_nac              CHAR(6)
)
RETURNS TABLE (
    status_validacao         VARCHAR,
    detalhe                  VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_municipio_id BIGINT;
    v_servico_municipio_id BIGINT;
    v_contribuinte_id BIGINT;
BEGIN
    SELECT id INTO v_municipio_id
    FROM nfse_municipio
    WHERE codigo_ibge = p_codigo_ibge
      AND ativo = TRUE;

    IF v_municipio_id IS NULL THEN
        RETURN QUERY SELECT 'ERRO', 'Município não cadastrado na tabela interna.';
        RETURN;
    END IF;

    SELECT sm.id INTO v_servico_municipio_id
    FROM nfse_servico_municipio sm
    JOIN nfse_servico_nacional sn ON sn.id = sm.servico_nacional_id
    WHERE sm.municipio_id = v_municipio_id
      AND sn.ctrib_nac = p_ctrib_nac
      AND sm.ativo = TRUE
    LIMIT 1;

    IF v_servico_municipio_id IS NULL THEN
        RETURN QUERY SELECT 'ERRO', 'Município não possui vínculo ativo para o código de tributação nacional informado.';
        RETURN;
    END IF;

    SELECT id INTO v_contribuinte_id
    FROM nfse_contribuinte_municipio
    WHERE municipio_id = v_municipio_id
      AND cnpj = p_cnpj
      AND COALESCE(inscricao_municipal, '') = COALESCE(p_inscricao_municipal, '')
      AND ativo = TRUE
      AND autorizado_emitir_nfse = TRUE
    LIMIT 1;

    IF v_contribuinte_id IS NULL THEN
        RETURN QUERY SELECT 'ERRO', 'Contribuinte não autorizado ou não cadastrado para emitir NFS-e nesse município.';
        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM erp_servico_nfse_param p
        JOIN erp_servico es ON es.id = p.erp_servico_id
        WHERE p.empresa_id = p_empresa_id
          AND COALESCE(p.filial_id, 0) = COALESCE(p_filial_id, 0)
          AND es.codigo_interno = p_codigo_interno
          AND p.municipio_id = v_municipio_id
          AND p.contribuinte_municipio_id = v_contribuinte_id
          AND p.servico_municipio_id = v_servico_municipio_id
          AND p.ativo = TRUE
    ) THEN
        RETURN QUERY SELECT 'ERRO', 'Serviço interno do ERP não está parametrizado para esse município/contribuinte/código nacional.';
        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM nfse_contribuinte_servico cs
        WHERE cs.contribuinte_municipio_id = v_contribuinte_id
          AND cs.servico_municipio_id = v_servico_municipio_id
          AND cs.ativo = TRUE
    ) THEN
        RETURN QUERY SELECT 'ERRO', 'Contribuinte não possui habilitação ativa para o serviço neste município.';
        RETURN;
    END IF;

    RETURN QUERY SELECT 'OK', 'Serviço validado para emissão.';
END;
$$;

-- =========================
-- 13) USO DA FUNÇÃO
-- =========================
-- SELECT * FROM fn_nfse_validar_servico(
--     1,
--     NULL,
--     'SERV-CONSULTORIA',
--     '3550308',
--     '12345678000199',
--     '123456',
--     '170101'
-- );
