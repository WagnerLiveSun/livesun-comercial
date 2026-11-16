from datetime import timedelta
from unittest.mock import patch,Mock
import test_central_assinatura_separation as integration_cases
from src.models import db,Empresa,User,AssinaturaEmpresa
from src.models.central_integracao import CentralCadastroPendente,CentralVinculo,CentralConfiguracao,utcnow
from src.services.central_autocadastro import enqueue,send_one,awaits_approval


class AutocadastroTests(integration_cases.CentralIntegrationTests):
    def setUp(self):
        super().setUp()
        db.create_all()

    def enqueue_company(self):
        company=db.session.get(Empresa,2)
        company.cnpj='12345678000190'
        user=User(email='owner@example.com',full_name='Responsável',empresa_id=2)
        row=enqueue(company,user)
        db.session.commit()
        return row

    def test_outbox_contains_no_password_and_does_not_release(self):
        row=self.enqueue_company()
        self.assertEqual(row.status,'PENDENTE_ENVIO')
        self.assertNotIn('senha',row.dados)
        self.assertNotIn('password',row.dados)
        self.assertTrue(awaits_approval(2))
        self.assertIsNone(db.session.get(CentralVinculo,2))

    def test_disabled_central_preserves_legacy_registration(self):
        cfg=db.session.get(CentralConfiguracao,1)
        cfg.ativo=False
        db.session.commit()
        self.assertIsNone(self.enqueue_company())
        self.assertEqual(db.session.query(CentralCadastroPendente).count(),0)
        self.assertFalse(awaits_approval(2))

    def test_missing_configuration_preserves_legacy_registration(self):
        db.session.delete(db.session.get(CentralConfiguracao,1))
        db.session.commit()
        self.assertIsNone(self.enqueue_company())
        self.assertFalse(awaits_approval(2))

    def test_disabled_central_does_not_block_or_send_existing_pending(self):
        row=self.enqueue_company()
        cfg=db.session.get(CentralConfiguracao,1)
        cfg.ativo=False
        db.session.commit()
        with patch('requests.Session.post') as send:
            self.assertFalse(send_one(2))
            send.assert_not_called()
        self.assertFalse(awaits_approval(2))
        self.assertEqual(row.status,'PENDENTE_ENVIO')
        self.assertEqual(row.tentativas,0)

    def test_environment_disabled_overrides_active_database_configuration(self):
        self.app.config.update(CENTRAL_USE_ENV=True,CENTRAL_ENABLED=False,
            CENTRAL_BASE_URL='https://central.example.invalid',CENTRAL_API_TOKEN='test-only',
            CENTRAL_WEBHOOK_SECRET='h'*40,CENTRAL_CACHE_TTL_SECONDS=900)
        self.assertIsNone(self.enqueue_company())
        self.assertFalse(awaits_approval(2))
        with patch('requests.Session.post') as send:
            self.assertFalse(send_one(2))
            send.assert_not_called()

    def test_offline_keeps_outbox_and_retry_is_same_event(self):
        row=self.enqueue_company()
        event=row.evento_id
        with patch('requests.Session.post',side_effect=TimeoutError):
            self.assertTrue(send_one(2))
        self.assertEqual(row.status,'PENDENTE_ENVIO')
        row.proxima_tentativa=utcnow()-timedelta(seconds=1);db.session.commit()
        response=Mock(status_code=202)
        response.json.return_value={'evento_id':event,'empresa_id':2,'produto':'COMERCIAL','solicitacao_id':7,'status':'PENDENTE'}
        with patch('requests.Session.post',return_value=response): self.assertTrue(send_one(2))
        self.assertEqual(row.status,'AGUARDANDO_HABILITACAO')
        self.assertEqual(row.evento_id,event)

    def test_signed_pending_feed_and_approval_callback(self):
        row=self.enqueue_company()
        import hashlib,hmac,time
        path='/central/cadastros-pendentes';stamp=str(int(time.time()))
        sig='sha256='+hmac.new(('h'*40).encode(),stamp.encode()+b'.'+path.encode(),hashlib.sha256).hexdigest()
        response=self.client.get(path,headers={'X-LiveSun-Timestamp':stamp,'X-LiveSun-Signature':sig})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['cadastros'][0]['dados']['evento_id'],row.evento_id)
        data={'evento_id':row.evento_id,'produto':'COMERCIAL','empresa_id':2,'cliente_id':456,
            'solicitacao_id':7,'assinatura_id':10,'status':'VINCULO_PENDENTE',
            'entitlements':{**self.payload,'cliente_id':'456'}}
        response=self.send('/central/cadastros/vincular',data,'CADASTRO_HABILITADO')
        self.assertEqual(response.status_code,200)
        self.assertEqual(db.session.get(CentralVinculo,2).cliente_id,456)
        self.assertEqual(row.status,'VINCULADO')
        self.assertFalse(awaits_approval(2))
        self.assertEqual(self.send('/central/cadastros/vincular',data,'CADASTRO_HABILITADO').status_code,200)