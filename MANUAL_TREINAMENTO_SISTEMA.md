# Manual de Treinamento do LiveSun Comercial

## 1. Objetivo

Este manual descreve o uso operacional do sistema, por modulo, com foco em treinamento de equipe, rotina diaria e controle de acesso. Tambem registra a revisao tecnica e logica da base para apoiar operacao em MySQL e PostgreSQL.

## 1.2 Escopo da base de dados

A entrega do projeto contempla a geracao completa da estrutura do banco para os dois ambientes suportados:

1. MySQL usa o schema principal de criacao do projeto.
2. PostgreSQL usa o conjunto de scripts de criacao dividido em partes.

Assim, o processo nao se limita a migracao de dados. Ele inclui a criacao da base do zero, a instalacao das tabelas do sistema e a aplicacao de ajustes de compatibilidade quando necessario.

## 1.1 Sumario executivo por setor

### Administracao

Uso principal: governar acesso, perfis, plano da empresa e saude da operacao.

O administrador deve criar usuarios, liberar processos, revisar o plano contratado e acompanhar falhas de schema ou permissao.

### Financeiro

Uso principal: manter contas bancarias, lancamentos e conciliacao.

O financeiro deve registrar entradas e saidas, conferir extratos, conciliar movimentos e revisar fluxo previsto e realizado.

### Comercial

Uso principal: manter cadastros, estoque, compras e vendas.

O comercial deve administrar filiais, produtos, servicos, compras manuais, documentos nao fiscais, tabelas de preco, orcamentos, pedidos e PDV.

### Operacao / Atendimento

Uso principal: executar tarefas do dia com agilidade e sem alterar regras centrais.

O operador faz cadastros e movimentos autorizados, enquanto o viewer apenas consulta e valida informacoes.

### Suporte / Backoffice

Uso principal: acompanhar a plataforma, assinaturas e ajustes administrativos da software house.

O acesso backoffice deve ser usado somente para suporte, manutencao e acompanhamento de conta, sem interferir no tenant do cliente.

## 2. Revisao tecnica e logica

### 2.1 Arquitetura geral

O sistema usa Flask, SQLAlchemy e Flask-Login. A navegacao e controlada por blueprints, e as regras de acesso acontecem em tres niveis:

1. Sessao autenticada com login e senha.
2. Permissao por processo, baseada em endpoint e papel do usuario.
3. Isolamento por empresa com filtro por `empresa_id` em quase todas as consultas.

### 2.2 Estrutura de banco

A base do projeto contem DDLs para MySQL e scripts dedicados para PostgreSQL. O arquivo `schema_comercial.sql` funciona como referencia de criacao da base MySQL, enquanto os arquivos de migracao e os scripts PostgreSQL servem para instalacao em ambientes diferentes.

### 2.3 Ponto de atencao sobre compatibilidade

Existe diferenca entre o modelo Python e o schema SQL em alguns pontos. Isso explica boa parte dos problemas de execucao quando o banco foi criado por script antigo ou quando a migracao nao foi concluida.

Campos e areas que exigem atencao:

- `empresas`: o modelo possui mais campos do que a tabela basica, como nome fantasia, atividades da empresa, endereco, inscricoes, contato, logo e parametros fiscais.
- `entidades`: o modelo inclui `codigo_municipio_ibge` e campos de comissao que podem faltar em bases antigas.
- `users`: o sistema aceita usuario LiveSun sem empresa para backoffice, mas o banco precisa permitir `empresa_id` nulo.
- `lancamentos`: o modelo usa rastreabilidade de origem e campos de apoio financeiro; a base precisa ter os campos de valor e referencia coerentes com o codigo.
- Modulos comerciais: filiais, produtos, servicos, estoque, compras, documentos, orcamentos, pedidos e PDV exigem as tabelas especificas do modulo comercial, nao apenas a estrutura financeira basica.

### 2.4 Hipotese pratica de falha

Se o sistema sobe mas quebra ao abrir telas ou ao gravar registros, a causa mais provavel e uma destas:

1. A tabela existe, mas faltam colunas que o modelo acessa.
2. A tabela foi criada em uma versao antiga, com nomes diferentes de colunas ou restricoes antigas de usuario.
3. O banco correto nao foi selecionado no ambiente, principalmente entre MySQL e PostgreSQL.

### 2.5 Checks rapidos de validacao

Antes de considerar a base pronta, vale conferir:

1. A tabela `users` aceita `empresa_id` nulo para admin da LiveSun.
2. A empresa possui `plano` e, se o sistema for usar dados completos, os campos adicionais de cadastro e atividade.
3. As tabelas `role_permissions` e `user_permission_overrides` existem.
4. As tabelas do comercial existem: `filiais`, `produtos`, `servicos`, `estoque_movimentos`, `compras_nf_manual`, `documentos_venda`, `tabelas_preco`, `orcamentos`, `pedidos_venda`, `pdv_*`.
5. As tabelas de conciliacao e fluxo existem: `contas_banco`, `fluxo_contas_modelo`, `lancamentos`, `fluxo_caixa_realizado`, `fluxo_caixa_previsto`, `conciliacao_bancaria`, `conciliacao_item`.

## 3. Controle de usuarios e acesso

### 3.1 Perfis existentes

O sistema trabalha com tres perfis logicos:

- `admin`: acesso total. Pode criar usuarios, ajustar permissoes e operar todos os modulos liberados pelo plano.
- `operator`: usuario operacional. Pode ter os processos liberados ou bloqueados pelo admin por meio da matriz de permissao.
- `viewer`: consulta apenas. O sistema bloqueia escrita em rotas de modificacao, mesmo que a tela seja acessivel para leitura.

### 3.2 Como o acesso funciona

O acesso eh decidido nesta ordem:

1. Login valida o usuario.
2. O plano da empresa permite ou nao o endpoint.
3. O papel do usuario libera ou nega o processo.
4. Overrides por usuario podem sobrescrever a permissao do papel.
5. Para viewer, qualquer acao de escrita e bloqueada centralmente.

### 3.3 Cadastro de usuario

Processo: `Gerenciar Usuarios`.

Passo a passo:

1. Entre como admin.
2. Abra a tela de criacao de usuario.
3. Informe username, email, senha e nome completo.
4. Escolha o perfil: admin, operator ou viewer.
5. Confirme se o usuario ficara ativo.
6. Se nao for admin, ajuste as permissoes de processo.

Exemplo:
Uso principal: manter cadastros, Estoque e vendas.
- Nome de login: `joao.vendas`
- Email: `joao@empresa.com.br`
 Modulos comerciais: Estoque, produtos, servicos, compras, documentos, orcamentos, pedidos e PDV exigem as tabelas especificas do modulo comercial, nao apenas a estrutura financeira basica.
- Permissoes: liberar comercial, entidades, lancamentos e relatorios.

 As tabelas do comercial existem: `filiais`, `produtos`, `servicos`, `estoque_movimentos`, `compras_nf_manual`, `documentos_venda`, `tabelas_preco`, `orcamentos`, `pedidos_venda`, `pdv_*`.

- O sistema nao permite remover o ultimo admin ativo da empresa.
- O usuario nao pode desativar o proprio acesso durante a sessao atual.
1. Cadastrar Estoque, produtos e servicos.
- O email e unico no sistema.
- O username e unico por empresa.

Processo: `Estoque`.

Processo: `Controle de Acesso` e `Controle de Processos`.
 Estoque `001` - Centro
Use quando precisar:
3. Relacione a Estoque de referencia, se houver.
1. Liberar ou bloquear modulos para operator.
4. Informe origem, documento de apoio e Estoque, quando aplicavel.
3. Revisar o que cada papel pode fazer em cada processo.
3. Selecione o cliente e a Estoque, se houver.
## 4. Rotina de uso por perfil
1. Cadastre o cliente e a Estoque.
### 4.1 Admin
 Liberar apenas Estoque, produtos, servicos, documentos e relatorios.
Uso recomendado:
1. Cadastrar ou revisar Estoque.
1. Cadastrar empresa e usuarios.
 Cadastrar uma nova Estoque.
3. Manter tabelas de permissao.
1. Estoque, produtos e servicos.
5. Fazer auditoria de operacao e relatorios.
2. Adicionar cliente, Estoque e itens.
### 4.2 Financeiro

Uso recomendado:

1. Cadastrar contas bancarias.
2. Cadastrar contas de fluxo.
3. Registrar lancamentos de receitas e despesas.
4. Fechar conciliacao bancaria.
5. Conferir fluxo realizado e previsto.

### 4.3 Comercial

Uso recomendado:

1. Cadastrar Estoque, produtos e servicos.
2. Atualizar estoque quando houver entrada ou saida.
3. Registrar compra manual de NF.
4. Emitir documentos de venda nao fiscal.
5. Operar orcamentos, pedidos e PDV, quando liberado no plano.

## 5. Manual por Bloco Funcional

### 5.1 Dashboard

O Dashboard é a tela inicial do sistema, dividido em painéis especializados para cada área da empresa.

#### 5.1.1 Painel Gerencial

**Objetivo:** Visão geral da empresa com indicadores estratégicos.

**Fluxo de Uso:**

1. Usuario acessa o sistema após login.
2. Sistema carrega o Painel Gerencial por padrão.
3. Usuario visualiza cards de resumo:
   a. Total de entidades cadastradas.
   b. Total de usuarios ativos.
   c. Total de filiais.
   d. Status da assinatura.
4. Usuario visualiza graficos de tendência:
   a. Crescimento de cadastros.
   b. Volume de vendas por periodo.
   c. Status de lancamentos financeiros.
5. Usuario clica em cards para acessar modulos detalhados.
6. Sistema redireciona para modulo correspondente.

**Indicadores Disponiveis:**

- Quantidade de clientes, fornecedores e vendedores.
- Quantidade de produtos e servicos.
- Quantidade de lancamentos em aberto.
- Quantidade de pedidos pendentes.
- Status da assinatura (ativa, vencida, cancelada).

#### 5.1.2 Painel Comercial

**Objetivo:** Acompanhamento de vendas, estoque e propostas.

**Fluxo de Uso:**

1. Usuario clica em "Painel Comercial" no menu.
2. Sistema carrega indicadores comerciais.
3. Usuario visualiza cards de resumo:
   a. Vendas do dia/semana/mes.
   b. Pedidos em aberto.
   c. Propostas pendentes de aprovacao.
   d. Estoque critico (itens abaixo do minimo).
4. Usuario visualiza graficos:
   a. Vendas por periodo.
   b. Top produtos mais vendidos.
   c. Top clientes por volume.
5. Usuario clica em "Ver Detalhes" em qualquer card.
6. Sistema redireciona para modulo correspondente.

**Indicadores Disponiveis:**

- Total de vendas no periodo.
- Quantidade de pedidos por status.
- Quantidade de propostas por status.
- Itens de estoque abaixo do minimo.
- Produtos mais vendidos.
- Clientes com maior volume de compras.

#### 5.1.3 Painel Financeiro

**Objetivo:** Acompanhamento de lancamentos, fluxo de caixa e conciliacao.

**Fluxo de Uso:**

1. Usuario clica em "Painel Financeiro" no menu.
2. Sistema carrega indicadores financeiros.
3. Usuario visualiza cards de resumo:
   a. Receitas do periodo.
   b. Despesas do periodo.
   c. Lancamentos vencidos.
   d. Lancamentos a vencer nos proximos 7 dias.
   e. Saldo em contas bancarias.
4. Usuario visualiza graficos:
   a. Fluxo de caixa previsto vs realizado.
   b. Receitas por categoria.
   c. Despesas por categoria.
5. Usuario clica em "Ver Detalhes" em qualquer card.
6. Sistema redireciona para modulo correspondente.

**Indicadores Disponiveis:**

- Total de receitas no periodo.
- Total de despesas no periodo.
- Saldo consolidado das contas bancarias.
- Quantidade de lancamentos vencidos.
- Quantidade de lancamentos a vencer.
- Conciliacoes pendentes.

#### 5.1.4 Painel Fiscal

**Objetivo:** Acompanhamento de NFS-e emitidas e status fiscais.

**Fluxo de Uso:**

1. Usuario clica em "Painel Fiscal" no menu.
2. Sistema carrega indicadores fiscais.
3. Usuario visualiza cards de resumo:
   a. NFS-e emitidas no periodo.
   b. NFS-e canceladas no periodo.
   c. NFS-e autorizadas.
   d. NFS-e em processamento.
   e. NFS-e rejeitadas.
4. Usuario visualiza graficos:
   a. NFS-e por status.
   b. NFS-e por servico.
   c. NFS-e por tomador.
5. Usuario clica em "Ver Detalhes" em qualquer card.
6. Sistema redireciona para modulo de NFS-e.

**Indicadores Disponiveis:**

- Quantidade de NFS-e emitidas.
- Valor total de NFS-e emitidas.
- Quantidade de NFS-e por status.
- Servicos mais emitidos.
- Tomadores com maior volume.

#### 5.1.5 Painel Locação

**Objetivo:** Acompanhamento de locacoes, disponibilidade e contratos.

**Fluxo de Uso:**

1. Usuario clica em "Painel Locação" no menu.
2. Sistema carrega indicadores de locacao.
3. Usuario visualiza cards de resumo:
   a. Locacoes em andamento.
   b. Locacoes concluidas no periodo.
   c. Reservas para hoje.
   d. Reservas para a semana.
   e. Pecas em manutencao.
4. Usuario visualiza graficos:
   a. Locacoes por periodo.
   b. Pecas mais locadas.
   c. Receita de locacao.
5. Usuario clica em "Ver Detalhes" em qualquer card.
6. Sistema redireciona para modulo de locacao.

**Indicadores Disponiveis:**

- Quantidade de locacoes ativas.
- Quantidade de reservas pendentes.
- Pecas disponiveis no acervo.
- Pecas em manutencao.
- Receita de locacao no periodo.

#### 5.1.6 Painel Propostas

**Objetivo:** Acompanhamento de propostas comerciais e status de aprovacao.

**Fluxo de Uso:**

1. Usuario clica em "Painel Propostas" no menu.
2. Sistema carrega indicadores de propostas.
3. Usuario visualiza cards de resumo:
   a. Propostas emitidas no periodo.
   b. Propostas aprovadas.
   c. Propostas rejeitadas.
   d. Propostas pendentes de aprovacao.
   e. Propostas convertidas em pedidos.
4. Usuario visualiza graficos:
   a. Propostas por status.
   b. Taxa de conversao.
   c. Valor total por status.
5. Usuario clica em "Ver Detalhes" em qualquer card.
6. Sistema redireciona para modulo de propostas.

**Indicadores Disponiveis:**

- Quantidade de propostas por status.
- Valor total de propostas por status.
- Taxa de conversao (aprovadas/emitidas).
- Propostas pendentes de aprovacao.
- Tempo medio de aprovacao.

### 5.2 Cadastros

Bloco de cadastros básicos do sistema, essenciais para operação de todos os outros módulos.

#### 5.2.1 Entidades

**Objetivo:** Cadastro de clientes, fornecedores, vendedores e colaboradores.

**Fluxo de Criacao de Entidade:**

1. Usuario acessa modulo "Cadastros" > "Entidades".
2. Clica em "Nova Entidade".
3. Preenche nome completo da entidade.
4. Seleciona tipo de entidade:
   a. C - Cliente
   b. F - Fornecedor
   c. V - Vendedor
   d. T - Transportador
   e. O - Outros
5. Informa documento (CNPJ/CPF).
6. Sistema normaliza documento (remove caracteres especiais).
7. Preenche endereco completo:
   a. Rua/Logradouro.
   b. Numero.
   c. Bairro.
   d. Cidade.
   e. UF.
   f. CEP.
8. Seleciona municipio no autocomplete (busca por nome, UF ou codigo IBGE).
9. Sistema preenche UF automaticamente baseada no municipio.
10. Informa telefone e email.
11. Informa inscricao municipal (se aplicavel).
12. Informa inscricao estadual (se aplicavel).
13. Se entidade for cliente:
    a. Seleciona vendedor vinculado.
    b. Define aliquota de comissao especifica (opcional).
    c. Se nao definido, usa aliquota padrao da empresa.
14. Se entidade for fornecedor:
    a. Define condicoes de pagamento padrao.
    b. Define prazo medio de entrega.
15. Salva entidade.
16. Sistema valida unicidade do documento.
17. Entidade fica disponivel para uso em outros modulos.

**Fluxo de Edicao de Entidade:**

1. Usuario acessa lista de entidades.
2. Busca por nome, documento ou tipo.
3. Clica em entidade desejada.
4. Edita dados necessarios.
5. Salva alteracoes.
6. Sistema atualiza registros relacionados.

**Fluxo de Inativacao de Entidade:**

1. Usuario acessa entidade.
2. Desmarca checkbox "Ativo".
3. Salva alteracoes.
4. Entidade nao aparece mais em selecoes.
5. Registros existentes sao mantidos.

#### 5.2.2 Fluxo de Caixa (Plano de Contas)

**Objetivo:** Estrutura do plano de contas para classificacao de lancamentos.

**Fluxo de Criacao de Estrutura de Fluxo:**

1. Usuario acessa modulo "Cadastros" > "Fluxo de Caixa".
2. Clica em "Nova Estrutura".
3. Cria contas sinteticas (categorias principais):
   a. 1 - Receitas
   b. 2 - Despesas
4. Cria subcategorias sinteticas:
   a. 1.1 - Receitas de Vendas
   b. 1.2 - Receitas de Servicos
   c. 2.1 - Despesas Administrativas
   d. 2.2 - Despesas Comerciais
5. Cria contas analiticas (subcategorias detalhadas):
   a. 1.1.1 - Vendas de Produtos
   b. 1.1.2 - Vendas de Servicos
   c. 2.1.1 - Aluguel
   d. 2.1.2 - Energia Eletrica
6. Define tipo de cada conta (entrada ou saida).
7. Define nivel hierarquico.
8. Salva estrutura.
9. Estrutura fica disponivel para classificacao de lancamentos.

**Fluxo de Edicao de Conta:**

1. Usuario acessa estrutura de fluxo.
2. Clica em conta desejada.
3. Edita nome, tipo ou nivel.
4. Salva alteracoes.
5. Sistema atualiza lancamentos vinculados.

#### 5.2.3 Contas Banco

**Objetivo:** Cadastro de contas bancarias para lancamentos financeiros.

**Fluxo de Criacao de Conta Bancaria:**

1. Usuario acessa modulo "Cadastros" > "Contas Banco".
2. Clica em "Nova Conta".
3. Informa nome da conta (ex: "Banco do Brasil - Matriz").
4. Seleciona banco:
   a. Sistema lista bancos disponiveis.
   b. Usuario seleciona ou digita codigo do banco.
5. Informa agencia.
6. Informa numero da conta.
7. Informa digito verificador (se aplicavel).
8. Seleciona tipo de conta:
   a. Corrente
   b. Poupanca
   c. Investimento
9. Seleciona fluxo de conta associado (plano de contas).
10. Marca como principal se necessario (apenas uma conta por empresa).
11. Salva conta.
12. Conta fica disponivel para lancamentos.

**Fluxo de Edicao de Conta:**

1. Usuario acessa lista de contas.
2. Clica em conta desejada.
3. Edita dados necessarios.
4. Salva alteracoes.
5. Sistema atualiza registros relacionados.

**Fluxo de Inativacao de Conta:**

1. Usuario acessa conta.
2. Desmarca checkbox "Ativa".
3. Salva alteracoes.
4. Conta nao aparece mais em selecoes.
5. Registros existentes sao mantidos.

#### 5.2.4 Estoque

**Objetivo:** Cadastro de locais de estoque da empresa.

**Fluxo de Criacao de Estoque:**

1. Usuario acessa modulo "Cadastros" > "Estoque".
2. Clica em "Novo Estoque".
3. Informa codigo unico por empresa (ex: "001", "002").
4. Preenche nome do estoque (ex: "Estoque Centro", "Estoque Deposito").
5. Preenche endereco completo.
6. Seleciona municipio no autocomplete.
7. Sistema preenche UF automaticamente.
8. Define se estoque esta ativo.
9. Salva cadastro.
10. Sistema valida unicidade do codigo.
11. Estoque fica disponivel para uso em produtos, controle de estoque, vendas.

**Fluxo de Edicao de Estoque:**

1. Usuario acessa lista de estoques.
2. Clica em estoque desejado.
3. Edita dados necessarios.
4. Salva alteracoes.
5. Sistema atualiza registros relacionados.

**Fluxo de Inativacao de Estoque:**

1. Usuario acessa estoque.
2. Desmarca checkbox "Ativo".
3. Salva alteracoes.
4. Estoque nao aparece mais em selecoes.
5. Registros existentes sao mantidos.

#### 5.2.5 Produtos

**Objetivo:** Cadastro de produtos para venda e controle de estoque.

**Fluxo de Criacao de Produto:**

1. Usuario acessa modulo "Cadastros" > "Produtos".
2. Clica em "Novo Produto".
3. Informa codigo interno (ex: "PROD-001").
4. Preenche descricao resumida.
5. Informa unidade de medida:
   a. UN - Unidade
   b. KG - Quilograma
   c. MT - Metro
   d. LT - Litro
   e. CX - Caixa
6. Preenche NCM (Nomenclatura Comum do Mercosul).
7. Informa GTIN/EAN (codigo de barras, se aplicavel).
8. Informa custo de aquisicao.
9. Informa preco de venda.
10. Marca se controla estoque.
11. Se controla estoque:
    a. Informa estoque inicial.
    b. Seleciona estoque de referencia.
    c. Sistema gera movimentacao de estoque inicial.
12. Salva cadastro.
13. Produto fica disponivel para uso em vendas, compras e estoque.

**Fluxo de Edicao de Produto:**

1. Usuario acessa lista de produtos.
2. Clica em produto desejado.
3. Edita dados necessarios.
4. Salva alteracoes.
5. Sistema atualiza registros relacionados.

**Fluxo de Inativacao de Produto:**

1. Usuario acessa produto.
2. Desmarca checkbox "Ativo".
3. Salva alteracoes.
4. Produto nao aparece mais em selecoes.
5. Registros existentes sao mantidos.

#### 5.2.6 Servicos

**Objetivo:** Cadastro de servicos para venda e emissao de NFS-e.

**Fluxo de Criacao de Servico:**

1. Usuario acessa modulo "Cadastros" > "Servicos".
2. Clica em "Novo Servico".
3. Informa codigo interno (ex: "SERV-010").
4. Preenche descricao do servico.
5. Informa codigo de servico nacional para NFS-e (opcional).
6. Sistema carrega lista de codigos nacionais.
7. Usuario seleciona ou digita codigo.
8. Sistema preenche NBS relacionado automaticamente.
9. Informa NBS manualmente se necessario.
10. Informa CNAE do servico (opcional).
11. Relaciona estoque de referencia (se aplicavel).
12. Define preco padrao.
13. Marca se servico esta ativo.
14. Salva cadastro.
15. Servico fica disponivel para uso em documentos, orcamentos e NFS-e.

**Fluxo de Edicao de Servico:**

1. Usuario acessa lista de servicos.
2. Clica em servico desejado.
3. Edita dados necessarios.
4. Salva alteracoes.
5. Sistema atualiza registros relacionados.

#### 5.2.7 Tabelas de Preco

**Objetivo:** Cadastro de tabelas de preco para orcamentos e pedidos.

**Fluxo de Criacao de Tabela:**

1. Usuario acessa modulo "Cadastros" > "Tabelas de Preco".
2. Clica em "Nova Tabela".
3. Informa codigo da tabela (ex: "TABELA-2026").
4. Informa nome da tabela (ex: "Tabela de Preco 2026").
5. Define periodo de vigencia:
   a. Data de inicio.
   b. Data de fim.
6. Salva tabela.

**Fluxo de Adicao de Itens:**

1. Usuario acessa tabela.
2. Clica em "Adicionar Item".
3. Seleciona produto ou servico.
4. Informa preco de custo.
5. Informa preco de venda.
6. Informa desconto maximo permitido.
7. Salva item.
8. Repete para cada item.

**Fluxo de Uso em Orcamentos/Pedidos:**

1. Usuario cria orcamento ou pedido.
2. Seleciona tabela de preco.
3. Sistema preenche precos automaticamente.
4. Usuario pode ajustar dentro dos limites.
5. Sistema aplica descontos conforme tabela.

### 5.3 Comercial

Bloco de operações comerciais, incluindo estoque, compras, propostas, pedidos e PDV.

#### 5.3.1 Movimento de Estoque

**Objetivo:** Controle de entradas, saidas e ajustes de estoque.

**Fluxo de Entrada de Estoque:**

1. Usuario acessa modulo "Comercial" > "Movimento de Estoque".
2. Clica em "Nova Movimentacao".
3. Seleciona tipo: "Entrada".
4. Seleciona produto.
5. Informa quantidade positiva.
6. Informa data da movimentacao.
7. Seleciona origem:
   a. Compra
   b. Ajuste
   c. Devolucao
   d. Transferencia
8. Informa documento de apoio (NF, recibo, etc).
9. Seleciona estoque (se aplicavel).
10. Salva movimentacao.
11. Sistema atualiza saldo do produto.
12. Sistema gera lancamento financeiro se vinculado a compra.

**Fluxo de Saida de Estoque:**

1. Usuario acessa modulo "Comercial" > "Movimento de Estoque".
2. Clica em "Nova Movimentacao".
3. Seleciona tipo: "Saida".
4. Seleciona produto.
5. Informa quantidade positiva.
6. Sistema converte para negativo internamente.
7. Informa data da movimentacao.
8. Seleciona destino:
   a. Venda
   b. Baixa
   c. Ajuste
   d. Transferencia
9. Informa documento de apoio.
10. Seleciona estoque (se aplicavel).
11. Salva movimentacao.
12. Sistema atualiza saldo do produto.

**Fluxo de Ajuste de Estoque:**

1. Usuario acessa modulo "Comercial" > "Movimento de Estoque".
2. Clica em "Nova Movimentacao".
3. Seleciona tipo: "Ajuste".
4. Seleciona produto.
5. Informa quantidade (positiva para acrescer, negativa para diminuir).
6. Informa motivo do ajuste (inventario, perda, etc).
7. Salva movimentacao.
8. Sistema atualiza saldo do produto.
9. Sistema registra auditoria do ajuste.

#### 5.3.2 Importação de XML de NF-e de Compra

**Objetivo:** Importação automática de notas fiscais de compra a partir de arquivo XML.

**Fluxo de Importação de XML:**

1. Usuario acessa modulo "Comercial" > "Compras".
2. Clica em "Importar XML".
3. Sistema exibe formulario de upload.
4. Usuario seleciona arquivo XML da NF-e.
5. Clica em "Processar".
6. Sistema valida formato do XML.
7. Sistema extrai dados do XML:
   a. Numero da nota (nNF).
   b. Serie da nota.
   c. Data de emissao.
   d. Natureza da operacao.
   e. Dados do emitente (CNPJ, nome, endereco, telefone).
   f. Dados dos itens (codigo, descricao, NCM, CFOP, quantidade, valor).
   g. Valor total da nota.
8. Sistema verifica se fornecedor existe pelo CNPJ:
   a. Se existir, vincula a nota ao fornecedor.
   b. Se nao existir, cria automaticamente cadastro do fornecedor com todos os dados.
9. Sistema cria registro de importacao com status "pendente".
10. Sistema redireciona para tela de validacao.

**Fluxo de Validacao de Dados Importados:**

1. Usuario acessa tela de validacao da importacao.
2. Sistema mostra dados da nota:
   a. Numero, serie, data.
   b. Valor total.
   c. Dados do fornecedor (com opcao de editar).
3. Sistema mostra lista de itens:
   a. Codigo do produto (cProd).
   b. Descricao (xProd).
   c. NCM, CFOP.
   d. Quantidade, valor unitario, valor total.
   e. Dropdown para selecionar produto existente (busca por codigo ou descricao).
   f. Checkbox para confirmar item.
4. Usuario edita dados necessarios:
   a. Vencimento das parcelas.
   b. Numero de parcelas.
   c. Intervalo entre parcelas.
   d. Conta bancaria.
   e. Conta de fluxo.
   f. Observacoes.
5. Usuario vincula itens a produtos existentes:
   a. Para cada item, seleciona produto correspondente.
   b. Se nao encontrar, pode deixar sem vinculo (descricao livre).
6. Usuario marca itens que deseja confirmar.
7. Clica em "Confirmar e Gerar Lancamentos".
8. Sistema valida se pelo menos um item foi confirmado.
9. Sistema cria registro de compra.
10. Sistema cria itens da compra.
11. Sistema gera lancamentos financeiros conforme parcelamento.
12. Sistema atualiza estoque dos produtos vinculados.
13. Sistema cria movimentos de estoque.
14. Sistema atualiza status da importacao para "confirmada".
15. Sistema redireciona para detalhe da compra.

**Fluxo de Cancelamento de Importacao:**

1. Usuario acessa tela de validacao.
2. Clica em "Cancelar Importacao".
3. Sistema confirma operacao.
4. Sistema atualiza status da importacao para "cancelada".
5. Sistema redireciona para lista de compras.

#### 5.3.3 Entrada de NF de Compra

**Objetivo:** Registro manual de notas fiscais de compra.

**Fluxo de Criacao de Compra:**

1. Usuario acessa modulo "Comercial" > "Entrada de NF de Compra".
2. Clica em "Nova Nota".
3. Seleciona fornecedor (entidade tipo F).
4. Informa numero da nota fiscal.
5. Informa serie da nota.
6. Informa data de emissao.
7. Informa data de entrada.
8. Informa valor total da nota.
9. Adiciona itens da nota:
   a. Seleciona produto.
   b. Informa quantidade.
   c. Informa valor unitario.
   d. Sistema calcula subtotal.
   e. Repete para cada item.
10. Informa observacoes.
11. Se houver parcelamento:
    a. Clica em "Gerar Parcelas".
    b. Informa numero de parcelas.
    c. Informa intervalo entre parcelas.
    d. Sistema gera lancamentos financeiros.
12. Salva operacao.
13. Sistema atualiza estoque dos produtos.
14. Sistema gera lancamentos financeiros vinculados.

#### 5.3.3 Propostas Comerciais

**Objetivo:** Criacao e gerenciamento de propostas de venda, com fluxo completo de aprovacao e geracao de contrato de servicos.

**Fluxo de Criacao de Proposta:**

1. Usuario acessa modulo "Comercial" > "Propostas Comerciais".
2. Clica em "Nova Proposta".
3. Seleciona cliente.
4. Seleciona estoque (se aplicavel).
5. Seleciona tabela de preco (opcional).
6. Adiciona itens:
   a. Seleciona produto ou servico.
   b. Sistema preenche preco da tabela ou padrao.
   c. Informa quantidade.
   d. Ajusta preco se necessario.
   e. Sistema calcula subtotal.
   f. Repete para cada item.
7. Sistema calcula total geral.
8. Define validade da proposta.
9. Informa condicoes de pagamento.
10. Informa observacoes.
11. Salva proposta.
12. Sistema define status como "emitida".

**Fluxo de Impressao Resumida de Proposta:**

1. Usuario acessa proposta emitida.
2. Clica em "Imprimir Resumida".
3. Sistema gera visualizacao resumida:
   a. Numero da proposta.
   b. Data de emissao.
   c. Cliente.
   d. Validade.
   e. Total geral.
   f. Lista de itens resumida (descricao, quantidade, valor unitario, subtotal).
4. Usuario imprime ou salva como PDF.
5. Documento serve para apresentacao rapida ao cliente.

**Fluxo de Impressao Detalhada de Proposta:**

1. Usuario acessa proposta emitida.
2. Clica em "Imprimir Detalhada".
3. Sistema gera visualizacao detalhada:
   a. Numero da proposta.
   b. Data de emissao.
   c. Cliente (dados completos).
   d. Validade.
   e. Condicoes de pagamento.
   f. Observacoes.
   g. Lista de itens detalhada (codigo, descricao completa, quantidade, valor unitario, subtotal).
   h. Total geral.
   i. Termos e condicoes.
4. Usuario imprime ou salva como PDF.
5. Documento serve para apresentacao formal ao cliente.

#### 5.3.4 Aprovacao de Propostas

**Objetivo:** Aprovacao, reprovação e conversao de propostas em pedidos ou contratos de servicos.

**Fluxo de Aprovacao de Proposta:**

1. Usuario acessa modulo "Comercial" > "Aprovacao de Propostas".
2. Sistema lista propostas com status "emitida".
3. Usuario seleciona proposta.
4. Clica em "Aprovar".
5. Sistema muda status para "aprovada".
6. Sistema registra data de aprovacao.
7. Sistema envia notificacao ao cliente.

**Fluxo de Rejeicao de Proposta:**

1. Usuario acessa proposta.
2. Clica em "Rejeitar".
3. Informa motivo da rejeicao.
4. Sistema muda status para "rejeitada".
5. Sistema registra motivo.
6. Sistema envia notificacao ao cliente.

**Fluxo de Conversao em Pedido de Venda:**

1. Usuario acessa proposta aprovada.
2. Clica em "Converter em Pedido".
3. Sistema cria pedido de venda.
4. Sistema copia itens da proposta.
5. Sistema muda status da proposta para "convertida em pedido".
6. Usuario pode editar pedido antes de finalizar.
7. Sistema define status do pedido como "pendente".

**Fluxo de Geracao de Contrato de Servicos a partir de Proposta:**

1. Usuario acessa proposta aprovada.
2. Clica em "Gerar Contrato de Servicos".
3. Sistema preenche dados do contrato:
   a. Numero sequencial do contrato.
   b. Cliente (contratante).
   c. Empresa (contratada).
   d. Data de inicio de vigencia.
   e. Data de fim de vigencia (baseada na validade da proposta).
   f. Valor total do contrato (baseado na proposta).
   g. Valor mensal se recorrente.
   h. Forma de pagamento (baseada na proposta).
   i. Periodicidade (mensal, trimestral, anual).
4. Sistema adiciona itens da proposta como servicos contratados.
5. Sistema adiciona clausulas padrao:
   a. Clausulas financeiras.
   b. Clausulas tecnicas.
   c. Clausulas juridicas.
6. Usuario pode adicionar clausulas personalizadas.
7. Sistema substitui placeholders nos textos (nome cliente, valores, datas).
8. Usuario revisa contrato.
9. Salva contrato.
10. Sistema define status como "rascunho".
11. Sistema vincula contrato a proposta.
12. Sistema muda status da proposta para "convertida em contrato".

#### 5.3.5 Pedidos de Venda

**Objetivo:** Gerenciamento de pedidos de venda.

**Fluxo de Criacao de Pedido:**

1. Usuario acessa modulo "Comercial" > "Pedidos de Venda".
2. Clica em "Novo Pedido".
3. Pode criar a partir de proposta ou manualmente.
4. Se manual:
   a. Seleciona cliente.
   b. Seleciona estoque.
   c. Adiciona itens.
5. Se a partir de proposta:
   a. Sistema copia dados automaticamente.
   b. Usuario pode ajustar.
6. Define data de entrega.
7. Informa condicoes de pagamento.
8. Salva pedido.
9. Sistema define status como "pendente".

**Fluxo de Atendimento de Pedido:**

1. Usuario acessa pedido.
2. Atualiza quantidades atendidas.
3. Registra data de atendimento parcial.
4. Salva alteracoes.
5. Sistema recalcula pendencias.

**Fluxo de Faturamento de Pedido:**

1. Usuario acessa pedido atendido.
2. Clica em "Faturar".
3. Sistema gera documento de venda.
4. Sistema vincula documento ao pedido.
5. Sistema muda status para "faturado".
6. Sistema gera lancamento financeiro.

#### 5.3.6 PDV Caixa

**Objetivo:** Ponto de venda para vendas rapidas.

**Fluxo de Abertura de Caixa:**

1. Usuario acessa modulo "Comercial" > "PDV Caixa".
2. Clica em "Abrir Caixa".
3. Informa valor inicial do caixa.
4. Sistema registra abertura.
5. Sistema inicia sessao de caixa.
6. Usuario pode iniciar vendas.

**Fluxo de Venda no PDV:**

1. Usuario inicia nova venda.
2. Digita ou busca produto/servico.
3. Sistema preenche descricao e preco.
4. Informa quantidade.
5. Sistema calcula subtotal.
6. Repete para cada item.
7. Sistema calcula total geral.
8. Usuario seleciona forma de pagamento:
   a. Dinheiro
   b. Cartao de credito
   c. Cartao de debito
   d. PIX
   e. Boleto
   f. Multiplos meios
9. Se dinheiro, sistema calcula troco.
10. Usuario finaliza venda.
11. Sistema gera cupom interno.
12. Sistema atualiza estoque.
13. Sistema registra lancamento financeiro.
14. Sistema atualiza sessao de caixa.

**Fluxo de Fechamento de Caixa:**

1. Usuario clica em "Fechar Caixa".
2. Sistema calcula total vendido.
3. Usuario informa total em dinheiro.
4. Sistema calcula divergencia.
5. Usuario justifica divergencia se houver.
6. Sistema registra fechamento.
7. Sistema encerra sessao de caixa.
8. Sistema gera relatorio de fechamento.

### 5.4 Locação

Bloco de operações de locação, incluindo acervo, agenda, contratos e orçamentos.

#### 5.4.1 Acervo

**Objetivo:** Cadastro de pecas e kits para locacao.

**Fluxo de Cadastro de Peca:**

1. Usuario acessa modulo "Locação" > "Acervo".
2. Clica em "Nova Peca".
3. Informa codigo da peca.
4. Preenche descricao detalhada.
5. Informa categoria:
   a. Roupa
   b. Fantasia
   c. Acessorio
6. Informa tamanho.
7. Informa cor.
8. Informa estado:
   a. Novo
   b. Usado
   c. Em manutencao
9. Define valor de locacao.
10. Define valor de caucao.
11. Salva peca.
12. Peca fica disponivel para reserva.

**Fluxo de Criacao de Kit:**

1. Usuario acessa modulo "Locação" > "Acervo" > "Kits".
2. Clica em "Novo Kit".
3. Informa nome do kit.
4. Adiciona pecas ao kit:
   a. Seleciona peca.
   b. Informa quantidade.
   c. Repete para cada peca.
5. Define valor do kit.
6. Salva kit.
7. Kit fica disponivel para reserva.

#### 5.4.2 Agenda / Disponibilidade

**Objetivo:** Consulta de disponibilidade de pecas por periodo.

**Fluxo de Consulta de Disponibilidade:**

1. Usuario acessa modulo "Locação" > "Agenda / Disponibilidade".
2. Seleciona periodo desejado (data inicio e fim).
3. Sistema verifica disponibilidade de pecas.
4. Sistema mostra pecas disponiveis.
5. Sistema mostra pecas reservadas.
6. Sistema mostra pecas em manutencao.
7. Usuario pode filtrar por:
   a. Categoria
   b. Tamanho
   c. Cor
8. Usuario visualiza calendario de ocupacao.

#### 5.4.3 Contrato de Locação

**Objetivo:** Gerenciamento de contratos de locacao.

**Fluxo de Criacao de Contrato:**

1. Usuario acessa modulo "Locação" > "Contrato de Locação".
2. Clica em "Novo Contrato".
3. Sistema gera numero sequencial.
4. Seleciona cliente.
5. Define periodo de locacao (data inicio e fim).
6. Adiciona pecas ou kits:
   a. Sistema verifica disponibilidade.
   b. Se disponivel, adiciona ao contrato.
   c. Informa quantidade.
   d. Sistema calcula valor.
7. Sistema calcula valor total.
8. Define valor de caucao.
9. Define condicoes de pagamento.
10. Salva contrato.
11. Sistema define status como "rascunho".

**Fluxo de Assinatura de Contrato:**

1. Usuario acessa contrato rascunho.
2. Revisa todas as clausulas.
3. Clica em "Assinar".
4. Sistema gera PDF do contrato.
5. Usuario assina digitalmente.
6. Sistema registra data de assinatura.
7. Sistema define status como "ativo".
8. Sistema envia copia para cliente.

#### 5.4.4 Orçamento de Locação

**Objetivo:** Criacao de orcamentos para locacao.

**Fluxo de Criacao de Orcamento:**

1. Usuario acessa modulo "Locação" > "Orçamento de Locação".
2. Clica em "Novo Orcamento".
3. Seleciona cliente.
4. Define periodo desejado (data inicio e fim).
5. Adiciona pecas ou kits:
   a. Sistema verifica disponibilidade.
   b. Se disponivel, adiciona ao orcamento.
   c. Informa quantidade.
   d. Sistema calcula valor.
6. Sistema calcula valor total.
7. Define valor de caucao.
8. Salva orcamento.
9. Sistema define status como "orcado".

**Fluxo de Conversao em Contrato:**

1. Usuario acessa orcamento aprovado.
2. Clica em "Converter em Contrato".
3. Sistema cria contrato de locacao.
4. Sistema copia dados do orcamento.
5. Sistema muda status do orcamento para "convertido".
6. Usuario pode editar contrato antes de finalizar.

### 5.5 Contratos de Serviços

Bloco de contratos de prestacao de servicos, gerados a partir de propostas comerciais aprovadas. Este bloco é separado e independente dos Contratos de Locação (seção 5.4).

#### 5.5.1 Contrato de Serviços

**Objetivo:** Contratos de prestacao de servicos gerados a partir de propostas comerciais aprovadas.

**Fluxo de Criacao de Contrato:**

1. Usuario acessa modulo "Contratos" > "Contrato de Vendas".
2. Clica em "Novo Contrato".
3. Sistema gera numero sequencial.
4. Seleciona cliente (contratante).
5. Sistema preenche dados da empresa (contratada).
6. Define data de inicio de vigencia.
7. Define data de fim de vigencia.
8. Define valor total do contrato.
9. Define valor mensal se recorrente.
10. Define forma de pagamento.
11. Define periodicidade:
    a. Mensal
    b. Trimestral
    c. Anual
12. Adiciona clausulas:
    a. Seleciona clausulas padrao.
    b. Sistema adiciona ao contrato.
    c. Adiciona clausulas personalizadas.
13. Sistema substitui placeholders nos textos.
14. Salva contrato.
15. Sistema define status como "rascunho".

#### 5.5.2 Minuta de Contrato

**Objetivo:** Criacao de minutas para aprovacao.

**Fluxo de Criacao de Minuta:**

1. Usuario acessa modulo "Contratos" > "Minuta de Contrato".
2. Clica em "Nova Minuta".
3. Seleciona template base (se houver).
4. Preenche dados preliminares.
5. Adiciona clausulas preliminares.
6. Salva minuta.
7. Sistema define status como "minuta".

**Fluxo de Conversao em Contrato:**

1. Usuario acessa minuta aprovada.
2. Clica em "Converter em Contrato".
3. Sistema cria contrato definitivo.
4. Sistema copia dados da minuta.
5. Sistema muda status da minuta para "convertida".

#### 5.5.3 Cláusulas Padrão

**Objetivo:** Cadastro de clausulas reutilizaveis.

**Fluxo de Criacao de Clausula Padrao:**

1. Usuario acessa modulo "Contratos" > "Cláusulas Padrão".
2. Clica em "Nova Clausula".
3. Informa titulo da clausula.
4. Escreve texto da clausula.
5. Define se clausula e obrigatoria ou opcional.
6. Define tipo:
    a. Financeira
    b. Tecnica
    c. Juridica
7. Salva clausula.
8. Clausula fica disponivel para contratos.

### 5.6 Financeiro

Bloco de operacoes financeiras.

#### 5.6.1 Lancamentos

**Objetivo:** Registro de receitas e despesas.

**Fluxo de Criacao de Lancamento de Receita:**

1. Usuario acessa modulo "Financeiro" > "Lancamentos".
2. Clica em "Novo Lancamento".
3. Seleciona tipo: "Receita".
4. Seleciona entidade (cliente).
5. Informa data do evento.
6. Informa data de vencimento.
7. Informa data de pagamento (se ja pago).
8. Seleciona conta de fluxo (plano de contas).
9. Seleciona conta bancaria.
10. Informa valor real.
11. Informa valor pago (se aplicavel).
12. Informa impostos e descontos.
13. Sistema calcula valor liquido.
14. Adiciona observacoes.
15. Salva lancamento.
16. Sistema atualiza fluxo de caixa.

**Fluxo de Criacao de Lancamento de Despesa:**

1. Usuario acessa modulo "Financeiro" > "Lancamentos".
2. Clica em "Novo Lancamento".
3. Seleciona tipo: "Despesa".
4. Seleciona entidade (fornecedor).
5. Informa data do evento.
6. Informa data de vencimento.
7. Informa data de pagamento (se ja pago).
8. Seleciona conta de fluxo.
9. Seleciona conta bancaria.
10. Informa valor real.
11. Informa valor pago.
12. Sistema calcula valor liquido.
13. Adiciona observacoes.
14. Salva lancamento.
15. Sistema atualiza fluxo de caixa.

**Fluxo de Baixa de Lancamento:**

1. Usuario acessa lancamento em aberto.
2. Clica em "Baixar".
3. Informa data de pagamento.
4. Informa valor pago.
5. Sistema calcula diferenca se houver.
6. Usuario justifica diferenca.
7. Salva baixa.
8. Sistema atualiza status para "pago".
9. Sistema atualiza fluxo de caixa realizado.

#### 5.6.2 Fluxo de Caixa

**Objetivo:** Visualizacao e gerenciamento do fluxo de caixa.

**Fluxo de Consulta de Fluxo de Caixa:**

1. Usuario acessa modulo "Financeiro" > "Fluxo de Caixa".
2. Seleciona periodo.
3. Sistema mostra fluxo previsto.
4. Sistema mostra fluxo realizado.
5. Sistema mostra saldo projetado.
6. Usuario pode filtrar por conta.
7. Usuario pode exportar relatorio.

#### 5.6.3 Listagem de Lancamentos

**Objetivo:** Consulta e gerenciamento de lancamentos.

**Fluxo de Consulta de Lancamentos:**

1. Usuario acessa modulo "Financeiro" > "Listagem de Lancamentos".
2. Define periodo.
3. Filtra por tipo (receita/despesa).
4. Filtra por status (aberto/pago).
5. Filtra por entidade (opcional).
6. Sistema gera listagem.
7. Usuario pode editar lancamentos.
8. Usuario pode baixar lancamentos.
9. Usuario pode estornar lancamentos pagos.

### 5.7 Serviços / Fiscal

Bloco de operações fiscais e emissão de NFS-e.

#### 5.7.1 Importação de XML NFSe

**Objetivo:** Importação de NFS-e recebidas de terceiros.

**Fluxo de Importacao de NFSe:**

1. Usuario acessa modulo "Serviços / Fiscal" > "Importação de XML NFSe".
2. Clica em "Importar".
3. Seleciona arquivo XML ou PDF.
4. Sistema processa arquivo.
5. Sistema extrai dados:
   a. Numero da NFS-e.
   b. Data de emissao.
   c. Tomador.
   d. Prestador.
   e. Servicos.
   f. Valores.
6. Sistema busca tomador no cadastro.
7. Se nao encontrado, sugere criacao.
8. Sistema busca servicos no cadastro.
9. Se nao encontrado, sugere criacao.
10. Usuario confirma dados.
11. Sistema gera lancamento financeiro.
12. Sistema salva NFS-e importada.
13. Sistema vincula lancamento a NFS-e.

#### 5.7.2 NFS-e Emitidas

**Objetivo:** Listagem e gerenciamento de NFS-e emitidas.

**Fluxo de Consulta de NFS-e Emitidas:**

1. Usuario acessa modulo "Serviços / Fiscal" > "NFS-e Emitidas".
2. Sistema lista todas as NFS-e emitidas.
3. Usuario filtra por:
   a. Periodo
   b. Status
   c. Tomador
   d. Servico
4. Usuario clica em NFS-e para ver detalhes.
5. Sistema mostra dados completos.
6. Usuario pode baixar XML ou PDF.

#### 5.7.3 Nova Emissão

**Objetivo:** Emissão de novas NFS-e.

**Fluxo de Emissao de NFS-e:**

1. Usuario acessa modulo "Serviços / Fiscal" > "Nova Emissão".
2. Clica em "Nova Emissao".
3. Seleciona tomador (cliente).
4. Sistema preenche dados do tomador automaticamente.
5. Adiciona servicos:
   a. Seleciona servico cadastrado.
   b. Sistema preenche codigo de servico e NBS.
   c. Ajusta se necessario.
   d. Informa valor do servico.
   e. Sistema calcula aliquotas.
   f. Repete para cada servico.
6. Sistema calcula total geral.
7. Informa data de emissao e prestacao.
8. Seleciona ambiente:
   a. Homologacao
   b. Producao
9. Clica em "Emitir".
10. Sistema valida dados.
11. Sistema gera XML da NFS-e.
12. Sistema assina XML digitalmente.
13. Sistema envia para webservice da prefeitura.
14. Sistema recebe protocolo de autorizacao.
15. Sistema salva numero da NFS-e.
16. Sistema atualiza status para "autorizada".
17. Usuario pode imprimir ou baixar PDF.

#### 5.7.4 Consultar NFS-e

**Objetivo:** Consulta de status de NFS-e na prefeitura.

**Fluxo de Consulta de NFS-e:**

1. Usuario acessa lista de emissões.
2. Clica em emissao desejada.
3. Sistema mostra detalhes da NFS-e.
4. Usuario clica em "Consultar".
5. Sistema consulta status na prefeitura.
6. Sistema atualiza status local.
7. Usuario pode baixar XML ou PDF.

#### 5.7.5 Cancelamento

**Objetivo:** Cancelamento de NFS-e autorizadas.

**Fluxo de Cancelamento de NFS-e:**

1. Usuario acessa NFS-e autorizada.
2. Clica em "Cancelar".
3. Informa motivo do cancelamento.
4. Sistema valida se cancelamento é permitido (prazo, status).
5. Sistema gera XML de cancelamento.
6. Sistema assina XML.
7. Sistema envia para webservice.
8. Sistema recebe confirmacao.
9. Sistema atualiza status para "cancelada".
10. Sistema registra historico de cancelamento.

#### 5.7.6 Cancelamento por Substituição

**Objetivo:** Cancelamento com emissão de nova NFS-e substituta.

**Fluxo de Cancelamento por Substituição:**

1. Usuario acessa NFS-e autorizada.
2. Clica em "Cancelar por Substituicao".
3. Informa motivo da substituicao.
4. Sistema valida se substituicao é permitida.
5. Sistema preenche dados da NFS-e original.
6. Usuario ajusta dados necessarios.
7. Sistema gera nova NFS-e.
8. Sistema cancela NFS-e original.
9. Sistema vincula NFS-e original a substituta.
10. Sistema registra historico de substituicao.

#### 5.7.7 Configurações

**Objetivo:** Configuracao de parametros fiscais da empresa.

**Fluxo de Configuracao Fiscal:**

1. Usuario acessa modulo "Serviços / Fiscal" > "Configurações".
2. Aba "Geral" - Configura dados da empresa:
   a. CNPJ.
   b. Inscrição municipal.
   c. Regime tributario.
3. Aba "Ambiente" - Define ambiente de emissao:
   a. Homologacao.
   b. Producao.
4. Aba "Certificado" - Configura certificado digital.
5. Aba "Parametros" - Define parametros de emissao:
   a. Serie da NFS-e.
   b. Numero inicial.
   c. Natureza da operacao.
6. Salva configuracoes.
7. Sistema valida configuracoes.

#### 5.7.8 Tomadores

**Objetivo:** Cadastro de tomadores para NFS-e.

**Fluxo de Cadastro de Tomador:**

1. Usuario acessa modulo "Serviços / Fiscal" > "Tomadores".
2. Clica em "Novo Tomador".
3. Informa razao social.
4. Informa CNPJ/CPF.
5. Preenche endereco completo.
6. Seleciona municipio no autocomplete.
7. Sistema preenche UF automaticamente.
8. Informa email para envio da NFS-e.
9. Salva tomador.
10. Tomador fica disponivel para emissao.

#### 5.7.9 Emissão de NF-e Avulsa

**Objetivo:** Emissão de NFS-e avulsa (sem vinculo a contrato).

**Fluxo de Emissao de NF-e Avulsa:**

1. Usuario acessa modulo "Serviços / Fiscal" > "Emissão de NF-e Avulsa".
2. Clica em "Nova Avulsa".
3. Seleciona ou cadastra tomador.
4. Adiciona servicos.
5. Sistema calcula valores.
6. Informa data de prestacao.
7. Seleciona ambiente.
8. Clica em "Emitir".
9. Sistema emite NFS-e avulsa.

#### 5.7.10 Listagem das NFS-e Importadas

**Objetivo:** Consulta de NFS-e importadas.

**Fluxo de Consulta de NFS-e Importadas:**

1. Usuario acessa modulo "Serviços / Fiscal" > "Listagem das NFS-e Importadas".
2. Sistema lista todas as NFS-e importadas.
3. Usuario filtra por:
   a. Periodo
   b. Tomador
   c. Servico
4. Usuario clica em NFS-e para ver detalhes.
5. Sistema mostra dados completos.
6. Usuario pode vincular lancamento financeiro.

### 5.8 Admin

Bloco de administracao do sistema.

#### 5.8.1 Adicionar Usuário

**Objetivo:** Criacao de novos usuarios do sistema.

**Fluxo de Criacao de Usuario:**

1. Usuario acessa modulo "Admin" > "Adicionar Usuário".
2. Clica em "Novo Usuario".
3. Informa username (unico por empresa).
4. Informa email (unico no sistema).
5. Informa senha inicial.
6. Informa nome completo.
7. Seleciona perfil:
   a. Admin
   b. Operator
   c. Viewer
8. Define se usuario estara ativo.
9. Salva cadastro.
10. Sistema cria usuario vinculado a empresa do admin.

#### 5.8.2 Controle de Acesso

**Objetivo:** Gerenciamento de permissoes de acesso.

**Fluxo de Edicao de Permissoes (Controle de Acesso):**

1. Usuario acessa modulo "Admin" > "Controle de Acesso".
2. Visualiza matriz de permissoes por processo.
3. Para cada processo, pode liberar ou bloquear para operator.
4. Alteracoes sao salvas imediatamente.
5. Viewer sempre tem acesso apenas leitura, independente da configuracao.

**Fluxo de Edicao de Permissoes Individuais (Controle de Usuario):**

1. Usuario acessa modulo "Admin" > "Controle de Acesso" > "Por Usuario".
2. Seleciona usuario especifico.
3. Visualiza permissoes herdadas do perfil.
4. Pode fazer override individual por processo.
5. Override sobrescreve configuracao do perfil.
6. Salva alteracoes.

**Fluxo de Ativacao/Desativacao de Usuario:**

1. Usuario acessa lista de usuarios.
2. Clica em editar usuario.
3. Marca ou desmarca checkbox "Ativo".
4. Salva alteracoes.
5. Usuario inativo nao pode fazer login.

## 6. Manual consolidado por perfil

### 6.1 Administrador

Responsabilidade: governar usuarios, permissões, plano da empresa e saude da operacao.

Rotina padrao:

1. Entrar no sistema e validar se a empresa correta foi carregada.
2. Conferir dashboard, pendencias e alertas de acesso.
3. Criar ou ajustar usuarios.
4. Revisar permissões de processos.
5. Verificar se o plano contratado permite os modulos em uso.
6. Acompanhar logs de erro e falhas de gravacao.

Exemplo prático:

- Criar um novo operador para o comercial.
- Liberar apenas filiais, produtos, servicos, documentos e relatorios.
- Bloquear PDV e contratos se o cargo nao exigir.

### 6.2 Financeiro

Responsabilidade: manter contas bancarias, lancamentos e conciliacao em dia.

Rotina padrao:

1. Conferir contas bancarias principais.
2. Abrir lancamentos vencidos e pagos do dia.
3. Registrar entradas e saidas que chegaram por fora.
4. Importar extrato e conciliar movimentos.
5. Verificar fluxo previsto e realizado.

Exemplo prático:

- Lançar aluguel, energia e fornecedores.
- Conciliar um credito bancario com uma mensalidade recebida.
- Corrigir uma divergencia de valor antes do fechamento.

### 6.3 Comercial

Responsabilidade: manter cadastro, estoque e vendas organizados.

Rotina padrao:

1. Cadastrar ou revisar filiais.
2. Cadastrar produtos e servicos com codigo interno padrao.
3. Atualizar estoque quando houver movimentacao.
4. Abrir compra manual quando receber NF fisica.
5. Emitir documento de venda nao fiscal ou montar orcamento.

Exemplo prático:

- Criar novo produto com estoque inicial.
- Registrar compra do fornecedor e gerar parcelamento.
- Emitir documento de venda para um cliente ja cadastrado.

### 6.4 Operador

Responsabilidade: executar rotinas operacionais sem alterar regras centrais.

Rotina padrao:

1. Entrar no sistema e verificar o que foi liberado para seu perfil.
2. Executar cadastros ou movimentos permitidos.
3. Registrar documentos, compras ou vendas.
4. Conferir se a gravacao foi concluida.
5. Comunicar o administrador em caso de bloqueio.

Exemplo prático:

- Cadastrar uma novo estoque.
- Registrar uma venda simples.
- Consultar relatorios, sem alterar permissões.

### 6.5 Viewer

Responsabilidade: consulta e auditoria visual.

Rotina padrao:

1. Entrar no sistema.
2. Consultar listas e detalhes.
3. Validar informacoes antes de um fechamento.
4. Nao tentar gravar alterações, porque o sistema bloqueia escrita.

Exemplo prático:

- Conferir status de lancamentos.
- Consultar documentos de venda.
- Validar saldos e conciliacao para apoio ao financeiro.

### 6.6 Backoffice LiveSun

Responsabilidade: uso administrativo da software house, sem vinculo a empresa cliente.

Rotina padrao:

1. Usar apenas quando houver necessidade de suporte ou manutencao.
2. Nao operar tarefas de negocio da empresa cliente.
3. Respeitar controles de assinatura, ativacao e plano.

Exemplo prático:

- Acompanhar status de assinatura.
- Ajustar parametros de plataforma.
- Apoiar a empresa cliente sem interferir no tenant dela.

## 7. Roteiro de treinamento recomendado

### Etapa 1 - Acesso e base

1. Login, logout e leitura de mensagens do sistema.
2. Entendimento de empresa, usuario e papel.
3. Navegacao entre dashboard e modulos.

### Etapa 2 - Cadastros essenciais

1. Empresas e dados basicos.
2. Usuarios, perfis e permissões.
3. Entidades, contas bancarias e fluxo de caixa.

### Etapa 3 - Rotina financeira

1. Lancamentos de receita e despesa.
2. Ajustes de fluxo de caixa.
3. Conciliacao bancaria e conferencia.

### Etapa 4 - Rotina comercial

1. Filiais, produtos e servicos.
2. Estoque e compra manual.
3. Documento nao fiscal, tabelas de preco, orcamentos e pedidos.

### Etapa 5 - Operacao avançada

1. PDV e fechamento.
2. Importacoes e relatorios.
3. Comissoes, locacao, contratos e NFSe.

## 8. Roteiro diario de operacao

### Inicio do dia

1. Entrar no sistema.
2. Conferir dashboard e avisos.
3. Verificar acessos liberados para o perfil.
4. Abrir filas de lancamentos, pedidos e documentos pendentes.

### Durante o dia

1. Fazer cadastros novos somente quando necessario.
2. Registrar movimentacoes com a maior quantidade possivel de dados.
3. Conferir se o item entrou na listagem e ficou filtrado pela empresa correta.
4. Revisar divergencias logo apos a gravacao.

### Final do dia

1. Revisar lancamentos do dia.
2. Conciliar movimentos bancarios que ja chegaram.
3. Fechar caixas ou sessoes de PDV.
4. Gerar relatorios de acompanhamento.

## 9. Cenarios práticos de treinamento

### Cenário 1 - Cadastro de cliente novo

1. Abrir entidades.
2. Criar cliente.
3. Vincular vendedor ou dados de comissao, se houver.
4. Salvar e conferir se o cliente aparece na listagem da empresa.

### Cenário 2 - Compra de mercadoria

1. Abrir compras manuais.
2. Informar fornecedor, nota e itens.
3. Gerar lancamento parcelado, se necessario.
4. Atualizar estoque do produto associado.

### Cenário 3 - Venda nao fiscal

1. Abrir documentos de venda.
2. Adicionar cliente, Estoque e itens.
3. Conferir total e vencimento.
4. Salvar e usar a visualizacao para impressao ou conferencia.

### Cenário 4 - Fechamento financeiro

1. Abrir lancamentos em aberto.
2. Marcar pagos os que ja entraram.
3. Conciliar extrato bancario.
4. Emitir relatorio do periodo.

## 10. Recomendacao final de operacao

Para evitar falhas de execucao:

1. Garanta que o banco esteja no dialeto correto para o ambiente.
2. Aplique as migracoes que completam as colunas ausentes.
3. Teste o login de admin, operador e viewer.
4. Valide o fluxo comercial e financeiro em uma empresa de testes antes de usar em producao.
5. Sempre confirme se o usuario esta operando dentro da empresa correta antes de gravar qualquer registro.

## 11. Versao para impressao

Esta versao do manual foi escrita para leitura em tela e impressao em PDF sem depender de elementos visuais da interface.

Recomendacoes para impressao:

1. Use orientacao retrato para o texto geral.
2. Use paisagem apenas se quiser destacar as tabelas do quadro de compatibilidade.
3. O sumario executivo por setor deve ser usado como primeira pagina de treinamento.
4. O roteiro por perfil deve ser usado durante o onboarding de novos usuarios.
5. Os cenarios praticos devem ser usados em treinamento assistido.

Sequencia recomendada para impressão:

1. Sumario executivo por setor.
2. Controle de usuarios e acesso.
3. Manual consolidado por perfil.
4. Roteiro de treinamento recomendado.
5. Cenarios praticos de treinamento.
6. Recomendacao final de operacao.
