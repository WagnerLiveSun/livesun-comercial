"""Cadastro e trial com SQLite em memória e sem factory/integrações externas."""

import ast
from datetime import date, datetime, timedelta
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from flask import Flask, flash, redirect, request, url_for
from flask_login import LoginManager, current_user, login_required
from flask_wtf.csrf import CSRFProtect, generate_csrf

from src.extensions import require_role
from src.models import AssinaturaEmpresa, Empresa, HistoricoMudancaPlano, User, db
from src.services.assinatura import ServicoAssinatura
from src.services.planos import PLAN_CHOICES, normalize_plan, plan_rank, sync_empresa_modules


SRC = Path(__file__).resolve().parents[1]
TODAY = date(2026, 10, 26)


def load_view(relative_path, name, namespace):
    tree = ast.parse((SRC / relative_path).read_text(encoding='utf-8-sig'))
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    node.decorator_list = []
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SRC / relative_path), 'exec'), namespace)
    return namespace[name]


class RegistrationTrialTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY='local-only',
                               SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
                               SQLALCHEMY_TRACK_MODIFICATIONS=False,
                               ASSINATURA_TRIAL_DIAS=30, WTF_CSRF_ENABLED=True)
        db.init_app(self.app)
        CSRFProtect(self.app)
        manager = LoginManager(self.app)

        @manager.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

        self.app.add_url_rule('/csrf', 'csrf', lambda: generate_csrf())
        self.app.add_url_rule('/auth/login', 'auth.login', lambda: 'login')
        self.app.add_url_rule('/backoffice/comercial/', 'admin_comercial.index', lambda: 'backoffice')
        self.event = Mock()
        self.gate = Mock(return_value=None)
        common = dict(db=db, Empresa=Empresa, User=User, AssinaturaEmpresa=AssinaturaEmpresa,
                      ServicoAssinatura=ServicoAssinatura, request=request, flash=flash,
                      redirect=redirect, url_for=url_for, sync_empresa_modules=sync_empresa_modules,
                      datetime=datetime, timedelta=timedelta, current_user=current_user,
                      PLAN_CHOICES=PLAN_CHOICES, normalize_plan=normalize_plan, plan_rank=plan_rank,
                      HistoricoMudancaPlano=HistoricoMudancaPlano,
                      _require_backoffice_access=self.gate, _registrar_evento=self.event,
                      _normalize_document=lambda value: ''.join(c for c in value or '' if c.isdigit()),
                      FISCAL_TIPO_LABELS={})
        register = load_view('routes/auth.py', 'register', dict(common))
        self.app.add_url_rule('/auth/register', 'auth.register', register, methods=['POST'])
        for name, suffix in (('atualizar_bonus_assinatura', 'bonus'), ('atualizar_plano_assinatura', 'plano')):
            view = load_view('routes/admin_comercial.py', name, dict(common))
            protected = login_required(require_role('admin')(view))
            self.app.add_url_rule('/assinatura/<int:empresa_id>/' + suffix,
                                  'admin_comercial.' + name, protected, methods=['POST'])
        with self.app.app_context():
            db.create_all()
        self.gateway = patch.object(ServicoAssinatura, 'provisionar_gateway_asaas')
        self.gateway_mock = self.gateway.start()
        self.addCleanup(self.gateway.stop)
        self.clock = patch('src.services.assinatura._today', return_value=TODAY)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def data(self, **values):
        values['csrf_token'] = self.client.get('/csrf').get_data(as_text=True)
        return values

    def register_company(self, **overrides):
        data = dict(empresa_nome='Nova Empresa', empresa_cnpj='12345678000190',
                    username='owner', email='owner@teste.local', password='local-test-only',
                    full_name='Owner', plano='premium')
        data.update(overrides)
        return self.client.post('/auth/register', data=self.data(**data))

    def login_admin(self):
        with self.app.app_context():
            user = User.query.filter_by(username='owner').one()
            user_id, empresa_id = user.id, user.empresa_id
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user_id)
            session['_fresh'] = True
        return empresa_id

    def test_register_persists_intermediate_and_seven_day_trial_atomically(self):
        response = self.register_company()
        self.assertEqual(response.location, '/auth/login')
        # Contexto novo: comprova commit, não apenas flush/identity map.
        with self.app.app_context():
            empresa = Empresa.query.one()
            assinatura = AssinaturaEmpresa.query.one()
            self.assertEqual(empresa.plano, 'intermediate')
            self.assertEqual(assinatura.plano_codigo, 'intermediate')
            self.assertEqual(assinatura.status, 'trial')
            self.assertEqual(assinatura.data_inicio, TODAY)
            self.assertEqual(assinatura.data_fim_trial, TODAY + timedelta(days=7))
            self.assertEqual(assinatura.data_vencimento, assinatura.data_fim_trial)
            self.assertTrue(empresa.atividade_financeiro)
            self.assertTrue(empresa.atividade_locacao)
            self.assertEqual(User.query.count(), 1)
        self.gateway_mock.assert_not_called()

    def test_integrated_registration_queues_before_commit_without_local_trial(self):
        from src.models.central_integracao import CentralCadastroPendente, CentralConfiguracao
        self.app.config.update(CENTRAL_RUNTIME_ENV='testing',CENTRAL_SUPPORTED=True)
        with self.app.app_context():
            CentralCadastroPendente.__table__.create(db.engine,checkfirst=True)
            db.session.add(CentralConfiguracao(id=1, base_url='https://central.example.invalid',
                token='test-only', hmac_secret='test-only', ativo=True, cache_ttl=900,
                purga_habilitada=False))
            db.session.commit()
        with patch('src.services.central_autocadastro.notify_after_commit') as notify:
            response=self.register_company()
            self.assertEqual(response.location,'/auth/login')
            notify.assert_called_once()
        with self.app.app_context():
            row=CentralCadastroPendente.query.one()
            self.assertEqual(row.status,'PENDENTE_ENVIO')
            self.assertEqual(row.dados['email'],'owner@teste.local')
            self.assertNotIn('password',row.dados)
            self.assertEqual(AssinaturaEmpresa.query.count(),0)
            self.assertEqual(User.query.count(), 1)
        self.gateway_mock.assert_not_called()

    def test_signature_failure_rolls_back_whole_registration(self):
        with patch.object(ServicoAssinatura, 'obter_ou_criar_assinatura', side_effect=RuntimeError('local failure')):
            response = self.register_company()
        self.assertEqual(response.location, '/auth/register')
        with self.app.app_context():
            self.assertEqual(Empresa.query.count(), 0)
            self.assertEqual(User.query.count(), 0)
            self.assertEqual(AssinaturaEmpresa.query.count(), 0)

    def test_invalid_initial_fiscal_data_rolls_back_registration(self):
        response = self.register_company(fiscal_tipo='invalido', fiscal_valor='123')
        self.assertEqual(response.location, '/auth/register')
        with self.app.app_context():
            self.assertEqual(Empresa.query.count(), 0)
            self.assertEqual(User.query.count(), 0)

    def test_backoffice_can_set_and_change_trial_without_changing_plan(self):
        self.register_company()
        empresa_id = self.login_admin()
        for dias in (14, 3):
            response = self.client.post(f'/assinatura/{empresa_id}/bonus',
                data=self.data(acao='configurar_trial', trial_dias=str(dias)))
            self.assertEqual(response.location, '/backoffice/comercial/')
            with self.app.app_context():
                assinatura = AssinaturaEmpresa.query.one()
                self.assertEqual(assinatura.plano_codigo, 'intermediate')
                self.assertEqual(assinatura.data_fim_trial, TODAY + timedelta(days=dias))
                self.assertEqual(assinatura.data_vencimento, assinatura.data_fim_trial)
                self.assertEqual(assinatura.status, 'trial')
                ServicoAssinatura.obter_ou_criar_assinatura(empresa_id, provisionar_gateway=False)
                self.assertEqual(assinatura.data_fim_trial, TODAY + timedelta(days=dias))
        self.gateway_mock.assert_not_called()

    def test_invalid_trial_does_not_change_saved_deadline(self):
        self.register_company()
        empresa_id = self.login_admin()
        for invalid in ('0', '-1', 'abc', '1.5', '9999999999999999999999'):
            self.client.post(f'/assinatura/{empresa_id}/bonus',
                             data=self.data(acao='configurar_trial', trial_dias=invalid))
            with self.app.app_context():
                self.assertEqual(AssinaturaEmpresa.query.one().data_fim_trial, TODAY + timedelta(days=7))

    def test_backoffice_can_grant_trial_without_previous_signature(self):
        self.register_company()
        empresa_id = self.login_admin()
        with self.app.app_context():
            db.session.delete(AssinaturaEmpresa.query.one())
            db.session.commit()
        self.client.post(f'/assinatura/{empresa_id}/bonus',
                         data=self.data(acao='configurar_trial', trial_dias='10'))
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            self.assertEqual(assinatura.plano_codigo, 'intermediate')
            self.assertEqual(assinatura.data_fim_trial, TODAY + timedelta(days=10))

    def test_plan_change_updates_company_and_preserves_trial(self):
        self.register_company()
        empresa_id = self.login_admin()
        self.client.post(f'/assinatura/{empresa_id}/plano', data=self.data(novo_plano='basic'))
        with self.app.app_context():
            self.assertEqual(Empresa.query.one().plano, 'basic')
            assinatura = AssinaturaEmpresa.query.one()
            self.assertEqual(assinatura.plano_codigo, 'basic')
            self.assertEqual(assinatura.data_fim_trial, TODAY + timedelta(days=7))
            self.assertEqual(HistoricoMudancaPlano.query.count(), 1)

    def test_plan_change_without_signature_is_persisted(self):
        self.register_company()
        empresa_id = self.login_admin()
        with self.app.app_context():
            db.session.delete(AssinaturaEmpresa.query.one())
            db.session.commit()
        self.client.post(f'/assinatura/{empresa_id}/plano', data=self.data(novo_plano='premium'))
        with self.app.app_context():
            self.assertEqual(Empresa.query.one().plano, 'premium')
            self.assertEqual(AssinaturaEmpresa.query.one().plano_codigo, 'premium')

    def test_csrf_and_backoffice_gate_remain_required(self):
        self.register_company()
        empresa_id = self.login_admin()
        self.assertEqual(self.client.post(f'/assinatura/{empresa_id}/bonus',
                         data={'acao': 'configurar_trial', 'trial_dias': '14'}).status_code, 400)
        self.gate.return_value = ('denied', 403)
        response = self.client.post(f'/assinatura/{empresa_id}/bonus',
                                   data=self.data(acao='configurar_trial', trial_dias='14'))
        self.assertEqual(response.status_code, 403)
        with self.app.app_context():
            self.assertEqual(AssinaturaEmpresa.query.one().data_fim_trial, TODAY + timedelta(days=7))

    def test_trial_does_not_reactivate_deleted_company(self):
        self.register_company()
        empresa_id = self.login_admin()
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            assinatura.status = 'excluida'
            db.session.commit()
        self.client.post(f'/assinatura/{empresa_id}/bonus',
                         data=self.data(acao='configurar_trial', trial_dias='14'))
        with self.app.app_context():
            self.assertEqual(AssinaturaEmpresa.query.one().status, 'excluida')

    def test_non_admin_cannot_change_trial(self):
        self.register_company()
        empresa_id = self.login_admin()
        with self.app.app_context():
            user = User.query.one()
            user.role = 'operator'
            user.is_admin = False
            db.session.commit()
        response = self.client.post(f'/assinatura/{empresa_id}/bonus',
                                   data=self.data(acao='configurar_trial', trial_dias='14'))
        self.assertEqual(response.status_code, 302)
        self.gate.assert_not_called()
        with self.app.app_context():
            self.assertEqual(AssinaturaEmpresa.query.one().data_fim_trial, TODAY + timedelta(days=7))

    def test_repeated_signature_lookup_does_not_duplicate_subscription(self):
        self.register_company()
        empresa_id = self.login_admin()
        with self.app.app_context():
            first = ServicoAssinatura.obter_ou_criar_assinatura(empresa_id, provisionar_gateway=False)
            second = ServicoAssinatura.obter_ou_criar_assinatura(empresa_id, provisionar_gateway=False)
            self.assertEqual(first.id, second.id)
            self.assertEqual(AssinaturaEmpresa.query.count(), 1)

    def test_finite_trial_replaces_unlimited_bonus(self):
        self.register_company()
        empresa_id = self.login_admin()
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            assinatura.bonus_liberado = True
            assinatura.bonus_tipo = 'ilimitado'
            assinatura.bonus_concedido_em = datetime.now()
            db.session.commit()
        self.client.post(f'/assinatura/{empresa_id}/bonus',
                         data=self.data(acao='configurar_trial', trial_dias='7'))
        with self.app.app_context():
            assinatura = AssinaturaEmpresa.query.one()
            self.assertFalse(assinatura.bonus_liberado)
            self.assertIsNone(assinatura.bonus_tipo)
            self.assertEqual(assinatura.data_fim_trial, TODAY + timedelta(days=7))


if __name__ == '__main__':
    unittest.main()