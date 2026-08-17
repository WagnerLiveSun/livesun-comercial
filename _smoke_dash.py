import re
import sys
sys.path.insert(0, '.')

from src.app import create_app
from src.models import db, Empresa, User

app = create_app('development')

CNPJ = '99999999000192'
USERNAME = 'smoke_dash'
PASSWORD = 'Senha123!'

PATHS = ['/', '/comercial', '/locacao', '/financeiro', '/propostas', '/fiscal']

with app.app_context():
    emp = Empresa.query.filter_by(cnpj=CNPJ).first()
    if not emp:
        emp = Empresa(nome='DASHBOARD_SMOKE_TEMP', cnpj=CNPJ, plano='premium',
                      atividade_dashboard=True, atividade_comercial=True,
                      atividade_financeiro=True, atividade_servicos=True,
                      atividade_locacao=True, atividade_contratos=True,
                      atividade_propostas=True)
        db.session.add(emp)
        db.session.flush()
    if not User.query.filter_by(username=USERNAME).first():
        u = User(username=USERNAME, email='smoke_dash@example.com',
                 role='admin', is_admin=True, is_active=True, empresa_id=emp.id,
                 full_name='Smoke Dash')
        u.set_password(PASSWORD)
        db.session.add(u)
        db.session.commit()

client = app.test_client()

html = client.get('/login').get_data(as_text=True)
m = re.search(r'name="csrf_token" value="([^"]+)"', html)
csrf = m.group(1) if m else ''

r = client.post('/login', data={
    'empresa_cnpj': CNPJ,
    'username': USERNAME,
    'password': PASSWORD,
    'csrf_token': csrf,
}, follow_redirects=True)
print('LOGIN status: - _smoke_dash.py:46', r.status_code)

ok = 0
for path in PATHS:
    resp = client.get(path)
    status = resp.status_code
    flag = 'OK' if status == 200 else 'FAIL'
    if status == 200:
        ok += 1
    print(f'{flag} {status} {path} - _smoke_dash.py:55')

print('HTML OK: - _smoke_dash.py:57', ok, '/', len(PATHS))

# Cleanup
with app.app_context():
    u = User.query.filter_by(username=USERNAME).first()
    if u:
        db.session.delete(u)
    emp = Empresa.query.filter_by(cnpj=CNPJ).first()
    if emp:
        db.session.delete(emp)
    db.session.commit()
print('Cleanup done - _smoke_dash.py:68')
