import io
import sys
sys.path.insert(0, '.')

import os
os.environ['DB_TYPE'] = 'sqlite'

from src.app import create_app
from src.models import db, Empresa, User, NfseNacionalCertificado

app = create_app('testing')

CNPJ = '99999999000194'
USERNAME = 'nfse_dash'
PASSWORD = 'Senha123!'

with app.app_context():
    emp = Empresa.query.filter_by(cnpj=CNPJ).first()
    if not emp:
        emp = Empresa(nome='NFSE_SMOKE_TEMP', cnpj=CNPJ, plano='premium')
        db.session.add(emp)
        db.session.flush()
    if not User.query.filter_by(username=USERNAME).first():
        u = User(username=USERNAME, email='nfse@example.com',
                 role='admin', is_admin=True, is_active=True, empresa_id=emp.id,
                 full_name='Nfse Smoke')
        u.set_password(PASSWORD)
        db.session.add(u)
        db.session.commit()

client = app.test_client()

html = client.get('/auth/login').get_data(as_text=True)
import re
m = re.search(r'name="csrf_token" value="([^"]+)"', html)
csrf = m.group(1) if m else ''

client.post('/auth/login', data={
    'empresa_cnpj': CNPJ,
    'username': USERNAME,
    'password': PASSWORD,
    'csrf_token': csrf,
}, follow_redirects=True)

# POST configuracoes with a dummy certificate file (content not parsed because invalid pfx)
data = {
    'ambiente': 'homologacao',
    'inscricao_municipal': '12345',
    'codigo_municipio': '3550308',
    'versao_layout': '1.0',
    'emissor_ativo': 'on',
    'csrf_token': csrf,
}
data['certificado_arquivo'] = (io.BytesIO(b'not-a-real-pfx'), 'cert.pfx')

resp = client.post('/nfse/configuracoes', data=data,
                   content_type='multipart/form-data', follow_redirects=True)
print('POST /configuracoes status: - _smoke_nfse_cert.py:58', resp.status_code)
body = resp.get_data(as_text=True)

has_invalid_kw = "invalid keyword argument" in body
has_success = "atualizada com sucesso" in body
print('contains invalid keyword error: - _smoke_nfse_cert.py:63', has_invalid_kw)
print('contains success msg: - _smoke_nfse_cert.py:64', has_success)

with app.app_context():
    certs = NfseNacionalCertificado.query.filter_by(empresa_id=emp.id).all()
    print('certificados criados: - _smoke_nfse_cert.py:68', len(certs))
    for c in certs:
        print('  ', c.arquivo_nome, c.ambiente, 'ativo=', c.ativo)
    # cleanup
    for c in certs:
        db.session.delete(c)
    u = User.query.filter_by(username=USERNAME).first()
    if u:
        db.session.delete(u)
    emp = Empresa.query.filter_by(cnpj=CNPJ).first()
    if emp:
        db.session.delete(emp)
    db.session.commit()

print('Done - _smoke_nfse_cert.py:82')
