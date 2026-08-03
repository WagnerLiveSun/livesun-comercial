# Modelo de Dados - Módulo de Gestão de Contratos

## Visão Geral

Este documento define o modelo conceitual de dados para o módulo de gestão de contratos, integrado ao ERP existente.

## Entidades Principais

### 1. clausulas_contrato_padrao (Biblioteca de Cláusulas)

Biblioteca central de cláusulas padrão que podem ser reutilizadas em múltiplos contratos.

```sql
CREATE TABLE clausulas_contrato_padrao (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Identificação
    codigo VARCHAR(50) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    
    -- Conteúdo
    texto_base TEXT NOT NULL,
    descricao TEXT,
    
    -- Configuração
    tipo VARCHAR(20) NOT NULL DEFAULT 'opcional', -- 'obrigatoria', 'opcional', 'condicional'
    editavel BOOLEAN NOT NULL DEFAULT true,
    ordem_padrao INTEGER NOT NULL DEFAULT 0,
    
    -- Categorização
    categoria VARCHAR(50), -- 'geral', 'financeiro', 'juridico', 'tecnico', 'trabalhista'
    tipo_contrato VARCHAR(50), -- 'prestacao_servicos', 'fornecimento', 'parceria', etc.
    
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
```

### 2. contratos (Contratos)

Registro principal de contratos gerados a partir de orçamentos.

```sql
CREATE TABLE contratos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Identificação
    numero VARCHAR(50) NOT NULL,
    serie VARCHAR(10) DEFAULT 'CTR',
    titulo VARCHAR(200),
    
    -- Vinculação
    orcamento_id INTEGER,
    cliente_id INTEGER NOT NULL,
    vendedor_id INTEGER,
    
    -- Dados das partes
    contratada_entidade_id INTEGER NOT NULL, -- Empresa prestadora (ex: LiveSun)
    contratante_entidade_id INTEGER NOT NULL, -- Cliente
    
    -- Dados comerciais
    valor_total NUMERIC(15,2) NOT NULL,
    valor_mensal NUMERIC(15,2),
    forma_pagamento VARCHAR(100),
    periodicidade VARCHAR(50), -- 'mensal', 'trimestral', 'semestral', 'anual', 'unico'
    data_inicio_vigencia DATE NOT NULL,
    data_fim_vigencia DATE,
    
    -- Status e controle
    status VARCHAR(20) NOT NULL DEFAULT 'rascunho', -- 'rascunho', 'aguardando_assinatura', 'assinado', 'cancelado', 'rescindido'
    motivo_cancelamento TEXT,
    
    -- Descrição dos serviços
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
```

### 3. contrato_clausulas (Instâncias de Cláusulas no Contrato)

Cada cláusula incluída em um contrato específico, com seu texto personalizado.

```sql
CREATE TABLE contrato_clausulas (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL,
    
    -- Referência à cláusula padrão
    clausula_padrao_id INTEGER,
    
    -- Dados da cláusula no contrato
    titulo VARCHAR(200) NOT NULL,
    texto TEXT NOT NULL,
    
    -- Configuração
    ordem INTEGER NOT NULL,
    editavel BOOLEAN NOT NULL DEFAULT true,
    obrigatoria BOOLEAN NOT NULL DEFAULT false,
    
    -- Controle de alterações
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
```

### 4. contrato_historico (Versionamento de Contratos)

Histórico de alterações do contrato para auditoria e rastreabilidade.

```sql
CREATE TABLE contrato_historico (
    id BIGSERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL,
    
    -- Versão
    versao INTEGER NOT NULL,
    acao VARCHAR(50) NOT NULL, -- 'criado', 'editado', 'assinado', 'cancelado', 'rescindido'
    
    -- Estado do contrato naquele momento
    status_anterior VARCHAR(20),
    status_novo VARCHAR(20),
    
    -- Detalhes da alteração
    descricao_alteracao TEXT,
    campos_alterados JSONB, -- Lista de campos que foram alterados
    clausulas_alteradas JSONB, -- Lista de cláusulas alteradas
    
    -- Quem fez a alteração
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
```

### 5. contrato_anexos (Anexos do Contrato)

Arquivos anexados ao contrato (PDF assinado, documentos complementares, etc.).

```sql
CREATE TABLE contrato_anexos (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL,
    
    -- Arquivo
    nome_arquivo VARCHAR(255) NOT NULL,
    tipo_arquivo VARCHAR(100) NOT NULL, -- 'pdf', 'docx', 'jpg', etc.
    tamanho_bytes BIGINT,
    caminho_arquivo VARCHAR(500) NOT NULL,
    
    -- Descrição
    descricao VARCHAR(255),
    tipo_anexo VARCHAR(50) NOT NULL, -- 'contrato_assinado', 'documento_identificacao', 'comprovante', 'outro'
    
    -- Controle
    criado_por_user_id INTEGER NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_anexo_contrato FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_contrato_anexo_criado_por FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_contrato_anexo_contrato ON contrato_anexos(contrato_id);
CREATE INDEX idx_contrato_anexo_tipo ON contrato_anexos(tipo_anexo);
```

### 6. contrato_parametros (Parâmetros de Substituição)

Definição de parâmetros/variáveis que podem ser usados nas cláusulas para substituição dinâmica.

```sql
CREATE TABLE contrato_parametros (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Identificação
    codigo VARCHAR(50) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    
    -- Configuração
    tipo_dado VARCHAR(20) NOT NULL DEFAULT 'texto', -- 'texto', 'numero', 'data', 'moeda', 'boolean'
    valor_padrao TEXT,
    origem VARCHAR(50), -- 'empresa', 'cliente', 'orcamento', 'manual'
    
    -- Controle
    ativo BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_contrato_parametro_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT uq_contrato_parametro_empresa_codigo UNIQUE (empresa_id, codigo)
);

CREATE INDEX idx_contrato_parametro_empresa ON contrato_parametros(empresa_id);
CREATE INDEX idx_contrato_parametro_origem ON contrato_parametros(origem);
```

### 7. contrato_parametros_valores (Valores de Parâmetros por Contrato)

Valores específicos dos parâmetros para cada contrato.

```sql
CREATE TABLE contrato_parametros_valores (
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
```

## Relacionamentos

```
empresas (1) ----< (N) clausulas_contrato_padrao
empresas (1) ----< (N) contratos
empresas (1) ----< (N) contrato_parametros

orcamentos (1) ----< (1) contratos
entidades (1) ----< (N) contratos (como cliente)
entidades (1) ----< (N) contratos (como vendedor)
entidades (1) ----< (N) contratos (como contratada)
entidades (1) ----< (N) contratos (como contratante)

contratos (1) ----< (N) contrato_clausulas
contratos (1) ----< (N) contrato_historico
contratos (1) ----< (N) contrato_anexos
contratos (1) ----< (N) contrato_parametros_valores

clausulas_contrato_padrao (1) ----< (N) contrato_clausulas
contrato_parametros (1) ----< (N) contrato_parametros_valores

users (1) ----< (N) contratos (gerado_por)
users (1) ----< (N) contratos (assinado_por)
users (1) ----< (N) clausulas_contrato_padrao (criado_por)
users (1) ----< (N) clausulas_contrato_padrao (atualizado_por)
users (1) ----< (N) contrato_clausulas (alterado_por)
users (1) ----< (N) contrato_historico (alterado_por)
users (1) ----< (N) contrato_anexos (criado_por)
```

## Placeholders Padrão

Parâmetros de substituição que podem ser usados nas cláusulas:

| Código | Nome | Origem | Exemplo |
|--------|------|--------|---------|
| CONTRATADA_RAZAO_SOCIAL | Razão Social Contratada | empresa | LiveSun Tecnologia Ltda |
| CONTRATADA_CNPJ | CNPJ Contratada | empresa | 12.345.678/0001-90 |
| CONTRATADA_ENDERECO | Endereço Contratada | empresa | Rua Example, 123 |
| CONTRATADA_CIDADE | Cidade Contratada | empresa | São Paulo |
| CONTRATADA_UF | UF Contratada | empresa | SP |
| CONTRATANTE_RAZAO_SOCIAL | Razão Social Contratante | cliente | Cliente Exemplo Ltda |
| CONTRATANTE_CNPJ_CPF | CNPJ/CPF Contratante | cliente | 98.765.432/0001-10 |
| CONTRATANTE_ENDERECO | Endereço Contratante | cliente | Av. Example, 456 |
| CONTRATANTE_CIDADE | Cidade Contratante | cliente | Rio de Janeiro |
| CONTRATANTE_UF | UF Contratante | cliente | RJ |
| CONTRATO_VALOR_TOTAL | Valor Total do Contrato | orcamento | R$ 50.400,00 |
| CONTRATO_VALOR_MENSAL | Valor Mensal | orcamento | R$ 4.200,00 |
| CONTRATO_FORMA_PAGAMENTO | Forma de Pagamento | orcamento | Boleto bancário, vencimento dia 5 |
| CONTRATO_PERIODICIDADE | Periodicidade | orcamento | Mensal |
| CONTRATO_DATA_INICIO | Data Início Vigência | contrato | 01/01/2026 |
| CONTRATO_DATA_FIM | Data Fim Vigência | contrato | 31/12/2026 |
| CONTRATO_DESCRICAO_SERVICOS | Descrição dos Serviços | orcamento | Serviços remotos de apoio à escrituração contábil |
| CONTRATO_NUMERO | Número do Contrato | contrato | CTR-2026-0001 |
| CONTRATO_DATA_ASSINATURA | Data de Assinatura | contrato | 15/01/2026 |

## Exemplo de Cláusula com Placeholders

```text
CLÁUSULA PRIMEIRA - DO OBJETO

1.1. O presente contrato tem como objeto a prestação de serviços de {CONTRATO_DESCRICAO_SERVICOS} pela CONTRATADA em favor da CONTRATANTE.

1.2. Os serviços serão executados de forma remota, utilizando meios eletrônicos e digitais, conforme especificações técnicas acordadas entre as partes.

1.3. A CONTRATADA compromete-se a executar os serviços com o grau de diligência e profissionalismo adequados, observando as melhores práticas de mercado.
```

## Integração com Módulos Existentes

### Módulo de Orçamentos
- `orcamentos` → `contratos.orcamento_id`
- Dados comerciais (valor, itens, condições) são copiados para o contrato

### Módulo de Entidades
- `entidades` → `contratos.cliente_id` (CONTRATANTE)
- `entidades` → `contratos.contratada_entidade_id` (CONTRATADA)
- `entidades` → `contratos.vendedor_id`

### Módulo de Faturamento
- `contratos.valor_mensal` → base para cobrança recorrente
- `contratos.periodicidade` → define frequência de cobrança
- `contratos.data_inicio_vigencia` → data início cobranças

### Módulo Financeiro
- `contratos.forma_pagamento` → define método de pagamento
- `contratos.status = 'assinado'` → gera lançamentos financeiros
