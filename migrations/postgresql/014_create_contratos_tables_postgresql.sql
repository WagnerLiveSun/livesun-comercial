-- =====================================================================
-- Modulo de Gestao de Contratos - PostgreSQL
-- =====================================================================
-- Tabelas para gestao de contratos, clausulas e historico
-- =====================================================================

-- =========================
-- 1) CLAUSULAS CONTRATO PADRAO
-- =========================
CREATE TABLE IF NOT EXISTS clausulas_contrato_padrao (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Identificacao
    codigo VARCHAR(50) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    
    -- Conteudo
    texto_base TEXT NOT NULL,
    descricao TEXT,
    
    -- Configuracao
    tipo VARCHAR(20) NOT NULL DEFAULT 'opcional',
    editavel BOOLEAN NOT NULL DEFAULT true,
    ordem_padrao INTEGER NOT NULL DEFAULT 0,
    
    -- Categorizacao
    categoria VARCHAR(50),
    tipo_contrato VARCHAR(50),
    
    -- Controle
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_por_user_id INTEGER NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_por_user_id INTEGER,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_clausula_padrao_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_clausula_padrao_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id),
    CONSTRAINT fk_clausula_padrao_atualizado_por FOREIGN KEY (atualizado_por_user_id) REFERENCES users(id),
    CONSTRAINT uq_clausula_padrao_empresa_codigo UNIQUE (empresa_id, codigo)
);

CREATE INDEX idx_clausula_padrao_empresa ON clausulas_contrato_padrao(empresa_id);
CREATE INDEX idx_clausula_padrao_tipo ON clausulas_contrato_padrao(tipo);
CREATE INDEX idx_clausula_padrao_categoria ON clausulas_contrato_padrao(categoria);
CREATE INDEX idx_clausula_padrao_tipo_contrato ON clausulas_contrato_padrao(tipo_contrato);

CREATE TRIGGER update_clausulas_contrato_padrao_atualizado_em
    BEFORE UPDATE ON clausulas_contrato_padrao
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================
-- 2) CONTRATOS
-- =========================
CREATE TABLE IF NOT EXISTS contratos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Identificacao
    numero VARCHAR(50) NOT NULL,
    serie VARCHAR(10) DEFAULT 'CTR',
    titulo VARCHAR(200),
    
    -- Vinculacao
    orcamento_id INTEGER,
    cliente_id INTEGER NOT NULL,
    vendedor_id INTEGER,
    
    -- Dados das partes
    contratada_entidade_id INTEGER NOT NULL,
    contratante_entidade_id INTEGER NOT NULL,
    
    -- Dados comerciais
    valor_total NUMERIC(15,2) NOT NULL,
    valor_mensal NUMERIC(15,2),
    forma_pagamento VARCHAR(100),
    periodicidade VARCHAR(50),
    data_inicio_vigencia DATE NOT NULL,
    data_fim_vigencia DATE,
    
    -- Status e controle
    status VARCHAR(20) NOT NULL DEFAULT 'rascunho',
    motivo_cancelamento TEXT,
    
    -- Descricao dos servicos
    descricao_servicos TEXT,
    objeto_contrato TEXT,
    
    -- Metadados
    data_geracao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_assinatura DATE,
    gerado_por_user_id INTEGER NOT NULL,
    assinado_por_user_id INTEGER,
    
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_contrato_orcamento FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id),
    CONSTRAINT fk_contrato_cliente FOREIGN KEY (cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_contrato_vendedor FOREIGN KEY (vendedor_id) REFERENCES entidades(id),
    CONSTRAINT fk_contrato_contratada FOREIGN KEY (contratada_entidade_id) REFERENCES entidades(id),
    CONSTRAINT fk_contrato_contratante FOREIGN KEY (contratante_entidade_id) REFERENCES entidades(id),
    CONSTRAINT fk_contrato_gerado_por FOREIGN KEY (gerado_por_user_id) REFERENCES users(id),
    CONSTRAINT fk_contrato_assinado_por FOREIGN KEY (assinado_por_user_id) REFERENCES users(id),
    CONSTRAINT uq_contrato_empresa_numero_serie UNIQUE (empresa_id, numero, serie)
);

CREATE INDEX idx_contrato_empresa ON contratos(empresa_id);
CREATE INDEX idx_contrato_orcamento ON contratos(orcamento_id);
CREATE INDEX idx_contrato_cliente ON contratos(cliente_id);
CREATE INDEX idx_contrato_status ON contratos(status);
CREATE INDEX idx_contrato_vigencia ON contratos(data_inicio_vigencia, data_fim_vigencia);
CREATE INDEX idx_contrato_numero ON contratos(numero);

CREATE TRIGGER update_contratos_atualizado_em
    BEFORE UPDATE ON contratos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================
-- 3) CONTRATO CLAUSULAS
-- =========================
CREATE TABLE IF NOT EXISTS contrato_clausulas (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL,
    
    -- Referencia a clausula padrao
    clausula_padrao_id INTEGER,
    
    -- Dados da clausula no contrato
    titulo VARCHAR(200) NOT NULL,
    texto TEXT NOT NULL,
    
    -- Configuracao
    ordem INTEGER NOT NULL,
    editavel BOOLEAN NOT NULL DEFAULT true,
    obrigatoria BOOLEAN NOT NULL DEFAULT false,
    
    -- Controle de alteracoes
    alterado_por_user_id INTEGER,
    data_alteracao TIMESTAMP,
    
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_clausula_contrato FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_contrato_clausula_padrao FOREIGN KEY (clausula_padrao_id) REFERENCES clausulas_contrato_padrao(id),
    CONSTRAINT fk_contrato_clausula_alterado_por FOREIGN KEY (alterado_por_user_id) REFERENCES users(id),
    CONSTRAINT uq_contrato_clausula_ordem UNIQUE (contrato_id, ordem)
);

CREATE INDEX idx_contrato_clausula_contrato ON contrato_clausulas(contrato_id);
CREATE INDEX idx_contrato_clausula_padrao ON contrato_clausulas(clausula_padrao_id);
CREATE INDEX idx_contrato_clausula_ordem ON contrato_clausulas(contrato_id, ordem);

CREATE TRIGGER update_contrato_clausulas_atualizado_em
    BEFORE UPDATE ON contrato_clausulas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================
-- 4) CONTRATO HISTORICO
-- =========================
CREATE TABLE IF NOT EXISTS contrato_historico (
    id BIGSERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL,
    
    -- Versao
    versao INTEGER NOT NULL,
    acao VARCHAR(50) NOT NULL,
    
    -- Estado do contrato naquele momento
    status_anterior VARCHAR(20),
    status_novo VARCHAR(20),
    
    -- Detalhes da alteracao
    descricao_alteracao TEXT,
    campos_alterados JSONB,
    clausulas_alteradas JSONB,
    
    -- Quem fez a alteracao
    alterado_por_user_id INTEGER NOT NULL,
    data_alteracao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Snapshot opcional do contrato completo
    snapshot_contrato JSONB,
    
    CONSTRAINT fk_contrato_historico_contrato FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_contrato_historico_usuario FOREIGN KEY (alterado_por_user_id) REFERENCES users(id),
    CONSTRAINT uq_contrato_historico_versao UNIQUE (contrato_id, versao)
);

CREATE INDEX idx_contrato_historico_contrato ON contrato_historico(contrato_id);
CREATE INDEX idx_contrato_historico_data ON contrato_historico(data_alteracao);
CREATE INDEX idx_contrato_historico_acao ON contrato_historico(acao);

-- =========================
-- 5) CONTRATO ANEXOS
-- =========================
CREATE TABLE IF NOT EXISTS contrato_anexos (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL,
    
    -- Arquivo
    nome_arquivo VARCHAR(255) NOT NULL,
    tipo_arquivo VARCHAR(100) NOT NULL,
    tamanho_bytes BIGINT,
    caminho_arquivo VARCHAR(500) NOT NULL,
    
    -- Descricao
    descricao VARCHAR(255),
    tipo_anexo VARCHAR(50) NOT NULL,
    
    -- Controle
    criado_por_user_id INTEGER NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_anexo_contrato FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_contrato_anexo_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_contrato_anexo_contrato ON contrato_anexos(contrato_id);
CREATE INDEX idx_contrato_anexo_tipo ON contrato_anexos(tipo_anexo);

-- =========================
-- 6) CONTRATO PARAMETROS
-- =========================
CREATE TABLE IF NOT EXISTS contrato_parametros (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Identificacao
    codigo VARCHAR(50) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    
    -- Configuracao
    tipo_dado VARCHAR(20) NOT NULL DEFAULT 'texto',
    valor_padrao TEXT,
    origem VARCHAR(50),
    
    -- Controle
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_parametro_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_contrato_parametro_empresa_codigo UNIQUE (empresa_id, codigo)
);

CREATE INDEX idx_contrato_parametro_empresa ON contrato_parametros(empresa_id);
CREATE INDEX idx_contrato_parametro_origem ON contrato_parametros(origem);

CREATE TRIGGER update_contrato_parametros_atualizado_em
    BEFORE UPDATE ON contrato_parametros
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================
-- 7) CONTRATO PARAMETROS VALORES
-- =========================
CREATE TABLE IF NOT EXISTS contrato_parametros_valores (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL,
    parametro_id INTEGER NOT NULL,
    
    valor TEXT NOT NULL,
    
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_parametro_valor_contrato FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_contrato_parametro_valor_parametro FOREIGN KEY (parametro_id) REFERENCES contrato_parametros(id),
    CONSTRAINT uq_contrato_parametro_valor UNIQUE (contrato_id, parametro_id)
);

CREATE INDEX idx_contrato_parametro_valor_contrato ON contrato_parametros_valores(contrato_id);
CREATE INDEX idx_contrato_parametro_valor_parametro ON contrato_parametros_valores(parametro_id);

CREATE TRIGGER update_contrato_parametros_valores_atualizado_em
    BEFORE UPDATE ON contrato_parametros_valores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================
-- 8) DADOS INICIAIS - CLAUSULAS PADRAO
-- =========================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM empresas WHERE id = 1) THEN
        INSERT INTO clausulas_contrato_padrao (
            empresa_id, codigo, titulo, texto_base, descricao, tipo, editavel, ordem_padrao, 
            categoria, tipo_contrato, criado_por_user_id
        ) VALUES
(1, 'OBJ', 'Objeto', 
'CLAUSULA PRIMEIRA - DO OBJETO

1.1. O presente contrato tem como objeto a prestacao de servicos de {CONTRATO_DESCRICAO_SERVICOS} pela CONTRATADA em favor da CONTRATANTE.

1.2. Os servicos serao executados de forma remota, utilizando meios eletronicos e digitais, conforme especificacoes tecnicas acordadas entre as partes.

1.3. A CONTRATADA compromete-se a executar os servicos com o grau de diligencia e profissionalismo adequados, observando as melhores praticas de mercado.',
'Define o objeto do contrato de prestacao de servicos.', 'obrigatoria', true, 1, 'geral', 'prestacao_servicos', 1),

(1, 'EXEC', 'Execucao Remota',
'CLAUSULA SEGUNDA - DA EXECUCAO REMOTA

2.1. A prestacao dos servicos sera realizada predominantemente de forma remota, sem necessidade de deslocamento fisico da CONTRATADA as instalacoes da CONTRATANTE.

2.2. A CONTRATANTE devera disponibilizar acesso aos sistemas e informacoes necessarios para a execucao dos servicos, bem como manter ponto de contato para comunicacao.

2.3. A CONTRATADA podera solicitar reunioes presenciais quando necessario para alinhamento estrategico ou treinamento.',
'Define a forma de execucao remota dos servicos.', 'obrigatoria', true, 2, 'tecnico', 'prestacao_servicos', 1),

(1, 'SIGILO', 'Sigilo e Confidencialidade',
'CLAUSULA TERCEIRA - DO SIGILO E CONFIDENCIALIDADE

3.1. A CONTRATADA compromete-se a manter em sigilo todas as informacoes confidenciais da CONTRATANTE a que tiver acesso em razao da execucao deste contrato.

3.2. O dever de confidencialidade perdura apos o termino deste contrato, independentemente da causa de sua rescisao.

3.3. A CONTRATADA nao podera divulgar, reproduzir ou utilizar as informacoes confidenciais para qualquer finalidade que nao a execucao dos servicos contratados.',
'Estabelece o dever de sigilo e confidencialidade.', 'obrigatoria', true, 3, 'juridico', 'prestacao_servicos', 1),

(1, 'HONOR', 'Honorarios e Condicoes de Pagamento',
'CLAUSULA QUARTA - DOS HONORARIOS E CONDICOES DE PAGAMENTO

4.1. Pelos servicos objeto deste contrato, a CONTRATANTE pagara a CONTRATADA o valor total de {CONTRATO_VALOR_TOTAL}, na forma e condicoes a seguir descritas.

4.2. O valor mensal dos servicos e de {CONTRATO_VALOR_MENSAL}, pagavel mediante {CONTRATO_FORMA_PAGAMENTO}.

4.3. O pagamento devera ser efetuado ate o dia 5 de cada mes, referente aos servicos prestados no mes anterior.

4.4. O atraso no pagamento implicara na incidencia de juros de mora de 1% ao mes e multa de 2% sobre o valor em atraso.',
'Define os honorarios e condicoes de pagamento.', 'obrigatoria', true, 4, 'financeiro', 'prestacao_servicos', 1),

(1, 'VIGENC', 'Vigencia e Rescisao',
'CLAUSULA QUINTA - DA VIGENCIA E RESCISAO

5.1. O presente contrato tera vigencia de {CONTRATO_DATA_INICIO} a {CONTRATO_DATA_FIM}, podendo ser prorrogado mediante acordo expresso entre as partes.

5.2. Qualquer das partes podera rescindir este contrato mediante aviso previo de 30 (trinta) dias, por escrito.

5.3. A rescisao por justa causa, decorrente de inadimplemento de obrigacao contratual, nao exigira aviso previo.

5.4. Em caso de rescisao, a CONTRATANTE pagara os servicos ja executados ate a data da rescisao.',
'Define a vigencia do contrato e condicoes de rescisao.', 'obrigatoria', true, 5, 'juridico', 'prestacao_servicos', 1),

(1, 'RESP', 'Responsabilidades Tecnicas',
'CLAUSULA SEXTA - DAS RESPONSABILIDADES TECNICAS

6.1. A CONTRATADA responsabiliza-se pela qualidade tecnica dos servicos prestados, comprometendo-se a corrigir eventuais falhas ou erros que venham a ser identificados.

6.2. A CONTRATADA nao se responsabiliza por danos decorrentes de informacoes incorretas ou incompletas fornecidas pela CONTRATANTE.

6.3. A CONTRATADA mantera equipe tecnica qualificada para a execucao dos servicos, garantindo a continuidade e qualidade do atendimento.',
'Define as responsabilidades tecnicas da CONTRATADA.', 'opcional', true, 6, 'tecnico', 'prestacao_servicos', 1),

(1, 'VINCULO', 'Inexistencia de Vinculo Trabalhista',
'CLAUSULA SETIMA - DA INEXISTENCIA DE VINCULO TRABALHISTA

7.1. O presente contrato constitui relacao de prestacao de servicos autonomos, nao caracterizando vinculo empregaticio entre a CONTRATANTE e os colaboradores da CONTRATADA.

7.2. A CONTRATADA e responsavel por todos os encargos trabalhistas, previdenciarios e fiscais relativos aos seus colaboradores.

7.3. A CONTRATANTE nao exerce qualquer poder de direcao, fiscalizacao ou controle sobre os colaboradores da CONTRATADA, limitando-se a receber os resultados dos servicos contratados.',
'Estabelece expressamente a inexistencia de vinculo trabalhista.', 'obrigatoria', false, 7, 'trabalhista', 'prestacao_servicos', 1),

(1, 'FORO', 'Foro',
'CLAUSULA OITAVA - DO FORO

8.1. As partes elegem o foro da comarca de {CONTRATADA_CIDADE} para dirimir quaisquer duvidas ou controversias decorrentes deste contrato, com renuncia expressa a qualquer outro, por mais privilegiado que seja.',
'Define o foro competente para solucao de controversias.', 'opcional', true, 8, 'juridico', 'prestacao_servicos', 1),

(1, 'ACEITE', 'Aceitacao com Efeito Contratual',
'CLAUSULA NONA - DA ACEITACAO COM EFEITO CONTRATUAL

9.1. A assinatura deste contrato pelas partes implica aceitacao integral de todas as suas clausulas e condicoes.

9.2. Este contrato entra em vigor na data de sua assinatura, salvo disposicao em contrario.

9.3. As partes declaram que leram e compreenderam todas as clausulas deste contrato, assinando-o em duas vias de igual teor e forma.',
'Estabelece que a assinatura implica aceitacao das clausulas.', 'obrigatoria', true, 9, 'juridico', 'prestacao_servicos', 1)
ON CONFLICT (empresa_id, codigo) DO NOTHING;
    END IF;
END $$;

-- =========================
-- 9) DADOS INICIAIS - PARAMETROS
-- =========================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM empresas WHERE id = 1) THEN
        INSERT INTO contrato_parametros (
            empresa_id, codigo, nome, descricao, tipo_dado, valor_padrao, origem, ativo
        ) VALUES
(1, 'CONTRATADA_RAZAO_SOCIAL', 'Razao Social Contratada', 'Razao social da empresa prestadora', 'texto', NULL, 'empresa', true),
(1, 'CONTRATADA_CNPJ', 'CNPJ Contratada', 'CNPJ da empresa prestadora', 'texto', NULL, 'empresa', true),
(1, 'CONTRATADA_ENDERECO', 'Endereco Contratada', 'Endereco completo da empresa prestadora', 'texto', NULL, 'empresa', true),
(1, 'CONTRATADA_CIDADE', 'Cidade Contratada', 'Cidade da empresa prestadora', 'texto', NULL, 'empresa', true),
(1, 'CONTRATADA_UF', 'UF Contratada', 'UF da empresa prestadora', 'texto', NULL, 'empresa', true),
(1, 'CONTRATANTE_RAZAO_SOCIAL', 'Razao Social Contratante', 'Razao social ou nome do cliente', 'texto', NULL, 'cliente', true),
(1, 'CONTRATANTE_CNPJ_CPF', 'CNPJ/CPF Contratante', 'CNPJ ou CPF do cliente', 'texto', NULL, 'cliente', true),
(1, 'CONTRATANTE_ENDERECO', 'Endereco Contratante', 'Endereco completo do cliente', 'texto', NULL, 'cliente', true),
(1, 'CONTRATANTE_CIDADE', 'Cidade Contratante', 'Cidade do cliente', 'texto', NULL, 'cliente', true),
(1, 'CONTRATANTE_UF', 'UF Contratante', 'UF do cliente', 'texto', NULL, 'cliente', true),
(1, 'CONTRATO_VALOR_TOTAL', 'Valor Total do Contrato', 'Valor total do contrato', 'moeda', NULL, 'orcamento', true),
(1, 'CONTRATO_VALOR_MENSAL', 'Valor Mensal', 'Valor mensal do contrato', 'moeda', NULL, 'orcamento', true),
(1, 'CONTRATO_FORMA_PAGAMENTO', 'Forma de Pagamento', 'Forma de pagamento acordada', 'texto', NULL, 'orcamento', true),
(1, 'CONTRATO_PERIODICIDADE', 'Periodicidade', 'Periodicidade do pagamento', 'texto', NULL, 'orcamento', true),
(1, 'CONTRATO_DATA_INICIO', 'Data Inicio Vigencia', 'Data de inicio da vigencia do contrato', 'data', NULL, 'contrato', true),
(1, 'CONTRATO_DATA_FIM', 'Data Fim Vigencia', 'Data de fim da vigencia do contrato', 'data', NULL, 'contrato', true),
(1, 'CONTRATO_DESCRICAO_SERVICOS', 'Descricao dos Servicos', 'Descricao resumida dos servicos contratados', 'texto', NULL, 'orcamento', true),
(1, 'CONTRATO_NUMERO', 'Numero do Contrato', 'Numero de identificacao do contrato', 'texto', NULL, 'contrato', true),
(1, 'CONTRATO_DATA_ASSINATURA', 'Data de Assinatura', 'Data de assinatura do contrato', 'data', NULL, 'contrato', true)
ON CONFLICT (empresa_id, codigo) DO NOTHING;
    END IF;
END $$;

-- =========================
-- FIM DO SCRIPT
-- =========================
