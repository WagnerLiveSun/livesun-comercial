# Análise de Erros - Script PostgreSQL

## Problemas Identificados

### 1. Tabelas Faltantes no Script Principal

O script `criar_banco_comercial_postgresql.sql` está **INCOMPLETO**. Faltam as seguintes tabelas do schema MySQL:

#### Tabelas Operacionais (Comercial)
- ❌ `filiais` - Filiais da empresa
- ❌ `produtos` - Cadastro de produtos
- ❌ `servicos` - Cadastro de serviços
- ❌ `estoque_movimentos` - Movimentação de estoque
- ❌ `compras_nf_manual` - Notas fiscais de compra manual
- ❌ `compras_nf_itens` - Itens de notas de compra
- ❌ `compras_nf_lancamentos` - Lançamentos financeiros de compras
- ❌ `documentos_venda` - Documentos de venda
- ❌ `documentos_venda_itens` - Itens de documentos de venda

#### Tabelas de Preço
- ❌ `tabelas_preco` - Tabelas de preço
- ❌ `tabelas_preco_itens` - Itens de tabelas de preço

#### Tabelas de Orçamento e Pedidos
- ❌ `orcamentos` - Orçamentos
- ❌ `orcamentos_itens` - Itens de orçamentos
- ❌ `pedidos_venda` - Pedidos de venda
- ❌ `pedidos_venda_itens` - Itens de pedidos

#### Tabelas de PDV (Ponto de Venda)
- ❌ `pdv_sessoes` - Sessões de caixa
- ❌ `pdv_vendas` - Vendas do PDV
- ❌ `pdv_itens` - Itens de vendas PDV

#### Tabelas de Assinatura/Cobrança (estão em migração 009, mas não no script principal)
- ⚠️ `catalogo_planos_comercial` - Apenas no script de migração
- ⚠️ `assinatura_empresa` - Apenas no script de migração
- ⚠️ `cobranca_recorrente` - Apenas no script de migração
- ⚠️ `evento_cobranca` - Apenas no script de migração
- ⚠️ `historico_mudanca_plano` - Apenas no script de migração
- ⚠️ `notificacao_comercial` - Apenas no script de migração

#### Tabelas NF-e Nacional (estão em migração 013, mas não no script principal)
- ⚠️ `nfse_nacional_configuracoes` - Apenas no script de migração
- ⚠️ `nfse_nacional_certificados` - Apenas no script de migração
- ⚠️ `nfse_nacional_integracoes_origem` - Apenas no script de migração
- ⚠️ `nfse_nacional_emissoes` - Apenas no script de migração
- ⚠️ `nfse_nacional_fila` - Apenas no script de migração
- ⚠️ `nfse_nacional_eventos` - Apenas no script de migração

### 2. Erro de Digitação

**Linha 336 do script PostgreSQL:**
```sql
fonte VARCHAR(50) NOT NULL DEFAULT 'manaul'
```
- ❌ Erro: "manaul" em vez de "manual"

**Correção:**
```sql
fonte VARCHAR(50) NOT NULL DEFAULT 'manual'
```

### 3. Índices Faltantes

Comparando com o schema MySQL, os seguintes índices estão ausentes no script PostgreSQL:

#### Tabela `comissoes`
- ❌ `idx_comissoes_lancamento_data` (dt_lancamento)
- ❌ `idx_comissoes_vencimento` (dt_vencimento)
- ❌ `idx_comissao_empresa_lancamento` (empresa_id, lancamento_id, entidade_cliente_id, entidade_vendedor_id)

#### Tabela `importacao_nfse`
- ❌ `idx_nfse_chave` (chave_nota)

#### Tabela `conciliacao_item`
- ❌ `idx_conciliacao_item_data` (data_movimento)

#### Tabela `assinatura_empresa` (se incluída)
- ❌ `idx_assinatura_gateway_customer` (gateway_customer_id)
- ❌ `idx_assinatura_gateway_subscription` (gateway_subscription_id)
- ❌ `idx_assinatura_renovacao` (data_renovacao)
- ❌ `idx_assinatura_fim_trial` (data_fim_trial)
- ❌ `idx_assinatura_limite_carencia` (data_limite_carencia)
- ❌ `idx_assinatura_mudanca` (mudanca_plano_efetivar_em)

#### Tabela `cobranca_recorrente` (se incluída)
- ❌ `idx_cobranca_gateway` (gateway)

#### Tabela `evento_cobranca` (se incluída)
- ❌ `idx_evento_gateway` (gateway)

#### Tabela `historico_mudanca_plano` (se incluída)
- ❌ `idx_hist_solicitado_por` (solicitado_por_user_id)
- ❌ `idx_hist_executado_por` (executado_por_user_id)

### 4. Problema no INSERT do fluxo_contas_modelo

**Linha 186-234 do script PostgreSQL:**
```sql
INSERT INTO fluxo_contas_modelo (...) VALUES
(1, '1', 'Entradas de Caixa', ...),
```

- ⚠️ Problema: Usa `empresa_id = 1` hardcoded
- ⚠️ Se a tabela `empresas` não tiver um registro com ID=1, o INSERT falhará
- ⚠️ O script MySQL original usa uma variável `@empresa_id`

**Solução recomendada:**
- Remover o INSERT do script principal
- Adicionar instrução para inserir após criar a empresa
- Ou usar `ON CONFLICT DO NOTHING` para evitar erro

### 5. Trigger Faltante

A tabela `rbac_roles` tem trigger, mas a tabela `rbac_permissions` não tem trigger (embora não tenha campo `atualizado_em`).

### 6. Constraint Única Faltante

Tabela `comissoes`:
- MySQL tem: `UNIQUE INDEX idx_comissao_unica (lancamento_id, entidade_cliente_id, entidade_vendedor_id, situacao)`
- PostgreSQL tem: ❌ Ausente

## Resumo

| Categoria | Total | Presentes | Faltantes |
|-----------|-------|-----------|-----------|
| Tabelas Core | 10 | 10 | 0 |
| Tabelas Operacionais | 9 | 0 | 9 |
| Tabelas de Preço | 2 | 0 | 2 |
| Orçamentos/Pedidos | 4 | 0 | 4 |
| PDV | 3 | 0 | 3 |
| Assinatura/Cobrança | 6 | 0 (em migração) | 6 |
| NF-e Nacional | 6 | 0 (em migração) | 6 |
| **TOTAL** | **40** | **10** | **30** |

## Recomendação

O script principal deve ser **reescrito** para incluir todas as tabelas faltantes. As tabelas de migração (assinatura e NF-e) podem permanecer separadas, mas deveriam ser documentadas claramente como etapas adicionais.
