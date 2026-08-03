# Migração de Dados: MySQL → PostgreSQL

## Visão Geral

Este documento descreve como migrar os dados do banco MySQL para PostgreSQL.

## Método 1: Script Python (Recomendado)

### Pré-requisitos

```bash
pip install pymysql psycopg2-binary
```

### Configurar Variáveis de Ambiente

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

### Executar Migração

```bash
cd D:\App_LiveSun\LiveSun_Comercial_X
python migrar_dados_mysql_postgresql.py
```

### O que o script faz

1. Conecta ao MySQL e PostgreSQL
2. Para cada tabela:
   - Lê as colunas da tabela
   - Lê todos os dados do MySQL
   - Insere no PostgreSQL usando batch inserts
   - Desabilita triggers durante a migração (performance)
   - Usa ON CONFLICT DO NOTHING para evitar duplicatas

### Tabelas Migradas

O script migra todas as 38 tabelas principais:
- empresas, users, role_permissions, user_permission_overrides
- fluxo_contas_modelo, contas_banco, entidades, lancamentos
- fluxo_caixa_realizado, fluxo_caixa_previsto, parametros_sistema
- comissoes, importacao_nfse, conciliacao_bancaria, conciliacao_item
- filiais, produtos, servicos, estoque_movimentos
- compras_nf_manual, compras_nf_itens, compras_nf_lancamentos
- documentos_venda, documentos_venda_itens
- tabelas_preco, tabelas_preco_itens
- orcamentos, orcamentos_itens
- pedidos_venda, pedidos_venda_itens
- pdv_sessoes, pdv_vendas, pdv_itens
- rbac_roles, rbac_permissions, rbac_user_roles, rbac_role_permissions
- auditoria_eventos

## Método 2: pgloader (Alternativa)

### Instalar pgloader

Windows: Baixar de https://pgloader.io/

### Executar

```bash
pgloader mysql://root:senha@localhost/comercial postgresql://postgres:livesun@localhost/comercial
```

## Método 3: Dump/Restore Manual

### Exportar do MySQL

```bash
mysqldump -u root -p comercial > mysql_dump.sql
```

### Converter para PostgreSQL

Usar ferramentas como:
- https://github.com/dimitri/pgloader
- https://github.com/lanyado/mysql-postgresql-converter

### Importar no PostgreSQL

```bash
psql -U postgres -d comercial < converted_dump.sql
```

## Verificação Pós-Migração

```sql
-- Contar registros em cada tabela
SELECT 
    tablename,
    (xpath('/row/count/text()', query_to_xml(format('SELECT COUNT(*) AS count FROM %I', tablename), false, true)))[1]::text::int AS row_count
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
```

## Solução de Problemas

### Erro: Tabela não existe no PostgreSQL

Certifique-se de executar os scripts de criação primeiro:
```bash
psql -U postgres -f criar_banco_comercial_postgresql.sql
psql -U postgres -f criar_banco_comercial_postgresql_part2.sql
psql -U postgres -f criar_banco_comercial_postgresql_part3.sql
psql -U postgres -f criar_banco_comercial_postgresql_part4.sql
psql -U postgres -f criar_banco_comercial_postgresql_part5.sql
```

### Erro: Conexão MySQL recusada

Verifique se o MySQL está rodando e as credenciais estão corretas.

### Erro: Conexão PostgreSQL recusada

Verifique se o PostgreSQL está rodando e as credenciais estão corretas.

### Erro: Dados duplicados

O script usa `ON CONFLICT DO NOTHING`, então duplicatas são ignoradas.

## Considerações Importantes

1. **Backup sempre:** Faça backup de ambos os bancos antes da migração
2. **Teste em ambiente de staging:** Teste a migração em ambiente de teste primeiro
3. **Tempo de inatividade:** A migração pode levar tempo dependendo do volume de dados
4. **Validação:** Valide os dados após a migração
5. **Sequências:** As sequências (SERIAL) podem precisar de ajuste após a migração

## Ajuste de Sequências (se necessário)

```sql
-- Ajustar todas as sequências para o maior ID atual
DO $$
DECLARE
    seq_name text;
    max_id bigint;
BEGIN
    FOR seq_name IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public' LOOP
        EXECUTE format('SELECT last_value FROM %I', seq_name) INTO max_id;
        IF max_id IS NOT NULL THEN
            EXECUTE format('SELECT setval(%L, %s + 1)', seq_name, max_id);
        END IF;
    END LOOP;
END $$;
```

## Próximos Passos

Após a migração:
1. Configure o `.env` para usar PostgreSQL
2. Teste a aplicação com PostgreSQL
3. Monitore logs e erros
4. Mantenha o MySQL como backup por um período
