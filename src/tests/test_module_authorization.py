"""Autorização local: sem factory de produção, rede ou banco persistente."""

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from flask import Flask
from jinja2 import Environment

from src.access_control import can_access_dashboard
from src.services.authorization import (
    ENDPOINT_ACCESS_RULES, MODULE_LABELS, can_access_endpoint,
    endpoint_is_managed, update_company_modules,
)
from test_contas_banco_access import install_access_hook


SRC = Path(__file__).resolve().parents[1]


class ModuleAuthorizationTestCase(unittest.TestCase):
    def setUp(self):
        self.company = SimpleNamespace(plano='premium', **{
            f'atividade_{key}': True for key in MODULE_LABELS
        })
        self.company.atividade_dashboard = False
        self.user = SimpleNamespace(id=10, empresa_id=1, empresa=self.company,
                                    is_authenticated=True, is_admin=False, role='operator')

    def test_every_managed_route_has_explicit_rule(self):
        for path in (SRC / 'routes').glob('*.py'):
            if path.stem in {'auth', 'admin_comercial', 'comercial'}:
                continue
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and any('.route(' in ast.unparse(d) for d in node.decorator_list):
                    blueprint = {'nfse_financeiro': 'nfse_nacional'}.get(path.stem, path.stem)
                    endpoint = f'{blueprint}.{node.name}'
                    with self.subTest(endpoint=endpoint):
                        self.assertIn(endpoint, ENDPOINT_ACCESS_RULES)

    def test_all_modules_block_admin_and_operator_before_user_permission(self):
        for endpoint, rule in ENDPOINT_ACCESS_RULES.items():
            if not rule.module:
                continue
            for admin in (False, True):
                with self.subTest(endpoint=endpoint, admin=admin):
                    self.user.is_admin = admin
                    setattr(self.company, f'atividade_{rule.module}', False)
                    with patch('src.access_control.has_permission_key', return_value=True) as permission:
                        self.assertFalse(can_access_endpoint(self.user, endpoint))
                        permission.assert_not_called()
                    setattr(self.company, f'atividade_{rule.module}', True)

    def test_function_permission_remains_required(self):
        with patch('src.access_control.has_permission_key', return_value=False):
            for endpoint in ENDPOINT_ACCESS_RULES:
                with self.subTest(endpoint=endpoint):
                    self.assertFalse(can_access_endpoint(self.user, endpoint))

    def test_basic_plan_does_not_allow_intermediate_functions(self):
        self.company.plano = 'basic'
        with patch('src.access_control.has_permission_key', return_value=True):
            for endpoint, rule in ENDPOINT_ACCESS_RULES.items():
                with self.subTest(endpoint=endpoint):
                    self.assertEqual(can_access_endpoint(self.user, endpoint), rule.level == 1)

    def test_allowed_and_dashboard_independent_modules(self):
        with patch('src.access_control.has_permission_key', return_value=True):
            for endpoint in ENDPOINT_ACCESS_RULES:
                self.assertTrue(can_access_endpoint(self.user, endpoint), endpoint)
            for module in MODULE_LABELS:
                setattr(self.company, f'atividade_{module}', False)
            self.assertTrue(can_access_dashboard(self.user, 'dashboard.index'))
            for panel in ('comercial', 'financeiro', 'fiscal', 'locacao', 'propostas'):
                self.assertFalse(can_access_dashboard(self.user, f'dashboard.{panel}'))

    def test_company_context_and_unknown_endpoint_fail_closed(self):
        self.user.empresa_id = None
        with patch('src.access_control.has_permission_key', return_value=True):
            self.assertFalse(can_access_endpoint(self.user, 'contas_banco.index'))
            self.assertFalse(can_access_endpoint(self.user, 'contas_banco.future_action'))
            self.assertTrue(endpoint_is_managed('contas_banco.future_action'))
            self.assertFalse(endpoint_is_managed('admin_comercial.index'))
        self.user.is_authenticated = False
        self.assertFalse(can_access_endpoint(self.user, 'dashboard.index'))

    def test_backoffice_changes_modules_only_and_preserves_functions(self):
        self.company.atividade_contas_banco = False
        self.company.atividade_estoque = True
        self.company.atividade_controle_acesso = False
        update_company_modules(self.company, {'modulo_financeiro': 'on', 'modulo_estoque': 'on'})
        self.assertTrue(self.company.atividade_financeiro)
        self.assertFalse(self.company.atividade_comercial)
        self.assertFalse(self.company.atividade_contas_banco)
        self.assertTrue(self.company.atividade_estoque)
        self.assertFalse(self.company.atividade_controle_acesso)
        self.assertFalse(self.company.atividade_dashboard)
        update_company_modules(self.company, {'modulo_comercial': 'on'})
        self.assertTrue(self.company.atividade_comercial)
        self.assertTrue(self.company.atividade_estoque)

    def test_backoffice_template_has_only_module_selectors(self):
        source = (SRC / 'templates/admin/comercial_panel.html').read_text(encoding='utf-8')
        start = source.index('{% set grupos_modulos = [')
        end = source.index('] %}', start) + 4
        env = Environment()
        template = env.from_string(source[start:end] + '{{ grupos_modulos }}')
        groups = ast.literal_eval(template.render())
        keys = {key for _, items in groups for key, _, _ in items}
        self.assertEqual(keys, set(MODULE_LABELS))
        self.assertNotIn('name="modulo_dashboard"', source)
        self.assertNotIn('name="modulo_entidades" value="on"', source)

    def test_server_denial_stops_read_and_write_business(self):
        app = Flask(__name__)
        app.config.update(SECRET_KEY='local-only', TESTING=True)
        business = Mock(return_value='business')
        app.add_url_rule('/bank', 'contas_banco.index', lambda: business(), methods=['GET', 'POST'])
        app.add_url_rule('/dashboard', 'dashboard.index', lambda: 'home')
        install_access_hook(app)
        with patch('src.core.tenant_context.persist_auth_tenant_session'), \
                patch('src.core.tenant_context.apply_postgres_tenant_context'):
            hook = app.before_request_funcs[None][-1]
            with patch.dict(hook.__globals__, current_user=self.user), \
                    patch('src.models.AssinaturaEmpresa') as subscription, \
                    patch('src.access_control.has_permission_key', return_value=True):
                subscription.query.filter_by.return_value.first.return_value = None
                self.company.atividade_financeiro = False
                for method in ('GET', 'POST'):
                    response = app.test_client().open('/bank', method=method, follow_redirects=True)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, b'home')
                business.assert_not_called()

    def test_dashboard_denial_has_no_redirect_loop(self):
        app = Flask(__name__)
        app.config.update(SECRET_KEY='local-only', TESTING=True)
        business = Mock(return_value='business')
        app.add_url_rule('/', 'dashboard.index', lambda: business())
        install_access_hook(app)
        hook = app.before_request_funcs[None][-1]
        with patch.dict(hook.__globals__, current_user=self.user), \
                patch('src.core.tenant_context.persist_auth_tenant_session'), \
                patch('src.core.tenant_context.apply_postgres_tenant_context'), \
                patch('src.models.AssinaturaEmpresa') as subscription, \
                patch('src.access_control.has_permission_key', return_value=False):
            subscription.query.filter_by.return_value.first.return_value = None
            self.assertEqual(app.test_client().get('/', follow_redirects=True).status_code, 403)
            business.assert_not_called()

    def test_real_sidebar_hides_denied_modules_and_keeps_independent_panels(self):
        source = (SRC / 'templates/layout.html').read_text(encoding='utf-8')
        sidebar = source[source.index('<aside class="ls-sidebar">'):source.index('</aside>') + len('</aside>')]
        template = Environment().from_string(sidebar)
        self.user.full_name = 'Local'
        with patch('src.access_control.has_permission_key', return_value=True):
            def render():
                return template.render(
                    current_user=self.user, request=SimpleNamespace(endpoint='dashboard.index'),
                    can_access_endpoint=lambda endpoint: can_access_endpoint(self.user, endpoint),
                    can_access_dashboard=lambda endpoint: can_access_dashboard(self.user, endpoint),
                    has_activity=lambda key: getattr(self.company, f'atividade_{key}', False),
                    has_permission=lambda key: True,
                    plan_allows_endpoint=lambda endpoint: True,
                    url_for=lambda endpoint: '/' + endpoint,
                    safe_url_for=lambda endpoint: '/' + endpoint,
                )
            self.company.atividade_financeiro = False
            self.company.atividade_comercial = False
            html = render()
            self.assertNotIn('href="/contas_banco.index"', html)
            self.assertNotIn('href="/dashboard.financeiro"', html)
            self.assertNotIn('href="/dashboard.comercial"', html)
            self.assertIn('href="/dashboard.propostas"', html)
            self.assertIn('href="/relatorios_p1.orcamentos"', html)
            self.assertIn('href="/dashboard.index"', html)
            self.company.atividade_propostas = False
            self.assertNotIn('href="/relatorios_p1.orcamentos"', render())

    def test_comercial_menu_group_is_independent_of_fiscal_selector(self):
        source = (SRC / 'templates/layout.html').read_text(encoding='utf-8')
        sidebar = source[source.index('<aside class="ls-sidebar">'):source.index('</aside>') + len('</aside>')]
        template = Environment().from_string(sidebar)
        commercial_heading = '<i class="fas fa-briefcase"></i> Comercial</div>'
        fiscal_heading = '<i class="fas fa-file-invoice"></i> Serviços / Fiscal</div>'
        with patch('src.access_control.has_permission_key', return_value=True):
            for commercial in (False, True):
                for fiscal in (False, True):
                    with self.subTest(commercial=commercial, fiscal=fiscal):
                        self.company.atividade_comercial = commercial
                        self.company.atividade_servicos = fiscal
                        html = template.render(
                            current_user=self.user, request=SimpleNamespace(endpoint='dashboard.index'),
                            can_access_endpoint=lambda endpoint: can_access_endpoint(self.user, endpoint),
                            can_access_dashboard=lambda endpoint: can_access_dashboard(self.user, endpoint),
                            has_activity=lambda key: getattr(self.company, f'atividade_{key}', False),
                            has_permission=lambda key: True,
                            plan_allows_endpoint=lambda endpoint: True,
                            url_for=lambda endpoint: '/' + endpoint,
                            safe_url_for=lambda endpoint: '/' + endpoint,
                        )
                        self.assertEqual(commercial_heading in html, commercial)
                        financial_integration = can_access_endpoint(
                            self.user, 'nfse_nacional.integracao_financeira',
                        )
                        self.assertEqual(fiscal_heading in html, fiscal or financial_integration)
                        self.assertEqual(
                            'href="/nfse_nacional.integracao_financeira"' in html,
                            financial_integration,
                        )
                        self.assertEqual('href="/comercial_operacional.estoque_index"' in html, commercial)
                        self.assertEqual('href="/comercial_operacional.documentos_index"' in html, fiscal)

    def test_general_dashboard_does_not_query_denied_indicators(self):
        tree = ast.parse((SRC / 'routes/dashboard.py').read_text(encoding='utf-8-sig'))
        node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'index')
        node.decorator_list = []
        models = {name: Mock() for name in ('Entidade', 'User', 'Produto', 'Servico', 'AssinaturaEmpresa')}
        self.user.is_admin = False
        render = Mock(return_value='home')
        namespace = dict(models, current_user=self.user, render_template=render,
                         can_access_endpoint=lambda user, endpoint: endpoint == 'dashboard.index')
        from datetime import datetime
        namespace['datetime'] = datetime
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'dashboard.py', 'exec'), namespace)
        self.assertEqual(namespace['index'](), 'home')
        for model in models.values():
            self.assertEqual(model.mock_calls, [])
        self.assertIsNone(render.call_args.kwargs['total_usuarios'])
        self.assertIsNone(render.call_args.kwargs['total_produtos'])

    def test_specific_dashboard_denied_indicators_use_informative_state(self):
        tree = ast.parse((SRC / 'routes/dashboard.py').read_text(encoding='utf-8-sig'))
        node = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'restrict_dashboard_indicators')
        node.decorator_list = []
        render = Mock(return_value='restricted')
        namespace = dict(current_user=self.user, render_template=render,
                         can_access_endpoint=lambda user, endpoint: False)
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'dashboard.py', 'exec'), namespace)
        app = Flask(__name__)
        app.add_url_rule('/financeiro', 'dashboard.financeiro', lambda: 'business')
        with app.test_request_context('/financeiro'):
            self.assertEqual(namespace['restrict_dashboard_indicators'](), 'restricted')
        render.assert_called_once_with('dashboard_restrito.html')


if __name__ == '__main__':
    unittest.main()