# Roadmap Comercial - LiveSun Controller

## Visao Geral
O LiveSun Controller evolui de uma solucao de controle financeiro pessoal para uma plataforma profissional escalavel para empresas de pequeno porte, mantendo seguranca de dados, controle por usuario e crescimento por planos.

Regra de comunicacao: para usuario final, nao usar o termo multiempresa.

## Etapa 0 - Migracao e Rebranding
Objetivo: preparar base para expansao comercial sem perder estabilidade.

- Criar novo workspace/pasta do projeto com o nome LiveSun Controller.
- Replicar objetos do ambiente atual para o novo ambiente.
- Atualizar branding em textos, telas, documentos e mensagens do sistema.
- Preservar comportamento funcional atual antes de iniciar evolucoes.

## Etapa 1 - Versao Pessoal (PF)
Objetivo: atrair usuario individual com experiencia simples e util no dia a dia.

- Lancamentos simplificados de despesas e receitas pessoais.
- Categorias de gastos (alimentacao, transporte, lazer, saude e outras), no lugar de entidade para contexto PF.
- Relatorios basicos e graficos intuitivos.
- Alertas de vencimento de contas.
- Plano Gratuito/Basico para entrada.

## Etapa 2 - Versao MEI e Negocio Domestico
Objetivo: profissionalizar gestao financeira de pequenos negocios.

- Fluxo de caixa previsto e realizado.
- Cadastro de clientes e fornecedores.
- Relatorios financeiros mais detalhados.
- Exportacao de relatorios em PDF e Excel.
- Transicao de dados PF para MEI sem retrabalho.

## Etapa 3 - Versao Microempresa
Objetivo: reduzir trabalho manual, aumentar controle operacional e previsibilidade.

- Importacao de XML de NFS-e.
- Importacao de XML de NF-e.
- Gestao de comissoes com formulas editaveis.
- Multiusuarios com controle de acesso por papel (RBAC).
- Integracao com contas bancarias.
- Importacao de OFX para conciliacao bancaria entre conta corrente e lancamentos.

## Etapa 4 - Versao Escalavel para Pequenas Empresas
Objetivo: consolidar o LiveSun Controller como solucao robusta para operacao financeira.

- Segregacao de dados por empresa/CNPJ/usuario (caracteristica interna de arquitetura e seguranca).
- Relatorios avancados para tomada de decisao.
- Seguranca reforcada: hardening de autenticacao, sessao, segredos, auditoria e monitoracao.
- Experiencia responsiva para desktop, tablet e celular.

## Seguranca e Governanca (Transversal)
Itens obrigatorios ao longo das etapas:

- Remover credenciais padrao previsiveis.
- Convite por e-mail para primeiro usuario da empresa.
- Politica de senha segura e fluxo de esqueci minha senha com token expiravel.
- CSRF, rate limiting e protecao anti-enumeracao em autenticacao.
- Segregacao e validacao de acesso por empresa em todas as rotas criticas.
- Auditoria de eventos sensiveis.
- Backup e restauracao testados.

## Estrategia Comercial
- Plano Gratuito/Basico: PF e MEI em inicio de operacao.
- Plano Profissional: microempresas com demanda de controle ampliado.
- Plano Corporativo: pequenas empresas em expansao.

## Etapa Comercial para Implementacao (Registrada em 2026-04-06)

### 1) Ciclo de assinatura
- Status da assinatura: ativa, trial, suspensa, cancelada.
- Data de vencimento e renovacao.
- Periodo de trial.

### 2) Cobranca recorrente
- Integracao com gateway (Asaas, Stripe, Mercado Pago etc.).
- Geracao de cobranca mensal/anual.
- Webhook para atualizar status apos pagamento.

### 3) Regra de inadimplencia
- Bloqueio parcial/total quando vencer.
- Janela de carencia (ex.: 3-7 dias).
- Mensagens claras na UI sobre bloqueio e como regularizar.

### 4) Upgrade/downgrade com efeito controlado
- Definir quando muda: imediato ou proximo ciclo.
- Tratar downgrade com excesso de usuarios e recursos ja usados.
- Politica de proporcionalidade/pro-rata (se houver).

### 5) Painel comercial/admin interno
- Lista de empresas com plano/status/vencimento.
- Trocar plano manualmente.
- Liberar excecao temporaria (ex.: 15 dias).

### 6) Contrato de oferta
- Congelar catalogo de planos (nome, preco, limites).
- Separar regra tecnica da regra comercial para facilitar mudanca de preco sem deploy.

### 7) Auditoria e suporte
- Log de alteracoes de plano/status por usuario/admin.
- Historico de cobrancas e tentativas de pagamento.

### 8) Comunicacao automatica
- Aviso pre-vencimento.
- Aviso de falha de pagamento.
- Confirmacao de pagamento e reativacao.

## Cobranca e Upgrade
- Integracao de assinatura recorrente (Stripe).
- Upgrade por limite de usuarios por plano.
- Regras claras de upgrade/downgrade sem perda de dados historicos.

## Criterios de Prontidao para Lancamento
- Seguranca validada em testes tecnicos e funcionais.
- Jornada completa por etapa (PF, MEI, Microempresa, Escalavel) validada.
- Monitoracao, alertas e playbook operacional ativos.
- Piloto com clientes controlados antes da divulgacao ampla.

## Conclusao
O LiveSun Controller acompanha o usuario desde o controle pessoal ate a gestao financeira profissional, com evolucao gradual, foco em experiencia pratica, seguranca operacional e capacidade de crescimento comercial.
