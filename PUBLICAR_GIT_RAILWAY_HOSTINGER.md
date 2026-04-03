# 🚀 PUBLICAR NO GIT, RAILWAY E HOSTINGER

Este guia rápido mostra como publicar seu LiveSun Financeiro em diferentes plataformas.

## 📋 Sumário Rápido

| Plataforma | Dificuldade | Custo | Tempo |
|-----------|-----------|-------|--------|
| [Git/GitHub](#-gitgithub) | ⭐ Fácil | Grátis | 5 min |
| [Railway](#-railway) | ⭐⭐ Médio | $5-20/mês | 10 min |
| [Hostinger](#-hostinger) | ⭐⭐⭐ Difícil | $15-30/mês | 30 min |
| [Docker Local](#-docker-local) | ⭐⭐ Médio | Grátis | 10 min |

---

## 📦 Git/GitHub

### O que é?
Git é um sistema de controle de versão. GitHub é uma plataforma para hospedar repositórios do Git.

### ✅ Pré-requisitos
- [ ] Git instalado (`git --version`)
- [ ] Conta GitHub
- [ ] Terminal/CMD

### 🎯 Passos

#### 1️⃣ Inicializar repositório (primeira vez)
```bash
git init
git add .
git commit -m "Inicial: LiveSun Financeiro com módulo de comissões"
```

#### 2️⃣ Criar repositório no GitHub

1. Acesse [github.com/new](https://github.com/new)
2. Nome: `Livesun_Financeiro`
3. Descrição: `Sistema de gestão financeira com comissões`
4. **Não** inicialize com README (temos um)
5. Clique **Create repository**

#### 3️⃣ Conectar repositório local ao GitHub

```bash
git remote add origin https://github.com/SEU_USUARIO/Livesun_Financeiro.git
git branch -M main
git push -u origin main
```

#### 4️⃣ Fazer push de changes

```bash
# Após fazer mudanças
git add .
git commit -m "Descrição clara da mudança"
git push origin main
```

### ✨ Pronto!
Seu código está no GitHub!

---

## 🚁 Railway

### O que é?
Railway é uma plataforma de deploy moderna. Gerencia servidor, banco de dados, SSL, etc automaticamente.

### ✅ Pré-requisitos
- [ ] Repositório no GitHub (veja acima)
- [ ] Conta Railway ([railway.app](https://railway.app))
- [ ] Node.js instalado (para CLI)

### 🎯 Passos

#### 1️⃣ Verifier se tudo está no Git

```bash
git push origin main
```

#### 2️⃣ Fazer login no Railway

1. Acesse [railway.app](https://railway.app)
2. Clique **"Create Account"**
3. Escolha **GitHub**
4. Autorize o Railway

#### 3️⃣ Criar novo projeto

1. Na dashboard, clique **"New Project"**
2. Selecione **"Deploy from GitHub"**
3. Selecione **seu repositório**
4. Railway detectará Python automaticamente

#### 4️⃣ Configurar variáveis de ambiente

No painel do Railway → **Variables**:

```
FLASK_ENV=production
FLASK_APP=src/app.py
FLASK_DEBUG=False
SECRET_KEY=gere-uma-chave-forte-aqui
DB_TYPE=mysql
```

**Para gerar SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 5️⃣ Adicionar MySQL

No painel:
1. Clique **"+ Create"**
2. Selecione **"MySQL"**
3. Railway criará e vinculará automaticamente

#### 6️⃣ Deploy automático

Pronto! A cada push no GitHub, Railway faz deploy automaticamente.

### 📊 Acessar após deploy

Railway fornecerá uma URL como:
```
https://livesun-financeiro-prod.railway.app
```

### 💡 Dica
Ative **"Automatic Deployments"** nas configurações para deploy automático com cada push.

---

## 🌐 Hostinger

Hostinger é hosting compartilhado. Mais barato, mas requer mais configuração manual.

### ✅ Pré-requisitos
- [ ] Conta Hostinger com suporte Python
- [ ] Acesso ao cPanel
- [ ] Cliente FTP (FileZilla) - opcional
- [ ] Terminal para SSH - opcional

### 🎯 Passos

#### 1️⃣ Preparar ambiente Hostinger

**Via cPanel:**

1. Abra **cPanel** (seu painel de controle)
2. Busque por **"Python"** → **"Setup Python App"**
3. Clique **"Create Application"**
4. Preencha:
   - **Python Version**: 3.12
   - **Application Root**: `/home/seu_usuario/public_html`
   - **Application Startup File**: `run.py`
   - **Application Entry Point**: `application`

#### 2️⃣ Criar banco MySQL

**Via cPanel:**

1. Vá para **"Databases"** → **"MySQL Databases"**
2. Clique **"Create New Database"**
3. Preencha:
   - Database name: `seu_usuario_gfinanceiro`
   - Database user: `seu_usuario_gfin`
   - Password: [gere uma senha forte]
4. Clique **"Create Database"**
5. **IMPORTANTE**: Clique em "All Privileges" e atribua ao usuário

#### 3️⃣ Executar script SQL

1. No cPanel, vá para **"phpMyAdmin"**
2. Selecione seu banco de dados
3. Clique em **"SQL"**
4. **Copie e cole** o conteúdo de `initialize_db_hostinger.sql`
5. Clique **"Go"** ou **"Executar"**
6. ✓ Se aparecer "X queries executed", deu certo!

#### 4️⃣ Upload dos arquivos

**Opção A: Usando deploy_hostinger.bat (Windows)**
```bash
deploy_hostinger.bat
```

**Opção B: Usando FileZilla (qualquer SO)**
1. Baixe [FileZilla](https://filezilla-project.org)
2. Conecte com:
   - Host: seu-ftp-server.hostinger.com
   - Usuário: seu-usuario-ftp
   - Senha: sua-senha-ftp
3. Navegue para `/public_html`
4. Copie do lado esquerdo:
   - `src/`
   - `config/`
   - `migrations/`
   - `requirements.txt`
   - `run.py`
   - `setup_db.py`
   - `.env` (configure antes!)

**Opção C: Via SSH** (mais rápido)
```bash
ssh seu_usuario@seu_servidor.hostinger.com
cd public_html
git clone https://github.com/SEU_USUARIO/Livesun_Financeiro.git .
pip install -r requirements.txt
python setup_db.py
```

#### 5️⃣ Configurar .env

Crie arquivo `.env` na raiz (`/public_html/.env`) com:

```env
FLASK_ENV=production
FLASK_APP=src/app.py
FLASK_DEBUG=False
SECRET_KEY=sua-chave-secreta-aqui

# Hostinger MySQL
DB_TYPE=mysql
DB_HOST=srv1124.hstgr.io     # Verifique seu host específico
DB_PORT=3306
DB_USER=seu_usuario_gfin
DB_PASSWORD=sua-senha-mysql
DB_NAME=seu_usuario_gfinanceiro

SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```

#### 6️⃣ Testar aplicação

Acesse: `https://seu-dominio.com`

Se não funcionar:
1. Verifique os logs: cPanel → **Error Log**
2. Verifique credenciais MySQL
3. Confirme se tabelas foram criadas: cPanel → phpMyAdmin

### 🔒 Segurança

Após primeiro login (**IMPORTANTE**):
1. Acesse `/entidades` e crie novo admin
2. Altere senha do usuário `admin` padrão
3. Configure `/comissoes/parametros`

---

## 🐳 Docker Local

Para desenvolvimento com tudo containerizado.

### ✅ Pré-requisitos
- [ ] Docker instalado
- [ ] Docker Compose instalado

### 🎯 Passos

```bash
# 1. Navegar ao diretório do projeto
cd Livesun_Financeiro

# 2. Subir containers (MySQL + App)
docker-compose up -d

# 3. Aguardar ~30 segundos para MySQL iniciar
sleep 30

# 4. Inicializar banco (se necessário)
docker-compose exec web python setup_db.py

# 5. Acessar
# App: http://localhost:5000
# MySQL: localhost:3306 (user: gfinanceiro, pass: gfinanceiro123)

# 6. Ver logs
docker-compose logs -f web

# 7. Parar
docker-compose down
```

---

## 🆚 Comparação

| Critério | GitHub | Railway | Hostinger |
|----------|--------|---------|-----------|
| Setup | 5 min | 10 min | 30 min |
| Custo | Grátis | $5-20/mês | $15-30/mês |
| Uptime | N/A | 99.9% | 99.9% |
| Escalabilidade | N/A | Automática | Manual |
| Suporte | Comunidade | Email | Email/Chat |
| SSL | N/A | ✓ Automático | ✓ Gerenciado |
| Banco dados | N/A | Incluído | Incluído |
| Performance | N/A | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🆘 Troubleshooting

### "Erro 502 Bad Gateway"
- Railway/Hostinger: Aguarde 2-3 minutos (pode estar inicializando)
- Verifique logs: `docker-compose logs web` ou cPanel Error Log

### "Tabelas não encontradas"
```bash
# Executar manualmente
python setup_db.py
```

### "Erro de senha MySQL"
- Verifique caracteres especiais no `.env` (coloque entre aspas)
- Exemplo: `DB_PASSWORD="senha@com#especiais"`

### "ModuleNotFoundError"
```bash
# Reinstalar dependências
pip install -r requirements.txt
# ou no Railway: forçar rebuild
railway up --force-rebuild
```

---

## 📚 Próximos passos

Após deploy em qualquer plataforma:

1. **Login**: `admin` / `admin123`
2. **Mude senha**: Vai em `/auth/perfil`
3. **Configure comissões**: `/comissoes/parametros`
4. **Crie entidades**: `/entidades` (Vendedores e Clientes)
5. **Registre lançamentos**: `/lancamentos`
6. **Apure comissões**: `/comissoes/apurar`

---

## 📞 Suporte

- 📖 Documentação completa: [DEPLOY.md](./DEPLOY.md)
- 🔧 Técnico: [TECHNICAL.md](./TECHNICAL.md)
- 💰 Comissões: [COMISSOES.md](./COMISSOES.md)

---

## ✅ Checklist Final

Antes de publicar:
- [ ] Git: `git log` mostra seus commits
- [ ] Railway: Configuração de secrets feita
- [ ] Hostinger: Banco MySQL criado e tabelas inseridas
- [ ] .env: Nunca fazer push (tá no .gitignore)
- [ ] SECRET_KEY: Gerado com valor forte
- [ ] Teste de login: Admin/admin123 funciona
- [ ] HTTPS: Certificado válido (Railway/Hostinger)

---

**🎉 Pronto! Seu LiveSun Financeiro está online!**
