# Etapa Comercial - Descritivo para Implementacao

Data: 2026-04-06
Fonte principal: ROADMAP_LIVESUN_CONTROLLER.md (secao "Etapa Comercial para Implementacao")
Escopo: Controller (sem migrar para outro projeto)

---

## 1) Objetivo da etapa comercial

Implementar o ciclo completo de monetizacao do LiveSun Controller, cobrindo:
- assinatura
- cobranca recorrente
- inadimplencia
- upgrade/downgrade
- painel interno de operacao comercial
- auditoria e comunicacao

Regra de produto:
- Separar regra comercial (catalogo e precificacao) da regra tecnica (gating por endpoint/feature).

---

## 2) Escopo funcional fechado (o que deve ser implementado)

## 2.1 Ciclo de assinatura
- Status da assinatura:
  - ativa
  - trial
  - suspensa
  - cancelada
- Campos obrigatorios:
  - data_inicio
  - data_vencimento
  - data_renovacao
  - data_fim_trial (quando houver)

Resultado esperado:
- Cada empresa passa a ter um estado comercial explicito e auditable.

## 2.2 Cobranca recorrente
- Integracao com gateway (provedor configuravel).
- Geracao de cobranca mensal/anual.
- Registro de eventos de cobranca.
- Processamento de webhook para atualizar status de pagamento.

Resultado esperado:
- Pagamentos atualizam assinatura automaticamente.

## 2.3 Regra de inadimplencia
- Detectar vencimento sem pagamento.
- Aplicar janela de carencia (ex.: 3-7 dias, configuravel).
- Bloqueio parcial/total apos carencia.
- Mensagens claras na interface (motivo, prazo, como regularizar).

Resultado esperado:
- Sistema aplica politicas de bloqueio de forma previsivel e transparente.

## 2.4 Upgrade/downgrade com efeito controlado
- Politica de efetivacao:
  - imediata ou
  - no proximo ciclo
- Tratar downgrade com uso acima do novo limite.
- Definir regra de pro-rata (se habilitada comercialmente).

Resultado esperado:
- Mudanca de plano sem perda de historico e sem comportamento ambiguo.

## 2.5 Painel comercial/admin interno
- Lista de empresas com:
  - plano
  - status de assinatura
  - vencimento
- Acoes:
  - trocar plano manualmente
  - liberar excecao temporaria (ex.: +15 dias)

Resultado esperado:
- Operacao comercial consegue atuar sem alterar banco manualmente.

## 2.6 Contrato de oferta (catalogo comercial)
- Congelar catalogo de planos:
  - nome
  - preco
  - limites
  - periodicidade
- Versao de oferta (para historico).
- Desacoplar mudanca de preco de deploy tecnico.

Resultado esperado:
- Ajustes comerciais futuros sem mexer no codigo de regra tecnica.

## 2.7 Auditoria e suporte
- Log de alteracoes de plano/status por usuario/admin.
- Historico de cobrancas e tentativas de pagamento.

Resultado esperado:
- Rastreabilidade para suporte, financeiro e governanca.

## 2.8 Comunicacao automatica
- Aviso pre-vencimento.
- Aviso de falha de pagamento.
- Confirmacao de pagamento e reativacao.

Resultado esperado:
- Menor churn e menos chamados manuais.

---

## 3) Fora de escopo nesta etapa

- Novos modulos de negocio financeiros.
- Mudanca estrutural de tenant/RBAC ja existente.
- Reescrita de layout global.

---

## 4) Dependencias tecnicas no Controller

Ja existente e deve ser reaproveitado:
- modelo de Empresa com campo plano
- servico de planos e gating por endpoint
- before_request com bloqueio por plano e permissao
- controle de acesso por papel/usuario

Sera adicionado nesta etapa:
- camada de assinatura e cobranca (novas tabelas/servicos/rotas)
- integracao webhook de gateway
- jobs de ciclo comercial (vencimento, notificacao, suspensao)

---

## 5) Entregaveis tecnicos minimos

## 5.1 Dados (novas estruturas)
Sugestao de entidades:
- assinatura_empresa
- cobranca_recorrente
- evento_cobranca (webhook/auditoria)
- catalogo_planos_comercial
- historico_mudanca_plano
- notificacao_comercial

## 5.2 Backend
- servico_assinatura
- servico_cobranca
- servico_inadimplencia
- servico_upgrade_downgrade
- webhook_controller (gateway)

## 5.3 Rotas/telas
- painel comercial interno (admin)
- detalhes da assinatura por empresa
- historico de cobrancas
- acao manual de excecao/carencia

## 5.4 Jobs
- job diario de vencimento/inadimplencia
- job de notificacoes (pre-vencimento/falha/reativacao)

---

## 6) Criterios de aceite da etapa comercial

- assinatura muda de estado corretamente por eventos de pagamento
- webhook idempotente (nao duplica processamento)
- bloqueio por inadimplencia respeita carencia configurada
- upgrade/downgrade aplica politica definida sem perda de historico
- painel interno permite operacao manual com auditoria
- notificacoes essenciais disparadas nos eventos criticos

---

## 7) Riscos principais

- processamento duplicado de webhook
- divergencia entre estado local e estado do gateway
- bloqueio indevido de cliente ativo
- downgrade sem tratar excesso de uso

Mitigacoes:
- idempotencia por event_id externo
- reconciliacao periodica com gateway
- trilha de auditoria obrigatoria em toda mudanca de status/plano
- validacoes de pre-condicao antes de efetivar downgrade

---

## 8) Ordem recomendada para iniciar implementacao

1. Modelagem de dados comercial + migracoes.
2. Servico de assinatura (estado e transicoes).
3. Servico de cobranca + webhook idempotente.
4. Regras de inadimplencia com carencia.
5. Painel comercial interno.
6. Upgrade/downgrade com politica configuravel.
7. Comunicacoes automaticas.
8. Homologacao fim-a-fim.

---

## 9) Definicao de pronto para abrir desenvolvimento

A implementacao pode iniciar quando:
- gateway alvo da Fase 1 for definido: Asaas
- politica inicial de carencia for definida: 7 dias
- regra de efetivacao de upgrade/downgrade for escolhida: apos 30 dias
- catalogo inicial de planos comerciais for aprovado (ver secao 10)

---

## 10) Catalogo inicial de planos comerciais (proposta v1)

Objetivo:
- Ter um catalogo comercial inicial para iniciar desenvolvimento e homologacao da etapa comercial.
- Manter alinhamento com os planos tecnicos ja existentes: basic, intermediate, premium.

### 10.1 Planos e precificacao (mensal)
- Basico: R$ 49,00/mes
- Intermediario: R$ 129,00/mes
- Premium: R$ 249,00/mes

### 10.2 Planos e precificacao (anual)
- Basico: R$ 490,00/ano (equivalente a 10 meses)
- Intermediario: R$ 1.290,00/ano (equivalente a 10 meses)
- Premium: R$ 2.490,00/ano (equivalente a 10 meses)

### 10.3 Limites e recursos por plano (alinhado ao tecnico)
- Basico:
  - usuarios ativos: ate 2
  - sem relatorios avancados de fluxo
  - sem importacoes (NFSe/OFX)
  - sem conciliacao
  - sem comissoes
  - sem governanca avancada
- Intermediario:
  - usuarios ativos: ate 5
  - com relatorios avancados de fluxo
  - com importacoes (NFSe/OFX)
  - com conciliacao
  - com comissoes
  - sem governanca avancada
- Premium:
  - usuarios ativos: ilimitado
  - todos os recursos liberados
  - governanca avancada liberada

### 10.4 Regras comerciais iniciais
- Trial inicial: 14 dias
- Carencia por inadimplencia: 7 dias
- Efetivacao de upgrade/downgrade: apos 30 dias
- Moeda de cobranca: BRL
- Ciclos de cobranca: mensal e anual

### 10.5 Observacao de governanca de catalogo
- O catalogo deve ser versionado como oferta comercial (ex.: catalogo v1).
- Mudancas de preco e condicoes devem gerar nova versao (v2, v3...) sem alterar historico.

Fim do descritivo.
