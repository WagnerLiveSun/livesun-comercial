# 📐 Documentação Técnica - LiveSun Financeiro

## Arquitetura

### Stack Tecnológico

```
Frontend:
├── HTML5 / CSS3 / JavaScript
├── Bootstrap 5 (Responsividade)
├── Font Awesome 6 (Ícones)
└── jQuery (Interatividade)

Backend:
├── Python 3.8+
├── Flask 3.0.0 (Web Framework)
├── SQLAlchemy 2.0 (ORM)
├── Flask-Login (Autenticação)
└── PyMySQL (Conector MySQL)

Banco de Dados:
├── MySQL 5.7+ ou MariaDB 10.3+
├── Modelos: Users, Entidades, Fluxo, Contas, Lançamentos
└── Migrations automáticas

Deployment:
├── Servidor: Flask built-in (dev) ou Gunicorn/uWSGI (prod)
├── Acesso: Rede local (0.0.0.0:5000)
└── SSL: Configurável para HTTPS
```

---

## Estrutura de Diretórios

```
Livesun_Financeiro/
│
├── src/
│   ├── app.py                   # Factory Pattern Flask
│   ├── models/
│   │   └── __init__.py
│   │       ├── User             # Autenticação
│   │       ├── Entidade         # Clientes/Fornecedores/etc
│   │       ├── FluxoContaModel  # Plano de Contas
│   │       ├── ContaBanco       # Contas Bancárias
│   │       ├── Lancamento       # Lançamentos (Receitas/Despesas)
│   │       └── FluxoCaixa*      # Relatórios
│   │
│   ├── routes/
│   │   ├── auth.py              # /auth/* (Login/Logout)
│   │   ├── dashboard.py         # / (Dashboard)
│   │   ├── entidades.py         # /entidades/*
│   │   ├── fluxo.py             # /fluxo/*
│   │   ├── contas_banco.py      # /contas-banco/*
│   │   ├── lancamentos.py       # /lancamentos/*
│   │   └── relatorios.py        # /relatorios/*
│   │
│   ├── templates/
│   │   ├── layout.html          # Template base
│   │   ├── dashboard.html
│   │   ├── auth/
│   │   │   └── login.html
│   │   ├── entidades/
│   │   │   ├── index.html
│   │   │   ├── form.html
│   │   │   └── details.html
│   │   ├── fluxo/
│   │   │   ├── index.html
│   │   │   └── form.html
│   │   ├── contas_banco/
│   │   │   ├── index.html
│   │   │   ├── form.html
│   │   │   └── details.html
│   │   ├── lancamentos/
│   │   │   ├── index.html
│   │   │   └── form.html
│   │   ├── relatorios/
│   │   │   ├── contas_pagar.html
│   │   │   ├── contas_receber.html
│   │   │   └── fluxo_caixa.html
│   │   └── errors/
│   │       ├── 404.html
│   │       ├── 403.html
│   │       └── 500.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Estilos customizados
│   │   ├── js/
│   │   │   └── main.js          # JavaScript customizado
│   │   └── images/
│   │       └── logo.png
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Funções utilitárias
│
├── config/
│   └── config.py                # Configurações por ambiente
│
├── data/
│   └── (runtime data)
│
├── .env                         # Variáveis de ambiente
├── .env.example                 # Template de .env
├── .gitignore
├── requirements.txt             # Dependências Python
├── setup.cfg                    # Metadados do projeto
├── run.py                       # Script de execução
├── inicializar_db.py            # Inicialização do BD
├── criar_banco.sql              # Script SQL
├── QUICK_START.md               # Guia rápido
├── README.md                    # Documentação principal
└── TECHNICAL.md                 # Este arquivo
```

---

## Modelos de Dados

### User
```python
id: Integer (PK)
username: String(80, unique)
email: String(120, unique)
password_hash: String(255)
full_name: String(120)
is_active: Boolean
is_admin: Boolean
created_at: DateTime
updated_at: DateTime
```

### Entidade
```python
id: Integer (PK)
tipo: String(1) # C(Cliente), F(Fornecedor), L(Colaborador), V(Vendedor)
cnpj_cpf: String(14, unique)
inscricao_estadual: String(20)
inscricao_municipal: String(20)
nome: String(150)
nome_fantasia: String(150)
endereco_*: String (rua, numero, bairro, cidade, uf, cep)
telefone: String(20)
email: String(120)
contrato_produto: Text
ativo: Boolean
criado_em: DateTime
atualizado_em: DateTime
```

### FluxoContaModel
```python
id: Integer (PK)
codigo: String(20, unique) # 999 ou 9.99
descricao: String(200)
tipo: String(1) # P(Pagamento), R(Recebimento)
mascara: String(50)
nivel_sintetico: Integer
nivel_analitico: Integer
ativo: Boolean
criado_em: DateTime
atualizado_em: DateTime
```

### ContaBanco
```python
id: Integer (PK)
nome: String(150)
banco: String(50)
agencia: String(10)
numero_conta: String(20)
dv: String(2)
tipo: String(20)
fluxo_conta_id: Integer (FK)
saldo_inicial: Numeric(15,2)
ativo: Boolean
criado_em: DateTime
atualizado_em: DateTime
```

### Lancamento
```python
id: Integer (PK)
data_evento: Date
data_vencimento: Date
data_pagamento: Date (nullable)
status: String(20) # aberto, pago, vencido
fluxo_conta_id: Integer (FK)
conta_banco_id: Integer (FK)
entidade_id: Integer (FK)
valor_real: Numeric(15,2)
valor_pago: Numeric(15,2)
numero_documento: String(50)
observacoes: Text
criado_em: DateTime
atualizado_em: DateTime
```

---

## Fluxo de Autenticação

```
1. Usuário acessa /auth/login
   ↓
2. Submete username + password
   ↓
3. Sistema verifica credenciais
   ├─ Se inválido → Flash error → Redirect /auth/login
   └─ Se válido → Cria session → Redirect /
   ↓
4. @login_required valida presença de sessão
   ├─ Se não authenticated → Redirect /auth/login
   └─ Se authenticated → Acessa recurso
   ↓
5. Logout Remove sessioncki → Redirect /auth/login
```

---

## Fluxo de Dados

### Exemplo: Criar Lançamento

```
Cliente (HTML Form)
   ↓
POST /lancamentos/novo
   ↓
lancamentos.criar() Route
   ├─ Valida formulário
   ├─ Cria objeto Lancamento
   ├─ db.session.add()
   ├─ db.session.commit()
   └─ Redirect /lancamentos/
   ↓
GET /lancamentos/
   ↓
lancamentos.index() Route
   ├─ Query Lancamento.query.all()
   ├─ Render template com dados
   └─ Return HTML
   ↓
Cliente Browser (Tabela renderizada)
```

---

## APIs REST (Futuro - Mobile)

Estrutura proposta para aplicativo Mobile:

```
GET  /api/v1/dashboard
GET  /api/v1/entidades
POST /api/v1/entidades
GET  /api/v1/entidades/{id}
PUT  /api/v1/entidades/{id}

GET  /api/v1/lancamentos
POST /api/v1/lancamentos
GET  /api/v1/lancamentos/{id}
PUT  /api/v1/lancamentos/{id}

GET  /api/v1/relatorios/contas-pagar
GET  /api/v1/relatorios/contas-receber
GET  /api/v1/relatorios/fluxo-caixa

GET  /api/v1/auth/me
POST /api/v1/auth/login
POST /api/v1/auth/logout
```

---

## Configuração de Segurança

### CSRF Protection
```python
# Automático com Flask-WTF
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

### Session Management
```python
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
SESSION_COOKIE_SECURE = True  # HTTPS only (prod)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

### Password Hashing
```python
# PBKDF2 com werkzeug
user.set_password('senha123')
user.check_password('senha123')  # True
```

---

## Performance

### Índices de Banco
```python
# Já definidos nos modelos
cnpj_cpf: indexed
data_evento: indexed
data_vencimento: indexed
username: indexed (unique)
```

### Query Optimization
```python
# Use .limit() para paginação
query.paginate(page=1, per_page=20)

# Use .select_related() para JOINs
Lancamento.query.select_related('entidade').all()

# Use .lazy='dynamic' para grandes datasets
lancamentos = db.relationship('Lancamento', lazy='dynamic')
```

---

## Deployment

### Development
```bash
python run.py
# Flask development server - NÃO usar em produção
```

### Production
```bash
# Opção 1: Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 'src.app:create_app()'

# Opção 2: uWSGI
uwsgi --http :5000 --wsgi-file run.py --callable app

# Com Nginx reverse proxy
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

---

## Monitoramento

### Logs
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f'Usuário {user.username} fez login')
```

### Erros
```python
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
```

---

## Testes

### Estrutura proposta
```
tests/
├── test_auth.py
├── test_models.py
├── test_routes.py
└── test_integration.py
```

### Exemplo
```python
def test_login(client):
    response = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    })
    assert response.status_code == 302  # Redirect
```

---

## Maintenance

### Backup
```bash
mysqldump -u root -p livesun_financeiro > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
mysql -u root -p livesun_financeiro < backup_20260220.sql
```

### Update dependências
```bash
pip list --outdated
pip install --upgrade -r requirements.txt
```

---

## Roadmap

- [ ] API REST completa para mobile
- [ ] Autenticação JWT
- [ ] Dashboard com gráficos (Chart.js)
- [ ] Exportação para Excel/PDF
- [ ] WebSockets para notificações real-time
- [ ] Integração com gateways de pagamento
- [ ] Multi-language support (PT/EN/ES)
- [ ] Dark theme toggle

---

**Documento de Arquitetura - v1.0 - 2026**
