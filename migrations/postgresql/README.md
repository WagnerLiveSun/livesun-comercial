# Migrações PostgreSQL para LiveSun Comercial

Este diretório contém os scripts de migração convertidos de MySQL para PostgreSQL.

## Diferenças Principais

### Tipos de Dados
- `INT AUTO_INCREMENT` → `SERIAL` ou `BIGSERIAL`
- `TINYINT(1)` → `BOOLEAN`
- `DATETIME` → `TIMESTAMP`
- `DECIMAL` → `NUMERIC`
- `LONGTEXT` → `TEXT`
- `JSON` → `JSONB`

### Auto-update de Timestamp
PostgreSQL não possui `ON UPDATE CURRENT_TIMESTAMP` nativo. Utilizamos triggers:

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tabela_atualizado_em
    BEFORE UPDATE ON tabela
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Índices e Constraints
- `KEY` → `INDEX` ou `CREATE INDEX`
- `UNIQUE KEY` → `CONSTRAINT ... UNIQUE`
- Constraints são definidas separadamente em PostgreSQL

### Inserção Condicional
- MySQL: `INSERT IGNORE` ou `INSERT ... WHERE NOT EXISTS`
- PostgreSQL: `INSERT ... ON CONFLICT (...) DO NOTHING`

## Scripts Disponíveis

- `001_create_comissoes_tables_postgresql.sql` - Tabelas de comissão
- `009_create_commercial_billing_tables_postgresql.sql` - Tabelas de assinatura e cobrança
- `013_create_nfse_nacional_tables_postgresql.sql` - Tabelas de NFS-e Nacional

## Execução

Execute os scripts em ordem numérica:

```bash
# Conectar ao PostgreSQL
psql -U postgres -d comercial

# Executar script
\i migrations/postgresql/001_create_comissoes_tables_postgresql.sql
```

## Observações

1. Certifique-se de que as tabelas base (empresas, users, entidades, etc.) já existam
2. Execute o script principal `criar_banco_comercial_postgresql.sql` antes das migrações
3. Verifique se a função `update_updated_at_column()` já existe antes de criar
