-- Migração de dados do Rio de Janeiro para nfse_ctrib_mun_referencia
-- Código IBGE do Rio de Janeiro: 3304557
-- Dados extraídos de Anexos/TabelaServicos.txt

-- Exemplo de INSERT (precisa ser preenchido com os dados reais do arquivo)
-- Como o arquivo tem muitos registros, recomendo processar via Python ou inserir manualmente os códigos mais usados

-- Exemplo de formato:
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
) VALUES
('3304557', 'RJ', 'Rio de Janeiro', '01', 'Serviços de informática e congêneres.', TRUE, NULL, 'TabelaServicos_RJ', TRUE, NOW(), NOW()),
('3304557', 'RJ', 'Rio de Janeiro', '01.01', 'Análise e desenvolvimento de sistemas.', TRUE, NULL, 'TabelaServicos_RJ', TRUE, NOW(), NOW()),
('3304557', 'RJ', 'Rio de Janeiro', '01.01.01', 'Análise de sistemas,', TRUE, NULL, 'TabelaServicos_RJ', TRUE, NOW(), NOW())
ON DUPLICATE KEY UPDATE 
    descricao = VALUES(descricao),
    exige_ctribmun = VALUES(exige_ctribmun),
    atualizado_em = NOW();

-- Nota: Para importar todos os dados do arquivo TabelaServicos.txt, 
-- use o script Python 025_import_rio_ctrib_mun.py dentro do contexto da aplicação Flask
-- ou processe o arquivo manualmente e gere os INSERTs completos
