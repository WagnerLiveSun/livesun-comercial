# ESPELHO TECNICO - LIVESUN CONTROLLER

Data de corte: 2026-04-06
Commit de referencia: 5bd2f2e
Branch de referencia: main

Objetivo deste documento:
- Registrar, de forma executavel, o que ja foi implementado no Controller.
- Servir como guia de espelhamento para o LiveSun Financeiro ate este ponto.
- Congelar escopo tecnico antes da etapa comercial.

Importante:
- Depois deste corte, novas evolucoes devem entrar como fase "Comercial".
- Este documento descreve o "como implementar" para reproduzir o sistema com paridade.

---

## 1) Escopo funcional implementado no Controller (ate o corte)

### 1.1 Fundacao da plataforma
- Aplicacao Flask em padrao factory.
- ORM com SQLAlchemy.
- Autenticacao com Flask-Login.
- Protecao CSRF.
- Rate limit em endpoints sensiveis de autenticacao.
- Camada de tema claro/escuro com variaveis CSS centrais.

### 1.2 Cadastros e operacao financeira
- Entidades (clientes, fornecedores, vendedores, etc).
- Plano de fluxo (contas de fluxo tipo Recebimento/Pagamento).
- Contas bancarias.
- Lancamentos financeiros.
- Dashboard operacional.

### 1.3 Relatorios
- Listagem de lancamentos.
- Listagem de notas NFSe importadas.
- Fluxo de caixa consolidado (HTML, JSON e exportacao Excel).
- Balancetes e relatorios auxiliares de fluxo (templates e filtros).

### 1.4 Importacao e conciliacao
- Importacao de NFSe via XML.
- Importacao de OFX.
- Conciliacao bancaria automatica e manual (vincular/desvincular item).

### 1.5 Modulo de comissoes
- Parametro de aliquota padrao por empresa.
- Campos de comissao no cliente e no lancamento.
- Apuracao de comissoes por periodo.
- Relatorio e exportacao CSV.

### 1.6 Multiempresa + seguranca de acesso
- Isolamento por empresa (tenant).
- RBAC com papeis admin/operator/viewer.
- Override de permissao por usuario.
- Restricao por plano (basic/intermediate/premium) por endpoint.

---

## 2) Estado arquitetural (o que deve ser espelhado)

### 2.1 Aplicacao e bootstrap
Arquivo de referencia: src/app.py

Implementado:
- Registro de blueprints principais.
- Mapa endpoint -> chave de permissao.
- Validacao de plano por endpoint em before_request.
- Validacao de permissao por papel em before_request.
- Regra global de viewer somente leitura (bloqueia POST/PUT/PATCH/DELETE).
- Filtro de moeda BRL para templates.
- Inicializacao de schema e bootstrap de admin.

Requisito para espelho:
- Reproduzir a mesma ordem de validacao: autenticacao -> plano -> permissao -> regra viewer.
- Reproduzir contexto global de template (plano atual, helpers de permissao).

### 2.2 Modelagem de dados
Arquivo de referencia: src/models/__init__.py

Entidades centrais implementadas:
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

Aspectos obrigatorios no espelho:
- Todas as tabelas com empresa_id para isolamento.
- Indices de desempenho nos pontos de consulta pesada.
- Relacionamentos e FKs com coerencia de tenant.
- Campos de rastreabilidade (fonte, referencia_banco, timestamps).

### 2.3 Tenant scoping
Arquivo de referencia: src/tenant.py

Implementado:
- tenant_id()
- scoped_query(model)
- scoped_get_or_404(model, id)

Requisito para espelho:
- Toda query de dominio deve ser tenant-scoped.
- Evitar uso de Model.query "solto" em rotas de dados de negocio.

### 2.4 Controle de acesso
Arquivo de referencia: src/access_control.py

Implementado:
- Catalogo de permissoes por processo.
- Matriz default por papel.
- Overrides por role e por usuario.
- Persistencia da matriz via tela administrativa.

Requisito para espelho:
- Garantir precedence correta:
  1) Admin total.
  2) Override de usuario.
  3) Override de role.
  4) Default do papel.

### 2.5 Plano comercial tecnico (gating de features)
Arquivo de referencia: src/services/planos.py

Implementado:
- Planos basic/intermediate/premium.
- Rank de plano.
- Matriz endpoint_min_level.
- max_users por plano.

Requisito para espelho:
- Centralizar regras no servico de planos.
- Nao espalhar ifs de plano em rotas sem padrao.

---

## 3) Modulos funcionais e como replicar

### 3.1 Autenticacao e usuarios
Arquivo de referencia: src/routes/auth.py

Implementado:
- Login com Empresa + Usuario + Senha.
- Registro de empresa/usuario admin.
- Adicao de usuarios por admin, com limite por plano.
- Gestao de papeis e status de usuario.
- Gestao de permissoes por processo e por usuario.
- Rate limiting em login/register/add_user.

Como replicar no Financeiro:
1. Copiar fluxo de login por empresa (documento normalizado).
2. Copiar fluxo de cadastro inicial com empresa + admin.
3. Implementar mesmas telas de controle de acesso.
4. Aplicar mesmos guards de role e mesmas mensagens de bloqueio.

### 3.2 Cadastros base
Arquivos de referencia:
- src/routes/entidades.py
- src/routes/fluxo.py
- src/routes/contas_banco.py

Implementado:
- CRUD completo com filtros/listagens.
- Campos adicionais para comissao no cliente.
- Conta bancaria com flag de principal.
- Vinculos com fluxo e consistencia de tenant.

Como replicar no Financeiro:
1. Migrar modelos primeiro.
2. Migrar rotas e validacoes.
3. Migrar templates mantendo nomes de campos.
4. Validar FKs e selects tenant-scoped.

### 3.3 Lancamentos
Arquivo de referencia: src/routes/lancamentos.py

Implementado:
- CRUD de lancamentos.
- Campos de imposto e outros custos.
- Status e datas de pagamento.
- Vinculo com entidade, conta e fluxo.

Como replicar no Financeiro:
1. Espelhar regra de status e campos monetarios.
2. Preservar origem/fonte de lancamento (manual/ofx/nfse).
3. Preservar comportamento da data de pagamento.

### 3.4 NFSe
Arquivo de referencia: src/routes/importacoes.py

Implementado:
- Upload XML.
- Parser com fallback de aliquota ISS:
  - pISSQN
  - aliquotaISS
  - pTotTribSN
  - leitura de texto da descricao (fallback)
  - padrao 6% se nada encontrado
- Criacao/atualizacao de Entidade tomador.
- Regra robusta de conta de fluxo padrao de recebimento.
- Criacao de lancamento da NFSe.
- Registro em importacao_nfse.

Ponto critico ja corrigido:
- Fallback de fluxo padrao para tomador e para lancamento quando nao houver conta definida.
- Compatibilidade com codigo legado de fluxo (1.1.1) e padrao atual (1).

Como replicar no Financeiro:
1. Copiar parser e validacoes na integra.
2. Copiar helper de conta de fluxo padrao.
3. Copiar criacao de entidade e lancamento com os mesmos fallbacks.
4. Testar XML com e sem aliquota no arquivo.

### 3.5 OFX e conciliacao bancaria
Arquivos de referencia:
- src/routes/importacoes.py
- src/routes/conciliacao.py
- src/services/conciliacao.py

Implementado:
- Importacao de OFX e criacao de conciliacao.
- Reconciliacao automatica.
- Vinculacao manual item <-> lancamento.
- Desvinculacao manual.
- Regras de consistencia:
  - mesma conta bancaria
  - debito com tipo P
  - credito com tipo R

Como replicar no Financeiro:
1. Reproduzir modelos ConciliacaoBancaria/Item.
2. Reproduzir servico de reconciliacao.
3. Reproduzir checks de consistencia no vinculo manual.
4. Reproduzir atualizacao de lancamento ao conciliar manualmente.

### 3.6 Comissoes
Arquivos de referencia:
- src/routes/comissoes.py
- src/services/comissoes.py
- src/templates/comissoes/*
- COMISSOES.md
- COMISSOES_IMPLEMENTATION.md

Implementado:
- Parametro aliquota_comissao_padrao por empresa.
- Regra de aliquota especifica por cliente ou padrao.
- Repasse e base liquida de calculo.
- Apuracao por periodo sem duplicidade.
- Relatorio e export CSV.

Formula implementada:
- vl_liquido = vl_nota - vl_imposto - vl_outros_custos - vl_repasse
- vl_comissao = vl_liquido * (aliquota / 100)

Como replicar no Financeiro:
1. Aplicar migracao de comissoes.
2. Reproduzir servico de apuracao e validacao de duplicidade.
3. Reproduzir telas de apuracao/lista/relatorio/parametros.
4. Reproduzir filtros e exportacao CSV.

### 3.7 Relatorio de fluxo consolidado
Arquivos de referencia:
- src/routes/relatorio_fluxo.py
- src/services/fluxo_relatorio.py

Implementado:
- Filtros por periodo, tipo, conta, entidade.
- Agrupamento por dia/semana/mes.
- Saida HTML e JSON.
- Exportacao Excel com abas Diario/Resumo/Grafico.
- Agregacao de contas sinteticas por prefixo de codigo.

Como replicar no Financeiro:
1. Copiar servico de consolidacao e agregacao.
2. Copiar endpoint de exportacao com openpyxl.
3. Garantir indices de performance (migracao 008).

### 3.8 UI e sistema de tema
Arquivos de referencia:
- src/templates/layout.html
- src/static/css/style.css

Implementado:
- Tema claro/escuro persistido em localStorage.
- Variaveis CSS centralizadas.
- Sidebar e topbar padronizados.
- Normalizacao de classes legadas Bootstrap para consistencia visual.
- Ajustes recentes de contraste de cabecalhos (inclusive Comissoes).

Como replicar no Financeiro:
1. Copiar layout base e variaveis.
2. Copiar classes utilitarias de tema.
3. Copiar normalizacao global de tabelas/cards/headings.
4. Revisar templates para remover estilos inline fixos.

---

## 4) Migracoes e evolucao de schema (ordem de aplicacao)

Diretorio de referencia: migrations/

Aplicar nesta ordem:
1. 001_create_comissoes_tables.sql
2. 002_fix_cross_tenant_fluxo_reference.sql (manutencao/diagnostico)
3. 003_add_entidade_id_to_importacao_nfse.sql
4. 004_remove_campo_cnpj_add_cnpj_cpf.sql
5. 005_add_is_principal_and_fluxo_conta_id.sql
6. 006_add_aliquota_iss_to_importacao_nfse.sql
7. 007_add_role_to_users.sql
8. 008_add_fluxo_report_indexes.sql

Observacoes:
- A migracao 002 e script de saneamento manual para inconsistencia cruzada de tenant.
- A migracao 008 e essencial para performance no relatorio de fluxo.

---

## 5) Sequencia recomendada de espelhamento no LiveSun Financeiro

### Fase A - Base tecnica
1. Config Flask factory + extensoes (db, csrf, login, limiter).
2. Configurar contexto de app, filtros e handlers de erro.
3. Criar tenant helpers e guards globais.

### Fase B - Dados e seguranca
1. Espelhar modelos e FKs.
2. Rodar migracoes na ordem.
3. Garantir indices.
4. Seed inicial de empresa/admin/plano de fluxo.

### Fase C - Modulos de negocio
1. Auth + controle de acesso.
2. Entidades, fluxo, contas banco, lancamentos.
3. Relatorios base.
4. Comissoes.
5. Importacoes NFSe/OFX.
6. Conciliacao.
7. Relatorio fluxo consolidado + exportacao.

### Fase D - Interface
1. Copiar layout e tema.
2. Padronizar templates para classes de tema.
3. Homologar claro/escuro em telas criticas.

### Fase E - Qualidade
1. Rodar testes existentes.
2. Executar roteiro manual de regressao.
3. Corrigir desvios de tenant/permissao/plano.
4. Congelar baseline do espelho.

---

## 6) Checklist de paridade (aceite do espelho)

Paridade funcional:
- [ ] Login por empresa + usuario + senha
- [ ] CRUDs base operando por tenant
- [ ] Comissoes completas (apurar, listar, relatorio, csv)
- [ ] Importacao NFSe com fallback de aliquota e conta de fluxo
- [ ] Importacao OFX + conciliacao automatica/manual
- [ ] Relatorio de fluxo consolidado com filtros e exportacao

Paridade de seguranca:
- [ ] Guards por plano aplicados em before_request
- [ ] Guards por permissao aplicados em before_request
- [ ] Viewer bloqueado para escrita
- [ ] Todas as queries de negocio tenant-scoped

Paridade de dados:
- [ ] Schema equivalente
- [ ] Indices equivalentes
- [ ] Migracoes executadas com sucesso

Paridade de UX:
- [ ] Tema claro/escuro consistente
- [ ] Cabecalhos com contraste padronizado
- [ ] Menu ativo correto nas secoes

---

## 7) O que fica fora deste corte (proxima etapa)

Escopo NAO implementado neste espelho (etapa comercial):
- Ciclo de assinatura (status, trial, renovacao).
- Cobranca recorrente e webhooks de gateway.
- Regras de inadimplencia e bloqueio por atraso.
- Upgrade/downgrade com efeito financeiro.
- Painel comercial interno de assinatura.
- Catalogo de planos comercial separado de regra tecnica.
- Historico de cobrancas e auditoria comercial.
- Comunicacoes automaticas de cobranca.

Referencia de backlog:
- ROADMAP_LIVESUN_CONTROLLER.md (secao "Etapa Comercial para Implementacao").

---

## 8) Riscos conhecidos e cuidados na replicacao

- Risco de vazamento cross-tenant se alguma query ficar sem filtro de empresa.
- Risco de regressao em NFSe se remover fallback de fluxo/aliquota.
- Risco de quebra de permissao se validations forem feitas somente em UI.
- Risco de performance no fluxo consolidado sem indices da migracao 008.
- Risco de inconsistencias visuais sem a normalizacao de classes legadas no layout.

Mitigacoes:
- Code review focado em tenant_id e scoped_query.
- Testes de permissao por role e por plano.
- Testes de NFSe com XML incompleto.
- Teste de carga basico para relatorio de fluxo.
- Checklist visual claro/escuro nas principais telas.

---

## 9) Evidencias principais do corte

Arquivos-chave para consulta rapida:
- src/app.py
- src/models/__init__.py
- src/tenant.py
- src/access_control.py
- src/services/planos.py
- src/routes/auth.py
- src/routes/importacoes.py
- src/routes/conciliacao.py
- src/routes/relatorio_fluxo.py
- src/services/fluxo_relatorio.py
- src/services/comissoes.py
- src/templates/layout.html
- COMISSOES.md
- COMISSOES_IMPLEMENTATION.md
- ROADMAP_LIVESUN_CONTROLLER.md

---

## 10) Definicao de pronto do espelho

O espelho para o LiveSun Financeiro sera considerado pronto quando:
1. O checklist de paridade estiver 100% marcado.
2. O comportamento de tenant, permissao e plano estiver igual ao Controller.
3. Os modulos NFSe/OFX/Conciliacao/Comissoes estiverem homologados.
4. O visual claro/escuro estiver consistente nas telas principais.
5. O baseline for versionado com tag de corte tecnico do Financeiro.

Fim do documento.
