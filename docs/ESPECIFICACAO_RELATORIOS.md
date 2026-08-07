# Especificação de Relatórios — LiveSun Comercial

**Versão:** 1.0 — 06/08/2026
**Escopo:** Sistema ERP LiveSun Comercial (gestão comercial, fiscal, financeira, locação, contratos e propostas).
**Finalidade:** Especificar relatórios funcionais, analíticos e gerenciais para operação diária, auditoria e tomada de decisão.

---

## 1. Regras globais (aplicáveis a todos os relatórios)

### 1.1 Isolamento por empresa (ID_EMPRESA)
- Todo relatório **deve** ser restrito à empresa do usuário logado por `ID_EMPRESA` (tabela `empresas`). O usuário **nunca** acessa dados de outra empresa.
- A regra é aplicada obrigatoriamente na consulta base (`WHERE empresa_id = <id_empresa_logado>`), independentemente de filtros de tela.
- Nunca retornar relatórios de empresas bloqueadas/excluídas.

### 1.2 Permissões por perfil
- Os relatórios respeitam a matriz de permissões (`PERMISSION_CATALOG`) e as sobreposições por usuário (`UserPermissionOverride`).
- Perfil `viewer`: somente leitura (não exporta? — regra: pode exportar leitura, bloqueado para escrita).
- Acesso administrativo/auditoria restrito por papel no backoffice.

### 1.3 Filtro por filial
- Relatórios com dimensão operacional devem permitir filtro por filial quando o módulo de filiais estiver habilitado.

### 1.4 Formato padrão de saída
- Impressão em tela (HTML) + exportação **CSV** (sempre) e **PDF** (quando houver motor de PDF já em uso).
- Datas em `dd/mm/aaaa`, valores monetários em `R$` (pt-BR), números de documento mascarados quando necessário.

### 1.5 Níveis dos relatórios
- **Sintético (resumo):** totalizadores e agrupamentos, sem linha a linha detalhada.
- **Analítico (detalhado):** linha a linha com todos os campos.

---

## 2. Estrutura de menu — item "Relatórios"

```
Relatórios
├── Administração
│   ├── Usuários Ativos e Inativos
│   ├── Permissões por Perfil e por Usuário
│   ├── Acessos Negados e Tentativas de Operação
│   ├── Plano Contratado por Empresa
│   └── Saúde da Base (Schema/Migração)
├── Cadastros
│   ├── Entidades por Tipo, Cidade, UF e Status
│   ├── Clientes com Vendedor e Comissão
│   ├── Serviços por Código, NBS, CNAE e Situação
│   ├── Tabelas de Preço Vigentes e Itens
│   └── Contas Bancárias e Conta Principal
├── Comercial
│   ├── Vendas por Período, Filial, Cliente e Vendedor
│   ├── Pedidos por Status, Atendimento Parcial e Faturamento
│   ├── Orçamentos por Status, Conversão e Validade
│   ├── Propostas Emitidas, Aprovadas, Rejeitadas e Convertidas
│   ├── Documentos de Venda Não Fiscal
│   ├── Compras Manuais por Fornecedor
│   ├── Importação de XML de NF-e
│   ├── Estoque Atual, Entradas, Saídas e Ajustes
│   ├── Movimentação de Estoque por Produto e Período
│   ├── PDV por Caixa, Operador e Forma de Pagamento
│   └── Fechamento de Caixa
├── Financeiro
│   ├── Fluxo de Caixa Previsto x Realizado
│   ├── Saldo por Conta Bancária
│   ├── Extrato Bancário
│   └── Receitas e Despesas por Categoria do Fluxo
├── Fiscal / Serviços
│   ├── NFS-e Emitidas por Período, Status, Tomador e Serviço
│   ├── NFS-e Autorizadas, Canceladas, Rejeitadas e em Processamento
│   ├── NFS-e por Valor e por Município
│   ├── Tomadores com Maior Volume
│   ├── Serviços Mais Utilizados
│   ├── Cancelamentos e Substituições
│   └── Configurações Fiscais por Empresa
├── Locação
│   ├── Peças e Kits Cadastrados
│   ├── Disponibilidade por Período
│   ├── Reservas em Aberto
│   ├── Locações Ativas, Concluídas e Atrasadas
│   ├── Contratos por Status
│   ├── Receita de Locação por Período
│   ├── Peças em Manutenção
│   ├── Utilização por Item
│   └── Caução, Devolução e Pendências
├── Contratos
│   ├── Contratos de Serviços por Status
│   ├── Contratos por Cliente, Vigência e Valor
│   ├── Minutas Criadas, Aprovadas e Convertidas
│   ├── Contratos Gerados a Partir de Propostas
│   ├── Vencimentos e Renovações
│   └── Valores Mensais Contratados
└── Dashboard / Gerencial
    ├── Executivo Consolidado por Empresa
    ├── Faturamento, Margem e Resultado do Período
    ├── Indicadores Comerciais e Financeiros
    ├── Evolução Mensal de Vendas, Receitas e Despesas
    ├── Alertas Operacionais
    └── Pendências Críticas do Sistema
```

> **Nota de navegação:** os sub-itens só devem aparecer quando o **módulo** estiver habilitado para a empresa (controle de módulos/assinatura do Backoffice Comercial) e o usuário tiver permissão `relatorios`/específica.

A seguir, a especificação detalhada de cada relatório, com os 10 atributos solicitados. As prioridades `P(numero)` seguem o indicador do enunciado.
---

# 3. Módulo Administração

## 3.1 Relatório de Usuários Ativos e Inativos — **P1**
1. **Nome:** R_USUARIOS_STATUS — Usuários Ativos e Inativos.
2. **Objetivo:** Auditar a força de trabalho de cada empresa e identificar contas ativas, inativas e bloqueadas por assinatura.
3. **Filtros obrigatórios:** Empresa (`ID_EMPRESA`, implícito); status (ativo/inativo/todos); período de criação; perfil (admin/operator/viewer).
4. **Campos exibidos:** usuário, nome completo, e-mail, perfil, status, data de criação, último acesso, empresa, bloqueio por assinatura.
5. **Agrupamentos/totalizadores:** por perfil e por status; totalizadores de ativos/inativos; percentual de inatividade.
6. **Regras de negócio:** contas de empresas com assinatura `suspensa/cancelada/excluída` são marcadas como bloqueadas automaticamente; inativas há > 90 dias entram em alerta.
7. **Status/alertas:** destaque para bloqueados por assinatura e inativos > 90 dias.
8. **Layout:** síntese em cards (ativos, inativos, bloqueados) + grade analítica com filtros.
9. **Exportação:** CSV e PDF.
10. **Origem:** `users` (join `empresas` e `assinatura_empresa`).

## 3.2 Relatório de Permissões por Perfil e por Usuário — **P3**
1. **Nome:** R_PERMISSOES — Matriz de Permissões por Perfil e Usuário.
2. **Objetivo:** Auditar quem pode fazer o quê, comparando regras de papel e sobreposições por usuário.
3. **Filtros:** Empresa; papel; usuário; grupo de permissão (Geral, Cadastros, Comercial, Locação, Contratos, Administração).
4. **Campos:** permissão, grupo, papel default (permitida/negada), override por usuário (herdar/permitir/negar), alteração recente.
5. **Agrupamentos/totalizadores:** por papel e por grupo; total de permissões concedidas/negadas.
6. **Regras:** admin sempre tem acesso total; viewer só leitura; divergências entre override e default são destacadas.
7. **Alertas:** sobreposições que **expandem** a permissão do papel (risco de segurança).
8. **Layout:** matriz (linhas=permissões, colunas=papéis/usuários) com semáforo.
9. **Exportação:** CSV.
10. **Origem:** `role_permissions`, `user_permission_overrides`, `PERMISSION_CATALOG`.

## 3.3 Relatório de Acessos Negados e Tentativas de Operação — **P3**
1. **Nome:** R_ACESSOS_NEGADOS — Logs de Acesso Negado e Bloqueio.
2. **Objetivo:** Auditoria de segurança: tentativas de acesso a recursos sem permissão, escritas de viewer e logins bloqueados por assinatura.
3. **Filtros:** Empresa; período; tipo (login negado, permissão negada, escrita viewer, bloqueio assinatura); usuário.
4. **Campos:** data/hora, usuário, empresa, endpoint/recurso, motivo do bloqueio, IP.
5. **Agrupamentos:** por tipo de bloqueio e por usuário; total de ocorrências.
6. **Regras:** cada bloqueio registrado em log; não expor senhas.
7. **Alertas:** concentração de tentativas de um mesmo usuário (possível ataque).
8. **Layout:** grade analítica com filtros temporais.
9. **Exportação:** CSV.
10. **Origem:** arquivo `app_errors.log`/tabela de auditoria de acesso (a estruturar), bloqueios em `before_request` e login.


## 3.4 Relatório de Plano Contratado por Empresa — **P3**
1. **Nome:** R_PLANOS_EMPRESA — Planos e Assinaturas por Empresa.
2. **Objetivo:** Visão comercial/backoffice dos planos, vigência, status e módulos liberados.
3. **Filtros:** Plano; status da assinatura; vigência; empresa.
4. **Campos:** empresa, CNPJ, plano, ciclo, status, vigência, renovação, limite de usuários, módulos habilitados, valores.
5. **Agrupamentos:** por plano e por status; total de clientes por plano.
6. **Regras:** apenas backoffice/administração vê múltiplas empresas; usuário comum vê somente a própria.
7. **Alertas:** assinaturas vencidas, suspensas, canceladas e em retenção (exclusão).
8. **Layout:** cards de resumo + tabela analítica.
9. **Exportação:** CSV/PDF.
10. **Origem:** `assinatura_empresa`, `catalogo_planos_comercial`, `empresas`.

## 3.5 Relatório de Saúde da Base (Schema/Migração) — **P3**
1. **Nome:** R_SAUDE_BASE — Inconsistências de Schema e Pendências de Migração.
2. **Objetivo:** Detectar colunas/tabelas ausentes ou com tipos divergentes e migrações pendentes.
3. **Filtros:** Banco (schema atual); pendência por tabela.
4. **Campos:** tabela, coluna esperada, coluna presente, tipo esperado/atual, status (ok/ausente/divergente), script de migração.
5. **Agrupamentos:** por tabela e por tipo de divergência.
6. **Regras:** comparar modelo SQLAlchemy (`Empresa.atividade_*`, `AssinaturaEmpresa.data_exclusao`, etc.) com o schema real.
7. **Alertas:** itens críticos (colunas usadas em consultas) ausentes.
8. **Layout:** semáforo por tabela + lista de pendências.
9. **Exportação:** CSV/PDF.
10. **Origem:** `inspect(db.engine)` + catálogo de migrações `migrations/`.

---

# 4. Módulo Cadastros

## 4.1 Relatório de Entidades por Tipo, Cidade, UF e Status — **P1**
1. **Nome:** R_ENTIDADES — Entidades por Tipo, Cidade, UF e Status.
2. **Objetivo:** Consolidar o cadastro de clientes/fornecedores para análise de base e conferência cadastral.
3. **Filtros:** Empresa; tipo (cliente/fornecedor/ambos); UF; cidade; situação; período de cadastro.
4. **Campos:** código, nome/razão social, CPF/CNPJ, tipo, cidade/UF, situação, data de cadastro, vendedor.
5. **Agrupamentos:** por tipo → UF → cidade → situação; totalizadores por grupo.
6. **Regras:** entidades inativas não somam em relatórios de venda; CPF/CNPJ duplicados sinalizados.
7. **Alertas:** duplicidade de documento e entidades sem endereço/UF.
8. **Layout:** sintético (ranking por UF) + analítico.
9. **Exportação:** CSV/PDF.
10. **Origem:** `entidades` (campos `tipo`, `cidade`, `uf`, `situacao`, `vendedor_id`).

## 4.2 Relatório de Clientes com Vendedor e Comissão Configurados — **P1**
1. **Nome:** R_CLIENTES_COMISSAO — Clientes com Vendedor e Comissão.
2. **Objetivo:** Garantir que clientes estejam com vendedor e comissão corretamente configurados para apuração.
3. **Filtros:** Empresa; vendedor; possui/ausência de comissão; situação.
4. **Campos:** cliente, vendedor, comissão (padrão/específica), valor repasse, situação.
5. **Agrupamentos:** por vendedor; total de clientes sem vendedor/comissão.
6. **Regras:** cliente sem vendedor gera alerta de apuração incompleta; comissão específica prevalece sobre a geral.
7. **Alertas:** clientes ativos sem vendedor ou sem comissão (bloqueiam apuração correta).
8. **Layout:** cards de déficit + grade.
9. **Exportação:** CSV.
10. **Origem:** `entidades` (`vendedor_id`, `aliquota_comissao_especifica`, `valor_repasse`).

## 4.3 Relatório de Serviços por Código, NBS, CNAE e Situação — **P2**
1. **Nome:** R_SERVICOS — Serviços por Código, NBS, CNAE e Situação.
2. **Objetivo:** Auditoria do catálogo de serviços para fiscal e precificação.
3. **Filtros:** Empresa; situação; CNAE; NBS; tipo de serviço.
4. **Campos:** código, descrição, NBS, CNAE, CST/ISS, situação, valor.
5. **Agrupamentos:** por CNAE e por NBS; contagem de serviços.
6. **Regras:** serviço sem NBS utilizado em NFS-e deve ser impedido/bloqueado.
7. **Alertas:** serviços sem NBS/CNAE e serviços inativos vinculados a documentos.
8. **Layout:** grade analítica com filtros.
9. **Exportação:** CSV/PDF.
10. **Origem:** `servicos` (comercial) + `empresa_fiscal_item`.

## 4.4 Relatório de Tabelas de Preço Vigentes e Itens Vinculados — **P3**
1. **Nome:** R_TABELAS_PRECO — Tabelas de Preço Vigentes e Itens.
2. **Objetivo:** Conferir tabelas vigentes, vigências e itens vinculados.
3. **Filtros:** Empresa; tabela; vigência; item.
4. **Campos:** tabela, vigência início/fim, status (vigente/vencida), itens, preço, percentual sobre base.
5. **Agrupamentos:** por tabela e por vigência.
6. **Regras:** itens sem preço na tabela vigente usam preço base com flag.
7. **Alertas:** tabelas vencidas e itens sem preço.
8. **Layout:** cartões por tabela + listagem de itens.
9. **Exportação:** CSV/PDF.
10. **Origem:** `tabelas_preco` + `tabela_preco_itens`.

## 4.5 Relatório de Contas Bancárias e Conta Principal — **P2**
1. **Nome:** R_CONTAS_BANCO — Contas Bancárias e Conta Principal.
2. **Objetivo:** Consolidar contas cadastradas, banco, agência e conta principal para fluxo/extração.
3. **Filtros:** Empresa; banco; tipo; conta principal.
4. **Campos:** banco, agência, conta, tipo, titular, saldo, conta principal (S/N), situação.
5. **Agrupamentos:** por banco; total por tipo.
6. **Regras:** deve haver ao menos uma conta principal; movimentações têm vínculo com a conta.
7. **Alertas:** ausência de conta principal e saldo divergente da conciliação.
8. **Layout:** cards + grade.
9. **Exportação:** CSV.
10. **Origem:** `contas_banco`.


---

# 5. Módulo Comercial

## 5.1 Relatório de Vendas por Período, Filial, Cliente e Vendedor — **P1**
1. **Nome:** R_VENDAS — Vendas por Período, Filial, Cliente e Vendedor.
2. **Objetivo:** Consolidar o faturamento de vendas por múltiplas dimensões (tempo, filial, cliente, vendedor).
3. **Filtros:** Empresa; período (obrigatório); filial; cliente; vendedor; forma de pagamento; status fiscal.
4. **Campos:** data, documento, filial, cliente, vendedor, quantidade, valor bruto, descontos, impostos, valor líquido.
5. **Agrupamentos:** por período → vendedor/filial; totalizadores de valor, quantidade e ticket médio.
6. **Regras:** apenas vendas válidas (não canceladas); impostos separados do líquido.
7. **Alertas:** vendas com desconto atípico (> X%) e documentos cancelados.
8. **Layout:** sintético (evolução/top) + analítico; gráfico de barras temporal.
9. **Exportação:** CSV/PDF.
10. **Origem:** documentos de venda/PDV/pedidos faturados (join `filiais`, `entidades`, `users`).

## 5.2 Relatório de Pedidos por Status, Atendimento Parcial e Faturamento — **P1**
1. **Nome:** R_PEDIDOS — Pedidos por Status, Atendimento Parcial e Faturamento.
2. **Objetivo:** Controlar a carteira de pedidos: abertos, parciais, faturados e pendentes de atendimento.
3. **Filtros:** Empresa; período; status; filial; cliente; forma de entrega.
4. **Campos:** pedido, data, cliente, status, valor, % atendido, itens pendentes, documento fiscal gerado.
5. **Agrupamentos:** por status; total de pedidos e valores; % de atendimento médio.
6. **Regras:** pedido parcial mantém saldo a faturar; pedido atrasado (prazo vencido) destacado.
7. **Alertas:** pedidos atrasados, parciais antigos e faturáveis pendentes.
8. **Layout:** funil por status + grade analítica.
9. **Exportação:** CSV/PDF.
10. **Origem:** `pedidos`, `pedido_itens`, documentos de faturamento.

## 5.3 Relatório de Orçamentos por Status, Conversão e Validade — **P1**
1. **Nome:** R_ORCAMENTOS — Orçamentos por Status, Conversão e Validade.
2. **Objetivo:** Medir a conversão de orçamentos em pedidos e controlar validade.
3. **Filtros:** Empresa; período; status; vendedor; validade (vencido/vigente).
4. **Campos:** orçamento, data, cliente, vendedor, valor, status, validade, pedido gerado.
5. **Agrupamentos:** por status; taxa de conversão (orçamento→pedido) por vendedor.
6. **Regras:** orçamento vencido não pode ser convertido sem nova validação.
7. **Alertas:** orçamentos vencidos não convertidos e com alto valor.
8. **Layout:** funil de conversão + grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** `orcamentos` + `pedidos`.

## 5.4 Relatório de Propostas Emitidas, Aprovadas, Rejeitadas e Convertidas — **P1**
1. **Nome:** R_PROPOSTAS — Propostas Emitidas, Aprovadas, Rejeitadas e Convertidas.
2. **Objetivo:** Acompanhar fluxo de propostas comerciais até conversão em contrato/pedido.
3. **Filtros:** Empresa; período; status; vendedor; cliente.
4. **Campos:** proposta, data, cliente, vendedor, valor, status, data aprovação, origem (contrato/pedido).
5. **Agrupamentos:** por status; taxa de aprovação e conversão.
6. **Regras:** proposta aprovada e não convertida entra em pendência.
7. **Alertas:** aprovadas há muito tempo sem conversão e rejeitadas com valores altos.
8. **Layout:** funil + grade analítica.
9. **Exportação:** CSV/PDF.
10. **Origem:** `propostas` + `contratos`/`pedidos` (geração a partir de proposta).

## 5.5 Relatório de Documentos de Venda Não Fiscal — **P2**
1. **Nome:** R_DOC_NAO_FISCAL — Documentos de Venda Não Fiscal.
2. **Objetivo:** Auditar documentos de saída sem NF (pré-venda, cupom manual, controle interno).
3. **Filtros:** Empresa; período; tipo de documento; filial; situação.
4. **Campos:** documento, data, cliente, vendedor, valor, tipo, situação, motivo de não emissão fiscal.
5. **Agrupamentos:** por tipo e situação; total de valores.
6. **Regras:** documento não fiscal não soma em tributos; controle de limite de emissão (ex.: por operador).
7. **Alertas:** volume elevado de não-fiscais (possível venda informal).
8. **Layout:** grade analítica.
9. **Exportação:** CSV.
10. **Origem:** `documentos` não fiscais (módulo comercial).

## 5.6 Relatório de Compras Manuais por Fornecedor, Data e Total — **P1**
1. **Nome:** R_COMPRAS — Compras Manuais (NF) por Fornecedor, Data e Total.
2. **Objetivo:** Consolidar compras manuais / NF de entrada para custo e apuração.
3. **Filtros:** Empresa; período; fornecedor; filial; situação.
4. **Campos:** NF, data, fornecedor, CFOP, valor, impostos, itens.
5. **Agrupamentos:** por fornecedor e por período; total de compras.
6. **Regras:** compra vincula custo ao estoque (entrada); integra importação de XML quando existente.
7. **Alertas:** valores divergentes do XML importado e fornecedores sem cadastro.
8. **Layout:** grade analítica com totais por fornecedor.
9. **Exportação:** CSV/PDF.
10. **Origem:** `compras` (NF manual) + `importacoes`/estoque.


## 5.7 Relatório de Importação de XML de NF-e — **P3**
1. **Nome:** R_IMPORTACAO_XML — Importação de XML de NF-e (Sucesso, Rejeição e Pendências).
2. **Objetivo:** Auditar o pipeline de importação de XML: sucesso, rejeição e pendências.
3. **Filtros:** Empresa; período; status (sucesso/rejeitado/pendente); fornecedor.
4. **Campos:** arquivo, data, fornecedor, chave, status, motivo de rejeição, documento gerado.
5. **Agrupamentos:** por status; volume e taxa de sucesso.
6. **Regras:** arquivo rejeitado não gera compra/estoque até correção.
7. **Alertas:** pendências antigas e taxa de rejeição elevada.
8. **Layout:** funil de importação + grade.
9. **Exportação:** CSV.
10. **Origem:** tabela de importação de XML / `importacoes`.

## 5.8 Relatório de Estoque Atual, Entradas, Saídas e Ajustes — **P1**
1. **Nome:** R_ESTOQUE_ATUAL — Estoque Atual, Entradas, Saídas e Ajustes.
2. **Objetivo:** Posição real de estoque por produto/filial e fluxo de movimentações.
3. **Filtros:** Empresa; filial; produto/categoria; faixa de saldo; período.
4. **Campos:** produto, código, categoria, filial, estoque atual, mínimo, entradas, saídas, ajustes, custo/valor.
5. **Agrupamentos:** por categoria e por filial; totais de itens e valor.
6. **Regras:** estoque não pode ficar negativo; valores a custo médio.
7. **Alertas:** abaixo do mínimo, estoque zerado e possíveis saldos negativos.
8. **Layout:** cards (total itens, abaixo do mínimo) + grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** `estoque` + `movimentacao_estoque` (entradas/saídas/ajustes).

## 5.9 Relatório de Movimentação de Estoque por Produto e Período — **P2**
1. **Nome:** R_MOV_ESTOQUE — Movimentação de Estoque por Produto e Período.
2. **Objetivo:** Rastrear histórico de movimentações (entrada/saída/ajuste/transferência).
3. **Filtros:** Empresa; período (obrigatório); produto; tipo de movimento; filial.
4. **Campos:** data/hora, produto, tipo, quantidade, saldo após, documento origem, filial, usuário.
5. **Agrupamentos:** por produto e por tipo; somatório de quantidades.
6. **Regras:** cada movimento gera saldo consistente; auditoria de usuário.
7. **Alertas:** movimentações fora de horário padrão e descontos de estoque sem origem de venda.
8. **Layout:** grade analítica com filtros e saldo corrido.
9. **Exportação:** CSV/PDF.
10. **Origem:** `movimentacao_estoque`.

## 5.10 Relatório de PDV por Caixa, Operador, Forma de Pagamento e Divergências — **P1**
1. **Nome:** R_PDV — PDV por Caixa, Operador, Forma de Pagamento e Divergências.
2. **Objetivo:** Auditar operações de PDV: vendas, formas de pagamento, sangrias e divergências de caixa.
3. **Filtros:** Empresa; período; caixa; operador; forma de pagamento; com divergência (S/N).
4. **Campos:** caixa, operador, abertura/fechamento, vendas, por forma de pagamento, sangrias, suprimentos, divergência.
5. **Agrupamentos:** por caixa e operador; totais de vendas e divergências.
6. **Regras:** fechamento deve equilibrar (vendas + sangrias − suprimentos = caixa); divergência é destacada.
7. **Alertas:** caixas com divergência e abertos fora do expediente.
8. **Layout:** síntese por caixa + grade de divergências.
9. **Exportação:** CSV/PDF.
10. **Origem:** `pdv_caixa`, `pdv_vendas`, `pdv_movimentos` (sangria/suprimento/fechamento).

## 5.11 Relatório de Fechamento de Caixa — **P1**
1. **Nome:** R_FECHAMENTO_CAIXA — Fechamento de Caixa.
2. **Objetivo:** Conferência formal do fechamento de cada caixa/PDV por período.
3. **Filtros:** Empresa; período; caixa; operador; status do fechamento.
4. **Campos:** caixa, operador, data, total vendas, recebimentos, sangrias, suprimentos, saldo em caixa, status (conferido/divergente).
5. **Agrupamentos:** por operador e por data.
6. **Regras:** fechamento é base para lançamento financeiro; divergência exige justificativa.
7. **Alertas:** fechamentos com divergência e abertos não fechados.
8. **Layout:** resumo por caixa + grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** `pdv_fechamento`/`fechamento_caixa`.


---

# 6. Módulo Financeiro

## 6.1 Relatório de Fluxo de Caixa Previsto x Realizado — **P1**
1. **Nome:** R_FLUXO_PREV_REAL — Fluxo de Caixa Previsto x Realizado.
2. **Objetivo:** Comparar projeções (previsto) com o efetivamente realizado por período, apoiando decisões de caixa.
3. **Filtros:** Empresa; período (obrigatório); conta; categoria; previsão/realizado.
4. **Campos:** competência, categoria, conta, previsto, realizado, variação (R$ e %), status de conciliação.
5. **Agrupamentos:** por mês e por categoria; total previsto, realizado e variação acumulada.
6. **Regras:** realizado considera lançamentos efetivados; variação negativa acima de limite gera alerta.
7. **Alertas:** desvio previsto × realizado acima de X% e saldo projetado negativo.
8. **Layout:** tabela comparativa por mês + gráfico de linha previsto × realizado.
9. **Exportação:** CSV/PDF.
10. **Origem:** `fluxo`/`lancamentos` (previsto) e lançamentos efetivados/conciliados.

## 6.2 Relatório de Saldo por Conta Bancária — **P1**
1. **Nome:** R_SALDO_CONTAS — Saldo por Conta Bancária.
2. **Objetivo:** Posição de saldos por conta e consolidação do caixa.
3. **Filtros:** Empresa; conta; banco; período.
4. **Campos:** banco, agência, conta, saldo inicial, entradas, saídas, saldo final (sistema e banco).
5. **Agrupamentos:** por conta/banco; saldo total consolidado.
6. **Regras:** saldo do sistema deve casar com conciliação; divergências destacadas.
7. **Alertas:** saldo negativo e divergência com extrato.
8. **Layout:** cards de saldo por conta + grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** `contas_banco`, `lancamentos`, `conciliacao`.

## 6.3 Relatório de Extrato Bancário — **P1**
1. **Nome:** R_EXTRATO_BANCO — Extrato Bancário.
2. **Objetivo:** Extrato analítico da conta no período, com conciliação.
3. **Filtros:** Empresa; conta (obrigatório); período (obrigatório).
4. **Campos:** data, histórico, documento, valor (D/C), saldo, conciliado (S/N).
5. **Agrupamentos:** por dia; saldo acumulado; totais de débitos e créditos.
6. **Regras:** valores conciliados com lançamentos do sistema; itens não conciliados destacados.
7. **Alertas:** lançamentos não conciliados e saldo divergente.
8. **Layout:** extrato banco com colunas de conciliação.
9. **Exportação:** CSV/PDF.
10. **Origem:** `conciliacao`/`conciliacao_item` + `lancamentos`.

## 6.4 Relatório Analítico de Receitas e Despesas por Categoria do Fluxo — **P1**
1. **Nome:** R_REC_DESP_CAT — Receitas e Despesas por Categoria do Fluxo.
2. **Objetivo:** Analisar composição de receitas e despesas por categoria/centro de custo.
3. **Filtros:** Empresa; período; categoria; tipo (receita/despesa); conta.
4. **Campos:** data, categoria, conta, descrição, valor, tipo, forma de pagamento.
5. **Agrupamentos:** por categoria e por mês; totais de receita, despesa e saldo.
6. **Regras:** categoria obrigatória para classificação correta no fluxo.
7. **Alertas:** despesas sem categoria e concentração de despesas em poucas categorias.
8. **Layout:** sintético (top categorias) + analítico; gráfico de pizza/barra por categoria.
9. **Exportação:** CSV/PDF.
10. **Origem:** `lancamentos` com categoria do `fluxo`.


---

# 7. Módulo Fiscal / Serviços

## 7.1 Relatório de NFS-e Emitidas por Período, Status, Tomador e Serviço — **P1**
1. **Nome:** R_NFSE_EMITIDAS — NFS-e Emitidas por Período, Status, Tomador e Serviço.
2. **Objetivo:** Consolidar a emissão de NFS-e para conferência fiscal e comercial.
3. **Filtros:** Empresa; período; status; tomador; serviço; município.
4. **Campos:** número, data, tomador, serviço, NBS, valor, impostos, status, município.
5. **Agrupamentos:** por status e por município; totais de valor e impostos.
6. **Regras:** apenas NFS-e válidas; canceladas/rejeitadas tratadas à parte.
7. **Alertas:** notas em processamento há muito tempo e valores divergentes do pedido.
8. **Layout:** sintético + analítico.
9. **Exportação:** CSV/PDF.
10. **Origem:** `nfse_emissao`/tabelas do módulo NFS-e nacional.

## 7.2 Relatório de NFS-e Autorizadas, Canceladas, Rejeitadas e em Processamento — **P2**
1. **Nome:** R_NFSE_STATUS — NFS-e por Status de Autorização.
2. **Objetivo:** Acompanhar fila de autorização e anomalias (rejeição/cancelamento).
3. **Filtros:** Empresa; período; status; tomador.
4. **Campos:** número, data, status (autorizada/cancelada/rejeitada/processando), motivo, protocolo.
5. **Agrupamentos:** por status; volume e valores por status.
6. **Regras:** rejeitada exige correção e nova emissão; cancelada deve justificar.
7. **Alertas:** processando > limite de tempo e taxa de rejeição alta.
8. **Layout:** funil por status + grade.
9. **Exportação:** CSV.
10. **Origem:** `nfse_emissao` (status/autorização).

## 7.3 Relatório de NFS-e por Valor e por Município — **P2**
1. **Nome:** R_NFSE_MUNICIPIO — NFS-e por Valor e por Município.
2. **Objetivo:** Análise tributária/fiscal de emissão por município (ISS).
3. **Filtros:** Empresa; período; município; UF.
4. **Campos:** município/UF, quantidade, valor total, valor ISS, alíquota média.
5. **Agrupamentos:** por município e por mês.
6. **Regras:** alíquota do ISS por município conforme cadastro fiscal.
7. **Alertas:** municípios sem alíquota cadastrada e valores < 0.
8. **Layout:** ranking por município + mapa/tabela.
9. **Exportação:** CSV/PDF.
10. **Origem:** `nfse_emissao` + dados do município (IBGE/ISSQN).

## 7.4 Relatório de Tomadores com Maior Volume — **P3**
1. **Nome:** R_TOMADORES_TOP — Tomadores com Maior Volume.
2. **Objetivo:** Identificar principais tomadores por valor e quantidade emitida.
3. **Filtros:** Empresa; período; quantidade de itens (top N).
4. **Campos:** tomador, CNPJ/CPF, quantidade de notas, valor total, participação %.
5. **Agrupamentos:** por tomador; ranking top N.
6. **Regras:** somente notas autorizadas; considera valor líquido.
7. **Alertas:** concentração elevada em poucos tomadores (risco de dependência).
8. **Layout:** ranking/barras horizontais.
9. **Exportação:** CSV/PDF.
10. **Origem:** `nfse_emissao` agrupado por `tomador`.

## 7.5 Relatório de Serviços Mais Utilizados — **P3**
1. **Nome:** R_SERVICOS_TOP — Serviços Mais Utilizados.
2. **Objetivo:** Identificar os serviços mais emitidos por volume e valor.
3. **Filtros:** Empresa; período; top N.
4. **Campos:** serviço, código, NBS, quantidade, valor total, participação %.
5. **Agrupamentos:** por serviço; ranking.
6. **Regras:** considera notas autorizadas.
7. **Alertas:** serviços sem NBS entre os mais usados.
8. **Layout:** ranking.
9. **Exportação:** CSV/PDF.
10. **Origem:** `nfse_emissao` agrupado por serviço.

## 7.6 Relatório de Cancelamentos e Substituições — **P3**
1. **Nome:** R_NFSE_CANCEL — Cancelamentos e Substituições.
2. **Objetivo:** Auditoria de notas canceladas, substituídas e reemitidas.
3. **Filtros:** Empresa; período; tipo (cancelada/substituída); operador.
4. **Campos:** número original, data, tomador, valor, motivo, nota substituta (se houver).
5. **Agrupamentos:** por tipo e por motivo; total de valores cancelados.
6. **Regras:** cancelamento exige justificativa/código; substituição rastreia a nova nota.
7. **Alertas:** taxa de cancelamento elevada e cancelamentos sem justificativa.
8. **Layout:** grade analítica.
9. **Exportação:** CSV.
10. **Origem:** histórico de cancelamento/substituição da NFS-e.

## 7.7 Relatório de Configurações Fiscais por Empresa — **P3**
1. **Nome:** R_CFG_FISCAL — Configurações Fiscais por Empresa.
2. **Objetivo:** Conferir parâmetros fiscais habilitados por empresa (NFS-e, NF-e, regime, itens fiscais).
3. **Filtros:** Empresa; módulo fiscal; ausência de configuração.
4. **Campos:** empresa, CNPJ, regime, inscrições, NBS/itens fiscais, NFS-e habilitado, NF-e habilitado.
5. **Agrupamentos:** por tipo de configuração; contagens.
6. **Regras:** empresa sem item fiscal principal é alerta crítico para emissão.
7. **Alertas:** ausência de item fiscal principal e inscrições vencidas/ausentes.
8. **Layout:** cards + grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** `empresas` (campos fiscais), `empresa_fiscal_item`.


---

# 8. Módulo Locação

## 8.1 Relatório de Peças e Kits Cadastrados — **P1**
1. **Nome:** R_LOC_ACERVO — Peças e Kits Cadastrados.
2. **Objetivo:** Inventário do acervo (peças e kits) de locação com status.
3. **Filtros:** Empresa; tipo (peça/kit); situação; categoria; faixa de quantidade.
4. **Campos:** código, descrição, tipo, categoria, quantidade, em uso, disponível, em manutenção, valor.
5. **Agrupamentos:** por tipo e categoria; totais.
6. **Regras:** quantidade = disponível + em uso + manutenção.
7. **Alertas:** itens sem estoque e acima do limite de manutenção.
8. **Layout:** cards + grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** tabelas do módulo de locação (acervo/peças/kits).

## 8.2 Relatório de Disponibilidade por Período — **P1**
1. **Nome:** R_LOC_DISPONIBILIDADE — Disponibilidade por Período.
2. **Objetivo:** Posição de peças/kits disponíveis para reserva num intervalo.
3. **Filtros:** Empresa; período (obrigatório); item; categoria.
4. **Campos:** item, quantidade total, reservada, em locação, em manutenção, disponível por dia.
5. **Agrupamentos:** por item e por dia do período.
6. **Regras:** sobreposição de reservas deve ser evitada pelo sistema.
7. **Alertas:** itens sem disponibilidade em datas-chave.
8. **Layout:** grade de disponibilidade (itens × datas).
9. **Exportação:** CSV.
10. **Origem:** acervo + reservas/locações no período.

## 8.3 Relatório de Reservas em Aberto — **P1**
1. **Nome:** R_LOC_RESERVAS — Reservas em Aberto.
2. **Objetivo:** Controlar reservas futuras e pendências de confirmação.
3. **Filtros:** Empresa; período; cliente; status; data de retirada.
4. **Campos:** reserva, data, cliente, itens, valor, status, data retirada/devolução.
5. **Agrupamentos:** por status e por data.
6. **Regras:** reserva não confirmada vence; confirmação gera locação.
7. **Alertas:** reservas vencidas e devoluções atrasadas.
8. **Layout:** agenda/grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** tabela de reservas de locação.

## 8.4 Relatório de Locações Ativas, Concluídas e Atrasadas — **P1**
1. **Nome:** R_LOC_OPERACAO — Locações Ativas, Concluídas e Atrasadas.
2. **Objetivo:** Acompanhar o ciclo de locação: ativas, concluídas e em atraso.
3. **Filtros:** Empresa; período; status; cliente.
4. **Campos:** locação, cliente, itens, início, devolução prevista/real, status, valor.
5. **Agrupamentos:** por status; totais e valores em atraso.
6. **Regras:** devolução em atraso gera cobrança adicional.
7. **Alertas:** locações atrasadas e sem previsão.
8. **Layout:** cards + grade por status.
9. **Exportação:** CSV/PDF.
10. **Origem:** tabela de locações/operação.

## 8.5 Relatório de Contratos por Status — **P1**
1. **Nome:** R_LOC_CONTRATOS — Contratos de Locação por Status.
2. **Objetivo:** Carteira de contratos de locação por status e vigência.
3. **Filtros:** Empresa; período; status; cliente.
4. **Campos:** contrato, cliente, vigência, valor, status, itens vinculados.
5. **Agrupamentos:** por status; totais.
6. **Regras:** renovação gera novo contrato ou aditivo.
7. **Alertas:** contratos vencendo e em aberto por tempo.
8. **Layout:** grade por status.
9. **Exportação:** CSV/PDF.
10. **Origem:** tabela de contratos de locação.

## 8.6 Relatório de Receita de Locação por Período — **P2**
1. **Nome:** R_LOC_RECEITA — Receita de Locação por Período.
2. **Objetivo:** Medir a receita de locação por período/cliente/item.
3. **Filtros:** Empresa; período; cliente; item; forma de pagamento.
4. **Campos:** data, cliente, item, valor, multas/caução, receita líquida.
5. **Agrupamentos:** por mês e por cliente; total de receita.
6. **Regras:** receita considera locações concluídas; caução não é receita (quando devolvida).
7. **Alertas:** receita com caução retida (pendência).
8. **Layout:** evolução temporal + ranking clientes.
9. **Exportação:** CSV/PDF.
10. **Origem:** locações + pagamentos/caução.

## 8.7 Relatório de Peças em Manutenção — **P1**
1. **Nome:** R_LOC_MANUTENCAO — Peças em Manutenção.
2. **Objetivo:** Controlar itens fora de circulação por manutenção.
3. **Filtros:** Empresa; situação; período de manutenção; item.
4. **Campos:** item, entrada manutenção, previsão saída, motivo, custo, status.
5. **Agrupamentos:** por motivo e por status; totais.
6. **Regras:** item em manutenção não é reservável.
7. **Alertas:** manutenções acima do prazo e custo elevado.
8. **Layout:** cards + grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** tabela de manutenção do acervo.

## 8.8 Relatório de Utilização por Item — **P1**
1. **Nome:** R_LOC_UTILIZACAO — Utilização por Item.
2. **Objetivo:** Taxa de utilização de cada peça/kit para gestão de acervo.
3. **Filtros:** Empresa; período; item; categoria.
4. **Campos:** item, nº de locações, dias locados, dias disponíveis, taxa de utilização %.
5. **Agrupamentos:** por item/categoria; média de utilização.
6. **Regras:** utilização = dias locados / dias no período.
7. **Alertas:** itens com baixa utilização (sugerir venda) e alta (sugerir compra).
8. **Layout:** ranking de utilização.
9. **Exportação:** CSV/PDF.
10. **Origem:** locações × acervo no período.

## 8.9 Relatório de Caução, Devolução e Pendências — **P2**
1. **Nome:** R_LOC_CAUCAO — Caução, Devolução e Pendências.
2. **Objetivo:** Controlar cações recebidas, devoluções de valores e pendências.
3. **Filtros:** Empresa; período; cliente; status da caução.
4. **Campos:** locação, cliente, valor caução, retido, devolvido, pendente, motivo retenção.
5. **Agrupamentos:** por status; total de cação e pendências.
6. **Regras:** caução devolvida integralmente ao fim da locação sem danos.
7. **Alertas:** cações retidas sem justificativa e pendentes antigas.
8. **Layout:** cards + grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** locações + movimentos de caução.


---

# 9. Módulo Contratos

## 9.1 Relatório de Contratos de Serviços por Status — **P1**
1. **Nome:** R_CTR_STATUS — Contratos de Serviços por Status.
2. **Objetivo:** Carteira de contratos de serviços por status (ativo, assinado, rascunho, cancelado).
3. **Filtros:** Empresa; status; período de assinatura; cliente.
4. **Campos:** contrato, cliente, status, assinatura, vigência, valor, tipo.
5. **Agrupamentos:** por status; totais.
6. **Regras:** apenas status válidos do fluxo de contratos; conversão de minuta registrada.
7. **Alertas:** contratos em rascunho há muito tempo e assinados sem vigência válida.
8. **Layout:** funil + grade.
9. **Exportação:** CSV/PDF.
10. **Origem:** `contratos` (modelo de contratos de serviços).

## 9.2 Relatório de Contratos por Cliente, Vigência e Valor — **P2**
1. **Nome:** R_CTR_CLIENTE — Contratos por Cliente, Vigência e Valor.
2. **Objetivo:** Visão financeira dos contratos por cliente, vigência e valor mensal.
3. **Filtros:** Empresa; cliente; vigência; status; período.
4. **Campos:** contrato, cliente, início, término, valor total, valor mensal, status.
5. **Agrupamentos:** por cliente e por ano de vigência.
6. **Regras:** valor mensal oriundo dos itens/serviços contratados.
7. **Alertas:** contratos com valor mensal zerado ou vigência sobreposta.
8. **Layout:** grade + resumo por cliente.
9. **Exportação:** CSV/PDF.
10. **Origem:** `contratos` + itens.

## 9.3 Relatório de Minutas Criadas, Aprovadas e Convertidas — **P2**
1. **Nome:** R_CTR_MINUTAS — Minutas Criadas, Aprovadas e Convertidas.
2. **Objetivo:** Acompanhar fluxo de minutas até a conversão em contrato.
3. **Filtros:** Empresa; período; status; criador.
4. **Campos:** minuta, data, cliente, valor, status, aprovado por, contrato gerado.
5. **Agrupamentos:** por status; taxa de conversão.
6. **Regras:** aprovação registra responsável e data.
7. **Alertas:** minutas aprovadas sem conversão.
8. **Layout:** funil + grade.
9. **Exportação:** CSV.
10. **Origem:** tabela de minutas + `contratos`.

## 9.4 Relatório de Contratos Gerados a Partir de Propostas — **P3**
1. **Nome:** R_CTR_PROPOSTA — Contratos Gerados a Partir de Propostas.
2. **Objetivo:** Rastrear a origem (proposta) de cada contrato para medir conversão comercial.
3. **Filtros:** Empresa; período; proposta; status.
4. **Campos:** contrato, proposta origem, cliente, valor, data, status.
5. **Agrupamentos:** por proposta e por status.
6. **Regras:** vínculo contrato↔proposta mantido quando gerado.
7. **Alertas:** contratos sem proposta vinculada (fora do funil).
8. **Layout:** grade.
9. **Exportação:** CSV.
10. **Origem:** `contratos` + `propostas`.

## 9.5 Relatório de Vencimentos e Renovações — **P3**
1. **Nome:** R_CTR_VENCIMENTOS — Vencimentos e Renovações.
2. **Objetivo:** Antecipar vencimentos/renovações de contratos.
3. **Filtros:** Empresa; horizonte (dias); status; cliente.
4. **Campos:** contrato, cliente, vigência, valor, dias para vencimento, renovável.
5. **Agrupamentos:** por mês de vencimento.
6. **Regras:** vencimento recente ativa fluxo de renovação.
7. **Alertas:** contratos vencendo em X dias e vencidos sem renovação.
8. **Layout:** agenda de vencimentos.
9. **Exportação:** CSV/PDF.
10. **Origem:** `contratos` (vigência).

## 9.6 Relatório de Valores Mensais Contratados — **P2**
1. **Nome:** R_CTR_MENSAL — Valores Mensais Contratados.
2. **Objetivo:** MRR (receita recorrente mensal) por contrato/cliente.
3. **Filtros:** Empresa; período; cliente; status.
4. **Campos:** contrato, cliente, valor mensal, vigência, total do contrato.
5. **Agrupamentos:** por cliente; total MRR.
6. **Regras:** somente contratos ativos contam no MRR.
7. **Alertas:** contratos ativos sem valor mensal definido.
8. **Layout:** ranking MRR + tabela.
9. **Exportação:** CSV/PDF.
10. **Origem:** `contratos` + valores mensais.


---

# 10. Módulo Dashboard / Gerencial

## 10.1 Relatório Executivo Consolidado por Empresa — **P2**
1. **Nome:** R_EXEC — Executivo Consolidado por Empresa.
2. **Objetivo:** Painel gerencial com visão consolidada (vendas, financeiro, estoque, clientes).
3. **Filtros:** Empresa (usuário); período (mês/ano).
4. **Campos:** faturamento, custos, margem, recebimentos, despesas, saldo de caixa, clientes ativos, pedidos abertos.
5. **Agrupamentos:** por período; variação vs período anterior.
6. **Regras:** consolida apenas dados de uma empresa (ID_EMPRESA).
7. **Alertas:** desvios de meta e indicadores negativos.
8. **Layout:** KPIs em cards + gráficos e tabela executiva.
9. **Exportação:** PDF (relatório gerencial).
10. **Origem:** consolidação de vendas, `lancamentos`, estoque, entidades.

## 10.2 Relatório de Faturamento, Margem e Resultado do Período — **P2**
1. **Nome:** R_RESULTADO — Faturamento, Margem e Resultado.
2. **Objetivo:** DRE simplificado do período com faturamento, custo, margem e resultado.
3. **Filtros:** Empresa; período; tipo de receita; centro de custo.
4. **Campos:** receita, custo dos produtos/serviços, margem bruta, despesas, resultado líquido.
5. **Agrupamentos:** por mês e por categoria.
6. **Regras:** custo de mercadoria pelo custo médio; despesas por competência.
7. **Alertas:** margem abaixo do esperado e prejuízo no período.
8. **Layout:** DRE em cascata + gráfico de margem.
9. **Exportação:** PDF.
10. **Origem:** vendas, compras, `lancamentos`.

## 10.3 Relatório de Indicadores Comerciais e Financeiros — **P2**
1. **Nome:** R_INDICADORES — Indicadores Comerciais e Financeiros.
2. **Objetivo:** Painel de KPIs (ticket médio, conversão, inadimplência, giro).
3. **Filtros:** Empresa; período; indicador.
4. **Campos:** ticket médio, conversão orçamento→pedido, inadimplência, dias de atraso, giro de estoque, churn.
5. **Agrupamentos:** por mês.
6. **Regras:** definição padronizada de cada KPI.
7. **Alertas:** indicadores fora da meta.
8. **Layout:** cards com sparklines + comparativo de metas.
9. **Exportação:** CSV/PDF.
10. **Origem:** consolidação dos módulos comercial/financeiro/estoque.

## 10.4 Relatório de Evolução Mensal de Vendas, Receitas e Despesas — **P2**
1. **Nome:** R_EVOLUCAO — Evolução Mensal de Vendas, Receitas e Despesas.
2. **Objetivo:** Série histórica mensal para análise de tendência e sazonalidade.
3. **Filtros:** Empresa; ano; série (vendas/receitas/despesas).
4. **Campos:** mês, vendas, receitas, despesas, resultado, variação.
5. **Agrupamentos:** por mês do ano.
6. **Regras:** comparação com mesmo período do ano anterior.
7. **Alertas:** quebra de tendência (queda acentuada).
8. **Layout:** gráfico de linhas/barras + tabela.
9. **Exportação:** CSV/PDF.
10. **Origem:** vendas, `lancamentos`.

## 10.5 Relatório de Alertas Operacionais — **P3**
1. **Nome:** R_ALERTAS — Alertas Operacionais.
2. **Objetivo:** Consolidar exceções (vencidos, abaixo do mínimo, divergentes) em uma visão única.
3. **Filtros:** Empresa; tipo de alerta; severidade; período.
4. **Campos:** tipo, prioridade, descrição, entidade/recurso, data, status.
5. **Agrupamentos:** por tipo e por prioridade.
6. **Regras:** agrega alertas dos módulos (estoque, financeiro, fiscal, locação, contratos).
7. **Alertas:** itens críticos em destaque.
8. **Layout:** central de alertas com filtros e severidade.
9. **Exportação:** CSV.
10. **Origem:** regras de exceção de cada módulo.

## 10.6 Relatório de Pendências Críticas do Sistema — **P3**
1. **Nome:** R_PENDENCIAS — Pendências Críticas do Sistema.
2. **Objetivo:** Listar pendências que bloqueiam operações (ex.: empresa sem item fiscal, sem conta principal).
3. **Filtros:** Empresa; categoria de pendência.
4. **Campos:** categoria, descrição, impacto, entidade, prazo, status.
5. **Agrupamentos:** por categoria e impacto.
6. **Regras:** pendência crítica impede/limita fluxo específico.
7. **Alertas:** pendências responsáveis por bloqueios.
8. **Layout:** quadro de pendências por prioridade.
9. **Exportação:** CSV/PDF.
10. **Origem:** checagens de integridade dos módulos.


---

# 11. KPIs e Cards para Dashboard (recomendados)

| Módulo | KPI / Card | Fórmula / Origem |
| --- | --- | --- |
| Comercial | Faturamento do período | Soma vendas válidas (R_VENDAS) |
| Comercial | Ticket médio | Valor vendas / nº vendas |
| Comercial | Conversão orçamento→pedido | Pedidos gerados / orçamentos |
| Comercial | Pedidos abertos | Contagem pedidos não faturados |
| Financeiro | Saldo de caixa | Soma saldos por conta (R_SALDO_CONTAS) |
| Financeiro | Inadimplência (R$ e %) | Vencidos / carteira |
| Financeiro | Fluxo previsto × realizado | Variação (R_FLUXO_PREV_REAL) |
| Estoque | Abaixo do mínimo | Contagem itens < mínimo (R_ESTOQUE_ATUAL) |
| Estoque | Giro de estoque | Saídas / estoque médio |
| PDV | Caixas com divergência | Contagem caixas divergentes (R_PDV) |
| Locação | Taxa de utilização | Dias locados / dias do período |
| Locação | Cações retidas | Valor retido (R_LOC_CAUCAO) |
| Contratos | MRR | Soma valores mensais ativos (R_CTR_MENSAL) |
| Contratos | Contratos vencendo | Contagem (R_CTR_VENCIMENTOS) |
| Fiscal | NFS-e rejeitadas/processando | Contagem (R_NFSE_STATUS) |

---

# 12. Lista priorizada — os 15 relatórios mais importantes para a operação

Ordem de implementação por impacto operacional, gerencial e de auditoria:

| # | Relatório | Módulo | Prioridade | Justificativa |
| --- | --- | --- | --- | --- |
| 1 | Vendas por Período, Filial, Cliente e Vendedor | Comercial | P1 | Núcleo de faturamento e comissão |
| 2 | Fluxo de Caixa Previsto x Realizado | Financeiro | P1 | Decisão de caixa diária |
| 3 | PDV por Caixa, Operador e Forma de Pagamento | Comercial | P1 | Auditoria de caixa e divergências |
| 4 | Fechamento de Caixa | Comercial | P1 | Conferência formal do PDV |
| 5 | Pedidos por Status, Atendimento Parcial e Faturamento | Comercial | P1 | Controle de carteira de pedidos |
| 6 | Estoque Atual, Entradas, Saídas e Ajustes | Comercial | P1 | Posição e mínimo de estoque |
| 7 | Receitas e Despesas por Categoria do Fluxo | Financeiro | P1 | Composição do resultado |
| 8 | NFS-e Emitidas por Período, Status, Tomador e Serviço | Fiscal/Serviços | P1 | Conferência fiscal |
| 9 | Extrato Bancário | Financeiro | P1 | Conciliação bancária |
| 10 | Locações Ativas, Concluídas e Atrasadas | Locação | P1 | Operação de locação |
| 11 | Disponibilidade por Período | Locação | P1 | Venda de reservas |
| 12 | Peças em Manutenção | Locação | P1 | Disponibilidade do acervo |
| 13 | Entidades por Tipo, Cidade, UF e Status | Cadastros | P1 | Qualidade da base |
| 14 | Clientes com Vendedor e Comissão Configurados | Cadastros | P1 | Apuração de comissão |
| 15 | Contratos de Serviços por Status | Contratos | P1 | Carteira de contratos |

> **Observações de implementação:**
> - Todos os relatórios aplicam `WHERE empresa_id = <id_empresa>` (isolamento `ID_EMPRESA`), respeitando permissões por perfil e filtros por filial.
> - Cada relatório deve ter versão **sintética** e **analítica** sempre que houver volume significativo de dados.
> - A tela de relatórios deve permitir exportação CSV (padrão) e PDF quando aplicável, com layout limpo (cabeçalho, filtros aplicados, totais e rodapé de geração).
> - Recomenda-se o menu único **"Relatórios"** com sub-itens por módulo, exibindo apenas os módulos habilitados pela assinatura da empresa.

