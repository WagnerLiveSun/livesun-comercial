# -*- coding: utf-8 -*-
"""
Valida que os painéis (Gerencial, Comercial, Financeiro, Locação, Propostas e
Fiscal) abrem normalmente mesmo quando o banco NÃO possui as tabelas/colunas
dos módulos (schema desatualizado). Nesse cenário o dashboard deve renderizar
com indicadores zerados (HTTP 200) — sem erro 500 e sem a mensagem de
"banco sem as tabelas/colunas do módulo".
"""
import unittest

from sqlalchemy import inspect, text

from src.app import create_app
from src.models import db, Empresa, User

# Tabelas do núcleo (essenciais para login/permissões) que permanecem no banco.
TABELAS_ESSENCIAIS = {
    'users',
    'empresas',
    'role_permissions',
    'user_permission_overrides',
    'assinatura_empresa',
}

PAINEIS = [
    ('/', 'Painel Gerencial'),
    ('/comercial', 'Painel Comercial'),
    ('/financeiro', 'Painel Financeiro'),
    ('/locacao', 'Painel Locação'),
    ('/propostas', 'Painel Propostas'),
    ('/fiscal', 'Painel Fiscal'),
]


class DashboardSemSchemaTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        db.drop_all()
        db.create_all()

        # Simula banco de produção ANTIGO: remove as tabelas dos módulos,
        # mantendo apenas o núcleo necessário para autenticação/permissoes.
        with db.engine.begin() as conn:
            for tabela in inspect(db.engine).get_table_names():
                if tabela not in TABELAS_ESSENCIAIS:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{tabela}"'))

        empresa = Empresa(nome='Empresa Teste', cnpj='99999999000199', plano='premium')
        db.session.add(empresa)
        db.session.flush()

        cls.user = User(
            empresa_id=empresa.id,
            username='dash_test',
            email='dash_test@test.local',
            full_name='Dash Test',
            is_active=True,
            is_admin=True,
        )
        cls.user.set_password('123456')
        db.session.add(cls.user)
        db.session.commit()

        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.ctx.pop()

    def _login(self):
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)
            sess['_fresh'] = True

    def test_paineis_abrem_sem_tabelas_dos_modulos(self):
        self._login()
        for url, titulo in PAINEIS:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200, f'{url} retornou {resp.status_code}')
                body = resp.get_data(as_text=True)
                self.assertIn(titulo, body)
                self.assertNotIn('banco sem as tabelas', body)

    def test_painel_fiscal_nao_retorna_erro_500(self):
        self._login()
        resp = self.client.get('/fiscal')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Painel Fiscal', resp.get_data(as_text=True))

    def test_painel_comercial_sem_mensagem_de_schema(self):
        self._login()
        resp = self.client.get('/comercial')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn('Painel Comercial', body)
        self.assertNotIn('banco sem as tabelas', body)
        self.assertNotIn('Não foi possível carregar os indicadores comerciais', body)


if __name__ == '__main__':
    unittest.main()