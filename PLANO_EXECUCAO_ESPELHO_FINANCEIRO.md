# Plano de Execucao Detalhado - Espelho Controller -> LiveSun Financeiro

Data: 2026-04-06
Base de referencia: ESPELHO_CONTROLLER_PONTO_CORTE_2026-04-06.md
Objetivo: implementar um espelho tecnico fiel do Controller no LiveSun Financeiro, sem incluir etapa comercial neste ciclo.

---

## 1) Regras de Operacao (anti-perda de contexto)

### 1.1 Regra de ouro
- Nunca iniciar uma tarefa sem criterio de aceite definido.
- Nunca fechar uma tarefa sem evidencia (teste, print, log, diff).
- Nunca avançar de fase com pendencia critica da fase anterior.

### 1.2 Fonte unica de verdade
- Documento de corte: ESPELHO_CONTROLLER_PONTO_CORTE_2026-04-06.md
- Este plano: PLANO_EXECUCAO_ESPELHO_FINANCEIRO.md

### 1.3 Controle de escopo
- Escopo permitido: paridade tecnica ate o ponto de corte.
- Escopo proibido nesta etapa: comercial (assinatura/cobranca/webhooks/inadimplencia).

### 1.4 Ritual diario (obrigatorio)
1. Ler pendencias abertas da fase atual.
2. Executar no maximo 1 tema funcional por vez (sem multitarefa entre modulos).
3. Rodar validacoes do modulo antes de comitar.
4. Registrar status no quadro de progresso ao final do dia.

---

## 2) Estrutura de acompanhamento

## 2.1 Quadro de progresso
- Backlog
- Em andamento
- Em validacao
- Concluido
- Bloqueado

## 2.2 Modelo de cartao de tarefa
- ID:
- Fase:
- Modulo:
- Objetivo:
- Entradas (arquivos de referencia):
- Saidas esperadas:
- Criterio de aceite:
- Evidencia:
- Risco:
- Status:

## 2.3 Definicao de pronto por tarefa (DoD)
- Codigo implementado.
- Sem erro de lint/sintaxe no arquivo alterado.
- Validacao funcional executada.
- Sem regressao visivel no modulo.
- Registro de evidencia anexado.

---

## 3) Plano em fases (ordem obrigatoria)

## Fase 0 - Preparacao e baseline
Objetivo: preparar ambiente e garantir trilho seguro.

Tarefas:
1. Criar branch de espelhamento no projeto Financeiro.
2. Confirmar versoes de Python/dependencias.
3. Validar .env e conexao com banco.
4. Validar boot da app sem quebra.
5. Importar/alinhar documento de corte no Financeiro.

Criterio de aceite:
- App sobe localmente e responde rota de health/dashboard.
- Banco acessivel e migrations executam sem erro basico.

Evidencias:
- comando de subida
- screenshot/saida de log

---

## Fase 1 - Fundacao de app e seguranca transversal
Objetivo: espelhar infraestrutura de execucao e guardas globais.

Entradas:
- src/app.py
- src/extensions.py
- src/access_control.py
- src/services/planos.py
- src/tenant.py

Tarefas:
1. Espelhar estrutura factory do Flask.
2. Registrar blueprints no mesmo padrao.
3. Aplicar before_request com ordem:
   - autenticacao
   - validacao de plano por endpoint
   - validacao de permissao por processo
   - bloqueio viewer para escrita
4. Espelhar context_processor com helpers de plano/permissao.
5. Espelhar CSRF e rate limiting.

Criterio de aceite:
- Usuario viewer nao consegue POST/PUT/PATCH/DELETE.
- Endpoint bloqueado por plano retorna aviso e redireciona.
- Endpoint sem permissao retorna aviso e redireciona.

Evidencias:
- testes manuais de 3 usuarios (admin/operator/viewer)
- logs de bloqueio

---

## Fase 2 - Modelo de dados e migracoes
Objetivo: reproduzir schema e indices com paridade.

Entradas:
- src/models/__init__.py
- migrations/001..008

Tarefas:
1. Espelhar modelos e relacionamentos com empresa_id.
2. Criar/aplicar migracoes na ordem oficial.
3. Garantir indices de desempenho (especialmente fluxo).
4. Validar integridade referencial em ambiente limpo e com dados.

Checklist tecnico:
- Empresa
- User
- RolePermission
- UserPermissionOverride
- Entidade
- FluxoContaModel
- ContaBanco
- Lancamento
- Comissao
- ParametroSistema
- ImportacaoNFSe
- ConciliacaoBancaria
- ConciliacaoItem
- FluxoCaixaPrevisto
- FluxoCaixaRealizado

Criterio de aceite:
- Schema criado sem erro.
- FKs e indices visiveis no banco.
- Operacoes CRUD basicas funcionando.

Evidencias:
- resultado das migracoes
- queries de validacao de schema

---

## Fase 3 - Autenticacao, usuarios e governanca operacional
Objetivo: espelhar controle de usuarios e papeis.

Entradas:
- src/routes/auth.py
- src/access_control.py

Tarefas:
1. Espelhar login por Empresa + Usuario + Senha.
2. Espelhar registro inicial com empresa e admin.
3. Espelhar tela de controle de acesso (role/status).
4. Espelhar controle de processos por operator.
5. Espelhar overrides por usuario.
6. Espelhar limite de usuarios por plano.

Criterio de aceite:
- Admin tem acesso total.
- Operator respeita matriz configurada.
- Viewer fica em leitura.
- Limite de usuarios por plano bloqueia criacao acima do teto.

Evidencias:
- matriz aplicada
- cenarios de login e permissao

---

## Fase 4 - Modulos core (cadastros + lancamentos)
Objetivo: consolidar base operacional financeira.

Entradas:
- src/routes/entidades.py
- src/routes/fluxo.py
- src/routes/contas_banco.py
- src/routes/lancamentos.py

Tarefas:
1. Espelhar CRUD de entidades.
2. Espelhar CRUD de fluxo.
3. Espelhar CRUD de contas banco com conta principal.
4. Espelhar CRUD de lancamentos (status, datas, valores).
5. Garantir tenant-scope em todas as consultas e mutacoes.

Criterio de aceite:
- CRUDs completos sem vazamento entre empresas.
- Vinculos (entidade/conta/fluxo) funcionando.

Evidencias:
- roteiro manual CRUD por modulo

---

## Fase 5 - Relatorios base e fluxo consolidado
Objetivo: entregar visao gerencial equivalente.

Entradas:
- src/routes/relatorios.py
- src/routes/relatorio_fluxo.py
- src/services/fluxo_relatorio.py

Tarefas:
1. Espelhar relatorios de listagem e exportacoes.
2. Espelhar relatorio consolidado de fluxo com filtros:
   - periodo
   - tipo R/P
   - conta bancaria
   - entidade
   - agrupamento dia/semana/mes
3. Espelhar exportacao Excel (abas Diario/Resumo/Grafico).
4. Validar performance com indices da migracao 008.

Criterio de aceite:
- Totais e saldos coerentes em HTML/JSON/Excel.
- Tempo de resposta aceitavel para volume medio.

Evidencias:
- arquivos exportados
- comparacao de totais

---

## Fase 6 - Comissoes
Objetivo: espelhar modulo completo de comissoes.

Entradas:
- src/routes/comissoes.py
- src/services/comissoes.py
- COMISSOES.md
- COMISSOES_IMPLEMENTATION.md

Tarefas:
1. Espelhar parametro aliquota padrao.
2. Espelhar campos de cliente e lancamento para comissao.
3. Espelhar regra de calculo:
   - vl_liquido = vl_nota - vl_imposto - vl_outros_custos - vl_repasse
   - vl_comissao = vl_liquido * (aliquota/100)
4. Espelhar apuracao com bloqueio de duplicidade.
5. Espelhar listagem/relatorio/export CSV.

Criterio de aceite:
- Apuracao correta para clientes com e sem aliquota especifica.
- Nao duplica comissao para mesmo evento elegivel.

Evidencias:
- planilha de amostras com calculo esperado vs obtido

---

## Fase 7 - NFSe, OFX e conciliacao
Objetivo: espelhar entradas automaticas e reconciliacao.

Entradas:
- src/routes/importacoes.py
- src/routes/conciliacao.py
- src/services/ofx_parser.py
- src/services/conciliacao.py

Tarefas:
1. Espelhar importacao NFSe XML.
2. Espelhar fallback de aliquota ISS.
3. Espelhar criacao de tomador e lancamento com fallback de fluxo padrao.
4. Espelhar importacao OFX.
5. Espelhar conciliacao automatica e manual.
6. Espelhar regras de consistencia (debito=P, credito=R, mesma conta).

Criterio de aceite:
- NFSe cria/atualiza entidade e gera lancamento sem falha de fluxo padrao.
- OFX gera conciliacao e permite ajuste manual seguro.

Evidencias:
- XML e OFX de teste com resultado documentado

---

## Fase 8 - UI, tema e padronizacao visual
Objetivo: manter consistencia visual com o Controller.

Entradas:
- src/templates/layout.html
- src/static/css/style.css
- templates de modulos

Tarefas:
1. Espelhar tema claro/escuro por variaveis CSS.
2. Espelhar sidebar/topbar e estado ativo de menu.
3. Normalizar classes legadas em tabelas/cards/headings.
4. Revisar contraste dos cabecalhos nas telas criticas.

Criterio de aceite:
- Paridade visual funcional em claro/escuro.
- Sem cabecalhos ilegiveis em telas principais.

Evidencias:
- capturas comparativas por tela

---

## Fase 9 - Homologacao final do espelho
Objetivo: declarar espelho pronto para iniciar comercial.

Tarefas:
1. Rodar checklist de paridade completo.
2. Executar regressao ponta-a-ponta.
3. Corrigir pendencias remanescentes.
4. Versionar baseline do espelho (tag).
5. Publicar relatorio de fechamento.

Criterio de aceite:
- 100% checklist marcado.
- Sem bloqueadores abertos.
- Baseline tagueado.

---

## 4) Matriz de risco e resposta

Risco: vazamento de dados entre empresas
- Sinal: query retornando dado de outra empresa
- Acao: bloquear release, revisar scoped_query e filtros empresa_id

Risco: permissao inconsistente
- Sinal: usuario acessa endpoint bloqueado
- Acao: revisar ENDPOINT_PERMISSION_MAP e guards de before_request

Risco: regressao de NFSe
- Sinal: falha ao criar lancamento para tomador novo
- Acao: validar helper de fluxo padrao e fallback legado

Risco: performance de fluxo
- Sinal: relatorio lento
- Acao: conferir migracao 008 + plano de execucao SQL

Risco: divergencia visual
- Sinal: contraste ruim em claro/escuro
- Acao: reforcar tokens de tema e remover estilos inline fixos

---

## 5) Politica de commits (para nao se perder)

Padrao de commit por tarefa:
- tipo(scope): resumo
Exemplos:
- feat(auth): espelha login por empresa e limites por plano
- feat(tenant): aplica scoped_query nas rotas de lancamento
- fix(nfse): corrige fallback de fluxo padrao para tomador
- chore(ui): harmoniza contraste de cabecalhos no tema

Regra:
- 1 commit por objetivo fechado (evitar commit misto).
- Sempre anexar evidencia no texto do PR (o que foi validado).

---

## 6) Roteiro de validacao por modulo (check rapido)

Auth/Governanca:
- [ ] login admin
- [ ] login operator
- [ ] login viewer
- [ ] bloqueio de escrita para viewer

Cadastros/Lancamentos:
- [ ] cria/edita/exclui entidade
- [ ] cria/edita/exclui conta banco
- [ ] cria/edita/exclui fluxo
- [ ] cria/edita/paga lancamento

Relatorios:
- [ ] listagens com filtro
- [ ] exportacoes
- [ ] fluxo consolidado html/json/excel

Comissoes:
- [ ] parametrizacao
- [ ] apuracao
- [ ] relatorio
- [ ] csv

Importacao/Conciliacao:
- [ ] NFSe XML valido
- [ ] NFSe com aliquota ausente
- [ ] OFX com conciliacao automatica
- [ ] vinculo manual e desvinculo

UI:
- [ ] claro/escuro
- [ ] contraste de cabecalhos
- [ ] menu ativo

---

## 7) Marco de encerramento deste plano

Este plano se encerra quando:
1. O espelho tecnico estiver homologado.
2. A baseline estiver tagueada.
3. O backlog da etapa comercial for iniciado em documento separado.

Entrega seguinte (fora deste plano):
- Plano de implementacao da etapa comercial.
