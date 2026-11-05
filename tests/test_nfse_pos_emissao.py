import ast
import base64
import gzip
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask
from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader

from src.routes import nfse_nacional as routes
from src.services import nfse_nacional as service
from src.services.nfse_retorno import (
    atualizar_identificadores_nfse, decodificar_xml_nfse, ler_retorno_nfse,
)


CHAVE = "1" * 50
XML = (f'<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse"><infNFSe Id="NFS{CHAVE}">'
       '<nNFSe>12345</nNFSe><cNFSe>987654321</cNFSe></infNFSe></NFSe>')


@pytest.mark.parametrize("namespace", ["http://www.sped.fazenda.gov.br/nfse",
                                        "http://www.abrasf.org.br/nfse", ""])
@pytest.mark.parametrize("formato", ["puro", "base64", "gzip"])
def test_numero_oficial_sem_depender_de_impressao(namespace, formato):
    xml = XML.replace(' xmlns="http://www.sped.fazenda.gov.br/nfse"',
                      f' xmlns="{namespace}"' if namespace else "")
    valor = xml
    if formato == "base64":
        valor = base64.b64encode(xml.encode()).decode()
    elif formato == "gzip":
        valor = base64.b64encode(gzip.compress(xml.encode())).decode()
    dados = ler_retorno_nfse({"response_body": {"nfseXmlGZipB64": valor}})
    assert dados == {"numero_nfse": "12345", "codigo_verificacao": "987654321",
                     "chave_nfse": CHAVE, "xml_nfse": xml}


def test_numero_nao_se_perde_por_falta_de_campos_opcionais():
    xml = '<NFSe><infNFSe><nNFSe>12345</nNFSe></infNFSe></NFSe>'
    assert routes._extrair_identificadores_fiscais_xml(xml)["numero_nfse"] == "12345"
    assert ler_retorno_nfse({"numero_nfse": 12345})["numero_nfse"] == "12345"
    assert ler_retorno_nfse({"numero_nfse": "999"}, XML)["numero_nfse"] == "12345"


@pytest.mark.parametrize("valor", [None, "", "invalido", "<DPS><infDPS/></DPS>",
                                    "<NFSe>", "[]", 123, "H4sIAAAAAAAA/w=="])
def test_nao_confunde_dps_ou_retorno_invalido_com_nfse(valor):
    assert decodificar_xml_nfse(valor) == ""


def test_atualizacao_local_idempotente_preserva_identificador_interno():
    nota = SimpleNamespace(numero_interno="NFSE-1-20261103135901-F2B9C701",
                           numero_nfse=None, xml_nfse=None,
                           payload_retorno=json.dumps({"response_body": {"nfseXml": XML}}))
    assert atualizar_identificadores_nfse(nota)
    assert nota.numero_nfse == "12345"
    assert nota.numero_interno == "NFSE-1-20261103135901-F2B9C701"
    assert not atualizar_identificadores_nfse(nota)


def test_transmissao_unica_devolve_numero_antes_da_impressao(monkeypatch):
    monkeypatch.setattr(service, "validateandsignxml", lambda *a, **k: {"valid": True, "signedxml": "<DPS/>"})
    monkeypatch.setattr(service, "resolve_certificate_settings", lambda **k: (None, None))
    resposta = SimpleNamespace(ok=True, status_code=201, headers={}, text="{}")
    retorno = {"nfseXmlGZipB64": base64.b64encode(gzip.compress(XML.encode())).decode()}
    monkeypatch.setattr(service, "response_payload", lambda r: retorno)
    post = MagicMock(return_value=resposta)
    monkeypatch.setattr(service.requests, "post", post)
    resultado = service.transmitiremissao({"empresa_id": 1, "ambiente": "producao", "xml_dps": "<DPS/>"})
    assert resultado["sucesso"]
    assert resultado["numero_nfse"] == "12345"
    assert resultado["xml_nfse"] == XML
    assert resultado["chave_nfse"] == CHAVE
    post.assert_called_once()


@pytest.fixture
def tela(monkeypatch):
    app = Flask(__name__)
    app.config.update(SECRET_KEY="test", LOGIN_DISABLED=True)
    app.register_blueprint(routes.nfse_nacional_bp)
    raiz = Path(__file__).resolve().parents[1]
    app.jinja_loader = ChoiceLoader([
        DictLoader({"layout.html": "{% block content %}{% endblock %}"}),
        FileSystemLoader(str(raiz / "src/templates")),
    ])
    app.jinja_env.globals.update(csrf_token=lambda: "token", can_access_endpoint=lambda e: True)
    app.jinja_env.filters["numero_nfse"] = lambda valor: str(valor or "")
    empresa = SimpleNamespace(nome="Empresa", nome_fantasia="Empresa", email="empresa@example.com", logo=None)
    nota = SimpleNamespace(
        id=29, empresa_id=1, empresa=empresa, configuracao=None, ambiente="producao",
        situacao_fiscal="AUTORIZADA", status_processamento="PROCESSADA", cancelado_em=None,
        protocolo_cancelamento=None, numero_interno="INTERNO-29", numero_nfse=None,
        chave_nfse=CHAVE, codigo_verificacao=None, xml_nfse=None,
        payload_retorno=json.dumps({"response_body": {"nfseXml": XML}}),
        criado_em=datetime(2026, 11, 3), lancamento=SimpleNamespace(id=40),
        tomador=SimpleNamespace(nome="Cliente", email="cliente@example.com",
                                email_comercial="comercial@example.com", contato_comercial="Maria"),
    )
    monkeypatch.setattr(routes, "scoped_get_or_404", lambda *a: nota)
    monkeypatch.setattr(routes, "_sincronizar_cancelamento_emissao", MagicMock(return_value=False))
    session = MagicMock()
    monkeypatch.setattr(routes, "db", SimpleNamespace(session=session))
    transmitir = MagicMock(side_effect=AssertionError("Não pode retransmitir"))
    consultar = MagicMock(side_effect=AssertionError("Dados locais dispensam consulta"))
    enviar = MagicMock(return_value=True)
    monkeypatch.setattr(routes, "transmitiremissao", transmitir)
    monkeypatch.setattr(routes, "consultar_nfse", consultar)
    monkeypatch.setattr(routes.brevo_service, "send_transactional_email", enviar)
    return SimpleNamespace(app=app, nota=nota, session=session, transmitir=transmitir,
                           consultar=consultar, enviar=enviar)


def test_conclusao_recupera_e_abre_previa_e_email_sem_enviar(tela):
    resposta = tela.app.test_client().get("/nfse-nacional/emissoes/29/conclusao")
    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert "NFS-e 12345" in html
    assert "previa=1" in html
    assert 'name="email_cliente"' in html
    assert "comercial@example.com" in html
    assert "danfse_12345.pdf" in html
    assert "window.print() - test_nfse_pos_emissao.py:127" not in html
    assert tela.nota.numero_nfse == "12345"
    tela.session.commit.assert_called_once()
    tela.enviar.assert_not_called()
    tela.transmitir.assert_not_called()
    tela.consultar.assert_not_called()


def test_recuperacao_de_nota_antiga_nao_reemite(tela):
    resposta = tela.app.test_client().post("/nfse-nacional/emissoes/29/recuperar-dados")
    assert resposta.status_code == 302
    assert resposta.location.endswith("/29/conclusao")
    assert tela.nota.numero_nfse == "12345"
    tela.transmitir.assert_not_called()
    tela.consultar.assert_not_called()


def test_download_pdf_nao_reemite(tela, monkeypatch):
    pdf = MagicMock(return_value=b"%PDF-1.7 teste")
    monkeypatch.setattr(routes, "_gerar_pdf_danfs_emissao", pdf)
    resposta = tela.app.test_client().get("/nfse-nacional/emissoes/29/download/danfs")
    assert resposta.status_code == 200
    assert resposta.mimetype == "application/pdf"
    assert "danfse_12345.pdf" in resposta.headers["Content-Disposition"]
    assert pdf.call_args.args[2]["numero_nfse"] == "12345"
    tela.transmitir.assert_not_called()


def test_previa_nao_dispara_impressora(tela, monkeypatch):
    capturado = {}
    def render(nome, **kw):
        capturado.update(kw)
        return "Prévia"
    monkeypatch.setattr(routes, "render_template", render)
    resposta = tela.app.test_client().get("/nfse-nacional/emissoes/29/imprimir/danfs?previa=1")
    assert resposta.status_code == 200
    assert capturado["auto_imprimir"] is False
    assert capturado["danfse_data"]["numero_nfse"] == "12345"
    tela.transmitir.assert_not_called()


def test_email_recupera_numero_antes_de_assunto_e_anexo(tela, monkeypatch):
    monkeypatch.setattr(routes, "_gerar_pdf_danfs_emissao", lambda *a: b"%PDF teste")
    monkeypatch.setattr(routes, "_construir_html_email", lambda mensagem, empresa: mensagem)
    resposta = tela.app.test_client().post("/nfse-nacional/listagem/29/enviar-email", data={})
    assert resposta.status_code == 302
    assert resposta.location.endswith("/29/conclusao")
    args = tela.enviar.call_args
    assert "12345" in args.args[2]
    assert "12345" in args.args[3]
    assert "INTERNO-29" not in args.args[2]
    assert args.kwargs["attachment"]["name"] == "danfse_12345.pdf"
    assert args.kwargs["cc"] == "empresa@example.com"
    tela.transmitir.assert_not_called()


def test_email_sem_xml_e_cancelada_nao_envia(tela):
    tela.nota.xml_nfse = ""
    tela.nota.payload_retorno = None
    tela.nota.chave_nfse = None
    resposta = tela.app.test_client().post("/nfse-nacional/listagem/29/enviar-email")
    assert resposta.status_code == 302
    tela.nota.situacao_fiscal = "CANCELADA"
    tela.app.test_client().post("/nfse-nacional/listagem/29/enviar-email")
    tela.enviar.assert_not_called()
    tela.transmitir.assert_not_called()


def test_falha_pdf_nao_afeta_autorizacao(tela, monkeypatch):
    monkeypatch.setattr(routes, "_gerar_pdf_danfs_emissao", MagicMock(side_effect=RuntimeError("PDF indisponível")))
    resposta = tela.app.test_client().get("/nfse-nacional/emissoes/29/download/danfs")
    assert resposta.status_code == 302
    assert tela.nota.situacao_fiscal == "AUTORIZADA"
    assert tela.nota.numero_nfse == "12345"
    tela.transmitir.assert_not_called()


def test_novas_rotas_tem_autorizacao_e_template_valido(tela):
    from src.services.authorization import ENDPOINT_ACCESS_RULES
    for endpoint in ("emissao_conclusao", "emissao_download_danfs", "emissao_recuperar_dados"):
        assert ENDPOINT_ACCESS_RULES[f"nfse_nacional.{endpoint}"].permission == "nfse_nacional"
    assert ENDPOINT_ACCESS_RULES["nfse_nacional.recuperar_lancamento"].permission == "lancamentos"
    tela.app.jinja_env.get_template("nfse_nacional/emissao_conclusao.html")
    raiz = Path(__file__).resolve().parents[1]
    tree = ast.parse((raiz / "src/routes/nfse_nacional.py").read_text(encoding="utf-8"))
    chamadas = [(node.name, call.lineno) for node in tree.body if isinstance(node, ast.FunctionDef)
                for call in ast.walk(node) if isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name) and call.func.id == "transmitiremissao"]
    assert len(chamadas) == 1
    assert chamadas[0][0] == "emissoes"