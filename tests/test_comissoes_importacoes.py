import unittest
from datetime import date
from decimal import Decimal
import csv
from io import StringIO

from sqlalchemy import func

from src.app import create_app
from src.models import (
    db,
    Empresa,
    User,
    Entidade,
    FluxoContaModel,
    ContaBanco,
    Lancamento,
    Comissao,
    ParametroSistema,
    ImportacaoNFSe,
)
from src.services.comissoes import ServicoComissoes
from src.routes.importacoes import processar_xml_nfse_completo


class ComissoesImportacoesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        db.drop_all()
        db.create_all()

        cls.empresa = Empresa(nome='Empresa Testes', cnpj='33333333000133')
        db.session.add(cls.empresa)
        db.session.flush()

        cls.vendedor = Entidade(
            empresa_id=cls.empresa.id,
            tipo='V',
            cnpj_cpf='33333333000134',
            nome='Vendedor Teste',
            ativo=True,
        )
        cls.cliente_especifico = Entidade(
            empresa_id=cls.empresa.id,
            tipo='C',
            cnpj_cpf='33333333000135',
            nome='Cliente Especifico',
            ativo=True,
            aliquota_comissao_especifica=Decimal('10.00'),
            valor_repasse=Decimal('50.00'),
        )
        cls.cliente_padrao = Entidade(
            empresa_id=cls.empresa.id,
            tipo='C',
            cnpj_cpf='33333333000136',
            nome='Cliente Padrao',
            ativo=True,
            valor_repasse=Decimal('0.00'),
        )
        db.session.add_all([cls.vendedor, cls.cliente_especifico, cls.cliente_padrao])
        db.session.flush()

        cls.cliente_especifico.vendedor_id = cls.vendedor.id
        cls.cliente_padrao.vendedor_id = cls.vendedor.id

        cls.fluxo = FluxoContaModel(
            empresa_id=cls.empresa.id,
            codigo='1.1.1',
            descricao='Receita de Servicos',
            tipo='R',
            ativo=True,
        )
        db.session.add(cls.fluxo)
        db.session.flush()

        cls.conta_principal = ContaBanco(
            empresa_id=cls.empresa.id,
            nome='Conta Principal',
            banco='Banco Teste',
            agencia='0001',
            numero_conta='12345',
            ativo=True,
            is_principal=True,
            saldo_inicial=0,
            fluxo_conta_id=cls.fluxo.id,
        )
        db.session.add(cls.conta_principal)
        db.session.flush()

        cls.parametro = ParametroSistema(
            empresa_id=cls.empresa.id,
            chave='aliquota_comissao_padrao',
            valor='5.00',
            tipo='numeric',
            descricao='Aliquota padrao de comissao',
        )
        db.session.add(cls.parametro)
        db.session.flush()

        cls.usuario = User(
            empresa_id=cls.empresa.id,
            username='comissoes',
            email='comissoes@test.local',
            full_name='Usuario Comissoes',
            is_active=True,
            is_admin=True,
        )
        cls.usuario.set_password('123456')
        db.session.add(cls.usuario)
        db.session.flush()

        cls.lancamento_especifico = Lancamento(
            empresa_id=cls.empresa.id,
            data_evento=date(2026, 3, 15),
            data_vencimento=date(2026, 3, 20),
            data_pagamento=date(2026, 3, 20),
            status='pago',
            entidade_id=cls.cliente_especifico.id,
            fluxo_conta_id=cls.fluxo.id,
            conta_banco_id=cls.conta_principal.id,
            valor_real=Decimal('1000.00'),
            valor_pago=Decimal('1000.00'),
            valor_imposto=Decimal('100.00'),
            valor_outros_custos=Decimal('50.00'),
            numero_documento='DOC-COM-1',
        )
        cls.lancamento_padrao = Lancamento(
            empresa_id=cls.empresa.id,
            data_evento=date(2026, 3, 16),
            data_vencimento=date(2026, 3, 20),
            data_pagamento=date(2026, 3, 20),
            status='pago',
            entidade_id=cls.cliente_padrao.id,
            fluxo_conta_id=cls.fluxo.id,
            conta_banco_id=cls.conta_principal.id,
            valor_real=Decimal('500.00'),
            valor_pago=Decimal('500.00'),
            valor_imposto=Decimal('0.00'),
            valor_outros_custos=Decimal('0.00'),
            numero_documento='DOC-COM-2',
        )
        db.session.add_all([cls.lancamento_especifico, cls.lancamento_padrao])
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        cls.ctx.pop()

    def setUp(self):
        self.client = self.app.test_client()

    def _login(self):
        response = self.client.post(
            '/auth/login',
            data={
                'empresa_cnpj': self.empresa.cnpj,
                'username': 'comissoes',
                'password': '123456',
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_apuracao_de_comissoes_usa_aliquota_especifica_e_padrao(self):
        resultado = ServicoComissoes.apurar_comissoes(
            self.empresa.id,
            date(2026, 3, 1),
            date(2026, 3, 31),
        )

        self.assertTrue(resultado['sucesso'])
        self.assertEqual(resultado['registros_criados'], 2)
        self.assertEqual(resultado['total_comissoes'], Decimal('105.00'))

        comissao_especifica = Comissao.query.filter_by(
            empresa_id=self.empresa.id,
            lancamento_id=self.lancamento_especifico.id,
        ).one()
        self.assertEqual(Decimal(str(comissao_especifica.aliquota_aplicada)), Decimal('10.00'))
        self.assertEqual(Decimal(str(comissao_especifica.vl_liquido)), Decimal('800.00'))
        self.assertEqual(Decimal(str(comissao_especifica.vl_comissao)), Decimal('80.00'))

        comissao_padrao = Comissao.query.filter_by(
            empresa_id=self.empresa.id,
            lancamento_id=self.lancamento_padrao.id,
        ).one()
        self.assertEqual(Decimal(str(comissao_padrao.aliquota_aplicada)), Decimal('5.00'))
        self.assertEqual(Decimal(str(comissao_padrao.vl_liquido)), Decimal('500.00'))
        self.assertEqual(Decimal(str(comissao_padrao.vl_comissao)), Decimal('25.00'))

        resultado_segunda_apuracao = ServicoComissoes.apurar_comissoes(
            self.empresa.id,
            date(2026, 3, 1),
            date(2026, 3, 31),
        )

        self.assertTrue(resultado_segunda_apuracao['sucesso'])
        self.assertEqual(
            db.session.query(func.count(Comissao.id)).filter_by(empresa_id=self.empresa.id).scalar(),
            2,
        )
        self.assertEqual(
            db.session.query(func.max(Comissao.id_apuracao)).filter_by(empresa_id=self.empresa.id).scalar(),
            2,
        )

    def test_exportacao_csv_de_comissoes_isolada_por_empresa(self):
        self._login()

        ServicoComissoes.apurar_comissoes(
            self.empresa.id,
            date(2026, 3, 1),
            date(2026, 3, 31),
        )

        response = self.client.get('/comissoes/exportar-csv', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        texto = response.data.decode('utf-8-sig')
        linhas = list(csv.reader(StringIO(texto), delimiter=';'))

        self.assertGreaterEqual(len(linhas), 2)
        self.assertEqual(linhas[0], [
            'Vendedor',
            'Quantidade de Lançamentos',
            'Total de Notas',
            'Total de Repasse',
            'Total Líquido',
            'Total de Comissões',
        ])
        self.assertIn('Vendedor Teste', texto)
        self.assertIn('2', texto)
        self.assertIn('105,00', texto)

    def test_exportacao_csv_de_comissoes_filtra_por_data(self):
        self._login()

        ServicoComissoes.apurar_comissoes(
            self.empresa.id,
            date(2026, 3, 1),
            date(2026, 3, 31),
        )

        comissao_abril = Comissao(
            empresa_id=self.empresa.id,
            id_apuracao=99,
            lancamento_id=self.lancamento_padrao.id,
            entidade_cliente_id=self.cliente_padrao.id,
            entidade_vendedor_id=self.vendedor.id,
            dt_lancamento=date(2026, 4, 5),
            dt_vencimento=date(2026, 4, 5),
            dt_pagamento_recebimento=date(2026, 4, 5),
            vl_nota=Decimal('250.00'),
            vl_imposto=Decimal('0.00'),
            vl_outros_custos=Decimal('0.00'),
            vl_repasse=Decimal('0.00'),
            vl_liquido=Decimal('250.00'),
            aliquota_aplicada=Decimal('10.00'),
            vl_comissao=Decimal('7.50'),
            situacao='ativo',
        )
        db.session.add(comissao_abril)
        db.session.commit()

        try:
            response = self.client.get('/comissoes/exportar-csv?data_fim=2026-03-31', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            texto = response.data.decode('utf-8-sig')
            self.assertIn('105,00', texto)
            self.assertNotIn('7,50', texto)

            response_abril = self.client.get('/comissoes/exportar-csv?data_inicio=2026-04-01&data_fim=2026-04-30', follow_redirects=True)
            self.assertEqual(response_abril.status_code, 200)
            texto_abril = response_abril.data.decode('utf-8-sig')
            self.assertIn('7,50', texto_abril)
            self.assertNotIn('105,00', texto_abril)
        finally:
            db.session.delete(comissao_abril)
            db.session.commit()

    def test_processamento_nfse_cria_registros_e_bloqueia_duplicidade(self):
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<root xmlns="http://www.abrasf.org.br/nfse.xsd">'
            '  <infNFSe Id="NFSE-TESTE-001">'
            '    <nNFSe>9001</nNFSe>'
            '    <dhProc>2026-03-18T10:00:00</dhProc>'
            '    <DPS>'
            '      <infDPS>'
            '        <toma><CNPJ>99999999000199</CNPJ></toma>'
            '      </infDPS>'
            '    </DPS>'
            '    <valores><vLiq>1500.00</vLiq></valores>'
            '    <xDescServ>Servico recorrente 6,0</xDescServ>'
            '  </infNFSe>'
            '</root>'
        )

        sucesso, mensagem = processar_xml_nfse_completo(xml, self.empresa.id)

        self.assertTrue(sucesso)
        self.assertIn('Nota importada', mensagem)

        importacao = ImportacaoNFSe.query.filter_by(
            empresa_id=self.empresa.id,
            chave_nota='NFSE-TESTE-001',
        ).one()
        lancamento = Lancamento.query.filter_by(
            empresa_id=self.empresa.id,
            numero_documento='9001',
        ).one()
        entidade = Entidade.query.filter_by(
            empresa_id=self.empresa.id,
            cnpj_cpf='99999999000199',
        ).one()

        self.assertEqual(importacao.entidade_id, entidade.id)
        self.assertEqual(lancamento.entidade_id, entidade.id)
        self.assertEqual(lancamento.fluxo_conta_id, self.fluxo.id)
        self.assertEqual(lancamento.conta_banco_id, self.conta_principal.id)

        sucesso_duplicado, mensagem_duplicada = processar_xml_nfse_completo(xml, self.empresa.id)
        self.assertFalse(sucesso_duplicado)
        self.assertIn('Nota já importada', mensagem_duplicada)
        self.assertEqual(
            db.session.query(func.count(ImportacaoNFSe.id)).filter_by(empresa_id=self.empresa.id).scalar(),
            1,
        )


if __name__ == '__main__':
    unittest.main()