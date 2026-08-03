import unittest
from datetime import date

from src.app import create_app
from src.models import db, Empresa, User, Entidade, FluxoContaModel, ContaBanco, Lancamento
from src.services.conciliacao import criar_conciliacao_ofx, reconciliar_conciliacao


OFX_SAMPLE = """OFXHEADER:100
DATA:OFXSGML
<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS><CODE>0<SEVERITY>INFO</STATUS>
<DTSERVER>20260403000000
<LANGUAGE>POR</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>1
<STATUS><CODE>0<SEVERITY>INFO</STATUS>
<STMTRS>
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260401
<TRNAMT>-150.00
<FITID>OFX-001
<NAME>Fornecedor X
<MEMO>Pagamento teste
</STMTTRN>
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20260402
<TRNAMT>300.00
<FITID>OFX-002
<NAME>Cliente Y
<MEMO>Recebimento teste
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>"""


class ConciliacaoPermissoesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        db.drop_all()
        db.create_all()

        cls.empresa = Empresa(nome='Empresa Conciliacao', cnpj='44444444000144')
        db.session.add(cls.empresa)
        db.session.flush()

        cls.admin = User(empresa_id=cls.empresa.id, username='admin', email='admin@teste.local', full_name='Admin', is_active=True, is_admin=True, role='admin')
        cls.admin.set_password('123456')
        cls.operator = User(empresa_id=cls.empresa.id, username='op', email='op@teste.local', full_name='Operator', is_active=True, is_admin=False, role='operator')
        cls.operator.set_password('123456')
        cls.viewer = User(empresa_id=cls.empresa.id, username='view', email='view@teste.local', full_name='Viewer', is_active=True, is_admin=False, role='viewer')
        cls.viewer.set_password('123456')
        db.session.add_all([cls.admin, cls.operator, cls.viewer])
        db.session.flush()

        cls.vendedor = Entidade(empresa_id=cls.empresa.id, tipo='V', cnpj_cpf='44444444000145', nome='Vendedor', ativo=True)
        cls.cliente = Entidade(empresa_id=cls.empresa.id, tipo='C', cnpj_cpf='44444444000146', nome='Cliente', ativo=True)
        db.session.add_all([cls.vendedor, cls.cliente])
        db.session.flush()
        cls.cliente.vendedor_id = cls.vendedor.id

        cls.fluxo = FluxoContaModel(empresa_id=cls.empresa.id, codigo='1.1', descricao='Receita', tipo='R', ativo=True)
        cls.fluxo_saida = FluxoContaModel(empresa_id=cls.empresa.id, codigo='2.1', descricao='Despesa', tipo='P', ativo=True)
        db.session.add_all([cls.fluxo, cls.fluxo_saida])
        db.session.flush()

        cls.conta = ContaBanco(empresa_id=cls.empresa.id, nome='Conta Principal', banco='Banco Teste', agencia='0001', numero_conta='12345', ativo=True, is_principal=True, fluxo_conta_id=cls.fluxo.id, saldo_inicial=1000)
        db.session.add(cls.conta)
        db.session.flush()

        cls.lancamento_saida = Lancamento(empresa_id=cls.empresa.id, data_evento=date(2026, 4, 1), data_vencimento=date(2026, 4, 1), data_pagamento=None, status='aberto', fluxo_conta_id=cls.fluxo_saida.id, conta_banco_id=cls.conta.id, entidade_id=cls.cliente.id, valor_real=150, valor_pago=0, numero_documento='DOC-SAIDA', observacoes='Pagamento teste')
        cls.lancamento_entrada = Lancamento(empresa_id=cls.empresa.id, data_evento=date(2026, 4, 2), data_vencimento=date(2026, 4, 2), data_pagamento=None, status='aberto', fluxo_conta_id=cls.fluxo.id, conta_banco_id=cls.conta.id, entidade_id=cls.cliente.id, valor_real=300, valor_pago=0, numero_documento='DOC-ENTRADA', observacoes='Recebimento teste')
        db.session.add_all([cls.lancamento_saida, cls.lancamento_entrada])
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.engine.dispose()
        cls.ctx.pop()

    def test_conciliacao_ofx_casa_transacoes(self):
        conciliacao = criar_conciliacao_ofx(self.empresa.id, self.conta.id, OFX_SAMPLE, criado_por_user_id=self.admin.id)
        resultado = reconciliar_conciliacao(conciliacao.id, self.empresa.id)
        self.assertEqual(resultado['conciliados'], 2)
        self.assertEqual(resultado['pendentes'], 0)
        self.assertEqual(resultado['divergentes'], 0)
        self.assertEqual(resultado['status'], 'fechada')

    def test_operator_is_role_allowed(self):
        self.assertEqual(self.operator.role, 'operator')
        self.assertNotEqual(self.viewer.role, 'admin')
