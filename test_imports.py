import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'LiveSun_Comercial'))

modules_to_test = [
    'flask',
    'flask_sqlalchemy',
    'flask_login',
    'flask_wtf',
    'wtforms',
    'pymysql',
    'sqlalchemy',
    'dotenv',
    'cryptography',
    'email_validator',
    'werkzeug',
    'jinja2',
    'markupsafe',
    'itsdangerous',
    'click',
    'colorama',
    'openpyxl',
    'requests',
    'signxml',
    'lxml',
    'fpdf'
]

print("Verificando dependências externas...")
missing = []
for mod in modules_to_test:
    try:
        __import__(mod)
        print(f"✅ {mod}")
    except ImportError as e:
        print(f"❌ {mod}: {e}")
        missing.append(mod)

if missing:
    print(f"\nDependências faltando: {', '.join(missing)}")
else:
    print("\nTodas as dependências externas básicas estão presentes.")

print("\nVerificando módulos do projeto...")
project_imports = [
    'src.app',
    'src.models',
    'src.models.locacao',
    'src.routes.auth',
    'src.routes.locacao',
    'src.services.nfse_nacional'
]

for mod in project_imports:
    try:
        __import__(mod, fromlist=['*'])
        print(f"✅ {mod}")
    except Exception as e:
        print(f"❌ {mod}: {e}")
