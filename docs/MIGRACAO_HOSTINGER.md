# Guia de Migração do Banco de Dados para Hostinger

## Visão Geral
Este guia explica como migrar o banco de dados do LiveSun Comercial do ambiente local para a Hostinger.

## Pré-requisitos
- Acesso ao painel da Hostinger
- Banco de dados MySQL ou PostgreSQL criado na Hostinger
- Credenciais do banco na Hostinger (host, porta, usuário, senha, nome do banco)

## Passo 1: Exportar Banco Local

### MySQL
```bash
# Usar o script de exportação
scripts\export_database_mysql.bat

# Ou manualmente
mysqldump -u root -p comercial > backup_mysql.sql
```

### PostgreSQL
```bash
# Usar o script de exportação
scripts\export_database_postgresql.bat

# Ou manualmente
pg_dump -U postgres comercial > backup_postgresql.sql
```

## Passo 2: Criar Banco na Hostinger

1. Acesse o painel da Hostinger
2. Vá em **Banco de Dados** > **Banco de Dados MySQL** ou **PostgreSQL**
3. Clique em **Criar novo banco de dados**
4. Preencha:
   - Nome do banco: `livesun_comercial` (ou conforme preferência)
   - Usuário: crie um usuário com senha forte
   - Anote as credenciais (host, porta, usuário, senha, nome do banco)

## Passo 3: Importar para Hostinger

### Via phpMyAdmin (MySQL)
1. Acesse o painel da Hostinger
2. Vá em **Banco de Dados** > **phpMyAdmin**
3. Selecione o banco criado
4. Clique em **Importar**
5. Selecione o arquivo `.sql` exportado
6. Clique em **Executar**

### Via pgAdmin (PostgreSQL)
1. Acesse o painel da Hostinger
2. Vá em **Banco de Dados** > **pgAdmin**
3. Conecte ao servidor
4. Clique com botão direito no banco > **Restore**
5. Selecione o arquivo `.sql` exportado
6. Clique em **Restore**

## Passo 4: Configurar Aplicação

### Variáveis de Ambiente no Render

No painel do Render, vá em **Environment Variables** e adicione:

```bash
# Tipo de banco (mysql ou postgresql)
DB_TYPE=mysql

# Host do banco (Hostinger)
DB_HOST=seu-host-hostinger.com

# Porta (MySQL: 3306, PostgreSQL: 5432)
DB_PORT=3306

# Usuário do banco
DB_USER=seu_usuario_hostinger

# Senha do banco
DB_PASSWORD=sua_senha_hostinger

# Nome do banco
DB_NAME=livesun_comercial
```

### Exemplo para PostgreSQL
```bash
DB_TYPE=postgresql
DB_HOST=seu-host-hostinger.com
DB_PORT=5432
DB_USER=seu_usuario_hostinger
DB_PASSWORD=sua_senha_hostinger
DB_NAME=livesun_comercial
```

## Passo 5: Testar Conexão

1. Faça deploy da aplicação no Render
2. Verifique os logs no painel do Render
3. Acesse a aplicação e teste as funcionalidades

## Solução de Problemas

### Erro de Conexão
- Verifique se o host da Hostinger permite conexões externas
- Verifique se as credenciais estão corretas
- Verifique se o firewall da Hostinger permite conexão do IP do Render

### Erro de Tabelas
- Execute o script de criação de tabelas via SQLAlchemy
- O Flask-SQLAlchemy criará as tabelas automaticamente se não existirem

### Erro de Charset (MySQL)
- Certifique-se de que o banco na Hostinger usa `utf8mb4`
- Execute: `ALTER DATABASE livesun_comercial CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`

## Scripts Disponíveis

- `scripts/export_database_mysql.bat` - Exporta banco MySQL local
- `scripts/export_database_postgresql.bat` - Exporta banco PostgreSQL local
- `scripts/create_database_mysql.sql` - Cria banco MySQL vazio
- `scripts/create_database_postgresql.sql` - Cria banco PostgreSQL vazio
- `scripts/drop_tables_mysql.sql` - Remove tabelas MySQL
- `scripts/drop_tables_postgresql.sql` - Remove tabelas PostgreSQL

## Suporte

Para dúvidas sobre a Hostinger, consulte: https://support.hostinger.com
