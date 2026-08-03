# Instalação e Configuração do PostgreSQL no Windows

## Problema: psql não reconhecido

O erro indica que o PostgreSQL não está instalado ou o `psql` não está no PATH do Windows.

## Solução 1: Instalar PostgreSQL (Recomendado)

### Baixar e Instalar

1. Acesse: https://www.postgresql.org/download/windows/
2. Baixe o instalador para Windows (versão 14 ou superior)
3. Execute o instalador com as seguintes configurações:
   - **Porta:** 5432 (padrão)
   - **Senha do postgres:** Defina uma senha forte (anote!)
   - **Components:** Marque "Command Line Tools" (importante para psql)
   - **Stack Builder:** Desmarque (não necessário)

### Adicionar ao PATH (Automático)

Durante a instalação, o instalador geralmente adiciona o PostgreSQL ao PATH automaticamente. Se não funcionar, siga a Solução 2.

## Solução 2: Adicionar psql ao PATH Manualmente

### Encontrar o caminho do psql

O psql geralmente fica em:
```
C:\Program Files\PostgreSQL\14\bin\psql.exe
```
Ou:
```
C:\Program Files\PostgreSQL\15\bin\psql.exe
```

### Adicionar ao PATH do Windows

1. Pressione `Win + X` e selecione **Sistema**
2. Clique em **Configurações avançadas do sistema**
3. Clique em **Variáveis de ambiente**
4. Em **Variáveis do sistema**, encontre **Path** e clique em **Editar**
5. Clique em **Novo** e adicione:
   ```
   C:\Program Files\PostgreSQL\14\bin
   ```
6. Clique em **OK** em todas as janelas
7. **Reinicie o PowerShell** para aplicar as mudanças

## Solução 3: Usar Caminho Completo (Temporário)

Se não quiser adicionar ao PATH, use o caminho completo:

```powershell
# Substitua 14 pela versão instalada
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres
```

## Solução 4: Usar pgAdmin (Interface Gráfica)

Se você instalou o pgAdmin junto com PostgreSQL:

1. Abra o pgAdmin
2. Conecte ao servidor PostgreSQL
3. Clique com botão direito no banco de dados
4. Selecione **Query Tool**
5. Cole o conteúdo dos scripts SQL
6. Execute clicando no botão de play (▶)

## Verificar Instalação

Para verificar se o PostgreSQL está instalado:

```powershell
# Verificar se o serviço está rodando
Get-Service postgresql*

# Verificar se o arquivo psql existe
Test-Path "C:\Program Files\PostgreSQL\14\bin\psql.exe"
```

## Executar Scripts Após Instalação

### Via PowerShell (após adicionar ao PATH)

```powershell
cd D:\App_LiveSun\LiveSun_Comercial_X
psql -U postgres -f criar_banco_comercial_postgresql.sql
psql -U postgres -f criar_banco_comercial_postgresql_part2.sql
psql -U postgres -f criar_banco_comercial_postgresql_part3.sql
psql -U postgres -f criar_banco_comercial_postgresql_part4.sql
psql -U postgres -f criar_banco_comercial_postgresql_part5.sql
```

### Via Caminho Completo

```powershell
cd D:\App_LiveSun\LiveSun_Comercial_X
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -f criar_banco_comercial_postgresql.sql
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -f criar_banco_comercial_postgresql_part2.sql
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -f criar_banco_comercial_postgresql_part3.sql
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -f criar_banco_comercial_postgresql_part4.sql
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -f criar_banco_comercial_postgresql_part5.sql
```

### Via pgAdmin

1. Abra pgAdmin
2. Conecte ao servidor
3. Clique com botão direito no banco `comercial` (ou crie primeiro)
4. **Query Tool** → **Open File** → Selecione cada script SQL
5. Execute na ordem

## Alternativa: Docker (Para Desenvolvimento)

Se não quiser instalar PostgreSQL no Windows, use Docker:

```powershell
# Instalar Docker Desktop primeiro
docker run --name postgres-comercial -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:14

# Executar scripts
docker exec -i postgres-comercial psql -U postgres < criar_banco_comercial_postgresql.sql
docker exec -i postgres-comercial psql -U postgres < criar_banco_comercial_postgresql_part2.sql
docker exec -i postgres-comercial psql -U postgres < criar_banco_comercial_postgresql_part3.sql
docker exec -i postgres-comercial psql -U postgres < criar_banco_comercial_postgresql_part4.sql
docker exec -i postgres-comercial psql -U postgres < criar_banco_comercial_postgresql_part5.sql
```

## Resumo

1. **Instale PostgreSQL** se não tiver
2. **Adicione ao PATH** ou use caminho completo
3. **Execute os scripts** na ordem indicada
4. **Configure o .env** com as credenciais

## Próximos Passos

Após criar o banco:

1. Configure o arquivo `.env`:
```bash
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua_senha_definida_na_instalacao
DB_NAME=comercial
```

2. Instale o driver Python:
```bash
pip install psycopg2-binary
```

3. Teste a conexão com a aplicação Flask
