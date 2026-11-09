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
    validar = MagicMock(return_value={"valid": True, "signedxml": "<DPS/>"})
    monkeypatch.setattr(service, "validateandsignxml", validar)
    monkeypatch.setattr(service, "builddpsxml", lambda *a, **k: pytest.fail("A DPS gravada não deve ser reconstruída"))
    monkeypatch.setattr(service, "resolve_certificate_settings", lambda **k: (None, None))
    monkeypatch.setattr(
        service,
        "get_base_distribuicao",
        lambda **k: pytest.fail("A emissão não deve resolver o endpoint de distribuição"),
    )
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
    assert "base_distribuicao" not in resultado["payload_retorno"]
    assert validar.call_args.args[0] == "<DPS/>"
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


def test_template_real_do_danfse_na_previa_e_impressao(tela):
    tela.app.jinja_env.globals["get_empresa_logo"] = lambda empresa: ""
    tela.app.jinja_env.filters.update(documento=lambda valor: str(valor or ""),
                                     brl=lambda valor: str(valor or 0))
    tela.nota.valor_servico = 150
    tela.nota.valor_deducoes = 0
    tela.nota.valor_iss = 5
    tela.nota.observacoes = "Serviço de teste"
    cliente = tela.app.test_client()
    previa = cliente.get("/nfse-nacional/emissoes/29/imprimir/danfs?previa=1")
    assert previa.status_code == 200
    assert "12345" in previa.get_data(as_text=True)
    assert "window.print()" not in previa.get_data(as_text=True)
    assert tela.nota.numero_nfse == "12345"
    tela.session.commit.assert_called_once()
    impressao = cliente.get("/nfse-nacional/emissoes/29/imprimir/danfs")
    assert impressao.status_code == 200
    assert "12345" in impressao.get_data(as_text=True)
    assert "window.print()" in impressao.get_data(as_text=True)
    tela.transmitir.assert_not_called()


@pytest.mark.parametrize("fonte", ["payload", "api"])
def test_download_xml_recupera_e_persiste_numero_oficial(tela, fonte):
    if fonte == "api":
        tela.nota.payload_retorno = None
        tela.consultar.side_effect = None
        tela.consultar.return_value = {"sucesso": True, "xml_nfse": XML}
    resposta = tela.app.test_client().get("/nfse-nacional/emissoes/29/download/nfse")
    assert resposta.status_code == 200
    assert resposta.get_data(as_text=True) == XML
    assert "nfse_12345.xml" in resposta.headers["Content-Disposition"]
    assert tela.nota.numero_nfse == "12345"
    assert tela.nota.xml_nfse == XML
    tela.session.commit.assert_called_once()
    tela.transmitir.assert_not_called()
    if fonte == "api":
        tela.consultar.assert_called_once()
    else:
        tela.consultar.assert_not_called()


def test_build_payload_preserva_datas_informadas(monkeypatch):
    empresa = SimpleNamespace(
        id=1, nome="Empresa", cnpj="12345678000199", codigo_municipio_ibge=None,
        endereco_cidade="Rio de Janeiro", endereco_uf="RJ", endereco_rua="Rua A",
        endereco_numero="10", endereco_bairro="Centro", endereco_cep="20000000",
    )
    configuracao = SimpleNamespace(ambiente="producao", versao_layout="1.00", inscricao_municipal="123")
    tomador = SimpleNamespace(id=10, nome="Cliente", cnpj_cpf="123", tipo="PF")
    servico = SimpleNamespace(id=20, codigo_interno="SERV", codigo_servico="170201",
                              nbs="", descricao="Serviço")
    gerar_xml = MagicMock(return_value="<DPS/>")
    monkeypatch.setattr(routes, "builddpsxml", gerar_xml)
    payload = routes._build_payload(
        empresa, configuracao, tomador, servico,
        {"valor_servico": "150", "data_emissao": "2026-11-03", "data_vencimento": "2026-11-30"},
        "INTERNO-29", "hash-29",
    )
    assert payload["data_emissao"] == "2026-11-03"
    assert payload["data_vencimento"] == "2026-11-30"
    assert gerar_xml.call_args.args[0]["data_emissao"] == "2026-11-03"


@pytest.fixture
def fluxo_emissao(monkeypatch):
    from src.services import nfse_financeiro

    app = Flask(__name__)
    app.config.update(SECRET_KEY="test", LOGIN_DISABLED=True)
    app.register_blueprint(routes.nfse_nacional_bp)
    empresa = SimpleNamespace(id=1)
    config = SimpleNamespace(ambiente="producao", versao_layout="1.00")
    tomador = SimpleNamespace(id=10, cnpj_cpf="123", fluxo_conta_id=2)
    servico = SimpleNamespace(id=20, codigo_interno="SERV", codigo_servico="170201", nbs="", descricao="Serviço")
    monkeypatch.setattr(routes, "Empresa", SimpleNamespace(query=SimpleNamespace(get_or_404=lambda _: empresa)))
    config_model = MagicMock()
    config_model.query.filter_by.return_value.first.return_value = config
    monkeypatch.setattr(routes, "NfseNacionalConfiguracao", config_model)
    monkeypatch.setattr(routes, "tenant_id", lambda: 1)
    monkeypatch.setattr(routes, "current_user", SimpleNamespace(id=7))
    monkeypatch.setattr(routes, "_get_or_create_config", lambda *a: config)
    monkeypatch.setattr(routes, "_get_or_create_tomador", lambda *a: tomador)
    monkeypatch.setattr(routes, "_get_or_create_servico", lambda *a: servico)
    monkeypatch.setattr(routes, "_campos_obrigatorios_tomador_nfse", lambda *a: [])
    monkeypatch.setattr(routes, "resolve_xsd_path", lambda *a, **k: "test.xsd")
    monkeypatch.setattr(routes, "_validar_emissao_nfse", lambda *a: (True, ""))
    monkeypatch.setattr(routes, "_ensure_integration_origin", lambda *a: None)
    monkeypatch.setattr(routes, "_proximo_ndps", lambda *a: "1")
    monkeypatch.setattr(routes, "_build_payload", lambda *a: {
        "xml_dps": "<DPS><infDPS/></DPS>", "empresa_id": 1, "ambiente": "producao",
        "data_emissao": "2026-11-03", "data_vencimento": "2026-11-30",
    })
    notas = []

    def criar(**kw):
        nota = SimpleNamespace(id=29, lancamento=None, **kw)
        notas.append(nota)
        return nota

    monkeypatch.setattr(routes, "NfseNacionalEmissao", criar)
    monkeypatch.setattr(routes, "NfseNacionalFila", lambda **kw: SimpleNamespace(**kw))
    monkeypatch.setattr(routes, "NfseNacionalEvento", lambda **kw: SimpleNamespace(**kw))
    query = MagicMock()
    query.filter_by.return_value = query
    query.first.return_value = None
    monkeypatch.setattr(routes, "scoped_query", lambda *a: query)
    session = MagicMock()
    monkeypatch.setattr(routes, "db", SimpleNamespace(session=session))

    def transmitir(payload, cfg):
        assert session.commit.call_count == 1  # Reserva antes da chamada externa.
        assert payload["xml_dps"] == notas[0].xml_dps == "<DPS><infDPS/></DPS>"
        assert notas[0].status_processamento == "PROCESSANDO"
        return {
            "sucesso": True, "status": "PROCESSADA", "situacao_fiscal": "AUTORIZADA",
            "payload_retorno": {"response_body": {"nfseXmlGZipB64":
                base64.b64encode(gzip.compress(XML.encode())).decode()}},
            "mensagem": "Autorizada",
        }

    transmissao = MagicMock(side_effect=transmitir)
    monkeypatch.setattr(routes, "transmitiremissao", transmissao)

    def integrar(*a, **k):
        assert notas[0].numero_nfse == "12345"
        assert notas[0].xml_nfse == XML
        assert session.commit.call_count == 2  # Fiscal salvo antes do financeiro.
        notas[0].lancamento = SimpleNamespace(id=40)
        return {"status": "criada", "lancamento_id": 40}

    financeiro = MagicMock(side_effect=integrar)
    monkeypatch.setattr(nfse_financeiro, "integrar_emissao", financeiro)
    return SimpleNamespace(app=app, notas=notas, query=query, session=session,
                           transmitir=transmissao, financeiro=financeiro)


def test_post_completo_recupera_numero_integra_e_abre_conclusao(fluxo_emissao):
    c = fluxo_emissao
    cliente = c.app.test_client()
    resposta = cliente.post("/nfse-nacional/emissoes", data={"valor_servico": "150"})
    assert resposta.status_code == 302
    assert resposta.location.endswith("/29/conclusao")
    assert c.notas[0].numero_nfse == "12345"
    assert c.notas[0].situacao_fiscal == "AUTORIZADA"
    assert c.notas[0].lancamento.id == 40
    payload_gravado = json.loads(c.notas[0].payload_envio)
    assert payload_gravado["data_emissao"] == "2026-11-03"
    assert payload_gravado["data_vencimento"] == "2026-11-30"
    assert "xml_dps" not in payload_gravado
    c.financeiro.assert_called_once()
    c.query.first.return_value = c.notas[0]
    repetida = cliente.post("/nfse-nacional/emissoes", data={"valor_servico": "150"})
    assert repetida.status_code == 302
    c.transmitir.assert_called_once()
    c.financeiro.assert_called_once()


def test_falha_financeira_preserva_nota_autorizada(fluxo_emissao):
    c = fluxo_emissao
    c.financeiro.side_effect = ValueError("Conta ausente")
    resposta = c.app.test_client().post("/nfse-nacional/emissoes", data={"valor_servico": "150"})
    assert resposta.status_code == 302
    assert resposta.location.endswith("/29/conclusao")
    assert c.notas[0].numero_nfse == "12345"
    assert c.notas[0].situacao_fiscal == "AUTORIZADA"
    c.transmitir.assert_called_once()


def test_timeout_preserva_reserva_e_nao_retransmite(fluxo_emissao):
    c = fluxo_emissao
    c.transmitir.side_effect = lambda *a: {
        "sucesso": False, "status": "ERRO_TRANSPORTE", "situacao_fiscal": "PENDENTE",
        "mensagem": "Timeout", "payload_retorno": {},
    }
    cliente = c.app.test_client()
    resposta = cliente.post("/nfse-nacional/emissoes", data={"valor_servico": "150"})
    assert resposta.status_code == 302
    assert c.notas[0].situacao_fiscal == "PENDENTE"
    c.query.first.return_value = c.notas[0]
    cliente.post("/nfse-nacional/emissoes", data={"valor_servico": "150"})
    c.transmitir.assert_called_once()
    c.financeiro.assert_not_called()


@pytest.mark.parametrize("json_request", [True, False])
def test_excecao_apos_reserva_nao_orienta_nova_emissao(fluxo_emissao, json_request):
    c = fluxo_emissao
    c.transmitir.side_effect = RuntimeError("Conexão interrompida")
    cliente = c.app.test_client()
    kwargs = {"json" if json_request else "data": {"valor_servico": "150"}}
    resposta = cliente.post("/nfse-nacional/emissoes", **kwargs)
    if json_request:
        assert resposta.status_code == 202
        assert resposta.json["emissao_id"] == "29"
        assert "Não emita novamente" in resposta.json["error"]
    else:
        assert resposta.status_code == 302
        assert resposta.location.endswith("/emissoes/29")
        with cliente.session_transaction() as session:
            assert any("Não emita novamente" in mensagem for _, mensagem in session["_flashes"])
    c.financeiro.assert_not_called()


def test_falha_ao_salvar_retorno_preserva_referencia_sem_retransmitir(fluxo_emissao):
    c = fluxo_emissao
    c.session.commit.side_effect = [None, RuntimeError("Banco indisponível")]
    resposta = c.app.test_client().post("/nfse-nacional/emissoes", json={"valor_servico": "150"})
    assert resposta.status_code == 202
    assert resposta.json["emissao_id"] == "29"
    assert "Não emita novamente" in resposta.json["error"]
    c.transmitir.assert_called_once()
    c.financeiro.assert_not_called()


def test_falha_antes_da_reserva_nao_indica_emissao_registrada(fluxo_emissao):
    c = fluxo_emissao
    c.session.commit.side_effect = RuntimeError("Banco indisponível")
    resposta = c.app.test_client().post("/nfse-nacional/emissoes", json={"valor_servico": "150"})
    assert resposta.status_code == 400
    assert "emissao_id" not in resposta.json
    c.transmitir.assert_not_called()
    c.financeiro.assert_not_called()


def test_conflito_de_reserva_reutiliza_emissao_sem_transmitir(fluxo_emissao):
    from sqlalchemy.exc import IntegrityError

    c = fluxo_emissao
    existente = SimpleNamespace(id=30, status_processamento="PROCESSANDO", situacao_fiscal="PENDENTE")
    c.query.first.side_effect = [None, existente]
    c.session.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    resposta = c.app.test_client().post("/nfse-nacional/emissoes", json={"valor_servico": "150"})
    assert resposta.status_code == 200
    assert resposta.json["emissao_id"] == "30"
    c.transmitir.assert_not_called()
    c.financeiro.assert_not_called()