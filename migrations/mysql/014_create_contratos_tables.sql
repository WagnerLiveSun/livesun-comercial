-- =====================================================================
-- Módulo de Gestão de Contratos - MySQL
-- =====================================================================
-- Tabelas para gestão de contratos, cláusulas e histórico
-- =====================================================================

-- =========================
-- 1) CLÁUSULAS CONTRATO PADRÃO
-- =========================
CREATE TABLE IF NOT EXISTS clausulas_contrato_padrao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    
    -- Identificação
    codigo VARCHAR(50) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    
    -- Conteúdo
    texto_base TEXT NOT NULL,
    descricao TEXT,
    
    -- Configuração
    tipo VARCHAR(20) NOT NULL DEFAULT 'opcional' COMMENT 'obrigatoria, opcional, condicional',
    editavel TINYINT(1) NOT NULL DEFAULT 1,
    ordem_padrao INT NOT NULL DEFAULT 0,
    
    -- Categorização
    categoria VARCHAR(50) COMMENT 'geral, financeiro, juridico, tecnico, trabalhista',
    tipo_contrato VARCHAR(50) COMMENT 'prestacao_servicos, fornecimento, parceria',
    
    -- Controle
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_por_user_id INT NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_por_user_id INT,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_clausula_padrao_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_clausula_padrao_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id),
    CONSTRAINT fk_clausula_padrao_atualizado_por FOREIGN KEY (atualizado_por_user_id) REFERENCES users(id),
    CONSTRAINT uq_clausula_padrao_empresa_codigo UNIQUE (empresa_id, codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_clausula_padrao_empresa ON clausulas_contrato_padrao(empresa_id);
CREATE INDEX idx_clausula_padrao_tipo ON clausulas_contrato_padrao(tipo);
CREATE INDEX idx_clausula_padrao_categoria ON clausulas_contrato_padrao(categoria);
CREATE INDEX idx_clausula_padrao_tipo_contrato ON clausulas_contrato_padrao(tipo_contrato);

-- =========================
-- 2) CONTRATOS
-- =========================
CREATE TABLE IF NOT EXISTS contratos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    
    -- Identificação
    numero VARCHAR(50) NOT NULL,
    serie VARCHAR(10) DEFAULT 'CTR',
    titulo VARCHAR(200),
    
    -- Vinculação
    orcamento_id INT,
    cliente_id INT NOT NULL,
    vendedor_id INT,
    
    -- Dados das partes
    contratada_entidade_id INT NOT NULL COMMENT 'Empresa prestadora',
    contratante_entidade_id INT NOT NULL COMMENT 'Cliente',
    
    -- Dados comerciais
    valor_total DECIMAL(15,2) NOT NULL,
    valor_mensal DECIMAL(15,2),
    forma_pagamento VARCHAR(100),
    periodicidade VARCHAR(50) COMMENT 'mensal, trimestral, semestral, anual, unico',
    data_inicio_vigencia DATE NOT NULL,
    data_fim_vigencia DATE,
    
    -- Status e controle
    status VARCHAR(20) NOT NULL DEFAULT 'rascunho' COMMENT 'rascunho, aguardando_assinatura, assinado, cancelado, rescindido',
    motivo_cancelamento TEXT,
    
    -- Descrição dos serviços
    descricao_servicos TEXT,
    objeto_contrato TEXT,
    
    -- Metadados
    data_geracao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_assinatura DATE,
    gerado_por_user_id INT NOT NULL,
    assinado_por_user_id INT,
    
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_contrato_orcamento FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id),
    CONSTRAINT fk_contrato_cliente FOREIGN KEY (cliente_id) REFERENCES entidades(id),
    CONSTRAINT fk_contrato_vendedor FOREIGN KEY (vendedor_id) REFERENCES entidades(id),
    CONSTRAINT fk_contrato_contratada FOREIGN KEY (contratada_entidade_id) REFERENCES entidades(id),
    CONSTRAINT fk_contrato_contratante FOREIGN KEY (contratante_entidade_id) REFERENCES entidades(id),
    CONSTRAINT fk_contrato_gerado_por FOREIGN KEY (gerado_por_user_id) REFERENCES users(id),
    CONSTRAINT fk_contrato_assinado_por FOREIGN KEY (assinado_por_user_id) REFERENCES users(id),
    CONSTRAINT uq_contrato_empresa_numero_serie UNIQUE (empresa_id, numero, serie)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_contrato_empresa ON contratos(empresa_id);
CREATE INDEX idx_contrato_orcamento ON contratos(orcamento_id);
CREATE INDEX idx_contrato_cliente ON contratos(cliente_id);
CREATE INDEX idx_contrato_status ON contratos(status);
CREATE INDEX idx_contrato_vigencia ON contratos(data_inicio_vigencia, data_fim_vigencia);
CREATE INDEX idx_contrato_numero ON contratos(numero);

-- =========================
-- 3) CONTRATO CLÁUSULAS
-- =========================
CREATE TABLE IF NOT EXISTS contrato_clausulas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contrato_id INT NOT NULL,
    
    -- Referência à cláusula padrão
    clausula_padrao_id INT,
    
    -- Dados da cláusula no contrato
    titulo VARCHAR(200) NOT NULL,
    texto TEXT NOT NULL,
    
    -- Configuração
    ordem INT NOT NULL,
    editavel TINYINT(1) NOT NULL DEFAULT 1,
    obrigatoria TINYINT(1) NOT NULL DEFAULT 0,
    
    -- Controle de alterações
    alterado_por_user_id INT,
    data_alteracao DATETIME,
    
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_clausula_contrato FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_contrato_clausula_padrao FOREIGN KEY (clausula_padrao_id) REFERENCES clausulas_contrato_padrao(id),
    CONSTRAINT fk_contrato_clausula_alterado_por FOREIGN KEY (alterado_por_user_id) REFERENCES users(id),
    CONSTRAINT uq_contrato_clausula_ordem UNIQUE (contrato_id, ordem)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_contrato_clausula_contrato ON contrato_clausulas(contrato_id);
CREATE INDEX idx_contrato_clausula_padrao ON contrato_clausulas(clausula_padrao_id);
CREATE INDEX idx_contrato_clausula_ordem ON contrato_clausulas(contrato_id, ordem);

-- =========================
-- 4) CONTRATO HISTÓRICO
-- =========================
CREATE TABLE IF NOT EXISTS contrato_historico (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contrato_id INT NOT NULL,
    
    -- Versão
    versao INT NOT NULL,
    acao VARCHAR(50) NOT NULL COMMENT 'criado, editado, assinado, cancelado, rescindido',
    
    -- Estado do contrato naquele momento
    status_anterior VARCHAR(20),
    status_novo VARCHAR(20),
    
    -- Detalhes da alteração
    descricao_alteracao TEXT,
    campos_alterados JSON COMMENT 'Lista de campos que foram alterados',
    clausulas_alteradas JSON COMMENT 'Lista de cláusulas alteradas',
    
    -- Quem fez a alteração
    alterado_por_user_id INT NOT NULL,
    data_alteracao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Snapshot opcional do contrato completo
    snapshot_contrato JSON,
    
    CONSTRAINT fk_contrato_historico_contrato FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_contrato_historico_usuario FOREIGN KEY (alterado_por_user_id) REFERENCES users(id),
    CONSTRAINT uq_contrato_historico_versao UNIQUE (contrato_id, versao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_contrato_historico_contrato ON contrato_historico(contrato_id);
CREATE INDEX idx_contrato_historico_data ON contrato_historico(data_alteracao);
CREATE INDEX idx_contrato_historico_acao ON contrato_historico(acao);

-- =========================
-- 5) CONTRATO ANEXOS
-- =========================
CREATE TABLE IF NOT EXISTS contrato_anexos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contrato_id INT NOT NULL,
    
    -- Arquivo
    nome_arquivo VARCHAR(255) NOT NULL,
    tipo_arquivo VARCHAR(100) NOT NULL COMMENT 'pdf, docx, jpg, etc',
    tamanho_bytes BIGINT,
    caminho_arquivo VARCHAR(500) NOT NULL,
    
    -- Descrição
    descricao VARCHAR(255),
    tipo_anexo VARCHAR(50) NOT NULL COMMENT 'contrato_assinado, documento_identificacao, comprovante, outro',
    
    -- Controle
    criado_por_user_id INT NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_anexo_contrato FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_contrato_anexo_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_contrato_anexo_contrato ON contrato_anexos(contrato_id);
CREATE INDEX idx_contrato_anexo_tipo ON contrato_anexos(tipo_anexo);

-- =========================
-- 6) CONTRATO PARÂMETROS
-- =========================
CREATE TABLE IF NOT EXISTS contrato_parametros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    
    -- Identificação
    codigo VARCHAR(50) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    
    -- Configuração
    tipo_dado VARCHAR(20) NOT NULL DEFAULT 'texto' COMMENT 'texto, numero, data, moeda, boolean',
    valor_padrao TEXT,
    origem VARCHAR(50) COMMENT 'empresa, cliente, orcamento, manual',
    
    -- Controle
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_parametro_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_contrato_parametro_empresa_codigo UNIQUE (empresa_id, codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_contrato_parametro_empresa ON contrato_parametros(empresa_id);
CREATE INDEX idx_contrato_parametro_origem ON contrato_parametros(origem);

-- =========================
-- 7) CONTRATO PARÂMETROS VALORES
-- =========================
CREATE TABLE IF NOT EXISTS contrato_parametros_valores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contrato_id INT NOT NULL,
    parametro_id INT NOT NULL,
    
    valor TEXT NOT NULL,
    
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_parametro_valor_contrato FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_contrato_parametro_valor_parametro FOREIGN KEY (parametro_id) REFERENCES contrato_parametros(id),
    CONSTRAINT uq_contrato_parametro_valor UNIQUE (contrato_id, parametro_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_contrato_parametro_valor_contrato ON contrato_parametros_valores(contrato_id);
CREATE INDEX idx_contrato_parametro_valor_parametro ON contrato_parametros_valores(parametro_id);

-- =========================
-- 8) DADOS INICIAIS - CLÁUSULAS PADRÃO
-- =========================
INSERT INTO clausulas_contrato_padrao (
    empresa_id, codigo, titulo, texto_base, descricao, tipo, editavel, ordem_padrao, 
    categoria, tipo_contrato, criado_por_user_id
) VALUES
-- Cláusulas Obrigatórias
(1, 'OBJ', 'Objeto', 
'CLÁUSULA PRIMEIRA - DO OBJETO

1.1. O presente contrato tem como objeto a prestação de serviços de {CONTRATO_DESCRICAO_SERVICOS} pela CONTRATADA em favor da CONTRATANTE.

1.2. Os serviços serão executados de forma remota, utilizando meios eletrônicos e digitais, conforme especificações técnicas acordadas entre as partes.

1.3. A CONTRATADA compromete-se a executar os serviços com o grau de diligência e profissionalismo adequados, observando as melhores práticas de mercado.',
'Define o objeto do contrato de prestação de serviços.', 'obrigatoria', 1, 1, 'geral', 'prestacao_servicos', 1),

(1, 'EXEC', 'Execução Remota',
'CLÁUSULA SEGUNDA - DA EXECUÇÃO REMOTA

2.1. A prestação dos serviços será realizada predominantemente de forma remota, sem necessidade de deslocamento físico da CONTRATADA às instalações da CONTRATANTE.

2.2. A CONTRATANTE deverá disponibilizar acesso aos sistemas e informações necessários para a execução dos serviços, bem como manter ponto de contato para comunicação.

2.3. A CONTRATADA poderá solicitar reuniões presenciais quando necessário para alinhamento estratégico ou treinamento.',
'Define a forma de execução remota dos serviços.', 'obrigatoria', 1, 2, 'tecnico', 'prestacao_servicos', 1),

(1, 'SIGILO', 'Sigilo e Confidencialidade',
'CLÁUSULA TERCEIRA - DO SIGILO E CONFIDENCIALIDADE

3.1. A CONTRATADA compromete-se a manter em sigilo todas as informações confidenciais da CONTRATANTE a que tiver acesso em razão da execução deste contrato.

3.2. O dever de confidencialidade perdura após o término deste contrato, independentemente da causa de sua rescisão.

3.3. A CONTRATADA não poderá divulgar, reproduzir ou utilizar as informações confidenciais para qualquer finalidade que não a execução dos serviços contratados.',
'Estabelece o dever de sigilo e confidencialidade.', 'obrigatoria', 1, 3, 'juridico', 'prestacao_servicos', 1),

(1, 'HONOR', 'Honorários e Condições de Pagamento',
'CLÁUSULA QUARTA - DOS HONORÁRIOS E CONDIÇÕES DE PAGAMENTO

4.1. Pelos serviços objeto deste contrato, a CONTRATANTE pagará à CONTRATADA o valor total de {CONTRATO_VALOR_TOTAL}, na forma e condições a seguir descritas.

4.2. O valor mensal dos serviços é de {CONTRATO_VALOR_MENSAL}, pagável mediante {CONTRATO_FORMA_PAGAMENTO}.

4.3. O pagamento deverá ser efetuado até o dia 5 de cada mês, referente aos serviços prestados no mês anterior.

4.4. O atraso no pagamento implicará na incidência de juros de mora de 1% ao mês e multa de 2% sobre o valor em atraso.',
'Define os honorários e condições de pagamento.', 'obrigatoria', 1, 4, 'financeiro', 'prestacao_servicos', 1),

(1, 'VIGENC', 'Vigência e Rescisão',
'CLÁUSULA QUINTA - DA VIGÊNCIA E RESCISÃO

5.1. O presente contrato terá vigência de {CONTRATO_DATA_INICIO} a {CONTRATO_DATA_FIM}, podendo ser prorrogado mediante acordo expresso entre as partes.

5.2. Qualquer das partes poderá rescindir este contrato mediante aviso prévio de 30 (trinta) dias, por escrito.

5.3. A rescisão por justa causa, decorrente de inadimplemento de obrigação contratual, não exigirá aviso prévio.

5.4. Em caso de rescisão, a CONTRATANTE pagará os serviços já executados até a data da rescisão.',
'Define a vigência do contrato e condições de rescisão.', 'obrigatoria', 1, 5, 'juridico', 'prestacao_servicos', 1),

(1, 'RESP', 'Responsabilidades Técnicas',
'CLÁUSULA SEXTA - DAS RESPONSABILIDADES TÉCNICAS

6.1. A CONTRATADA responsabiliza-se pela qualidade técnica dos serviços prestados, comprometendo-se a corrigir eventuais falhas ou erros que venham a ser identificados.

6.2. A CONTRATADA não se responsabiliza por danos decorrentes de informações incorretas ou incompletas fornecidas pela CONTRATANTE.

6.3. A CONTRATADA manterá equipe técnica qualificada para a execução dos serviços, garantindo a continuidade e qualidade do atendimento.',
'Define as responsabilidades técnicas da CONTRATADA.', 'opcional', 1, 6, 'tecnico', 'prestacao_servicos', 1),

(1, 'VINCULO', 'Inexistência de Vínculo Trabalhista',
'CLÁUSULA SÉTIMA - DA INEXISTÊNCIA DE VÍNCULO TRABALHISTA

7.1. O presente contrato constitui relação de prestação de serviços autônomos, não caracterizando vínculo empregatício entre a CONTRATANTE e os colaboradores da CONTRATADA.

7.2. A CONTRATADA é responsável por todos os encargos trabalhistas, previdenciários e fiscais relativos aos seus colaboradores.

7.3. A CONTRATANTE não exerce qualquer poder de direção, fiscalização ou controle sobre os colaboradores da CONTRATADA, limitando-se a receber os resultados dos serviços contratados.',
'Estabelece expressamente a inexistência de vínculo trabalhista.', 'obrigatoria', 0, 7, 'trabalhista', 'prestacao_servicos', 1),

(1, 'FORO', 'Foro',
'CLÁUSULA OITAVA - DO FORO

8.1. As partes elegem o foro da comarca de {CONTRATADA_CIDADE} para dirimir quaisquer dúvidas ou controvérsias decorrentes deste contrato, com renúncia expressa a qualquer outro, por mais privilegiado que seja.',
'Define o foro competente para solução de controvérsias.', 'opcional', 1, 8, 'juridico', 'prestacao_servicos', 1),

(1, 'ACEITE', 'Aceitação com Efeito Contratual',
'CLÁUSULA NONA - DA ACEITAÇÃO COM EFEITO CONTRATUAL

9.1. A assinatura deste contrato pelas partes implica aceitação integral de todas as suas cláusulas e condições.

9.2. Este contrato entra em vigor na data de sua assinatura, salvo disposição em contrário.

9.3. As partes declaram que leram e compreenderam todas as cláusulas deste contrato, assinando-o em duas vias de igual teor e forma.',
'Estabelece que a assinatura implica aceitação das cláusulas.', 'obrigatoria', 1, 9, 'juridico', 'prestacao_servicos', 1);

-- =========================
-- 9) DADOS INICIAIS - PARÂMETROS
-- =========================
INSERT INTO contrato_parametros (
    empresa_id, codigo, nome, descricao, tipo_dado, valor_padrao, origem, ativo
) VALUES
(1, 'CONTRATADA_RAZAO_SOCIAL', 'Razão Social Contratada', 'Razão social da empresa prestadora', 'texto', NULL, 'empresa', 1),
(1, 'CONTRATADA_CNPJ', 'CNPJ Contratada', 'CNPJ da empresa prestadora', 'texto', NULL, 'empresa', 1),
(1, 'CONTRATADA_ENDERECO', 'Endereço Contratada', 'Endereço completo da empresa prestadora', 'texto', NULL, 'empresa', 1),
(1, 'CONTRATADA_CIDADE', 'Cidade Contratada', 'Cidade da empresa prestadora', 'texto', NULL, 'empresa', 1),
(1, 'CONTRATADA_UF', 'UF Contratada', 'UF da empresa prestadora', 'texto', NULL, 'empresa', 1),
(1, 'CONTRATANTE_RAZAO_SOCIAL', 'Razão Social Contratante', 'Razão social ou nome do cliente', 'texto', NULL, 'cliente', 1),
(1, 'CONTRATANTE_CNPJ_CPF', 'CNPJ/CPF Contratante', 'CNPJ ou CPF do cliente', 'texto', NULL, 'cliente', 1),
(1, 'CONTRATANTE_ENDERECO', 'Endereço Contratante', 'Endereço completo do cliente', 'texto', NULL, 'cliente', 1),
(1, 'CONTRATANTE_CIDADE', 'Cidade Contratante', 'Cidade do cliente', 'texto', NULL, 'cliente', 1),
(1, 'CONTRATANTE_UF', 'UF Contratante', 'UF do cliente', 'texto', NULL, 'cliente', 1),
(1, 'CONTRATO_VALOR_TOTAL', 'Valor Total do Contrato', 'Valor total do contrato', 'moeda', NULL, 'orcamento', 1),
(1, 'CONTRATO_VALOR_MENSAL', 'Valor Mensal', 'Valor mensal do contrato', 'moeda', NULL, 'orcamento', 1),
(1, 'CONTRATO_FORMA_PAGAMENTO', 'Forma de Pagamento', 'Forma de pagamento acordada', 'texto', NULL, 'orcamento', 1),
(1, 'CONTRATO_PERIODICIDADE', 'Periodicidade', 'Periodicidade do pagamento', 'texto', NULL, 'orcamento', 1),
(1, 'CONTRATO_DATA_INICIO', 'Data Início Vigência', 'Data de início da vigência do contrato', 'data', NULL, 'contrato', 1),
(1, 'CONTRATO_DATA_FIM', 'Data Fim Vigência', 'Data de fim da vigência do contrato', 'data', NULL, 'contrato', 1),
(1, 'CONTRATO_DESCRICAO_SERVICOS', 'Descrição dos Serviços', 'Descrição resumida dos serviços contratados', 'texto', NULL, 'orcamento', 1),
(1, 'CONTRATO_NUMERO', 'Número do Contrato', 'Número de identificação do contrato', 'texto', NULL, 'contrato', 1),
(1, 'CONTRATO_DATA_ASSINATURA', 'Data de Assinatura', 'Data de assinatura do contrato', 'data', NULL, 'contrato', 1);

-- =========================
-- FIM DO SCRIPT
-- =========================
