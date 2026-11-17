import base64
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import requests
from flask import Flask

from src.routes.cobrancas_bancarias import cobrancas_bancarias_bp
from src.services.inter_bolepix import InterBolePixError, baixar_bolepix_pdf
from src.services.inter_bolepix_client import InterApiError, InterBolePixClient


PDF_CONTENT = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n'


def make_response(payload, status=200, content_type='application/json'):
    response = requests.Response()
    response.status_code = status
    response.headers['content-type'] = content_type
    response._content = payload if isinstance(payload, bytes) else json.dumps(payload).encode('utf-8')
    return response


class InterBolePixPdfClientTests(unittest.TestCase):
    def setUp(self):
        self.client = InterBolePixClient(
            client_id='test-client',
            client_secret='test-secret',
            certificate_path='test.crt',
            private_key_path='test.key',
            base_url='https://inter.example.invalid/',
            conta_corrente='123456',
        )
        self.client._access_token = 'test-token'

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_decodifica_pdf_do_json_e_envia_conta_corrente(self, get):
        get.return_value = make_response({'pdf': base64.b64encode(PDF_CONTENT).decode('ascii')})

        self.assertEqual(self.client.baixar_pdf('solicitacao-test'), PDF_CONTENT)

        get.assert_called_once_with(
            'https://inter.example.invalid/cobranca/v3/cobrancas/solicitacao-test/pdf',
            headers={
                'accept': 'application/json',
                'Authorization': 'Bearer test-token',
                'x-conta-corrente': '123456',
            },
            cert=('test.crt', 'test.key'),
            timeout=20,
        )

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_preserva_pdf_binario(self, get):
        get.return_value = make_response(PDF_CONTENT, content_type='application/pdf')
        self.assertEqual(self.client.baixar_pdf('test'), PDF_CONTENT)

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_decodifica_json_sem_content_type_correto(self, get):
        get.return_value = make_response(
            {'pdf': base64.b64encode(PDF_CONTENT).decode('ascii')},
            content_type='application/octet-stream',
        )
        self.assertEqual(self.client.baixar_pdf('test'), PDF_CONTENT)

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_aceita_quebras_de_linha_no_base64(self, get):
        get.return_value = make_response({'pdf': base64.encodebytes(PDF_CONTENT).decode('ascii')})
        self.assertEqual(self.client.baixar_pdf('test'), PDF_CONTENT)

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_rejeita_json_sem_pdf(self, get):
        for payload in ({}, {'pdf': None}, {'pdf': ''}, {'pdf': 123}, [], {'pdf': '  '}):
            with self.subTest(payload=payload):
                get.return_value = make_response(payload)
                with self.assertRaisesRegex(InterApiError, 'não retornou o PDF'):
                    self.client.baixar_pdf('test')

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_rejeita_base64_invalido(self, get):
        for encoded in ('%%%invalido', 'abc', 'inválido'):
            with self.subTest(encoded=encoded):
                get.return_value = make_response({'pdf': encoded})
                with self.assertRaisesRegex(InterApiError, 'Base64 inválida'):
                    self.client.baixar_pdf('test')

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_rejeita_base64_que_nao_contem_pdf(self, get):
        get.return_value = make_response({'pdf': base64.b64encode(b'<html>Erro</html>').decode('ascii')})
        with self.assertRaisesRegex(InterApiError, 'PDF válido'):
            self.client.baixar_pdf('test')

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_rejeita_corpo_vazio_html_e_json_malformado(self, get):
        for content in (b'', b'<html>Erro</html>', b'{"pdf":'):
            with self.subTest(content=content):
                get.return_value = make_response(content, content_type='application/pdf')
                with self.assertRaisesRegex(InterApiError, 'PDF válido'):
                    self.client.baixar_pdf('test')

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_erro_http_preserva_mensagem_do_inter(self, get):
        get.return_value = make_response({'detail': 'Cobrança não encontrada'}, status=404)
        with self.assertRaisesRegex(InterApiError, 'Inter PDF 404: Cobrança não encontrada'):
            self.client.baixar_pdf('test')

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_renova_token_uma_vez_apos_401(self, get):
        get.side_effect = [
            make_response({'detail': 'Token expirado'}, status=401),
            make_response({'pdf': base64.b64encode(PDF_CONTENT).decode('ascii')}),
        ]
        with patch.object(self.client, '_request_token', return_value='renewed-token') as renew:
            self.assertEqual(self.client.baixar_pdf('test'), PDF_CONTENT)
        renew.assert_called_once_with()
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args.kwargs['headers']['Authorization'], 'Bearer renewed-token')

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_nao_repete_indefinidamente_apos_401(self, get):
        get.return_value = make_response({'detail': 'Não autorizado'}, status=401)
        with patch.object(self.client, '_request_token', return_value='renewed-token'):
            with self.assertRaisesRegex(InterApiError, 'Inter PDF 401'):
                self.client.baixar_pdf('test')
        self.assertEqual(get.call_count, 2)

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_erro_de_rede_e_tratado_sem_expor_detalhes(self, get):
        for error in (requests.Timeout, requests.ConnectionError):
            with self.subTest(error=error):
                get.side_effect = error('detalhe interno')
                with self.assertRaisesRegex(InterApiError, 'Tente novamente') as raised:
                    self.client.baixar_pdf('test')
                self.assertNotIn('detalhe interno', str(raised.exception))

    @patch('src.services.inter_bolepix_client.requests.post', side_effect=requests.Timeout)
    def test_timeout_na_autenticacao_e_tratado(self, post):
        self.client._access_token = None
        with self.assertRaisesRegex(InterApiError, 'Tente novamente'):
            self.client.baixar_pdf('test')

    @patch('src.services.inter_bolepix_client.requests.get')
    def test_conta_corrente_opcional(self, get):
        self.client.conta_corrente = None
        get.return_value = make_response(PDF_CONTENT, content_type='application/pdf')
        self.assertEqual(self.client.baixar_pdf('test'), PDF_CONTENT)
        self.assertNotIn('x-conta-corrente', get.call_args.kwargs['headers'])


class InterBolePixPdfRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY='test-secret', LOGIN_DISABLED=True)
        self.app.register_blueprint(cobrancas_bancarias_bp)
        self.client = self.app.test_client()

    @patch('src.routes.cobrancas_bancarias.scoped_get_or_404')
    @patch('src.services.inter_bolepix.InterContaConfig')
    @patch('src.services.inter_bolepix._client')
    @patch('src.services.inter_bolepix_client.requests.get')
    def test_rota_entrega_pdf_decodificado(self, get, client_factory, config_model, lookup):
        client = InterBolePixClient('id', 'secret', 'test.crt', 'test.key', 'https://inter.example.invalid')
        client._access_token = 'test-token'
        client_factory.return_value = (client, [])
        lookup.return_value = SimpleNamespace(
            codigo_solicitacao='solicitacao-test', conta_banco_id=1, empresa_id=1,
        )
        get.return_value = make_response({'pdf': base64.b64encode(PDF_CONTENT).decode('ascii')})

        response = self.client.get('/cobrancas-bancarias/inter/2/pdf')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertEqual(response.data, PDF_CONTENT)
        self.assertEqual(response.content_length, len(PDF_CONTENT))
        self.assertIn('inline;', response.headers['Content-Disposition'])

    @patch('src.routes.cobrancas_bancarias.scoped_get_or_404')
    @patch('src.routes.cobrancas_bancarias.baixar_bolepix_pdf')
    def test_rota_redireciona_com_mensagem_em_vez_de_entregar_pdf_invalido(self, download, lookup):
        download.side_effect = InterBolePixError('O Banco Inter não retornou um PDF válido para a cobrança.')
        response = self.client.get('/cobrancas-bancarias/inter/2/pdf')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/cobrancas-bancarias/'))
        with self.client.session_transaction() as session:
            self.assertIn(('danger', str(download.side_effect)), session['_flashes'])

    @patch('src.services.inter_bolepix.os.unlink')
    @patch('src.services.inter_bolepix.InterContaConfig')
    @patch('src.services.inter_bolepix._client')
    def test_servico_converte_erro_e_remove_certificados_temporarios(self, client_factory, config_model, unlink):
        client_factory.return_value = (unittest.mock.Mock(), ['test.crt', 'test.key'])
        client_factory.return_value[0].baixar_pdf.side_effect = InterApiError('PDF inválido')
        cobranca = SimpleNamespace(conta_banco_id=1, empresa_id=1, codigo_solicitacao='test')
        with self.assertRaisesRegex(InterBolePixError, 'PDF inválido'):
            baixar_bolepix_pdf(cobranca)
        self.assertEqual(unlink.call_count, 2)
        unlink.assert_any_call('test.crt')
        unlink.assert_any_call('test.key')


if __name__ == '__main__':
    unittest.main()