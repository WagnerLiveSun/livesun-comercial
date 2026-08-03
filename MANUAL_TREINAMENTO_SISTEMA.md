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
Uso principal: manter cadastros, Filial/Estoque e vendas.
- Nome de login: `joao.vendas`
- Email: `joao@empresa.com.br`
 Modulos comerciais: Filial/Estoque, produtos, servicos, compras, documentos, orcamentos, pedidos e PDV exigem as tabelas especificas do modulo comercial, nao apenas a estrutura financeira basica.
- Permissoes: liberar comercial, entidades, lancamentos e relatorios.

 As tabelas do comercial existem: `filiais`, `produtos`, `servicos`, `estoque_movimentos`, `compras_nf_manual`, `documentos_venda`, `tabelas_preco`, `orcamentos`, `pedidos_venda`, `pdv_*`.

- O sistema nao permite remover o ultimo admin ativo da empresa.
- O usuario nao pode desativar o proprio acesso durante a sessao atual.
1. Cadastrar Filial/Estoque, produtos e servicos.
- O email e unico no sistema.
- O username e unico por empresa.

Processo: `Filial/Estoque`.

Processo: `Controle de Acesso` e `Controle de Processos`.
 Filial/Estoque `001` - Centro
Use quando precisar:
3. Relacione a Filial/Estoque de referencia, se houver.
1. Liberar ou bloquear modulos para operator.
4. Informe origem, documento de apoio e Filial/Estoque, quando aplicavel.
3. Revisar o que cada papel pode fazer em cada processo.
3. Selecione o cliente e a Filial/Estoque, se houver.
## 4. Rotina de uso por perfil
1. Cadastre o cliente e a Filial/Estoque.
### 4.1 Admin
 Liberar apenas Filial/Estoque, produtos, servicos, documentos e relatorios.
Uso recomendado:
1. Cadastrar ou revisar Filial/Estoque.
1. Cadastrar empresa e usuarios.
 Cadastrar uma nova Filial/Estoque.
3. Manter tabelas de permissao.
1. Filial/Estoque, produtos e servicos.
5. Fazer auditoria de operacao e relatorios.
2. Adicionar cliente, Filial/Estoque e itens.
### 4.2 Financeiro

Uso recomendado:

1. Cadastrar contas bancarias.
2. Cadastrar contas de fluxo.
3. Registrar lancamentos de receitas e despesas.
4. Fechar conciliacao bancaria.
5. Conferir fluxo realizado e previsto.

### 4.3 Comercial

Uso recomendado:

1. Cadastrar Filial/Estoque, produtos e servicos.
2. Atualizar estoque quando houver entrada ou saida.
3. Registrar compra manual de NF.
4. Emitir documentos de venda nao fiscal.
5. Operar orcamentos, pedidos e PDV, quando liberado no plano.

## 5. Manual por modulo

### 5.1 Dashboard

Objetivo: mostrar o resumo operacional da empresa.

Passo a passo:

1. Acesse a tela inicial apos o login.
2. Verifique os cards de cadastros, financeiro, comercial e pendencias.
3. Use os graficos para identificar volume, status e tendencias.
4. Use o dashboard como ponto de partida para a rotina do dia.

Exemplo de uso:

- O financeiro abre o dashboard para conferir lancamentos vencidos.
- O comercial verifica clientes, produtos e andamento de pedidos.

### 5.2 Cadastro de Entidades

Processo: `Cadastro de Entidades`.

Use para clientes, fornecedores, vendedores e colaboradores.

Passo a passo:

1. Abra o modulo de entidades.
2. Clique em novo cadastro.
3. Preencha nome, documento, tipo e endereco.
4. Informe telefone, email e inscricoes, quando houver.
5. Vincule fluxo de conta e dados de comissao, se aplicavel.
6. Salve e confira o registro na listagem.

Exemplo:

- Cliente: Empresa Alfa Ltda.
- Tipo: `C`
- Documento: `12345678000199`
- Vendedor vinculado: `Vendedor Padrao`.

### 5.3 Fluxo de Caixa

Processo: `Fluxo de Caixa`.

Use para classificar entradas e saidas no plano de contas.

Passo a passo:

1. Cadastre as contas sinteticas e analiticas do fluxo.
2. Defina contas de entrada e saida.
3. Use o fluxo para classificar cada lancamento.
4. Reveja periodicamente as contas analiticas ativas.

Exemplo:

- Recebimento de servico: conta `1.1.4`.
- Pagamento de aluguel: conta `2.2.1`.

### 5.4 Contas Bancarias

Processo: `Contas Banco`.

Passo a passo:

1. Abra `Contas Banco`.
2. Clique em nova conta.
3. Informe nome, banco, agencia, conta e tipo.
4. Selecione o fluxo associado.
5. Marque como principal quando necessario.
6. Salve e verifique se a conta ficou ativa.

Exemplo:

- Conta principal: `Banco do Brasil - Matriz`
- Banco: `001`
- Tipo: `Corrente`

### 5.5 Lancamentos Financeiros

Processo: `Lancamentos`.

Este modulo registra receitas e despesas e alimenta o fluxo de caixa.

Passo a passo:

1. Abra a tela de lancamentos.
2. Clique em novo lancamento.
3. Escolha a entidade relacionada.
4. Informe data de evento, vencimento e, se houver, pagamento.
5. Selecione a conta de fluxo e a conta bancaria.
6. Preencha valor real, valor pago, impostos e outros custos, se aplicavel.
7. Salve o registro.

Exemplo:

- Receita de mensalidade de `R$ 1.200,00`.
- Data de vencimento: `2026-08-10`.
- Status: `aberto` ou `pago`.

### 5.6 Conciliacao Bancaria

Processo: `Conciliacao Bancaria`.

Passo a passo:

1. Abra o modulo de conciliacao.
2. Selecione a conta bancaria e o periodo.
3. Importe ou lance os itens do extrato.
4. Compare cada item com o lancamento correspondente.
5. Marque como conciliado quando houver correspondencia.
6. Registre divergencias para tratamento posterior.

Exemplo:

- Extrato aponta credito de `R$ 1.200,00`.
- O sistema localiza um lancamento com mesmo valor e data proxima.
- O operador vincula ambos e conclui a conciliacao.

### 5.7 Modulo Comercial - Filial/Estoque

Processo: `Filial/Estoque`.

Passo a passo:

1. Cadastre a filial com codigo unico por empresa.
2. Informe nome, CNPJ e endereco.
3. Defina filial ativa ou inativa.
4. Use a filial como referencia para produtos, compras, vendas e PDV.

Exemplo:

- Filial `001` - Centro
- Filial `002` - Deposito

### 5.8 Modulo Comercial - Produtos

Processo: `Produtos`.

Passo a passo:

1. Abra o cadastro de produtos.
2. Clique em novo produto.
3. Informe codigo interno e descricao resumida.
4. Preencha unidade, NCM, GTIN, custo e preco de venda.
5. Marque controle de estoque se o item for movimentado fisicamente.
6. Salve o cadastro.

Exemplo:

- Codigo: `PROD-001`
- Descricao: `Cabo USB-C`
- Estoque inicial: `100`
- Preco de venda: `R$ 29,90`

### 5.9 Modulo Comercial - Servicos

Processo: `Servicos`.

Passo a passo:

1. Cadastre o servico com codigo interno.
2. Informe descricao e, quando necessario, codigo de servico e NBS.
3. Relacione a Filial/Estoque de referencia, se houver.
4. Use servicos em documentos, orcamentos, pedidos e precificacao.

Exemplo:

- Codigo: `SERV-010`
- Descricao: `Instalacao tecnica`

### 5.10 Modulo Comercial - Estoque

Processo: `Estoque`.

Passo a passo:

1. Registre entradas quando a mercadoria chegar.
2. Registre saidas quando o item for vendido ou baixado.
3. Registre ajustes apenas quando houver divergencia de inventario.
4. Informe origem, documento de apoio e filial, quando aplicavel.

Exemplo:

- Entrada de compra: +20 unidades.
- Saida por venda: -3 unidades.
- Ajuste de inventario: -1 unidade.

### 5.11 Modulo Comercial - Compra Manual de NF

Processo: `Compras NF Manual`.

Passo a passo:

1. Abra o modulo de compras manuais.
2. Clique em nova nota.
3. Informe fornecedor, numero, serie, data de emissao e entrada.
4. Adicione os itens da nota.
5. Informe valor total e observacoes.
6. Se houver parcelamento, gere os lancamentos vinculados.
7. Salve a operacao.

Exemplo:

- NF 1023, serie 1, fornecedor `Distribuidora X`.
- Total: `R$ 8.500,00`.
- 3 parcelas vinculadas ao financeiro.

### 5.12 Modulo Comercial - Documentos Nao Fiscais de Venda

Processo: `Documentos de Venda`.

Passo a passo:

1. Abra o modulo de documentos de venda.
2. Clique em novo documento.
3. Selecione o cliente e a Filial/Estoque, se houver.
4. Adicione itens de produto e servico.
5. Informe vencimento, pagamento e observacoes.
6. Salve e use a visualizacao para impressao ou conferencia.

Exemplo:

- Venda de produto e servico no mesmo documento.
- Cliente recebe impressao para conferencia comercial.

### 5.13 Modulo Comercial - Tabelas de Preco

Processo: `Tabelas de Preco`.

Passo a passo:

1. Crie uma tabela com codigo e nome.
2. Defina periodo de vigencia.
3. Adicione itens com preco de custo, venda e desconto maximo.
4. Use a tabela nos orcamentos e pedidos.

Exemplo:

- Tabela `TABELA-2026` com vigencia mensal.
- Markup padrao de 25%.

### 5.14 Modulo Comercial - Orcamentos

Processo: `Orcamentos`.

Passo a passo:

1. Cadastre o cliente e a filial.
2. Inclua itens de produto e servico.
3. Defina validade e condicoes.
4. Revise valores de desconto e total.
5. Converta para pedido quando aprovado.

Exemplo:

- Orcamento para instalacao com materiais e mao de obra.
- Status muda de `emitido` para `aprovado` ou `convertido`.

### 5.15 Modulo Comercial - Pedidos

Processo: `Pedidos de Venda`.

Passo a passo:

1. Gere o pedido a partir do orcamento ou manualmente.
2. Confira os itens e quantidades atendidas.
3. Registre entrega e faturamento.
4. Vincule o documento de venda, quando emitido.

Exemplo:

- Pedido aprovado hoje, faturado amanha e convertido em documento.

### 5.16 Modulo Comercial - PDV / Caixa

Processo: `PDV`.

Passo a passo:

1. Abra a sessao de caixa.
2. Registre a abertura com valor inicial.
3. Lance os itens da venda em tempo real.
4. Feche a venda com os meios de pagamento.
5. Finalize a sessao ao encerrar o turno.

Exemplo:

- Venda paga parte em dinheiro e parte no cartao.
- O sistema calcula troco e grava o cupom interno.

### 5.17 Importacoes

Processos: `Importacao NFSe` e `Importacao OFX`.

Passo a passo:

1. Abra o modulo de importacao.
2. Selecione o arquivo de origem.
3. Verifique a correspondencia de entidade e lancamento.
4. Analise itens processados e divergencias.
5. Conclua a importacao apenas apos auditoria minima.

Exemplo:

- Importar OFX do banco para localizar pagamentos automaticos.
- Importar NFSe para gerar ou vincular lancamentos de servico.

### 5.18 NFSe Nacional

Processo: `NFSe Nacional`.

Passo a passo:

1. Configure empresa, ambiente e parametros fiscais.
2. Cadastre tomadores e servicos conforme o catalogo.
3. Gere a emissao e acompanhe o status.
4. Use os detalhes da emissao para verificar retorno e cancelamento.

Exemplo:

- Emissao em homologacao antes de produzir.
- Cancelamento somente por usuarios autorizados.

### 5.19 Comissoes

Processo: `Comissoes`.

Passo a passo:

1. Defina a aliquota padrao da empresa.
2. Ajuste aliquota especifica no cliente, se necessario.
3. Apure comissoes por lancamento ou por periodo.
4. Revise o valor liquido, repasse e percentual aplicado.

Exemplo:

- Venda de `R$ 10.000,00` com comissao de 5%.
- Aliquota especifica do cliente pode substituir a padrao.

### 5.20 Locacao

Processos: `Acervo de Locacao`, `Agenda de Locacao`, `Contratos de Locacao` e `Operacao de Locacao`.

Passo a passo:

1. Cadastre itens do acervo.
2. Controle reserva, retirada e devolucao.
3. Registre eventos da operacao.
4. Acompanhe manutencao, faturamento e audit trail.

Exemplo:

- Equipamento reservado para uma data, retirado e devolvido com inspecao.

### 5.21 Contratos

Processos: `Visualizar Contratos`, `Criar Contratos`, `Editar Contratos`, `Excluir Contratos`, `Assinar Contratos`, `Exportar Contratos` e `Clausulas`.

Passo a passo:

1. Crie clausulas padrao por empresa.
2. Monte o contrato com cliente e numero sequencial.
3. Adicione clausulas obrigatorias e opcionais.
4. Registre historico de alteracoes e anexos.
5. Assine ou exporte quando aprovado.

Exemplo:

- Contrato de servico com clausula financeira e clausula tecnica.

### 5.22 Relatorios

Processo: `Relatorios`.

Passo a passo:

1. Escolha o relatorio desejado.
2. Filtre por periodo, empresa, conta ou status.
3. Exporte em CSV ou visualize em tela.
4. Use os relatarios para auditoria e fechamento.

Exemplo:

- Fluxo de caixa por periodo.
- Listagem de lancamentos em aberto.

### 5.23 Area Administrativa e Backoffice

Uso:

1. Admin interno da empresa opera apenas no proprio tenant.
2. Admin LiveSun sem empresa pode existir para backoffice.
3. Funcoes administrativas devem ser usadas com cautela, pois afetam permissao, plano e relacao com assinaturas.

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

- Cadastrar uma nova filial.
- Registrar uma venda simples.
- Consultar relatorios, sem alterar permissões.

### 6.5 Viewer

Responsabilidade: consulta e auditoria visual.

Rotina padrao:

1. Entrar no sistema.
2. Consultar listas e detalhes.
3. Validar informacoes antes de um fechamento.
4. Nao tentar gravar alteracoes, porque o sistema bloqueia escrita.

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
2. Adicionar cliente, Filial/Estoque e itens.
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
