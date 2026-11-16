import hashlib
import hmac
import json
import time
from datetime import date, datetime, timezone, timedelta
from flask import Flask
from flask_login import LoginManager
import pytest
from src.models import db, Empresa, User, AssinaturaEmpresa
from src.models.central_integracao import CentralConfiguracao, CentralVinculo, CentralCadastroPendente
from src.routes.central_integracao import register
from src.services.central_assinaturas import cipher, enabled
from src.services.central_empresas import legacy_event, fingerprint


@pytest.fixture
def application():
    app=Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY='local-only', SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False, CENTRAL_SUPPORTED=True)
    db.init_app(app)
    LoginManager(app)
    register(app,'testing')
    with app.app_context():
        db.create_all()
        company=Empresa(id=1,nome='Empresa A',cnpj='12345678000190',plano='premium',usuarios_maximos=7)
        other=Empresa(id=2,nome='Empresa B',cnpj='12345678000191',plano='basic',usuarios_maximos=2)
        db.session.add_all([company,other])
        db.session.flush()
        owner=User(empresa_id=1,username='owner',email='owner@example.com',full_name='Responsável',is_admin=True,is_active=True)
        owner.set_password('never-export-password')
        db.session.add(owner)
        db.session.add(AssinaturaEmpresa(empresa_id=1,plano_codigo='premium',status='suspensa',ciclo_cobranca='mensal',
            data_inicio=date(2024,1,15),data_vencimento=date(2026,12,15),bonus_liberado=False))
        db.session.add(CentralConfiguracao(id=1,base_url='https://central.example.invalid',
            token=cipher().encrypt(b'local-test').decode(),hmac_secret=cipher().encrypt(('h'*40).encode()).decode(),
            ativo=False,cache_ttl=900,purga_habilitada=False))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


def signed(raw, timestamp=None):
    stamp=str(timestamp or int(time.time()))
    return {'X-LiveSun-Timestamp':stamp,'X-LiveSun-Signature':'sha256='+hmac.new(
        ('h'*40).encode(),stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()}


def discovery(client,path='/central/empresas?apos=0'):
    return client.get(path,headers=signed(path.encode()))


def callback(client, data):
    raw=json.dumps(data).encode()
    headers={**signed(raw),'X-LiveSun-Event':'CADASTRO_HABILITADO'}
    return client.post('/central/cadastros/vincular',data=raw,headers=headers,content_type='application/json')


def link_data(item):
    return {'produto':'COMERCIAL','origem_legada':True,'origem_hash':fingerprint(item),
        'empresa_id':1,'cliente_id':123,'assinatura_id':10,'solicitacao_id':7,
        'evento_id':legacy_event(1),'status':'VINCULO_PENDENTE','cnpj_cpf':'12345678000190',
        'entitlements':{'produto':'COMERCIAL','cliente_id':'123','assinatura_id':10,'versao':1,
            'status':'SUSPENSA','plano':'PREMIUM','acesso_produto':False,'limites':{},
            'bonificada':False,'bonificacao_ate':None,
            'valido_ate':(datetime.now(timezone.utc)+timedelta(minutes=15)).isoformat()}}


def test_discovery_before_activation_is_readonly_and_excludes_secrets(application):
    client=application.test_client()
    response=discovery(client)
    assert response.status_code==200
    body=response.get_json()
    assert body['produto']=='COMERCIAL' and len(body['empresas'])==2
    assert body['empresas'][0]['assinatura']['status']=='suspensa'
    assert body['empresas'][0]['dados']['email']=='owner@example.com'
    for secret in ('password_hash','never-export-password','local-test','gateway_subscription_id'):
        assert secret not in response.get_data(as_text=True)
    assert not enabled()
    assert db.session.query(CentralCadastroPendente).count()==db.session.query(CentralVinculo).count()==0


def test_discovery_auth_covers_cursor_and_timestamp(application):
    client=application.test_client()
    assert client.get('/central/empresas?apos=0').status_code==401
    assert client.get('/central/empresas?apos=1',headers=signed(b'/central/empresas?apos=0')).status_code==401
    assert client.get('/central/empresas?apos=0',headers=signed(b'/central/empresas?apos=0',int(time.time())-600)).status_code==401
    assert discovery(client,'/central/empresas?apos=-1').status_code==422
    assert discovery(client,'/central/empresas/999').status_code==404


def test_link_suspended_legacy_before_activation_preserves_local_access_and_is_idempotent(application):
    client=application.test_client()
    item=discovery(client).json['empresas'][0]
    data=link_data(item)
    assert callback(client,data).status_code==200
    assert callback(client,data).status_code==200
    company=db.session.get(Empresa,1)
    assert company.plano=='premium' and company.usuarios_maximos==7
    assert db.session.query(CentralVinculo).one().cliente_id==123
    assert db.session.query(CentralCadastroPendente).one().status=='VINCULADO'
    assert not enabled()


def test_changed_origin_rejects_link(application):
    client=application.test_client()
    data=link_data(discovery(client).json['empresas'][0])
    db.session.get(Empresa,1).usuarios_maximos=9
    db.session.commit()
    assert callback(client,data).status_code==409
    assert db.session.query(CentralVinculo).count()==0


def test_disabled_control_still_rejects_operational_webhook(application):
    client=application.test_client()
    raw=b'{}'
    assert client.post('/webhooks/assinatura',data=raw,headers=signed(raw),content_type='application/json').status_code==503


def test_infinite_courtesy_cannot_be_lost(application):
    legacy=db.session.query(AssinaturaEmpresa).one()
    legacy.bonus_liberado=True
    db.session.commit()
    client=application.test_client()
    data=link_data(discovery(client).json['empresas'][0])
    assert callback(client,data).status_code==409
    assert db.session.query(CentralVinculo).count()==0


@pytest.mark.parametrize('changes', [{'status':'ATIVA','acesso_produto':True}, {'plano':'BASIC'},
    {'valido_ate':(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat()}])
def test_divergent_or_expired_callback_rejected(application, changes):
    client=application.test_client()
    data=link_data(discovery(client).json['empresas'][0])
    data['entitlements'].update(changes)
    assert callback(client,data).status_code==409
    assert db.session.query(CentralVinculo).count()==0


def test_discovery_paginates_without_missing_companies(application):
    for number in range(3,54):
        db.session.add(Empresa(id=number,nome=f'Empresa {number}',plano='premium'))
    db.session.commit()
    client=application.test_client()
    first=discovery(client).json
    assert len(first['empresas'])==50 and first['proximo']==50
    second=discovery(client,'/central/empresas?apos=50').json
    assert [item['dados']['empresa_id'] for item in second['empresas']]==[51,52,53]
    assert second['proximo'] is None


def test_valid_courtesy_callback_does_not_activate_or_change_legacy(application):
    legacy=db.session.query(AssinaturaEmpresa).one()
    legacy.bonus_liberado=True
    legacy.bonus_concedido_em=datetime.now(timezone.utc).replace(tzinfo=None)
    legacy.bonus_dias=20
    db.session.commit()
    client=application.test_client()
    item=discovery(client).json['empresas'][0]
    data=link_data(item)
    data['entitlements'].update(status='ATIVA', acesso_produto=True, limites={'usuarios':7},
        bonificada=True,bonificacao_ate=item['assinatura']['bonificacao_ate'])
    assert callback(client,data).status_code==200
    db.session.refresh(legacy)
    assert legacy.status=='suspensa' and legacy.bonus_dias==20
    assert not enabled()