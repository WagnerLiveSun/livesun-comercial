import ast
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask
from jinja2 import Environment

from src.services import nfse_financeiro as service
from src.routes.nfse_nacional import nfse_nacional_bp, _authorized_nfse_data


@pytest.fixture
def contexto(monkeypatch):
    nota = SimpleNamespace(
        id=29, empresa_id=1, situacao_fiscal="AUTORIZADA", cancelado_em=None,
        protocolo_cancelamento=None, lancamento=None, numero_nfse="100",
        xml_nfse="", xml_dps="", payload_retorno=None, tomador_id=10,
        tomador=SimpleNamespace(fluxo_conta_id=2), servico=SimpleNamespace(descricao="Descrição"),
        observacoes="Observações preservadas", valor_servico=Decimal("150.00"),
        valor_iss=Decimal("5.00"), criado_em=datetime(2026, 11, 2),
        payload_envio='{"data_emissao":"2026-10-31","data_vencimento":"2026-11-15"}',
        log_tecnico="Autorizada",
    )
    emissao_model = MagicMock()
    emissao_model.query.filter_by.return_value.with_for_update.return_value.first.return_value = nota
    emissao_model.query.filter_by.return_value.first.return_value = None
    lancamento_model = MagicMock()
    lancamento_model.query.filter_by.return_value.all.return_value = []
    lancamento_model.side_effect = lambda **kw: SimpleNamespace(id=40, **kw)
    fluxo_model = MagicMock()
    session = MagicMock()
    monkeypatch.setattr(service, "NfseNacionalEmissao", emissao_model)
    monkeypatch.setattr(service, "Lancamento", lancamento_model)
    monkeypatch.setattr(service, "FluxoContaModel", fluxo_model)
    monkeypatch.setattr(service, "db", SimpleNamespace(session=session))
    return SimpleNamespace(nota=nota, emissao=emissao_model, lancamento=lancamento_model,
                           session=session, conta=MagicMock(return_value=SimpleNamespace(id=3)),
                           fluxo=MagicMock(return_value=2))


def integrar(c, **kw):
    return service.integrar_emissao(1, 29, 7, c.conta, c.fluxo, **kw)


def test_cria_recebimento_preservando_campos_e_datas(contexto):
    c = contexto
    resultado = integrar(c)
    assert resultado == {"status": "criada", "lancamento_id": 40}
    assert c.nota.lancamento.numero_documento == "100"
    assert c.nota.lancamento.data_evento == date(2026, 10, 31)
    assert c.nota.lancamento.data_vencimento == date(2026, 11, 15)
    assert c.nota.lancamento.status == "aberto"
    assert c.nota.lancamento.valor_real == Decimal("150.00")
    assert c.nota.lancamento.observacoes == "Observações preservadas"
    assert "usuário 7" in c.nota.log_tecnico
    c.emissao.query.filter_by.assert_any_call(empresa_id=1, id=29)
    c.session.commit.assert_not_called()  # A rota controla a transação completa.


def test_reprocessamento_nao_duplica(contexto):
    integrar(contexto)
    assert integrar(contexto)["status"] == "ja_integrada"
    assert contexto.lancamento.call_count == 1


@pytest.mark.parametrize("campo,valor", [("situacao_fiscal", "CANCELADA"), ("cancelado_em", datetime(2026, 11, 2)), ("protocolo_cancelamento", "123")])
def test_canceladas_nao_integram(contexto, campo, valor):
    setattr(contexto.nota, campo, valor)
    with pytest.raises(ValueError, match="Somente notas autorizadas"):
        integrar(contexto)
    contexto.lancamento.assert_not_called()


def test_empresa_diferente_nao_encontra_nota(contexto):
    contexto.emissao.query.filter_by.return_value.with_for_update.return_value.first.return_value = None
    with pytest.raises(ValueError, match="não encontrada"):
        integrar(contexto)


def test_sem_conta_mantem_pendente(contexto):
    contexto.conta.return_value = None
    with pytest.raises(ValueError, match="conta bancária"):
        integrar(contexto)
    assert contexto.nota.lancamento is None


def test_vincula_lancamento_compativel_sem_duplicar(contexto):
    existente = SimpleNamespace(id=55, entidade_id=10, valor_real=Decimal("150"))
    contexto.lancamento.query.filter_by.return_value.all.return_value = [existente]
    assert integrar(contexto) == {"status": "vinculada", "lancamento_id": 55}
    contexto.lancamento.assert_not_called()


def test_colisao_de_numero_nao_vincula_cliente_errado(contexto):
    contexto.lancamento.query.filter_by.return_value.all.return_value = [
        SimpleNamespace(id=55, entidade_id=999, valor_real=Decimal("150")),
    ]
    with pytest.raises(ValueError, match="incompatível"):
        integrar(contexto)


def test_vencimento_manual_e_data_xml(contexto):
    contexto.nota.payload_envio = "{}"
    contexto.nota.xml_dps = "<DPS><dhEmi>2026-10-30T10:00:00-03:00</dhEmi></DPS>"
    integrar(contexto, data_vencimento=date(2026, 12, 1))
    assert contexto.nota.lancamento.data_evento == date(2026, 10, 30)
    assert contexto.nota.lancamento.data_vencimento == date(2026, 12, 1)


def test_numero_oficial_recuperado_localmente(contexto):
    contexto.nota.numero_nfse = None
    contexto.nota.xml_nfse = '<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse"><infNFSe><nNFSe>100</nNFSe></infNFSe></NFSe>'
    integrar(contexto)
    assert contexto.nota.lancamento.numero_documento == "100"


def test_danfse_nao_copia_texto_comercial_para_reserva_fiscal():
    xml = '<NFSe><infNFSe><serv><cServ><xDescServ>Descrição comercial</xDescServ></cServ><infoCompl><xInfComp>Observações comerciais</xInfComp></infoCompl></serv></infNFSe></NFSe>'
    dados = _authorized_nfse_data(xml)
    assert dados["descricao_servico"] == "Descrição comercial"
    assert dados["informacoes_complementares"] == ""


def test_rotas_templates_e_formulario():
    app = Flask(__name__)
    app.config.update(SECRET_KEY="test", LOGIN_DISABLED=True)
    app.register_blueprint(nfse_nacional_bp)
    rotas = {r.rule for r in app.url_map.iter_rules()}
    assert "/nfse-nacional/integracao-financeira" in rotas
    assert not any(r.endswith("/replicar") for r in rotas)
    raiz = Path(__file__).resolve().parents[1]
    for nome in ("index", "listagem", "emissoes", "integracao_financeira", "danfs_print"):
        Environment().parse((raiz / f"src/templates/nfse_nacional/{nome}.html").read_text(encoding="utf-8"))
    formulario = (raiz / "src/templates/nfse_nacional/emissoes.html").read_text(encoding="utf-8")
    assert "::-webkit-inner-spin-button" in formulario
    assert "passive: false" in formulario
    template = (raiz / "src/templates/nfse_nacional/danfs_print.html").read_text(encoding="utf-8")
    assert "emissao.observacoes or" in template
    ast.parse((raiz / "src/routes/nfse_financeiro.py").read_text(encoding="utf-8"))


def test_rota_manual_processa_independentemente_e_continua_apos_erro(monkeypatch):
    from src.routes import nfse_financeiro as route
    app = Flask(__name__)
    app.config.update(SECRET_KEY="test", LOGIN_DISABLED=True)
    app.register_blueprint(nfse_nacional_bp)
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.count.return_value = 2
    query.paginate.return_value = SimpleNamespace(items=[], page=1, pages=1)
    monkeypatch.setattr(route, "scoped_query", lambda model: query)
    monkeypatch.setattr(route, "tenant_id", lambda: 1)
    monkeypatch.setattr(route, "current_user", SimpleNamespace(id=7))
    session = MagicMock()
    # Mantém os operadores SQL reais; substitui somente a sessão de persistência.
    monkeypatch.setattr(route, "db", SimpleNamespace(session=session, and_=service.db.and_, or_=service.db.or_))
    integrar_mock = MagicMock(side_effect=[ValueError("Conta ausente"), {"status": "criada", "lancamento_id": 50}])
    monkeypatch.setattr(route, "integrar_emissao", integrar_mock)
    capturado = {}
    def render(nome, **kw):
        capturado.update(kw)
        return "Resultado"
    monkeypatch.setattr(route, "render_template", render)
    resposta = app.test_client().post("/nfse-nacional/integracao-financeira", data={"emissao_ids": ["29", "30"]})
    assert resposta.status_code == 200
    assert capturado["resultados"][0]["status"] == "erro"
    assert capturado["resultados"][1]["lancamento_id"] == 50
    assert session.rollback.call_count == 1
    assert session.commit.call_count == 1
    assert integrar_mock.call_count == 2


def test_renderizacao_da_tela_pendentes_processadas_e_resultado():
    from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader
    app = Flask(__name__)
    app.register_blueprint(nfse_nacional_bp)
    raiz = Path(__file__).resolve().parents[1]
    app.jinja_loader = ChoiceLoader([
        DictLoader({"layout.html": "{% block content %}{% endblock %}"}),
        FileSystemLoader(str(raiz / "src/templates")),
    ])
    app.jinja_env.globals["csrf_token"] = lambda: "token"
    app.jinja_env.filters["brl"] = lambda v: str(v)
    nota = SimpleNamespace(id=29, lancamento=None, numero_nfse="100", numero_interno="INTERNO",
                           ambiente="producao", tomador=SimpleNamespace(nome="Cliente"),
                           criado_em=datetime(2026, 11, 2), valor_servico=Decimal("150"))
    with app.test_request_context():
        html = app.jinja_env.get_template("nfse_nacional/integracao_financeira.html").render(
            pagination=SimpleNamespace(items=[nota], has_prev=False, has_next=False, page=1, pages=1),
            situacao="pendentes", busca="", resultados=[{"emissao_id": 30, "status": "criada", "lancamento_id": 50}],
            total_pendentes=1, total_processadas=2,
        )
    assert 'name="emissao_ids" value="29"' in html
    assert "lançamento 50" in html
    assert "Processadas" in html


def test_integracao_tem_permissao_financeira():
    from src.services.authorization import ENDPOINT_ACCESS_RULES
    regra = ENDPOINT_ACCESS_RULES["nfse_nacional.integracao_financeira"]
    assert regra.module == "financeiro"
    assert regra.permission == "lancamentos"


@pytest.fixture
def cancelamento(monkeypatch):
    from src.routes import nfse_nacional as route
    session = MagicMock()
    evento = MagicMock()
    evento.query.filter_by.return_value.first.return_value = None
    monkeypatch.setattr(route, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(route, "NfseNacionalEvento", evento)
    nota = SimpleNamespace(
        id=29, empresa_id=1, lancamento=SimpleNamespace(id=50, empresa_id=1),
        lancamento_id=50, situacao_fiscal="AUTORIZADA", status_processamento="PROCESSADA",
        protocolo_cancelamento=None, motivo_cancelamento=None, cancelado_em=None,
        cancelado_por_id=None, payload_cancelamento=None,
    )
    return SimpleNamespace(route=route, session=session, nota=nota, evento=evento)


def test_cancelamento_exclui_lancamento_e_limpa_vinculo(cancelamento):
    c = cancelamento
    lancamento = c.nota.lancamento
    c.route._gravar_cancelamento_local(c.nota, protocolo="123", usuario_id=7)
    c.session.delete.assert_called_once_with(lancamento)
    assert c.nota.lancamento is None and c.nota.lancamento_id is None
    assert c.nota.situacao_fiscal == "CANCELADA"
    c.session.commit.assert_not_called()


def test_cancelamento_sem_lancamento_e_idempotente(cancelamento):
    c = cancelamento
    c.nota.lancamento = None
    c.route._gravar_cancelamento_local(c.nota)
    c.route._gravar_cancelamento_local(c.nota)
    c.session.delete.assert_not_called()


def test_cancelamento_nao_exclui_lancamento_de_outra_empresa(cancelamento):
    c = cancelamento
    c.nota.lancamento.empresa_id = 2
    with pytest.raises(ValueError, match="outra empresa"):
        c.route._gravar_cancelamento_local(c.nota)
    c.session.delete.assert_not_called()
    assert c.nota.situacao_fiscal == "AUTORIZADA"


def test_sincronizacao_limpa_recebivel_de_nota_ja_cancelada(cancelamento):
    c = cancelamento
    c.nota.situacao_fiscal = c.nota.status_processamento = "CANCELADA"
    assert c.route._sincronizar_cancelamento_emissao(c.nota, consultar_api=False)
    c.session.delete.assert_called_once()
    c.session.commit.assert_called_once()


def test_sem_cancelamento_confirmado_nao_exclui(cancelamento):
    c = cancelamento
    assert not c.route._sincronizar_cancelamento_emissao(c.nota, consultar_api=False)
    c.session.delete.assert_not_called()


def test_substituicao_grava_cancelamento_apenas_no_sucesso():
    import inspect
    from src.routes.nfse_nacional import nfse_cancelamento_substituicao
    arvore = ast.parse(inspect.getsource(inspect.unwrap(nfse_cancelamento_substituicao)))
    sucesso = next(n for n in ast.walk(arvore) if isinstance(n, ast.If)
                   and ast.unparse(n.test) == "resultado.get('sucesso')")
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "_gravar_cancelamento_local"
               for bloco in sucesso.body for n in ast.walk(bloco))
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                   and n.func.id == "_gravar_cancelamento_local"
                   for bloco in sucesso.orelse for n in ast.walk(bloco))