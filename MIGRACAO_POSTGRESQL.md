# Guia de Migração para PostgreSQL - LiveSun Comercial

## Visão Geral

Este documento descreve o processo de migração do projeto LiveSun Comercial de MySQL para PostgreSQL, mantendo compatibilidade com ambos os bancos de dados através da mesma base de código.

## Checklist Técnico de Alterações

### ✅ Concluído
- [x] Análise do schema MySQL atual
- [x] Identificação de incompatibilidades com PostgreSQL
- [x] Criação do script de criação de banco PostgreSQL
- [x] Atualização do `config.py` para suporte multi-banco
- [x] Adição do driver `psycopg2-binary` ao `requirements.txt`
- [x] Criação de scripts de migração PostgreSQL
- [x] Atualização do `.env.example` com exemplos PostgreSQL

### ⏳ Pendente (Implementação Futura)
- [ ] Revisão dos models SQLAlchemy para portabilidade
- [ ] Implementação de Flask-Babel para internacionalização
- [ ] Configuração de Alembic/Flask-Migrate
- [ ] Testes de compatibilidade com ambos os bancos

## Estrutura de Arquivos

```
LiveSun_Comercial_X/
├── criar_banco_comercial_postgresql.sql      # Script principal de criação PostgreSQL
├── criar_banco_controller_mysql.sql         # Script MySQL existente
├── schema_comercial.sql                     # Schema MySQL existente
├── config/
│   └── config.py                            # Configuração atualizada (multi-banco)
├── migrations/
│   ├── *.sql                                # Migrações MySQL existentes
│   └── postgresql/
│       ├── 001_create_comissoes_tables_postgresql.sql
│       ├── 009_create_commercial_billing_tables_postgresql.sql
│       ├── 013_create_nfse_nacional_tables_postgresql.sql
│       └── README.md
├── requirements.txt                          # Dependências atualizadas
└── .env.example                             # Exemplos de configuração
```

## Configuração do Banco de Dados

### MySQL (Configuração Atual)

```bash
# .env
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=comercial
```

### PostgreSQL (Nova Configuração)

```bash
# .env
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua_senha_forte
DB_NAME=comercial
```

### Configuração em Produção (Render/Heroku)

```bash
# .env
DB_TYPE=postgresql
DB_HOST=seu-host.postgres.database.azure.com
DB_PORT=5432
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=comercial
```

## Diferenças Principais: MySQL vs PostgreSQL

### Tipos de Dados

| MySQL | PostgreSQL | Observação |
|-------|------------|------------|
| `INT AUTO_INCREMENT` | `SERIAL` | Auto-incremento |
| `BIGINT AUTO_INCREMENT` | `BIGSERIAL` | Auto-incremento grande |
| `TINYINT(1)` | `BOOLEAN` | Booleano |
| `DATETIME` | `TIMESTAMP` | Data/hora |
| `DECIMAL(M,N)` | `NUMERIC(M,N)` | Precisão decimal |
| `LONGTEXT` | `TEXT` | Texto longo |
| `JSON` | `JSONB` | JSON binário (mais eficiente) |
| `VARCHAR(N)` | `VARCHAR(N)` | String com limite |

### Auto-update de Timestamp

**MySQL:**
```sql
criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

**PostgreSQL:**
```sql
-- Criar função trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger à tabela
CREATE TRIGGER update_tabela_atualizado_em
    BEFORE UPDATE ON tabela
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Índices e Constraints

**MySQL:**
```sql
CREATE TABLE exemplo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120),
    UNIQUE KEY uq_email (email),
    KEY idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**PostgreSQL:**
```sql
CREATE TABLE exemplo (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120),
    CONSTRAINT uq_email UNIQUE (email)
);

CREATE INDEX idx_email ON exemplo(email);
```

### Inserção Condicional

**MySQL:**
```sql
INSERT IGNORE INTO tabela (col1, col2) VALUES (val1, val2);
-- ou
INSERT INTO tabela (col1, col2) 
SELECT val1, val2 
WHERE NOT EXISTS (SELECT 1 FROM tabela WHERE col1 = val1);
```

**PostgreSQL:**
```sql
INSERT INTO tabela (col1, col2) 
VALUES (val1, val2)
ON CONFLICT (col1) DO NOTHING;
```

## Scripts de Migração

### 1. Script Principal de Criação

**Arquivo:** `criar_banco_comercial_postgresql.sql`

Este script cria:
- Database `comercial`
- Usuário `comercial_db_owner`
- Todas as tabelas principais
- Função trigger para auto-update de timestamps
- Índices e constraints
- Dados iniciais (plano de contas, permissões RBAC)

**Execução:**
```bash
psql -U postgres -f criar_banco_comercial_postgresql.sql
```

### 2. Migrações Incrementais

Os scripts em `migrations/postgresql/` correspondem às migrações MySQL existentes:

- `001_create_comissoes_tables_postgresql.sql` - Tabelas de comissão
- `009_create_commercial_billing_tables_postgresql.sql` - Assinaturas e cobranças
- `013_create_nfse_nacional_tables_postgresql.sql` - NFS-e Nacional

**Execução em ordem:**
```bash
psql -U postgres -d comercial -f migrations/postgresql/001_create_comissoes_tables_postgresql.sql
psql -U postgres -d comercial -f migrations/postgresql/009_create_commercial_billing_tables_postgresql.sql
psql -U postgres -d comercial -f migrations/postgresql/013_create_nfse_nacional_tables_postgresql.sql
```

## Configuração da Aplicação

### Atualização do config.py

O arquivo `config/config.py` foi atualizado para detectar automaticamente o tipo de banco:

```python
DB_TYPE = os.environ.get('DB_TYPE', 'mysql')

if DB_TYPE.lower() == 'postgresql' or DB_TYPE.lower() == 'postgres':
    if DB_PORT == 3306:  # Default MySQL port
        DB_PORT = 5432
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{_DB_USER_ESCAPED}:{_DB_PASSWORD_ESCAPED}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
else:
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{_DB_USER_ESCAPED}:{_DB_PASSWORD_ESCAPED}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
```

### Dependências

O `requirements.txt` foi atualizado com:

```
psycopg2-binary==2.9.9
```

**Instalação:**
```bash
pip install -r requirements.txt
```

## Boas Práticas para Evitar Vendor Lock-in

### 1. Usar SQLAlchemy ORM

**✅ Recomendado:**
```python
from models import Lancamento

lancamento = Lancamento(
    data_evento=date.today(),
    valor_real=100.00,
    status='aberto'
)
db.session.add(lancamento)
db.session.commit()
```

**❌ Evitar:**
```python
db.session.execute(
    "INSERT INTO lancamentos (data_evento, valor_real, status) VALUES (?, ?, ?)",
    (date.today(), 100.00, 'aberto')
)
```

### 2. Tipos de Dados Portáveis

**✅ Recomendado:**
```python
from sqlalchemy import Integer, String, Numeric, Boolean, DateTime

class User(db.Model):
    id = db.Column(Integer, primary_key=True)
    nome = db.Column(String(150))
    valor = db.Column(Numeric(15, 2))
    ativo = db.Column(Boolean, default=True)
    criado_em = db.Column(DateTime, default=datetime.utcnow)
```

**❌ Evitar:**
```python
from sqlalchemy.dialects.mysql import TINYINT

class User(db.Model):
    ativo = db.Column(TINYINT(1))  # MySQL-specific
```

### 3. Funções SQL Portáveis

**✅ Recomendado:**
```python
from sqlalchemy import func

# Usar func para funções SQL
query = db.session.query(
    func.count(Lancamento.id),
    func.sum(Lancamento.valor_real)
)
```

**❌ Evitar:**
```python
# Funções específicas de banco
query = db.session.execute("SELECT COUNT(*), SUM(valor_real) FROM lancamentos")
```

### 4. Índices e Constraints via ORM

**✅ Recomendado:**
```python
class User(db.Model):
    id = db.Column(Integer, primary_key=True)
    email = db.Column(String(120), unique=True)
    empresa_id = db.Column(Integer, db.ForeignKey('empresas.id'))
    
    __table_args__ = (
        db.Index('idx_user_empresa', 'empresa_id'),
        db.CheckConstraint('email IS NOT NULL', name='ck_user_email_not_null')
    )
```

## Plano de Execução em Etapas

### Etapa 1: Preparação (Concluída)
- ✅ Análise do schema atual
- ✅ Criação de scripts PostgreSQL
- ✅ Atualização de configuração
- ✅ Adição de dependências

### Etapa 2: Testes Locais
1. Instalar PostgreSQL localmente
2. Criar banco de dados com o script
3. Configurar variáveis de ambiente para PostgreSQL
4. Executar a aplicação com PostgreSQL
5. Testar CRUD básico
6. Verificar integridade de dados

### Etapa 3: Revisão de Models
1. Revisar todos os models em `src/models/`
2. Verificar tipos de dados portáveis
3. Remover referências específicas de MySQL
4. Adicionar validações compatíveis

### Etapa 4: Migração de Dados (Opcional)
1. Exportar dados do MySQL atual
2. Transformar dados para formato PostgreSQL
3. Importar dados para PostgreSQL
4. Validar integridade

### Etapa 5: Deploy em Produção
1. Configurar banco PostgreSQL no provedor (Render/Heroku)
2. Executar scripts de criação
3. Atualizar variáveis de ambiente
4. Deploy da aplicação
5. Monitoramento inicial

### Etapa 6: Internacionalização (Futuro)
1. Instalar Flask-Babel
2. Configurar idiomas suportados (pt, en)
3. Marcar strings traduzíveis
4. Criar arquivos de tradução
5. Implementar seletor de idioma

## Riscos Técnicos e Pontos de Atenção

### ⚠️ Riscos

1. **Diferenças de comportamento em queries complexas**
   - JOINs podem ter performance diferente
   - Ordenação de strings com acentos
   - Case sensitivity em comparações

2. **Funções específicas de banco**
   - `GROUP_CONCAT` (MySQL) vs `string_agg` (PostgreSQL)
   - `DATE_FORMAT` (MySQL) vs `TO_CHAR` (PostgreSQL)
   - Funções de agregação podem ter sintaxe diferente

3. **Limites de tamanho**
   - PostgreSQL tem limites diferentes para tipos TEXT/BLOB
   - Nomes de tabelas/colunas têm limite de 63 caracteres

4. **Transações e locking**
   - Comportamento de locking pode ser diferente
   - Níveis de isolamento padrão diferem

### 🔍 Pontos de Atenção

1. **Timestamps**
   - PostgreSQL usa UTC por padrão
   - MySQL pode usar timezone do servidor
   - Necessário padronizar timezone na aplicação

2. **Case sensitivity**
   - PostgreSQL é case-sensitive em identificadores
   - MySQL não é (dependendo do sistema)
   - Usar sempre lowercase em nomes de tabelas/colunas

3. **NULL vs empty string**
   - PostgreSQL trata '' e NULL de forma diferente
   - MySQL pode converter '' para NULL em alguns contextos
   - Validar tratamento de NULL na aplicação

4. **Auto-incremento após rollback**
   - PostgreSQL não reseta sequências após rollback
   - MySQL pode ter comportamento diferente
   - Não depender de IDs sequenciais sem gaps

## Estratégia de Testes

### Testes de Compatibilidade

```python
# tests/test_database_compatibility.py
import pytest
from models import Lancamento, Entidade

def test_create_lancamento_mysql(client):
    """Testa criação de lançamento com MySQL"""
    # Configurar DB_TYPE=mysql
    # Executar teste
    pass

def test_create_lancamento_postgresql(client):
    """Testa criação de lançamento com PostgreSQL"""
    # Configurar DB_TYPE=postgresql
    # Executar teste
    pass

def test_decimal_precision(client):
    """Testa precisão de valores decimais"""
    lancamento = Lancamento(valor_real=1234567.89)
    db.session.add(lancamento)
    db.session.commit()
    
    assert lancamento.valor_real == 1234567.89

def test_boolean_values(client):
    """Testa valores booleanos"""
    entidade = Entidade(ativo=True)
    db.session.add(entidade)
    db.session.commit()
    
    assert entidade.ativo is True
```

### Testes de Migração

```python
def test_migration_001_comissoes():
    """Testa migração 001 (comissões)"""
    # Verificar se tabela foi criada
    # Verificar se trigger funciona
    # Verificar se índices existem
    pass
```

## Comandos Úteis

### PostgreSQL

```bash
# Conectar ao banco
psql -U postgres -d comercial

# Listar tabelas
\dt

# Descrever tabela
\d nome_tabela

# Executar script SQL
\i camho/script.sql

# Backup
pg_dump -U postgres comercial > backup.sql

# Restore
psql -U postgres comercial < backup.sql

# Verificar tamanho do banco
SELECT pg_size_pretty(pg_database_size('comercial'));
```

### MySQL (para comparação)

```bash
# Conectar ao banco
mysql -u root -p comercial

# Listar tabelas
SHOW TABLES;

# Descrever tabela
DESCRIBE nome_tabela;

# Executar script SQL
source caminho/script.sql

# Backup
mysqldump -u root -p comercial > backup.sql

# Restore
mysql -u root -p comercial < backup.sql
```

## Suporte e Troubleshooting

### Problema: Erro de conexão
**Solução:** Verificar se o PostgreSQL está rodando e se as credenciais estão corretas no `.env`

### Problema: Trigger não funciona
**Solução:** Verificar se a função `update_updated_at_column()` foi criada antes dos triggers

### Problema: Erro de tipo de dado
**Solução:** Revisar models SQLAlchemy para usar tipos portáveis (Integer, String, Numeric, Boolean)

### Problema: Performance lenta
**Solução:** Verificar índices, usar `EXPLAIN ANALYZE` para analisar queries

## Próximos Passos

1. **Implementar Flask-Babel** para internacionalização (pt/en)
2. **Configurar Alembic/Flask-Migrate** para migrations automáticas
3. **Criar suíte de testes** para validar compatibilidade
4. **Documentar processo de deploy** para produção
5. **Treinar equipe** sobre diferenças entre bancos

## Referências

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
