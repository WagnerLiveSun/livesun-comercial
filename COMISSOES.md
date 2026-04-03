# Documentação - Módulo de Comissões

## Visão Geral

O módulo de comissões do LiveSun Financeiro automatiza o cálculo, apuração e relatório de comissões sobre lançamentos financeiros, com suporte a alíquotas específicas por cliente e vendedor.

## Índice

1. [Instalação e Migração](#instalação-e-migração)
2. [Configuração Inicial](#configuração-inicial)
3. [Como Usar](#como-usar)
4. [Cálculos e Fórmulas](#cálculos-e-fórmulas)
5. [API de Serviços](#api-de-serviços)
6. [Exemplos](#exemplos)
7. [Troubleshooting](#troubleshooting)

## Instalação e Migração

### Passo 1: Criar as Tabelas no Banco de Dados

Execute um dos seguintes métodos:

#### Opção A: Usar o script Python de migração

```bash
python migrate_comissoes.py
```

Este script:
- Cria as tabelas necesárias (se não existirem)
- Verifica se há campos pendentes
- Inicializa os parâmetros de sistema

#### Opção B: Executar SQL manualmente

1. Abra seu cliente MySQL (phpMyAdmin, MySQL Workbench, etc.)
2. Execute os comandos SQL em `migrations/001_create_comissoes_tables.sql`

Os comandos principais a executar:

```sql
-- Adicionar campos a lançamentos
ALTER TABLE lancamentos 
ADD COLUMN valor_imposto DECIMAL(15, 2) DEFAULT 0.00,
ADD COLUMN valor_outros_custos DECIMAL(15, 2) DEFAULT 0.00;

-- Adicionar campos a entidades
ALTER TABLE entidades 
ADD COLUMN aliquota_comissao_especifica DECIMAL(5, 2),
ADD COLUMN valor_repasse DECIMAL(10, 2) DEFAULT 0.00,
ADD COLUMN entidade_vendedor_padrao_id INT;

-- Adicionar FK (se necessário)
ALTER TABLE entidades 
ADD FOREIGN KEY (entidade_vendedor_padrao_id) REFERENCES entidades(id);

-- Criar tabela de parâmetros
CREATE TABLE parametros_sistema (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    chave VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    tipo VARCHAR(20) DEFAULT 'string',
    descricao VARCHAR(255),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_parametro_chave (empresa_id, chave),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Criar tabela de comissões
CREATE TABLE comissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    id_apuracao INT NOT NULL,
    lancamento_id INT NOT NULL,
    entidade_cliente_id INT NOT NULL,
    entidade_vendedor_id INT NOT NULL,
    dt_lancamento DATE NOT NULL,
    dt_vencimento DATE NOT NULL,
    dt_pagamento_recebimento DATE NOT NULL,
    vl_nota DECIMAL(15, 2) NOT NULL,
    vl_imposto DECIMAL(15, 2) DEFAULT 0.00,
    vl_outros_custos DECIMAL(15, 2) DEFAULT 0.00,
    vl_repasse DECIMAL(15, 2) DEFAULT 0.00,
    vl_liquido DECIMAL(15, 2) NOT NULL,
    aliquota_aplicada DECIMAL(5, 2) NOT NULL,
    vl_comissao DECIMAL(15, 2) NOT NULL,
    situacao VARCHAR(20) DEFAULT 'ativo',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    FOREIGN KEY (entidade_cliente_id) REFERENCES entidades(id),
    FOREIGN KEY (entidade_vendedor_id) REFERENCES entidades(id),
    INDEX idx_comissao_apuracao (empresa_id, id_apuracao),
    INDEX idx_comissao_datas (dt_pagamento_recebimento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Inserir parâmetro padrão
INSERT INTO parametros_sistema (empresa_id, chave, valor, tipo, descricao)
VALUES (1, 'aliquota_comissao_padrao', '5.00', 'numeric', 'Alíquota padrão de comissão');
```

## Configuração Inicial

### 1. Criar Tipos de Entidade

Antes de configurar comissões, certifique-se de ter:

- **Vendedores**: Entidades do tipo "Vendedor" (V)
- **Clientes**: Entidades do tipo "Cliente" (C)

Vá para: **Entidades → Nova Entidade**

Crie pelo menos:
- Um vendedor
- Um cliente

### 2. Configurar Alíquota Padrão

1. Vá para: **Comissões → Parâmetros**
2. Configure a "**Alíquota Padrão de Comissão**" (ex: 5.00%)
3. Clique em "Salvar Parâmetros"

### 3. Configurar Cliente com Dados de Comissão

1. Vá para: **Entidades**
2. Clique em um cliente existente ou crie um novo
3. Preencha os campos:
   - **Alíquota Específica de Comissão**: (opcional - deixar em branco usa a padrão)
   - **Percentual de Repasse ao Fornecedor**: (ex: 10.00%)
   - **Vendedor Padrão**: Selecione um vendedor
4. Salve

### 4. Adicionar Campos a Lançamentos

Ao criar ou editar um lançamento, agora você pode preencher:
- **Valor do Imposto**: (ex: 50.00)
- **Valor de Outros Custos**: (ex: 10.00)

## Como Usar

### Fluxo Completo

#### 1º - Registrar Lançamentos

1. Vá para: **Lançamentos → Novo Lançamento**
2. Preencha os dados:
   - Cliente (tipo deve ser "Cliente")
   - Valor da nota
   - **Novo**: Valor do Imposto
   - **Novo**: Valor de Outros Custos
   - Data de pagamento (importante!)
3. Configure o status como "Pago"
4. Salve

#### 2º - Apurar Comissões

1. Vá para: **Comissões → Apurar**
2. Selecione o período desejado:
   - **Data de Início**: (ex: 2026-01-01)
   - **Data de Fim**: (ex: 2026-02-28)
3. Clique em "Executar Apuração"

O sistema:
- Busca todos os lançamentos pagos no período
- Calcula a comissão para cada um
- Registra na tabela de comissões
- Gera um ID de apuração (sequence)

#### 3º - Visualizar Comissões

1. Vá para: **Comissões → Lista**
2. Use os filtros para refinar:
   - Por período
   - Por vendedor
   - Por cliente
3. Veja o resumo no topo (totais)

#### 4º - Gerar Relatório

1. Vá para: **Comissões → Relatório**
2. Configure os mesmos filtros da lista
3. Dados agrupados por vendedor
4. Inclui subtotais e total geral

#### 5º - Exportar

1. Na lista de comissões, clique em "Exportar CSV"
2. O arquivo é baixado automaticamente
3. Abra em Excel para análise adicional

## Cálculos e Fórmulas

### Base de Cálculo (Valor Líquido)

```
vl_liquido = vl_nota - vl_imposto - vl_outros_custos - vl_repasse

Exemplo:
vl_nota = 1000.00
vl_imposto = 100.00
vl_outros_custos = 50.00
valor_repasse = 50.00
vl_liquido = 1000 - 100 - 50 - 50 = 800.00
```

### Seleção de Alíquota

```
IF cliente.aliquota_comissao_especifica IS NOT NULL
  THEN aliquota = cliente.aliquota_comissao_especifica
ELSE
  aliquota = parametro_sistema.aliquota_comissao_padrao
END
```

### Cálculo da Comissão

```
vl_comissao = vl_liquido × (aliquota / 100)

Exemplo:
vl_liquido = 800.00
aliquota = 5%
vl_comissao = 800 × (5 / 100) = 40.00
```

## API de Serviços

O módulo de comissões fornece uma API Python para integração:

```python
from src.services.comissoes import ServicoComissoes
from datetime import datetime

# 1. Obter alíquota padrão
aliquota = ServicoComissoes.obter_aliquota_padrao(empresa_id=1)

# 2. Calcular valor líquido
vl_liquido = ServicoComissoes.calcular_valor_liquido(lancamento, cliente)

# 3. Calcular comissão
vl_comissao = ServicoComissoes.calcular_comissao(vl_liquido, aliquota)

# 4. Executar apuração completa
resultado = ServicoComissoes.apurar_comissoes(
    empresa_id=1,
    data_inicio=datetime(2026, 1, 1).date(),
    data_fim=datetime(2026, 2, 28).date(),
    vendedor_id=None,  # opcional
    cliente_id=None    # opcional
)

# 5. Obter comissões filtradas
comissoes = ServicoComissoes.obter_comissoes_filtradas(
    empresa_id=1,
    data_inicio=datetime(2026, 1, 1).date(),
    data_fim=datetime(2026, 2, 28).date()
)

# 6. Obter resumo por vendedor
resumo = ServicoComissoes.obter_resumo_por_vendedor(
    empresa_id=1,
    data_inicio=datetime(2026, 1, 1).date(),
    data_fim=datetime(2026, 2, 28).date()
)
```

## Exemplos

### Exemplo 1: Cliente com Alíquota Específica

```
Cliente: ABC Ltda
Alíquota Específica: 3%
Valor da Nota: 2000.00
Imposto: 200.00
Outros Custos: 100.00
Repasse: 5% = 100.00

Cálculo:
vl_liquido = 2000 - 200 - 100 - 100 = 1600.00
aliquota = 3% (específica do cliente, não usa padrão)
vl_comissao = 1600 × 0.03 = 48.00
```

### Exemplo 2: Cliente usando Alíquota Padrão

```
Cliente: XYZ Ltda
Alíquota Específica: vazia (usa padrão)
Valor da Nota: 1500.00
Imposto: 150.00
Outros Custos: 50.00
Repasse: 10% = 150.00

Cálculo:
vl_liquido = 1500 - 150 - 50 - 150 = 1150.00
aliquota = 5% (padrão do sistema)
vl_comissao = 1150 × 0.05 = 57.50
```

## Troubleshooting

### P: "Erro na apuração: Lançamento 123 sem vendedor definido"

**R:** O cliente do lançamento não possui vendedor padrão configurado.

**Solução:**
1. Vá para **Entidades**
2. Abra o cliente
3. Configure o campo "**Vendedor Padrão**"
4. Salve
5. Tente a apuração novamente

### P: "Nenhuma comissão encontrada no período"

**R:** Pode ser por vários motivos:

**Verificar:**
1. Os lançamentos estão com status "Pago"?
2. A data de pagamento está dentro do período selecionado?
3. As entidades dos lançamentos são do tipo "Cliente"?
4. O cliente tem vendedor padrão configurado?

### P: Comissão foi calculada errada

**R:** Verificar:

1. **Alíquota**: cliente tem específica? Ou está usando a padrão?
2. **Base de cálculo**: os valores de imposto e outros custos estão corretos?
3. **Repasse**: o percentual de repasse está no cliente?

Use a fórmula acima para recalcular manualmente.

### P: Posso reapurar o mesmo período?

**R:** NÃO. O sistema bloqueia re-apuração da mesma nota.

Se precisar corrigir:
1. Edite o lançamento original
2. Crie um novo lançamento de ajuste (negativo ou positivo)
3. Apure novamente

## Segurança e Validações

- ✓ Anti-duplicidade: Uma nota não é apurada 2x
- ✓ Constraints de FK: Garantem integridade referencial
- ✓ Índices: Performance em consultas grandes
- ✓ Transações: Tudo ou nada na apuração
- ✓ Autenticação: Apenas usuários logados acessam comissões

## Contato e Suporte

Para dúvidas:
1. Consulte a documentação técnica em [TECHNICAL.md](./TECHNICAL.md)
2. Acesse o menu **Suporte** na aplicação
3. Envie um email com print da tela e descrição do problema
