# 🚀 Guia Rápido de Início - LiveSun Financeiro

## ⚡ Inicialização em 5 Minutos

### Windows

1. **Abra o prompt de comando** na pasta do projeto
2. **Execute**:
   ```bash
   iniciar.bat
   ```
3. **Acesse**: http://localhost:5000
4. **Login**: admin / admin123

### Linux/Mac

1. **Abra o terminal** na pasta do projeto
2. **Execute**:
   ```bash
   chmod +x iniciar.sh
   ./iniciar.sh
   ```
3. **Acesse**: http://localhost:5000
4. **Login**: admin / admin123

---

## 📋 Passos Manuais (Se necessário)

### 1. Criar Banco de Dados

```bash
mysql -u root -p < criar_banco.sql
```

### 2. Criar Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Inicializar Database

```bash
python inicializar_db.py
```

### 5. Executar Aplicação

```bash
python run.py
```

---

## 💡 Dicas Rápidas

### Mudar Senha do Admin

Via Python shell:
```python
python
>>> from src.app import create_app
>>> from src.models import db, User
>>> app = create_app()
>>> with app.app_context():
>>>     admin = User.query.filter_by(username='admin').first()
>>>     admin.set_password('nova_senha')
>>>     db.session.commit()
>>>     print('Senha alterada!')
```

### Criar Novo Usuário

```python
python
>>> from src.app import create_app
>>> from src.models import db, User
>>> app = create_app()
>>> with app.app_context():
>>>     user = User(username='novo', email='novo@email.com', is_admin=False)
>>>     user.set_password('senha123')
>>>     db.session.add(user)
>>>     db.session.commit()
>>>     print('Usuário criado!')
```

### Resetar Banco de Dados

```python
python
>>> from src.app import create_app
>>> from src.models import db
>>> app = create_app()
>>> with app.app_context():
>>>     db.drop_all()
>>>     db.create_all()
>>>     print('Reset completo!')
```

---

## 🌐 Acessar de Outro Computador

Edite `.env`:
```env
SERVER_HOST=0.0.0.0  # Aceita de qualquer IP
SERVER_PORT=5000
```

Acesse de outro PC:
```
http://seu_ip:5000
```

---

## 🔧 Troubleshooting

| Problema | Solução |
|----------|---------|
| Porta 5000 em uso | `SERVER_PORT=5001` no .env |
| MySQL não conecta | Verifique credenciais em .env |
| Módulos não encontrados | `pip install -r requirements.txt` |
| Erro de importação | `pip install --upgrade pip setuptools` |

---

## 📁 Próximos Passos

1. **Cadastre Entidades**: Clientes, Fornecedores
2. **Configure Fluxo**: Plano de Contas
3. **Registre Contas**: Bancárias
4. **Faça Lançamentos**: Receitas/Despesas
5. **Consulte Relatórios**: Visualize resultados

---

## 🆘 Ajuda

- Documentação completa: [README.md](README.md)
- Requisitos: Python 3.8+, MySQL 5.7+
- Suporte: Acesso pela rede local em 0.0.0.0:5000

**Enjoy! 🎉**
