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
