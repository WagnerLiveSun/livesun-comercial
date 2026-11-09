"""Regressão D4: rotas reais e SQLite em memória, sem iniciar a aplicação de produção.

O interceptor é carregado da AST de app.py para evitar os efeitos da factory
(dotenv, logs, diretórios, bootstrap e conexão configurada no ambiente).
"""

import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from flask import Flask, jsonify, redirect, url_for
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from jinja2 import Environment

from src.access_control import current_user_has_permission
from src.models import (
    ContaBanco, Empresa, FluxoContaModel, User, UserPermissionOverride, db,
)
from src.routes.contas_banco import contas_banco_bp
from src.services.planos import normalize_plan, plan_allows_endpoint


SRC = Path(__file__).resolve().parents[1]


def install_access_hook(app):
    """Executa o mapa e as funções reais sem importar/executar a factory."""
    tree = ast.parse((SRC / 'app.py').read_text(encoding='utf-8-sig'))
    factory = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == 'create_app')
    nodes = [next(node for node in tree.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name)
                          and target.id == 'ENDPOINT_PERMISSION_MAP'
                          for target in node.targets))]
    nodes.extend(node for node in factory.body if isinstance(node, ast.FunctionDef)
                 and node.name in {'_user_has_activity', 'enforce_process_permissions'})
    namespace = {
        'app': app, 'current_user': current_user, 'redirect': redirect,
        'url_for': url_for, 'normalize_plan': normalize_plan,
        'plan_allows_endpoint': plan_allows_endpoint,
        'current_user_has_permission': current_user_has_permission,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SRC / 'app.py'), 'exec'), namespace)


class ContasBancoAccessTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True, SECRET_KEY='local-test-only',
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            WTF_CSRF_ENABLED=True,
        )
        db.init_app(self.app)
        CSRFProtect(self.app)
        login = LoginManager(self.app)

        @login.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

        self.app.add_url_rule('/dashboard', 'dashboard.index', lambda: 'dashboard')
        self.app.add_url_rule('/csrf-token', 'csrf_token', lambda: generate_csrf())
        self.app.register_blueprint(contas_banco_bp)
        install_access_hook(self.app)

        # Renderização simplificada: mantém as rotas e as consultas reais.
        self.render = patch('src.routes.contas_banco.render_template', side_effect=self.render_data)
        self.render.start()
        self.addCleanup(self.render.stop)
        with self.app.app_context():
            db.create_all()
            empresa = Empresa(nome='Empresa A', cnpj='11111111000111', plano='premium',
                              atividade_financeiro=True, atividade_contas_banco=True)
            outra = Empresa(nome='Empresa B', cnpj='22222222000122', plano='premium',
                            atividade_financeiro=True, atividade_contas_banco=True)
            db.session.add_all([empresa, outra])
            db.session.flush()
            self.empresa_id = empresa.id
            self.outra_empresa_id = outra.id
            self.users = {}
            for role in ('operator', 'admin', 'viewer'):
                user = User(empresa_id=empresa.id, username=role, email=f'{role}@teste.local',
                            full_name=role, role=role, is_admin=role == 'admin', is_active=True)
                user.set_password('local-test-only')
                db.session.add(user)
                db.session.flush()
                self.users[role] = user.id
            fluxo = FluxoContaModel(empresa_id=empresa.id, codigo='1', descricao='Receita',
                                    tipo='R', ativo=True)
            db.session.add(fluxo)
            db.session.flush()
            self.fluxo_id = fluxo.id
            self.accounts = []
            for owner, name in ((empresa.id, 'Conta A'), (outra.id, 'Conta B')):
                conta = ContaBanco(empresa_id=owner, nome=name, banco='Banco', agencia='1',
                                   numero_conta=str(owner), ativo=True, is_principal=True)
                db.session.add(conta)
                db.session.flush()
                self.accounts.append(conta.id)
            db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    @staticmethod
    def render_data(template, **data):
        if 'contas' in data:
            return jsonify(ids=[conta.id for conta in data['contas']])
        if 'conta' in data:
            return jsonify(id=data['conta'].id)
        return jsonify(template=template)

    def login_as(self, role):
        with self.client.session_transaction() as session:
            session.clear()
            session['_user_id'] = str(self.users[role])
            session['_fresh'] = True

    def set_activities(self, financeiro=True, contas_banco=True):
        with self.app.app_context():
            empresa = db.session.get(Empresa, self.empresa_id)
            empresa.atividade_financeiro = financeiro
            empresa.atividade_contas_banco = contas_banco
            db.session.commit()

    def form(self):
        return dict(nome='Nova Conta', banco='Caixa', agencia='1', numero_conta='123',
                    tipo='Caixa', fluxo_conta_id=str(self.fluxo_id), saldo_inicial='10',
                    ativo='on', csrf_token=self.client.get('/csrf-token').get_data(as_text=True))

    def routes(self):
        conta_id = self.accounts[0]
        return [('GET', '/contas-banco/'), ('GET', '/contas-banco/nova'),
                ('GET', f'/contas-banco/{conta_id}/editar'),
                ('GET', f'/contas-banco/{conta_id}/ver'),
                ('GET', '/contas-banco/api/search?q=Conta'),
                ('POST', '/contas-banco/nova'),
                ('POST', f'/contas-banco/{conta_id}/editar'),
                ('POST', f'/contas-banco/{conta_id}/deletar')]

    def assert_all_routes_blocked(self):
        for method, path in self.routes():
            with self.subTest(method=method, path=path):
                data = self.form() if method == 'POST' else None
                with patch('src.routes.contas_banco.scoped_query') as query, \
                        patch('src.routes.contas_banco.scoped_get_or_404') as get, \
                        patch.object(db.session, 'add') as add, \
                        patch.object(db.session, 'commit') as commit:
                    response = self.client.open(path, method=method, data=data)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response.location, '/dashboard')
                    query.assert_not_called()
                    get.assert_not_called()
                    add.assert_not_called()
                    commit.assert_not_called()
        with self.app.app_context():
            self.assertEqual(ContaBanco.query.count(), 2)
            self.assertEqual(db.session.get(ContaBanco, self.accounts[0]).nome, 'Conta A')
            self.assertTrue(db.session.get(ContaBanco, self.accounts[0]).ativo)

    def test_financeiro_denied_for_operator_and_company_admin(self):
        self.set_activities(financeiro=False)
        for role in ('operator', 'admin'):
            with self.subTest(role=role):
                self.login_as(role)
                self.assert_all_routes_blocked()

    def test_legacy_function_activity_does_not_replace_access_control(self):
        self.set_activities(contas_banco=False)
        for role in ('operator', 'admin'):
            with self.subTest(role=role):
                self.login_as(role)
                self.assertEqual(self.client.get('/contas-banco/').status_code, 200)

    def test_user_permission_denied(self):
        with self.app.app_context():
            db.session.add(UserPermissionOverride(empresa_id=self.empresa_id,
                           user_id=self.users['operator'], permission_key='contas_banco', allowed=False))
            db.session.commit()
        self.login_as('operator')
        self.assert_all_routes_blocked()

    def test_allowed_reads_preserve_filters_and_company_isolation(self):
        for role in ('operator', 'admin'):
            self.login_as(role)
            for method, path in self.routes():
                if method == 'GET':
                    with self.subTest(role=role, path=path):
                        if path.endswith('/ver'):
                            # A ordenação textual preexistente falha no SQLAlchemy
                            # instalado; isolar só a relação, não o lookup por tenant.
                            with patch.object(ContaBanco, 'lancamentos') as lancamentos:
                                lancamentos.order_by.return_value.limit.return_value.all.return_value = []
                                self.assertEqual(self.client.get(path).status_code, 200)
                        else:
                            self.assertEqual(self.client.get(path).status_code, 200)
            self.assertEqual(self.client.get('/contas-banco/').json['ids'], [self.accounts[0]])
            result = self.client.get('/contas-banco/api/search?q=Conta').json
            self.assertEqual([row['id'] for row in result], [self.accounts[0]])
            self.assertEqual(self.client.get('/contas-banco/api/search?q=inexistente').json, [])
            for suffix in ('ver', 'editar'):
                self.assertEqual(self.client.get(f'/contas-banco/{self.accounts[1]}/{suffix}').status_code, 404)
            for suffix in ('editar', 'deletar'):
                response = self.client.post(f'/contas-banco/{self.accounts[1]}/{suffix}', data=self.form())
                self.assertEqual(response.status_code, 404)
        with self.app.app_context():
            outra = db.session.get(ContaBanco, self.accounts[1])
            self.assertEqual(outra.nome, 'Conta B')
            self.assertTrue(outra.ativo)

    def test_allowed_writes_preserve_company_and_previous_behavior(self):
        for role in ('operator', 'admin'):
            self.login_as(role)
            data = self.form()
            data['empresa_id'] = str(self.outra_empresa_id)
            response = self.client.post('/contas-banco/nova', data=data)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/contas-banco/')
            with self.app.app_context():
                conta = ContaBanco.query.filter_by(nome='Nova Conta').one()
                self.assertEqual(conta.empresa_id, self.empresa_id)
                conta_id = conta.id
            data = self.form()
            data['nome'] = f'Editada {role}'
            self.assertEqual(self.client.post(f'/contas-banco/{conta_id}/editar', data=data).status_code, 302)
            with self.app.app_context():
                self.assertEqual(db.session.get(ContaBanco, conta_id).nome, f'Editada {role}')
            self.assertEqual(self.client.post(f'/contas-banco/{conta_id}/deletar', data=self.form()).status_code, 302)
            with self.app.app_context():
                self.assertFalse(db.session.get(ContaBanco, conta_id).ativo)
                self.assertEqual(db.session.get(ContaBanco, conta_id).empresa_id, self.empresa_id)

    def test_csrf_remains_required(self):
        self.login_as('admin')
        with patch.object(db.session, 'commit') as commit:
            self.assertEqual(self.client.post('/contas-banco/nova', data={'nome': 'Sem CSRF'}).status_code, 400)
            commit.assert_not_called()

    def test_viewer_write_restriction_remains(self):
        self.login_as('viewer')
        with patch.object(db.session, 'commit') as commit:
            response = self.client.post(f'/contas-banco/{self.accounts[0]}/deletar', data=self.form())
            self.assertEqual(response.location, '/dashboard')
            commit.assert_not_called()

    def test_plan_denial_still_precedes_business_processing(self):
        self.login_as('admin')
        with patch('src.services.authorization.endpoint_plan_allows', return_value=False):
            self.assert_all_routes_blocked()

    def test_menu_requires_same_activities_permission_and_plan(self):
        source = (SRC / 'templates' / 'layout.html').read_text(encoding='utf-8-sig')
        condition = next(line.strip() for line in source.splitlines()
                         if '{% set show_contas_banco =' in line)
        template = Environment().from_string(condition + '{{ show_contas_banco }}')
        for financeiro, contas, permission, plan, visible in (
            (False, True, True, True, False), (True, False, True, True, True),
            (True, True, False, True, False), (True, True, True, False, False),
            (True, True, True, True, True),
        ):
            with self.subTest(financeiro=financeiro, contas=contas, permission=permission, plan=plan):
                rendered = template.render(
                    can_access_endpoint=lambda endpoint: financeiro and permission and plan,
                    has_activity=lambda key: {'financeiro': financeiro, 'contas_banco': contas}[key],
                    has_permission=lambda key: permission,
                    plan_allows_endpoint=lambda endpoint: plan,
                )
                self.assertEqual(rendered, str(visible))


if __name__ == '__main__':
    unittest.main()