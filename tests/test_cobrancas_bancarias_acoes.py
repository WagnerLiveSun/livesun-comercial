import base64
import json
import unittest
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from flask import Flask

from src.routes.asaas_boleto import asaas_boleto_bp
from src.routes.cobrancas_bancarias import cobrancas_bancarias_bp
from src.routes.inter_bolepix import inter_bolepix_bp
from src.services.asaas_boleto import AsaasBoletoError
from src.services.brevo import BrevoService
from src.services.inter_bolepix import InterBolePixError
from src.services.inter_bolepix_client import InterBolePixClient


PDF = b'%PDF-1.4\n%%EOF\n'


class CobrancasBancariasAcoesTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY='test-secret', LOGIN_DISABLED=True)
        self.app.register_blueprint(cobrancas_bancarias_bp)
        self.app.register_blueprint(inter_bolepix_bp)
        self.app.register_blueprint(asaas_boleto_bp)
        self.client = self.app.test_client()
        self.cobranca = SimpleNamespace(
            id=2, codigo_solicitacao='solicitacao-test', seu_numero='DOC-248',
            conta_banco_id=1, empresa_id=1, valor=Decimal('100.00'),
            data_vencimento=date(2026, 12, 10), status_interno='pendente',
            linha_digitavel='123', codigo_barras='456', qr_code='pix', pdf_url=None,
            lancamento=SimpleNamespace(entidade=SimpleNamespace(nome='Cliente', email='cliente@example.com')),
        )
        self.empresa = SimpleNamespace(nome='Empresa', nome_fantasia=None, email='empresa@example.com')

    def flashes(self):
        with self.client.session_transaction() as session:
            return session.get('_flashes', [])

    @patch('src.routes.inter_bolepix.scoped_get_or_404')
    @patch('src.routes.inter_bolepix.gerar_bolepix')
    def test_botao_inter_redireciona_com_sucesso(self, generate, lookup):
        generate.return_value = self.cobranca
        response = self.client.post('/inter-bolepix/lancamentos/248/gerar', data={'retorno': 'pagina'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/cobrancas-bancarias/'))
        generate.assert_called_once_with(lookup.return_value)
        self.assertEqual(self.flashes()[0][0], 'success')

    @patch('src.routes.inter_bolepix.scoped_get_or_404')
    @patch('src.routes.inter_bolepix.gerar_bolepix')
    def test_erro_no_botao_inter_e_exibido_na_pagina(self, generate, lookup):
        generate.side_effect = InterBolePixError('Este lançamento já possui uma cobrança Inter ativa.')
        response = self.client.post('/inter-bolepix/lancamentos/248/gerar', headers={'Accept': 'text/html'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(('danger', str(generate.side_effect)), self.flashes())

    @patch('src.routes.inter_bolepix.scoped_get_or_404')
    @patch('src.routes.inter_bolepix.gerar_bolepix')
    def test_integracao_inter_preserva_json(self, generate, lookup):
        generate.return_value = self.cobranca
        response = self.client.post('/inter-bolepix/lancamentos/248/gerar', json={})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json['sucesso'])
        self.assertEqual(response.json['cobranca_id'], 2)
        generate.side_effect = InterBolePixError('Conta não habilitada')
        response = self.client.post('/inter-bolepix/lancamentos/248/gerar', json={})
        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.json['sucesso'])

    @patch('src.routes.inter_bolepix.gerar_bolepix')
    def test_get_nao_emite_cobranca(self, generate):
        response = self.client.get('/inter-bolepix/lancamentos/248/gerar')
        self.assertEqual(response.status_code, 405)
        generate.assert_not_called()

    @patch('src.routes.asaas_boleto.scoped_get_or_404')
    @patch('src.routes.asaas_boleto.gerar_boleto')
    def test_botao_asaas_e_json_continuam_funcionais(self, generate, lookup):
        generate.return_value = SimpleNamespace(
            id=3, asaas_payment_id='pay-test', status_interno='pendente',
            invoice_url='https://example.invalid/invoice', bank_slip_url=None, identification_field='123',
        )
        url = '/asaas-boletos/lancamentos/248/gerar'
        response = self.client.post(url, data={'retorno': 'pagina'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.flashes()[0][0], 'success')
        response = self.client.post(url, json={})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['payment_id'], 'pay-test')
        generate.side_effect = AsaasBoletoError('Erro Asaas')
        self.assertEqual(self.client.post(url, data={'retorno': 'pagina'}).status_code, 302)
        self.assertEqual(self.client.post(url, json={}).status_code, 422)

    @patch('src.routes.cobrancas_bancarias.current_user')
    @patch('src.routes.cobrancas_bancarias.scoped_get_or_404')
    @patch('src.services.inter_bolepix.InterContaConfig')
    @patch('src.services.inter_bolepix._client')
    @patch('src.services.inter_bolepix_client.requests.get')
    @patch('src.services.brevo.requests.post')
    def test_email_individual_envia_pdf_decodificado_ao_brevo(self, post, get, factory, config, lookup, user):
        user.empresa = self.empresa
        lookup.return_value = self.cobranca
        inter = InterBolePixClient('id', 'secret', 'test.crt', 'test.key', 'https://inter.example.invalid')
        inter._access_token = 'test-token'
        factory.return_value = (inter, [])
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps({'pdf': base64.b64encode(PDF).decode('ascii')}).encode()
        get.return_value = response
        post.return_value = Mock(status_code=201)
        brevo = BrevoService()
        brevo.api_key = 'test-only'
        with patch('src.routes.cobrancas_bancarias.brevo_service', brevo):
            response = self.client.post('/cobrancas-bancarias/inter/2/enviar-email')
        self.assertEqual(response.status_code, 302)
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['to'][0]['email'], 'cliente@example.com')
        self.assertEqual(base64.b64decode(payload['attachment'][0]['content']), PDF)
        self.assertEqual(payload['attachment'][0]['name'], 'bolepix_solicitacao-test.pdf')
        self.assertEqual(self.flashes()[0][0], 'success')

    @patch('src.routes.cobrancas_bancarias.current_user')
    @patch('src.routes.cobrancas_bancarias.scoped_get_or_404')
    @patch('src.routes.cobrancas_bancarias.baixar_bolepix_pdf')
    @patch('src.routes.cobrancas_bancarias.brevo_service.send_transactional_email')
    def test_email_individual_nao_envia_se_pdf_falhar(self, send, download, lookup, user):
        user.empresa = self.empresa
        lookup.return_value = self.cobranca
        download.side_effect = InterBolePixError('PDF inválido')
        response = self.client.post('/cobrancas-bancarias/inter/2/enviar-email')
        self.assertEqual(response.status_code, 302)
        send.assert_not_called()
        self.assertIn(('danger', 'PDF inválido'), self.flashes())

    @patch('src.routes.cobrancas_bancarias.current_user')
    @patch('src.routes.cobrancas_bancarias.scoped_get_or_404')
    @patch('src.routes.cobrancas_bancarias.baixar_bolepix_pdf', return_value=PDF)
    @patch('src.routes.cobrancas_bancarias.brevo_service.send_transactional_email', return_value=False)
    def test_email_individual_informa_rejeicao_brevo(self, send, download, lookup, user):
        user.empresa = self.empresa
        lookup.return_value = self.cobranca
        self.client.post('/cobrancas-bancarias/inter/2/enviar-email')
        self.assertEqual(self.flashes()[0][0], 'danger')

    def query_lote(self, model):
        from src.models import InterCobranca
        query = Mock()
        query.filter.return_value.all.return_value = [self.cobranca] if model is InterCobranca else []
        return query

    @patch('src.routes.cobrancas_bancarias.current_user')
    @patch('src.routes.cobrancas_bancarias.scoped_query')
    @patch('src.routes.cobrancas_bancarias.baixar_bolepix_pdf', return_value=PDF)
    @patch('src.routes.cobrancas_bancarias.brevo_service.send_transactional_email', return_value=True)
    def test_lote_inter_sem_campos_asaas_envia_anexo(self, send, download, query, user):
        user.empresa = self.empresa
        query.side_effect = self.query_lote
        response = self.client.post('/cobrancas-bancarias/enviar-email-lote', data={'cobranca_ids': ['inter:2']})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(send.call_args.kwargs['attachment']['content'], PDF)
        self.assertEqual(self.flashes()[0][0], 'success')

    @patch('src.routes.cobrancas_bancarias.current_user')
    @patch('src.routes.cobrancas_bancarias.scoped_query')
    @patch('src.routes.cobrancas_bancarias.baixar_bolepix_pdf', return_value=PDF)
    @patch('src.routes.cobrancas_bancarias.brevo_service.send_transactional_email', return_value=True)
    def test_lote_misto_preserva_link_asaas_e_anexo_inter(self, send, download, query, user):
        user.empresa = self.empresa
        from src.models import AsaasCobranca
        asaas = SimpleNamespace(
            lancamento=self.cobranca.lancamento, bank_slip_url='https://example.invalid/boleto',
            invoice_url=None, valor=self.cobranca.valor, data_vencimento=self.cobranca.data_vencimento,
        )
        def rows(model):
            result = Mock()
            result.filter.return_value.all.return_value = [asaas] if model is AsaasCobranca else [self.cobranca]
            return result
        query.side_effect = rows
        response = self.client.post(
            '/cobrancas-bancarias/enviar-email-lote', data={'cobranca_ids': ['asaas:3', 'inter:2']},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(send.call_count, 2)
        self.assertIn('https://example.invalid/boleto', send.call_args_list[0].args[3])
        self.assertIsNone(send.call_args_list[0].kwargs['attachment'])
        self.assertEqual(send.call_args_list[1].kwargs['attachment']['content'], PDF)

    @patch('src.routes.cobrancas_bancarias.current_user')
    @patch('src.routes.cobrancas_bancarias.scoped_query')
    @patch('src.routes.cobrancas_bancarias.baixar_bolepix_pdf')
    @patch('src.routes.cobrancas_bancarias.brevo_service.send_transactional_email')
    def test_lote_inter_sem_email_nao_envia(self, send, download, query, user):
        user.empresa = self.empresa
        query.side_effect = self.query_lote
        self.cobranca.lancamento.entidade.email = None
        response = self.client.post('/cobrancas-bancarias/enviar-email-lote', data={'cobranca_ids': ['inter:2']})
        self.assertEqual(response.status_code, 302)
        send.assert_not_called()
        download.assert_not_called()
        self.assertEqual(self.flashes()[0][0], 'warning')

    @patch('src.routes.cobrancas_bancarias.current_user')
    @patch('src.routes.cobrancas_bancarias.scoped_query')
    @patch('src.routes.cobrancas_bancarias.baixar_bolepix_pdf', side_effect=InterBolePixError('PDF inválido'))
    @patch('src.routes.cobrancas_bancarias.brevo_service.send_transactional_email')
    def test_lote_inter_com_pdf_invalido_nao_envia(self, send, download, query, user):
        user.empresa = self.empresa
        query.side_effect = self.query_lote
        response = self.client.post('/cobrancas-bancarias/enviar-email-lote', data={'cobranca_ids': ['inter:2']})
        self.assertEqual(response.status_code, 302)
        send.assert_not_called()
        self.assertEqual(self.flashes()[0][0], 'warning')


if __name__ == '__main__':
    unittest.main()