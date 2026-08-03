# Checklist de migracao e validacao de banco

## Objetivo

Este checklist serve para preparar, migrar e validar o sistema sem interromper a operacao. Ele cobre MySQL e PostgreSQL e prioriza seguranca, compatibilidade de schema e verificacao funcional.

## 0. Escopo da geracao da base

Sim. A entrega do banco contempla scripts de criacao completa da estrutura para os dois ambientes:

1. MySQL: `schema_comercial.sql` como base principal de criacao.
2. PostgreSQL: `criar_banco_comercial_postgresql.sql` e as partes complementares `part2` a `part5`.

Em outras palavras, nao se trata apenas de migracao de dados. O projeto tambem possui scripts para criar a estrutura do banco do zero em cada tecnologia, e depois aplicar migracoes e ajustes de compatibilidade quando necessario.

## 1. Antes de qualquer migracao

1. Confirme o banco de origem e o banco de destino.
2. Faça backup completo do banco atual.
3. Pare rotinas automatizadas de importacao, conciliacao e emissao, se existirem.
4. Valide a versao do ambiente com a aplicacao que esta em uso.
5. Registre a janela de manutencao, mesmo que o sistema continue aberto para leitura.

## 2. Checklist geral de compatibilidade

1. A tabela users precisa aceitar empresa_id nulo para usuario backoffice da LiveSun.
2. A tabela empresas precisa ter o campo plano.
3. A tabela entidades precisa conter os campos usados pelo cadastro comercial e fiscal.
4. As tabelas role_permissions e user_permission_overrides precisam existir.
5. As tabelas operacionais precisam existir: filiais, produtos, servicos, estoque_movimentos, compras_nf_manual, documentos_venda, tabelas_preco, orcamentos, pedidos_venda e pdv_sessoes.
6. As tabelas financeiras precisam existir: fluxo_contas_modelo, contas_banco, lancamentos, fluxo_caixa_realizado, fluxo_caixa_previsto, conciliacao_bancaria e conciliacao_item.
7. Se o modulo de fiscalizacao estiver em uso, valide empresa_fiscal_itens e as tabelas de referencia de NFS-e.

## 3. Caminho recomendado para MySQL

### 3.1 Criacao da estrutura

1. Use o schema base do projeto para o banco comercial MySQL.
2. Confirme que o banco configurado no .env aponta para o schema correto.
3. Se o ambiente ja estiver em uso, aplique apenas migrations incrementais, nunca um re-criacao cega em producao.

### 3.2 Migracoes de compatibilidade mais comuns

1. Execute as migracoes que adicionam campos de empresa e entidade.
2. Execute as migracoes que ajustam login por empresa e isolamento por tenant.
3. Execute a migracao de itens fiscais da empresa quando o fluxo de NFS-e estiver ativo.

Arquivos de referencia mais relevantes no repositorio:

- migrations/016_add_entidades_cadastro_fields.sql
- migrations/018_add_codigo_municipio_ibge_to_entidades.sql
- migrations/019_add_codigo_municipio_ibge_to_empresas.sql
- migrations/022_add_atividade_contratos.sql
- migrations/030_add_regime_tributario.sql
- migrations/014_add_empresa_fiscal_fields.sql
- migrate_user_login_scope.py
- migrate_tenant_isolation.py

### 3.3 Validacao apos MySQL

1. Abra a aplicacao.
2. Teste login de admin, operator e viewer.
3. Abra dashboard, entidades, contas bancarias e lancamentos.
4. Crie uma filial, um produto e um servico.
5. Registre um lancamento financeiro e uma compra manual.
6. Verifique se o sistema grava e lista sem erro de coluna ausente.

## 4. Caminho recomendado para PostgreSQL

### 4.1 Criacao da estrutura

1. Execute os scripts em ordem:
   1. criar_banco_comercial_postgresql.sql
   2. criar_banco_comercial_postgresql_part2.sql
   3. criar_banco_comercial_postgresql_part3.sql
   4. criar_banco_comercial_postgresql_part4.sql
   5. criar_banco_comercial_postgresql_part5.sql
2. Aplique os scripts opcionais se o modulo correspondente estiver em uso.
3. Configure DB_TYPE=postgresql no .env da aplicacao.

### 4.2 Migracao de dados

1. Se os dados estiverem em MySQL, use migrar_dados_mysql_postgresql.py.
2. Como alternativa, use pgloader se a equipe ja tiver esse fluxo validado.
3. Migre primeiro a estrutura, depois os dados.
4. Confirme contagens basicas em empresas, users, entidades, contas_banco e lancamentos.

### 4.3 Validacao apos PostgreSQL

1. Teste login e permissao por papel.
2. Abra os modulos financeiros e comerciais principais.
3. Verifique se as telas de listagem carregam sem erro de coluna ou chave estrangeira.
4. Confirme se os scripts de verificação das partes retornam as tabelas esperadas.

## 5. Ordem segura de validacao funcional

1. Login e logout.
2. Dashboard.
3. Usuarios e controle de acesso.
4. Entidades.
5. Contas bancarias.
6. Lancamentos.
7. Conciliacao bancaria.
8. Filiais, produtos e servicos.
9. Compra manual.
10. Documento de venda.
11. Orcamentos, pedidos e PDV.

## 6. Sinais de que a migracao ainda nao esta pronta

1. Erro ao abrir tela por atributo ou coluna inexistente.
2. Erro ao gravar por foreign key ausente.
3. Usuario admin da LiveSun nao consegue entrar sem empresa vinculada.
4. Viewer consegue gravar algo que deveria ser somente leitura.
5. Modulo comercial abre, mas o schema nao tem tabelas operacionais completas.

## 7. Recomendacao operacional

1. Nao use o sistema de producao como ambiente de teste da primeira migracao.
2. Valide a compatibilidade com um banco espelho antes de repetir o processo.
3. Se a aplicacao ja estiver aberta e funcional, aplique somente as correcaoes de schema que faltam.
