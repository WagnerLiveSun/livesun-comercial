"""Integração isolada; nunca inicializa factory ou banco persistente do Comercial."""
import hashlib
import hmac
import json
import time
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
import unittest
from flask import Flask
from flask_login import LoginManager
from src.models import db,Empresa
from src.models.central_integracao import CentralVinculo,CentralConfiguracao,CentralEvento
from src.routes.central_integracao import register,purge_company
from src.services.central_assinaturas import cipher,store,check,enabled


class CentralIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app=Flask(__name__)
        self.app.config.update(SECRET_KEY='test-only',TESTING=True,SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            WTF_CSRF_ENABLED=False,CENTRAL_SUPPORTED=True)
        db.init_app(self.app)
        LoginManager(self.app)
        register(self.app,'testing')
        self.ctx=self.app.app_context(); self.ctx.push()
        # Só as tabelas necessárias: as demais não são importadas para este teste.
        for table in (Empresa.__table__,CentralVinculo.__table__,CentralConfiguracao.__table__,CentralEvento.__table__):
            table.create(db.engine,checkfirst=True)
        db.session.add(Empresa(id=1,nome='Um',cnpj='111',plano='basic',atividade_financeiro=True))
        db.session.add(Empresa(id=2,nome='Dois',cnpj='222',plano='basic'))
        db.session.add(CentralConfiguracao(id=1,base_url='http://127.0.0.1:5001',
            token=cipher().encrypt(b'test').decode(),hmac_secret=cipher().encrypt(('h'*40).encode()).decode(),ativo=True,cache_ttl=900,purga_habilitada=True))
        db.session.add(CentralVinculo(empresa_id=1,cliente_id=123))
        db.session.commit()
        self.payload={'cliente_id':'123','produto':'COMERCIAL','assinatura_id':10,'versao':1,'status':'ATIVA',
            'plano':'PREMIUM','acesso_produto':True,'modulos':[],'limites':{'usuarios':5},
            'gerado_em':datetime.now(timezone.utc).isoformat(),
            'valido_ate':(datetime.now(timezone.utc)+timedelta(minutes=15)).isoformat()}
        self.client=self.app.test_client()

    def tearDown(self):
        db.session.remove(); db.drop_all(); self.ctx.pop()

    def send(self,path,data,event='ASSINATURA_ATIVADA',stamp=None):
        raw=json.dumps(data).encode(); stamp=str(stamp or int(time.time()))
        signature='sha256='+hmac.new(('h'*40).encode(),stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
        return self.client.post(path,data=raw,content_type='application/json',headers={
            'X-LiveSun-Timestamp':stamp,'X-LiveSun-Signature':signature,'X-LiveSun-Event':event})

    def webhook(self,payload=None,event_id='evt_test'):
        state=payload or self.payload
        return self.send('/webhooks/assinatura',{'evento':'ASSINATURA_ATIVADA','evento_id':event_id,
            'produto':'COMERCIAL','cliente_id':'123','assinatura_id':state['assinatura_id'],
            'versao':state['versao'],'status_novo':state['status'],'entitlements':state})

    def test_cache_plan_sync_preserves_modules(self):
        self.assertEqual(self.webhook().status_code,200)
        company=db.session.get(Empresa,1)
        self.assertEqual(company.plano,'premium')
        self.assertTrue(company.atividade_financeiro)
        self.assertEqual(company.usuarios_maximos,5)
        self.assertEqual(check(1)['status'],'ATIVA')
        self.assertEqual(self.webhook().json['status'],'duplicado')

    def test_signature_and_blocking(self):
        self.assertEqual(self.client.post('/webhooks/assinatura',json={}).status_code,401)
        state={**self.payload,'status':'BLOQUEADA','acesso_produto':False}
        self.assertEqual(self.webhook(state).status_code,200)
        from werkzeug.exceptions import Forbidden
        with self.assertRaises(Forbidden): check(1)

    def test_receiver_probe_is_authenticated_product_specific_and_has_no_side_effects(self):
        data={'produto':'COMERCIAL','nonce':'a'*64}
        response=self.send('/webhooks/assinatura',data,'INTEGRACAO_TESTE')
        self.assertEqual(response.status_code,200)
        expected=hmac.new(('h'*40).encode(),('COMERCIAL:'+data['nonce']).encode(),hashlib.sha256).hexdigest()
        self.assertEqual(response.json['prova'],expected)
        self.assertEqual(CentralEvento.query.count(),0)
        self.assertEqual(self.send('/webhooks/assinatura',{**data,'produto':'PROPOSTAS'},'INTEGRACAO_TESTE').status_code,422)
        self.assertEqual(self.client.post('/webhooks/assinatura',json=data,headers={'X-LiveSun-Event':'INTEGRACAO_TESTE'}).status_code,401)

    def test_purge_only_target_company_with_idempotent_receipt(self):
        state={**self.payload,'status':'EXCLUIDA','acesso_produto':False,'versao':2}
        self.assertEqual(self.webhook(state).status_code,200)
        data={'produto':'COMERCIAL','cliente_id':'123','assinatura_id':10,'versao':2,'status':'EXCLUIDA',
            'operacao_id':'prg_test','antecipada':True,'excluida_em':datetime.now(timezone.utc).isoformat()}
        self.assertEqual(self.send('/central/purgar',data,'PURGA_SOLICITADA').status_code,200)
        self.assertIsNone(db.session.get(Empresa,1))
        self.assertIsNotNone(db.session.get(Empresa,2))
        self.assertEqual(self.send('/central/purgar',data,'PURGA_SOLICITADA').status_code,200)

    def test_purge_refuses_active_or_before_retention(self):
        self.assertEqual(self.webhook().status_code,200)
        data={'produto':'COMERCIAL','cliente_id':'123','assinatura_id':10,'versao':1,'status':'EXCLUIDA',
            'operacao_id':'prg_test','antecipada':False,'excluida_em':datetime.now(timezone.utc).isoformat()}
        self.assertEqual(self.send('/central/purgar',data,'PURGA_SOLICITADA').status_code,409)
        self.assertIsNotNone(db.session.get(Empresa,1))

    def test_legacy_subscription_gateway_disabled_without_touching_bank_services(self):
        from src.services.assinatura import ServicoAssinatura
        with self.assertRaises(ValueError):
            ServicoAssinatura.provisionar_gateway_asaas(None)

    def test_existing_bonus_without_central_link_is_preserved(self):
        from src.models import AssinaturaEmpresa
        AssinaturaEmpresa.__table__.create(db.engine,checkfirst=True)
        bonus=AssinaturaEmpresa(empresa_id=2,plano_codigo='basic',status='ativa',bonus_liberado=True,
            bonus_tipo='ilimitado',bonus_motivo='Concessão original',data_inicio=datetime.now().date(),
            data_vencimento=datetime.now().date())
        db.session.add(bonus);db.session.commit()
        with patch('requests.Session.get') as remote:
            result=check(2)
            remote.assert_not_called()
        self.assertTrue(result['bonificada'])
        self.assertTrue(bonus.bonus_liberado)
        self.assertEqual(bonus.bonus_motivo,'Concessão original')

    def test_expired_bonus_is_not_extended(self):
        from src.models import AssinaturaEmpresa
        from werkzeug.exceptions import Forbidden
        AssinaturaEmpresa.__table__.create(db.engine,checkfirst=True)
        bonus=AssinaturaEmpresa(empresa_id=2,plano_codigo='basic',status='ativa',bonus_liberado=True,
            bonus_tipo='trial',bonus_dias=7,bonus_concedido_em=datetime.now()-timedelta(days=30),
            data_inicio=datetime.now().date(),data_vencimento=datetime.now().date())
        db.session.add(bonus);db.session.commit()
        with self.assertRaises(Forbidden): check(2)