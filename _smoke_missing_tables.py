import re
import sys
sys.path.insert(0, '.')

# Force SQLAlchemy to only create core tables, NOT the commercial/locacao tables,
# simulating an old production DB missing those tables/columns.
os_env_patch = {}
import os
os.environ['DB_TYPE'] = 'sqlite'
os.environ['SECRET_KEY'] = 'test-key'

from sqlalchemy import inspect, text

from src.app import create_app
from src.models import db, Empresa, User

# Create app but manually drop tables that would cause 500 (locacao/comercial)
app = create_app('testing')

LOCACAO_TABLES = [
    'locacao_pecas', 'locacao_kits', 'locacao_kit_itens', 'locacao_orcamentos',
    'locacao_orcamento_itens', 'locacao_reservas', 'locacao_contratos',
    'locacao_retiradas', 'locacao_retirada_itens', 'locacao_devolucoes',
    'locacao_inspecoes', 'locacao_manutencoes', 'locacao_titulos',
    'locacao_cobrancas', 'locacao_devolucao_caucoes', 'locacao_faturamentos',
    'locacao_eventos', 'locacao_disponibilidades', 'locacao_auditoria',
    'locacao_parametros',
]
COMMERCIAL_TABLES = ['orcamentos', 'orcamento_itens', 'pedido_vendas', 'pedido_venda_itens']

CNPJ = '99999999000193'
USERNAME = 'smoke_missing'
PASSWORD = 'Senha123!'

with app.app_context():
    insp = inspect(db.engine)
    for t in LOCACAO_TABLES + COMMERCIAL_TABLES:
        if insp.has_table(t):
            db.session.execute(text(f'DROP TABLE IF EXISTS {t}'))
            db.session.commit()

    emp = Empresa(nome='MISSING_TABLES_TEMP', cnpj=CNPJ, plano='premium',
                  atividade_dashboard=True, atividade_comercial=True,
                  atividade_financeiro=True, atividade_servicos=True,
                  atividade_locacao=True, atividade_contratos=True,
                  atividade_propostas=True)
    db.session.add(emp)
    db.session.flush()
    u = User(username=USERNAME, email='missing@example.com',
             role='admin', is_admin=True, is_active=True, empresa_id=emp.id,
             full_name='Missing Tables')
    u.set_password(PASSWORD)
    db.session.add(u)
    db.session.commit()

client = app.test_client()

html = client.get('/auth/login').get_data(as_text=True)
m = re.search(r'name="csrf_token" value="([^"]+)"', html)
csrf = m.group(1) if m else ''

client.post('/auth/login', data={
    'empresa_cnpj': CNPJ,
    'username': USERNAME,
    'password': PASSWORD,
    'csrf_token': csrf,
}, follow_redirects=True)

for path in ['/comercial', '/locacao']:
    resp = client.get(path)
    status = resp.status_code
    flag = 'OK(graceful)' if status == 200 else 'FAIL'
    print(f'{flag} {status} {path} - _smoke_missing_tables.py:73')

print('Done - _smoke_missing_tables.py:75')
