from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask, render_template, url_for
from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader

from src.routes.comercial_operacional import comercial_bp
from src.routes.cobrancas_bancarias import cobrancas_bancarias_bp
from src.routes.lancamentos import lancamentos_bp
from src.routes.nfse_nacional import nfse_nacional_bp
from src.services.authorization import ENDPOINT_ACCESS_RULES, can_access_endpoint


ACOES = {
    'comercial_operacional.orcamentos_index': 'Propostas comerciais',
    'comercial_operacional.propostas_aprovacao': 'Aprovação de propostas',
    'nfse_nacional.listagem': 'NFS-e Emitidas',
    'nfse_nacional.emissoes': 'Geração de NFS-e',
    'lancamentos.index': 'Lançamentos',
    'cobrancas_bancarias.index': 'Cobranças bancárias',
}


class AtalhosParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.modulos = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'ls-quick-action' in attrs.get('class', '').split():
            self.links.append(attrs['href'])
        if 'data-quick-actions-module' in attrs:
            self.modulos.append(attrs['data-quick-actions-module'])


@pytest.fixture
def painel(monkeypatch):
    raiz = Path(__file__).resolve().parents[1]
    app = Flask(__name__)
    for blueprint in (comercial_bp, nfse_nacional_bp, lancamentos_bp, cobrancas_bancarias_bp):
        app.register_blueprint(blueprint)
    app.jinja_loader = ChoiceLoader([
        DictLoader({'layout.html': '{% block extra_css %}{% endblock %}{% block content %}{% endblock %}'}),
        FileSystemLoader(str(raiz / 'src/templates')),
    ])
    empresa = SimpleNamespace(
        plano='premium', atividade_propostas=True, atividade_servicos=True, atividade_financeiro=True,
    )
    usuario = SimpleNamespace(is_authenticated=True, is_admin=False, empresa_id=1, empresa=empresa)
    permissoes = {ENDPOINT_ACCESS_RULES[endpoint].permission for endpoint in ACOES}
    monkeypatch.setattr('src.access_control.has_permission_key', lambda user, key: key in permissoes)

    def renderizar(pagamento_pendente=False):
        with app.test_request_context('/'):
            html = render_template(
                'dashboard_geral.html', current_user=usuario,
                can_access_endpoint=lambda endpoint: not pagamento_pendente and can_access_endpoint(usuario, endpoint),
                fornecedores=2, clientes=3, vendedores=1,
                total_usuarios=4, total_produtos=5, total_servicos=6,
            )
            parser = AtalhosParser()
            parser.feed(html)
            urls = {endpoint: url_for(endpoint) for endpoint in ACOES}
        return SimpleNamespace(html=html, links=parser.links, modulos=parser.modulos, urls=urls)

    return SimpleNamespace(renderizar=renderizar, empresa=empresa, permissoes=permissoes)


def test_painel_exibe_seis_acoes_com_rotas_reais_e_preserva_indicadores(painel):
    resultado = painel.renderizar()
    assert resultado.modulos == ['propostas', 'fiscal', 'financeiro']
    assert resultado.links == list(resultado.urls.values())
    for rotulo in ACOES.values():
        assert rotulo in resultado.html
    assert resultado.html.index('Ações rápidas') < resultado.html.index('Fornecedores')
    for indicador in ('Fornecedores', 'Clientes', 'Vendedores', 'Usuários Ativos', 'Produtos', 'Serviços'):
        assert indicador in resultado.html
    assert 'css/dashboard_geral.css' in resultado.html
    assert 'col-12 col-md' in resultado.html
    assert 'aria-labelledby="acoes-rapidas-titulo"' in resultado.html


@pytest.mark.parametrize('endpoint', ACOES)
def test_atalho_respeita_permissao_funcional(painel, endpoint):
    permissao = ENDPOINT_ACCESS_RULES[endpoint].permission
    painel.permissoes.remove(permissao)
    resultado = painel.renderizar()
    for destino in ACOES:
        assert (resultado.urls[destino] in resultado.links) == (
            ENDPOINT_ACCESS_RULES[destino].permission != permissao
        )


@pytest.mark.parametrize('atividade,grupo', [
    ('propostas', 'propostas'), ('servicos', 'fiscal'), ('financeiro', 'financeiro'),
])
def test_modulo_desabilitado_nao_exibe_grupo_nem_atalhos(painel, atividade, grupo):
    setattr(painel.empresa, f'atividade_{atividade}', False)
    resultado = painel.renderizar()
    assert grupo not in resultado.modulos
    assert len(resultado.links) == 4


def test_plano_basico_oculta_acoes_fiscais(painel):
    painel.empresa.plano = 'basic'
    resultado = painel.renderizar()
    assert 'fiscal' not in resultado.modulos
    assert len(resultado.links) == 4


@pytest.mark.parametrize('pagamento_pendente', [False, True])
def test_sem_acesso_nao_exibe_card_vazio(painel, pagamento_pendente):
    if not pagamento_pendente:
        painel.permissoes.clear()
    resultado = painel.renderizar(pagamento_pendente=pagamento_pendente)
    assert not resultado.links
    assert not resultado.modulos
    assert 'id="acoes-rapidas-titulo"' not in resultado.html
    assert 'Fornecedores' in resultado.html