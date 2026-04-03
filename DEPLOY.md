# Guia de Deploy - LiveSun Financeiro

Este documento descreve como publicar e fazer deploy da aplicação em diferentes plataformas.

## Índice

1. [Git & GitHub](#git--github)
2. [Railway](#railway)
3. [Hostinger](#hostinger)
4. [Docker](#docker)
5. [Troubleshooting](#troubleshooting)

---

## Git & GitHub

### 1. Preparar o repositório local

```bash
# Clonar o repositório (se ainda não tiver)
git clone https://github.com/seu-usuario/Livesun_Financeiro.git
cd Livesun_Financeiro

# Ativar ambiente virtual
.venv\Scripts\activate  # Windows
# ou
source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### 2. Fazer commit e push

```bash
# Adicionar todos os arquivos
git add .

# Fazer commit
git commit -m "Adicionar módulo de comissões e configuração de deploy"

# Fazer push para main
git push origin main
```

### 3. Configurar Secrets no GitHub

Vá para: **Settings → Secrets and variables → Actions**

Adicione os seguintes secrets:

```
RAILWAY_TOKEN = seu-token-railway
HOSTINGER_FTP_SERVER = seu-servidor-ftp.hostinger.com
HOSTINGER_FTP_USER = seu-usuario-ftp
HOSTINGER_FTP_PASSWORD = sua-senha-ftp
```

---

## Railway

Railway é uma plataforma de deploy moderna que gerencia infraestrutura automaticamente.

### 1. Criar conta e conectar Git

1. Acesse [railway.app](https://railway.app)
2. Faça login com GitHub
3. Autorize o Railway a acessar seus repositórios

### 2. Criar novo projeto

1. Clique em **"Create a New Project"**
2. Selecione **"GitHub Repo"**
3. Escolha o repositório `Livesun_Financeiro`
4. Railway detectará automaticamente que é um app Python

### 3. Configurar variáveis de ambiente

No painel do Railway, vá para **Variables**:

```
FLASK_ENV=production
FLASK_APP=src/app.py
FLASK_DEBUG=False
SECRET_KEY=sua-chave-secreta-forte
DB_TYPE=mysql
DB_HOST=seu-db-railway.railway.internal
DB_USER=sua-nome-usuario
DB_PASSWORD=sua-senha-super-secreta
DB_NAME=livesun_financeiro
```

### 4. Adicionar banco MySQL

No painel:
1. Clique **"+ Create"**
2. Selecione **"MySQL"**
3. Railway criará automaticamente e linká ao seu app

### 5. Deploy

```bash
# Instalar a CLI do Railway
npm install -g @railway/cli

# Login no Railway
railway login

# Deploy
railway up
```

Ou simplesmente faça um push para GitHub e Railway fará o deploy automaticamente.

### 6. Acessar aplicação

Railway fornecerá uma URL como:
```
https://livesun-financeiro-production.railway.app
```

---

## Hostinger

Hostinger é uma hospedagem compartilhada com suporte a Python e MySQL.

### 1. Preparar ambiente Hostinger

#### Via cPanel:

1. Abra seu **cPanel**
2. Vá para **"Setup Python App"**
3. Selecione **Python 3.12**
4. Defina:
   - **Application root**: `/home/u951548013/public_html`
   - **Application URL**: `seu-dominio.com`
   - **Application startup file**: `run.py`

#### Via MySQL:

1. Vá para **"MySQL Databases"**
2. Crie um novo banco:
   - **Name**: `u951548013_gfinanceiro`
   - **Character Set**: `utf8mb4`
3. Crie um usuário MySQL
4. Atribua **TODOS** os privilégios

### 2. Executar script de inicialização do banco

1. Abra **phpMyAdmin**
2. Selecione seu banco `u951548013_gfinanceiro`
3. Clique em **"SQL"**
4. Copie e cole o conteúdo de `initialize_db_hostinger.sql`
5. Clique **"Go"** ou **"Executar"**
6. Verifique se todas as tabelas foram criadas

### 3. Configurar arquivo .env

Via FTP ou File Manager do cPanel:

1. Crie um arquivo `.env` na raiz do projeto
2. Preenchacomo este template:

```env
FLASK_ENV=production
FLASK_APP=src/app.py
FLASK_DEBUG=False
SECRET_KEY=sua-chave-secreta-muito-forte

# Hostinger MySQL
DB_TYPE=mysql
DB_HOST=srv1124.hstgr.io
DB_PORT=3306
DB_USER=u951548013_gfinanceiro
DB_PASSWORD=sua-senha-mysql-aqui
DB_NAME=u951548013_Gfinanceiro

SERVER_HOST=0.0.0.0
SERVER_PORT=5000
SESSION_TIMEOUT=3600
DB_POOL_RECYCLE=1800
```

### 4. Upload via FTP

```bash
# Windows
ftp seu-servidor-ftp.hostinger.com

# Comandos FTP
put requirements.txt
put src/*
put config/*
# ... etc

# Ou usar um cliente FTP como FileZilla
```

### 5. Instalar dependências

Via **SSH** (se disponível):

```bash
ssh seu-usuario@seu-servidor.hostinger.com
cd public_html
python3 -m pip install -r requirements.txt
python3 setup_db.py --hostinger
```

### 6. Acessar aplicação

```
https://seu-dominio.com
```

---

## Docker

Para desenvolvimento local ou deploy em qualquer servidor com Docker.

### 1. Build da imagem

```bash
docker build -t livesun-financeiro:latest .
```

### 2. Executar com Docker Compose (completo)

```bash
docker-compose up -d
```

Isso levanta:
- MySQL (porta 3306)
- Flask App (porta 5000)
- Rede compartilhada

### 3. Acessar

- Aplicação: http://localhost:5000
- MySQL: localhost:3306

### 4. Ver logs

```bash
docker-compose logs -f web
docker-compose logs -f mysql
```

### 5. Parar

```bash
docker-compose down
```

---

## Troubleshooting

### Problema: "Erro de conexão com banco de dados"

**Solução:**
1. Verifique variáveis de ambiente no seu `.env`
2. Teste a conexão:
   ```bash
   python
   >>> from src.app import create_app
   >>> app = create_app()
   >>> with app.app_context():
   ...     from src.models import db
   ...     db.session.execute('SELECT 1')
   >>> print("✓ Conexão OK")
   ```

### Problema: "Tabelas não encontradas"

**Solução:**
1. Execute o script SQL:
   ```bash
   python setup_db.py
   ```
   ou
   ```bash
   python setup_db.py --hostinger
   ```

### Problema: "Erro 500 em produção"

**Solução:**
1. Verifique os logs:
   ```bash
   # Railway
   railway logs

   # Docker
   docker-compose logs web

   # Hostinger
   # Verifique: cPanel → Error Log
   ```

2. Certifique-se de que `FLASK_DEBUG=False` e `FLASK_ENV=production`

3. Verifique permissões de diretórios (uploads/, data/, logs/)

### Problema: "Erro de autenticação no banco MySQL"

**Solução:**
1. Verifique credenciais no `.env`
2. Para Hostinger:
   - Abra phpMyAdmin
   - Verifique usuário e senha criados
   - Teste privilégios do usuário

### Problema: "Timeout na apuração de comissões"

**Solução:**
1. Aumente o timeout no Procfile:
   ```
   web: gunicorn ... --timeout 300
   ```

2. Considere usar workers assíncronos para apurações grandes

---

## Checklist de Deploy

### Antes de fazer push para Git:

- [ ] `.env` **NÃO** está versionado (.gitignore contém `.env`)
- [ ] `.env.example` está atualizado
- [ ] `requirements.txt` está completo
- [ ] Testes passam (`pytest tests/`)
- [ ] Não há histórico sensível de commits
- [ ] Documentação está atualizada

### Antes de fazer deploy em produção:

- [ ] Backup do banco de dados feito
- [ ] Variáveis de ambiente configuradas
- [ ] `SECRET_KEY` é uma chave forte aleatória
- [ ] `FLASK_DEBUG=False`
- [ ] `FLASK_ENV=production`
- [ ] Banco de dados inicializado (`setup_db.py`)
- [ ] Testes em staging passam
- [ ] Monitoramento configurado (logs, errors)

---

## Próximas etapas

Após o deploy:

1. **Acesse a aplicação** e teste as funcionalidades básicas
2. **Crie um usuário admin** via interface ou `setup_db.py`
3. **Configure alíquota padrão** em `/comissoes/parametros`
4. **Monitore logs** para erros iniciais
5. **Fique atualizado** com as novas versões

---

## Contato & Suporte

Para dúvidas ou problemas:
1. Consulte [COMISSOES.md](./COMISSOES.md)
2. Verifique [TECHNICAL.md](./TECHNICAL.md)
3. Envie uma issue no GitHub
4. Entre em contato com o suporte
