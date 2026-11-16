"""Trial expirado: bloqueio local e liberação após pagamento confirmado."""

from datetime import datetime, timedelta
from decimal import Decimal
import unittest
from unittest.mock import Mock, patch

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_user
from sqlalchemy import func

from src.models import AssinaturaEmpresa, CobrancaRecorrente, db
from src.services.assinatura import ServicoAssinatura
from test_contas_banco_access import install_access_hook
import test_registration_trial as registration
from test_registration_trial import TODAY, load_view


class TrialPaymentGateTestCase(unittest.TestCase):
    setUp = registration.RegistrationTrialTestCase.setUp
    tearDown = registration.RegistrationTrialTestCase.tearDown
    data = registration.RegistrationTrialTestCase.data
    register_company = registration.RegistrationTrialTestCase.register_company
    login_admin = registration.RegistrationTrialTestCase.login_admin

    def expire(self):
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            assinatura.data_fim_trial = TODAY
            assinatura.data_vencimento = TODAY
            assinatura.data_limite_carencia = TODAY + timedelta(days=7)
            db.session.commit()

    def charge(self, assinatura, status='pendente', company_id=None):
        charge = CobrancaRecorrente(
            empresa_id=company_id or assinatura.empresa_id, assinatura_id=assinatura.id,
            referencia_interna=f'test-{status}-{company_id}', competencia_ano=2026,
            competencia_mes=10, valor_previsto=100, status=status, data_vencimento=TODAY,
            data_pagamento=datetime(2026, 10, 26) if status == 'pago' else None,
        )
        db.session.add(charge)
        db.session.flush()
        return charge

    def test_expired_trial_blocks_even_in_grace_or_manually_active(self):
        self.register_company()
        self.expire()
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            self.assertTrue(ServicoAssinatura.exige_pagamento_apos_trial(assinatura))
            assinatura.status = 'ativa'
            assinatura.data_vencimento = TODAY + timedelta(days=30)
            assinatura.bonus_liberado = True
            assinatura.bonus_tipo = 'ilimitado'
            self.assertTrue(ServicoAssinatura.exige_pagamento_apos_trial(assinatura))
            self.charge(assinatura)
            self.assertTrue(ServicoAssinatura.exige_pagamento_apos_trial(assinatura))

    def test_active_trial_does_not_require_payment(self):
        self.register_company()
        with self.app.app_context():
            self.assertFalse(ServicoAssinatura.exige_pagamento_apos_trial(AssinaturaEmpresa.query.one()))

    def test_confirmed_payment_releases_and_is_idempotent(self):
        self.register_company()
        self.expire()
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            charge = self.charge(assinatura)
            self.assertTrue(ServicoAssinatura.exige_pagamento_apos_trial(assinatura))
            ServicoAssinatura.marcar_cobranca_paga(assinatura, charge, None, Decimal('100'))
            db.session.commit()
            self.assertFalse(ServicoAssinatura.exige_pagamento_apos_trial(assinatura))
            deadline = assinatura.data_vencimento
            ServicoAssinatura.marcar_cobranca_paga(assinatura, charge, None, Decimal('100'))
            self.assertEqual(assinatura.data_vencimento, deadline)

    def test_other_company_payment_does_not_release(self):
        self.register_company()
        self.expire()
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            assinatura.data_vencimento = TODAY + timedelta(days=30)
            charge = self.charge(assinatura, status='pago', company_id=999)
            self.assertTrue(ServicoAssinatura.exige_pagamento_apos_trial(assinatura))
            with self.assertRaises(ValueError):
                ServicoAssinatura.marcar_cobranca_paga(assinatura, charge, None, Decimal('100'))

    def test_expired_sessions_redirect_read_write_and_auth_routines(self):
        # Instalar o interceptor antes da primeira requisição.
        business = Mock(return_value='business')
        self.app.add_url_rule('/routine', 'contas_banco.index', lambda: business(), methods=['GET', 'POST'])
        self.app.add_url_rule('/users', 'auth.add_user', lambda: business(), methods=['GET', 'POST'])
        self.app.add_url_rule('/subscription', 'auth.assinatura', lambda: 'subscribe')
        self.app.add_url_rule('/logout', 'auth.logout', lambda: 'logout')
        install_access_hook(self.app)
        self.register_company()
        self.login_admin()
        data = self.data()
        self.expire()
        for path in ('/routine', '/users'):
            for method in ('GET', 'POST'):
                with self.subTest(path=path, method=method):
                    response = self.client.open(path, method=method, data=data, follow_redirects=True)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, b'subscribe')
        business.assert_not_called()
        self.assertEqual(self.client.get('/logout').status_code, 200)

    def test_paid_session_can_execute_routine_again(self):
        self.app.add_url_rule('/routine', 'contas_banco.index', lambda: 'allowed')
        self.app.add_url_rule('/subscription', 'auth.assinatura', lambda: 'subscribe')
        install_access_hook(self.app)
        self.register_company()
        self.login_admin()
        self.expire()
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            charge = self.charge(assinatura)
            ServicoAssinatura.marcar_cobranca_paga(assinatura, charge, None, Decimal('100'))
            db.session.commit()
        self.assertEqual(self.client.get('/routine').data, b'allowed')

    def test_non_admin_subscription_is_informational_and_rejects_post(self):
        render = Mock(return_value='ask company admin')
        namespace = dict(current_user=current_user, request=__import__('flask').request,
                         ServicoAssinatura=ServicoAssinatura, render_template=render)
        view = load_view('routes/auth.py', 'assinatura', namespace)
        self.app.add_url_rule('/subscription', 'auth.assinatura', view, methods=['GET', 'POST'])
        self.register_company()
        self.login_admin()
        self.expire()
        from src.models import User
        with self.app.app_context():
            user = User.query.one()
            user.is_admin = False
            user.role = 'operator'
            db.session.commit()
        self.assertEqual(self.client.get('/subscription').data, b'ask company admin')
        self.assertEqual(self.client.post('/subscription', data=self.data()).status_code, 403)

    def test_gateway_sync_confirmed_payment_activates_subscription(self):
        self.register_company()
        self.expire()
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            assinatura.gateway_subscription_id = 'local-subscription'
            client = Mock()
            client.list_subscription_payments.return_value = [{
                'id': 'local-payment', 'status': 'CONFIRMED', 'value': 100,
                'dueDate': TODAY.isoformat(), 'paymentDate': TODAY.isoformat(),
            }]
            with patch.object(ServicoAssinatura, '_is_asaas_enabled', return_value=True), \
                    patch.object(ServicoAssinatura, '_build_asaas_client', return_value=client):
                ServicoAssinatura.sincronizar_cobranca_pendente_asaas(assinatura)
                db.session.commit()
            self.assertFalse(ServicoAssinatura.exige_pagamento_apos_trial(assinatura))

    def test_login_expired_trial_ignores_next_and_goes_to_subscription(self):
        from src.models import Empresa, User
        from src.core.tenant_context import persist_auth_tenant_session
        namespace = dict(
            current_user=current_user, request=request, redirect=redirect,
            flash=flash, url_for=url_for, User=User, func=func,
            ServicoAssinatura=ServicoAssinatura, login_user=login_user,
            persist_auth_tenant_session=persist_auth_tenant_session,
            _normalize_document=lambda value: ''.join(c for c in value or '' if c.isdigit()),
            _find_empresa_by_document=lambda document: Empresa.query.filter_by(cnpj=document).first(),
        )
        view = load_view('routes/auth.py', 'login', namespace)
        # O endpoint auth.login já existe no aplicativo de teste.
        self.app.view_functions['auth.login'] = view
        self.app.add_url_rule('/login-submit', 'login_submit', view, methods=['POST'])
        self.app.add_url_rule('/subscription', 'auth.assinatura', lambda: 'subscribe')
        self.register_company()
        self.expire()
        response = self.client.post('/login-submit?next=/routine', data=self.data(
            empresa_cnpj='12345678000190', username='owner', password='local-test-only'))
        self.assertEqual(response.location, '/subscription')
        with self.client.session_transaction() as session:
            self.assertIn('_user_id', session)


if __name__ == '__main__':
    unittest.main()