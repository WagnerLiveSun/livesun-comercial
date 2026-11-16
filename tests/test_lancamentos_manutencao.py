"""Regressões de manutenção; banco SQLite exclusivamente em memória."""
import unittest
from datetime import date
from decimal import Decimal
from urllib.parse import quote

# src.app cria também uma instância global na importação. Isolar essa
# inicialização antes do import evita usar o banco configurado no .env.
from config.config import config
config['development'].SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
config['development'].SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
config['development'].ASAAS_ENABLED = False

from src.app import create_app
from src.models import db, Empresa, User, Entidade, FluxoContaModel, ContaBanco, Lancamento


class LancamentosManutencaoTestCase(unittest.TestCase):
    def __getattribute__(self, name):
        models = {'user': User, 'empresa': Empresa, 'entidade': Entidade,
                  'other_entidade': Entidade, 'fluxo': FluxoContaModel,
                  'padrao': FluxoContaModel, 'conta': ContaBanco, 'lancamento': Lancamento}
        ids = object.__getattribute__(self, '__dict__').get('_record_ids', {})
        if name in ids:
            return db.session.get(models[name], ids[name])
        return super().__getattribute__(name)

    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        assert db.engine.url.database in (None, ':memory:') and db.engine.dialect.name == 'sqlite'

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.engine.dispose()
        cls.ctx.pop()

    def setUp(self):
        self._record_ids = {}
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.empresa = Empresa(nome='Teste Manutenção', cnpj='10101010000101', plano='premium')
        other = Empresa(nome='Outra empresa', cnpj='20202020000102', plano='premium')
        db.session.add_all([self.empresa, other])
        db.session.flush()
        self.user = User(empresa_id=self.empresa.id, username='manutencao', email='manutencao@test.local',
                         full_name='Manutenção', is_active=True, is_admin=True, role='admin')
        self.user.set_password('senha-apenas-teste-local')
        self.fluxo = FluxoContaModel(empresa_id=self.empresa.id, codigo='1.1', descricao='Receita salva', tipo='R', ativo=True)
        self.padrao = FluxoContaModel(empresa_id=self.empresa.id, codigo='2.1', descricao='Despesa padrão', tipo='P', ativo=True)
        self.entidade = Entidade(empresa_id=self.empresa.id, nome='Cliente Teste', tipo='C', cnpj_cpf='10101010000103', ativo=True)
        self.other_entidade = Entidade(empresa_id=other.id, nome='Cliente externo', tipo='C', cnpj_cpf='20202020000104', ativo=True)
        db.session.add_all([self.user, self.fluxo, self.padrao, self.entidade, self.other_entidade])
        db.session.flush()
        self.entidade.fluxo_conta_id = self.padrao.id
        self.conta = ContaBanco(empresa_id=self.empresa.id, nome='Banco salvo', banco='Teste', agencia='1', numero_conta='123', ativo=True, saldo_inicial=0)
        db.session.add(self.conta)
        db.session.flush()
        self.lancamento = Lancamento(empresa_id=self.empresa.id, entidade_id=self.entidade.id, fluxo_conta_id=self.fluxo.id,
                                     conta_banco_id=self.conta.id, data_evento=date(2026, 11, 1), data_vencimento=date(2026, 11, 10),
                                     valor_real=Decimal('150.25'), valor_pago=0, status='aberto', numero_documento='DOC-TESTE')
        db.session.add(self.lancamento)
        db.session.commit()
        self._record_ids = {name: getattr(self, name).id for name in (
            'user', 'empresa', 'entidade', 'other_entidade', 'fluxo', 'padrao', 'conta', 'lancamento')}
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session['_user_id'] = str(self.user.id)
            session['_fresh'] = True
        self.edit_url = f'/lancamentos/{self.lancamento.id}/editar'
        self.pay_url = f'/lancamentos/{self.lancamento.id}/pagar'

    def form(self, **changes):
        values = dict(data_evento='2026-11-01', data_vencimento='2026-11-10', entidade_id=str(self.entidade.id),
                      fluxo_conta_id=str(self.fluxo.id), conta_banco_id=str(self.conta.id), valor_real='150.25',
                      valor_imposto='0', valor_outros_custos='0', numero_documento='DOC-EDITADO', observacoes='Alterado',
                      data_pagamento='', valor_pago='')
        values.update(changes)
        return values

    def test_listagem_rolagem_edicao_e_filtro_status(self):
        response = self.client.get('/lancamentos/?status=aberto&tipo=R')
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        for text in ('DOC-TESTE', 'overflow: auto', 'table-layout: fixed', 'Editar', 'Baixar', 'modal-baixa'):
            self.assertIn(text, body)
        self.assertNotIn('overflow-x: hidden', body)
        self.assertNotIn('col-fluxo', body)
        self.assertNotIn('Conta Fluxo</th>', body)
        table_styles = body.split('.ls-card .lancamentos-table {', 1)[1].split('</style>', 1)[0]
        self.assertNotIn('position: sticky', table_styles)

    def test_editar_preserva_conta_e_retorno(self):
        target = '/lancamentos/?status=aberto&tipo=R&page=1'
        response = self.client.post(self.edit_url, data=self.form(next=target))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, target)
        db.session.refresh(self.lancamento)
        self.assertEqual(self.lancamento.numero_documento, 'DOC-EDITADO')
        self.assertEqual(self.lancamento.fluxo_conta_id, self.fluxo.id)

    def test_cadastros_inativos_vinculados_continuam_editaveis(self):
        self.entidade.ativo = self.fluxo.ativo = self.conta.ativo = False
        db.session.commit()
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Banco salvo', response.get_data(as_text=True))
        self.assertEqual(self.client.post(self.edit_url, data=self.form()).status_code, 302)

    def test_baixa_usa_data_valor_e_preserva_filtro(self):
        response = self.client.post(self.pay_url, data=dict(data_pagamento='2026-11-12', valor_pago='155.50', next='/lancamentos/?status=aberto'))
        self.assertEqual(response.location, '/lancamentos/?status=aberto')
        db.session.refresh(self.lancamento)
        self.assertEqual(self.lancamento.data_pagamento, date(2026, 11, 12))
        self.assertEqual(self.lancamento.valor_pago, Decimal('155.50'))
        self.assertEqual(self.lancamento.status, 'pago')

    def test_baixa_duplicada_nao_sobrescreve(self):
        self.client.post(self.pay_url, data={'valor_pago': '151.50', 'data_pagamento': '2026-11-12'})
        self.client.post(self.pay_url, data={'valor_pago': '999', 'data_pagamento': '2026-11-13'})
        db.session.refresh(self.lancamento)
        self.assertEqual(self.lancamento.valor_pago, Decimal('151.50'))
        self.assertEqual(self.lancamento.data_pagamento, date(2026, 11, 12))

    def test_valores_invalidos_nao_baixam(self):
        for value in ('-1', '0', 'NaN', 'Infinity', '1.001', '10000000000000'):
            with self.subTest(value=value):
                self.client.post(self.pay_url, data={'valor_pago': value})
                db.session.refresh(self.lancamento)
                self.assertEqual(self.lancamento.status, 'aberto')

    def test_data_invalida_nao_baixa(self):
        self.client.post(self.pay_url, data={'data_pagamento': '2026-02-30', 'valor_pago': '100'})
        db.session.refresh(self.lancamento)
        self.assertEqual(self.lancamento.status, 'aberto')

    def test_criar_respeita_valor_pago_informado(self):
        response = self.client.post('/lancamentos/novo', data=self.form(data_pagamento='2026-11-12', valor_pago='152.35'))
        self.assertEqual(response.status_code, 302)
        created = Lancamento.query.filter_by(numero_documento='DOC-EDITADO').one()
        self.assertEqual(created.valor_pago, Decimal('152.35'))

    def test_editar_baixa_e_reabrir(self):
        self.client.post(self.edit_url, data=self.form(data_pagamento='2026-11-12', valor_pago='150.25'))
        db.session.refresh(self.lancamento)
        self.assertEqual(self.lancamento.status, 'pago')
        self.client.post(self.edit_url, data=self.form())
        db.session.refresh(self.lancamento)
        self.assertEqual(self.lancamento.status, 'aberto')
        self.assertIsNone(self.lancamento.data_pagamento)
        self.assertEqual(self.lancamento.valor_pago, 0)

    def test_erro_preserva_dados_digitados_sem_salvar(self):
        response = self.client.post(self.edit_url, data=self.form(valor_real='-1', numero_documento='MANTER-DIGITADO'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('MANTER-DIGITADO', response.get_data(as_text=True))
        db.session.refresh(self.lancamento)
        self.assertEqual(self.lancamento.numero_documento, 'DOC-TESTE')

    def test_rejeita_cadastro_de_outra_empresa(self):
        response = self.client.post(self.edit_url, data=self.form(entidade_id=str(self.other_entidade.id)))
        self.assertEqual(response.status_code, 200)
        db.session.refresh(self.lancamento)
        self.assertEqual(self.lancamento.entidade_id, self.entidade.id)

    def test_outra_empresa_nao_acessa_edicao_ou_baixa(self):
        self.user.empresa_id = self.other_entidade.empresa_id
        db.session.commit()
        self.assertEqual(self.client.get(self.edit_url).status_code, 404)
        self.assertEqual(self.client.post(self.pay_url).status_code, 404)

    def test_retorno_externo_rejeitado(self):
        for target in ('https://example.com', '//example.com/lancamentos/', '/outro', '/lancamentos/\\example.com'):
            with self.subTest(target=target):
                response = self.client.get(self.edit_url + '?next=' + quote(target, safe=''))
                self.assertEqual(response.status_code, 200)
                self.assertIn('name="next" value="/lancamentos/"', response.get_data(as_text=True))

    def test_plano_basico_cria_fluxo_padrao(self):
        self.empresa.plano = 'basic'
        db.session.commit()
        response = self.client.post('/lancamentos/novo', data=self.form(tipo_movimentacao='R'))
        self.assertEqual(response.status_code, 302)
        created = Lancamento.query.filter_by(numero_documento='DOC-EDITADO').one()
        self.assertEqual(created.fluxo_conta.codigo, '1')

    def test_csrf_bloqueia_baixa_sem_token(self):
        self.app.config['WTF_CSRF_ENABLED'] = True
        try:
            self.assertEqual(self.client.post(self.pay_url).status_code, 400)
        finally:
            self.app.config['WTF_CSRF_ENABLED'] = False


if __name__ == '__main__':
    unittest.main()