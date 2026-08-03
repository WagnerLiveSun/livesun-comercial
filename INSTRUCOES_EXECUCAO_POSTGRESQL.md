# Instruções de Execução - Scripts PostgreSQL

## Visão Geral

O script PostgreSQL foi dividido em 5 partes devido ao tamanho. Execute na ordem indicada.

## Arquivos

1. `criar_banco_comercial_postgresql.sql` - Parte 1: Database, Owner, Tabelas Core
2. `criar_banco_comercial_postgresql_part2.sql` - Parte 2: Conciliação e Operacional
3. `criar_banco_comercial_postgresql_part3.sql` - Parte 3: Preço, Orçamentos e Pedidos
4. `criar_banco_comercial_postgresql_part4.sql` - Parte 4: PDV / Caixa
5. `criar_banco_comercial_postgresql_part5.sql` - Parte 5: RBAC, Auditoria e Verificação

## Migrações Adicionais (Opcionais)

As seguintes tabelas estão em scripts de migração separados e devem ser executadas se necessário:

- `migrations/postgresql/009_create_commercial_billing_tables_postgresql.sql` - Assinaturas e Cobranças
- `migrations/postgresql/013_create_nfse_nacional_tables_postgresql.sql` - NFS-e Nacional

## Execução

### Via psql (Linha de Comando)

```bash
# Conectar ao PostgreSQL
psql -U postgres

# Executar em ordem
\i d:/App_LiveSun/LiveSun_Comercial_X/criar_banco_comercial_postgresql.sql
\i d:/App_LiveSun/LiveSun_Comercial_X/criar_banco_comercial_postgresql_part2.sql
\i d:/App_LiveSun/LiveSun_Comercial_X/criar_banco_comercial_postgresql_part3.sql
\i d:/App_LiveSun/LiveSun_Comercial_X/criar_banco_comercial_postgresql_part4.sql
\i d:/App_LiveSun/LiveSun_Comercial_X/criar_banco_comercial_postgresql_part5.sql

# Migrações opcionais
\i d:/App_LiveSun/LiveSun_Comercial_X/migrations/postgresql/009_create_commercial_billing_tables_postgresql.sql
\i d:/App_LiveSun/LiveSun_Comercial_X/migrations/postgresql/013_create_nfse_nacional_tables_postgresql.sql
```

### Via pgAdmin ou Outro Cliente GUI

1. Abra o cliente PostgreSQL
2. Conecte ao servidor PostgreSQL
3. Abra cada arquivo SQL
4. Execute na ordem indicada acima

## Pré-requisitos

- PostgreSQL 14 ou superior
- Usuário postgres com privilégios de superusuário
- Senha do usuário postgres (será solicitada durante a execução)

## Após Execução - Estrutura

O script Parte 5 inclui queries de verificação que mostrarão:
- Lista de todas as tabelas criadas
- Contagem de registros em tabelas principais

**Importante:** Os scripts de criação apenas criam a estrutura das tabelas (schema), não migram os dados.

## Migração de Dados (MySQL → PostgreSQL)

Para migrar os dados existentes do MySQL para PostgreSQL, use o script Python:

### 1. Instalar dependências

```bash
pip install pymysql psycopg2-binary
```

### 2. Configurar variáveis de ambiente

```bash
# MySQL (origem)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sua_senha_mysql
DB_NAME=comercial

# PostgreSQL (destino)
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=livesun
PG_DATABASE=comercial
```

### 3. Executar migração

```bash
cd D:\App_LiveSun\LiveSun_Comercial_X
python migrar_dados_mysql_postgresql.py
```

O script migrará todas as 38 tabelas com seus dados do MySQL para PostgreSQL.

Veja `MIGRACAO_DADOS_POSTGRESQL.md` para detalhes completos e métodos alternativos.

## Solução de Problemas

### Erro: "database already exists"
Se o banco já existir, você pode dropar antes de recriar:
```sql
DROP DATABASE IF EXISTS comercial;
```

### Erro: "role already exists"
Se o usuário já existir:
```sql
DROP USER IF EXISTS comercial_db_owner;
```

### Erro: "relation already exists"
Os scripts usam `IF NOT EXISTS`, então tabelas existentes não causarão erro.

## Configuração da Aplicação

Após criar o banco, configure o arquivo `.env`:

```bash
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_NAME=comercial
```

## Tabelas Criadas

### Parte 1 (Core)
- empresas
- users
- role_permissions
- user_permission_overrides
- fluxo_contas_modelo
- contas_banco
- entidades
- lancamentos
- fluxo_caixa_realizado
- fluxo_caixa_previsto
- parametros_sistema
- comissoes
- importacao_nfse

### Parte 2 (Conciliação e Operacional)
- conciliacao_bancaria
- conciliacao_item
- filiais
- produtos
- servicos
- estoque_movimentos
- compras_nf_manual
- compras_nf_itens
- compras_nf_lancamentos
- documentos_venda
- documentos_venda_itens

### Parte 3 (Preço, Orçamentos e Pedidos)
- tabelas_preco
- tabelas_preco_itens
- orcamentos
- orcamentos_itens
- pedidos_venda
- pedidos_venda_itens

### Parte 4 (PDV)
- pdv_sessoes
- pdv_vendas
- pdv_itens

### Parte 5 (RBAC e Auditoria)
- rbac_roles
- rbac_permissions
- rbac_user_roles
- rbac_role_permissions
- auditoria_eventos

### Migrações (Opcionais)
- catalogo_planos_comercial
- assinatura_empresa
- cobranca_recorrente
- evento_cobranca
- historico_mudanca_plano
- notificacao_comercial
- nfse_nacional_configuracoes
- nfse_nacional_certificados
- nfse_nacional_integracoes_origem
- nfse_nacional_emissoes
- nfse_nacional_fila
- nfse_nacional_eventos

**Total: 40 tabelas principais + 12 tabelas de migração opcional**
