"""PDF e rota isolados, sem factory de produção nem acesso ao banco persistente."""

from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask
from flask_login import LoginManager
from jinja2 import Environment
from PIL import Image
import pytest

from src.services.proposta_pdf import PDFNovoModelo, gerar_novo_modelo, localizar_logo


def proposta_exemplo():
    empresa = SimpleNamespace(
        id=7, nome='Empresa Exemplo Ltda.', nome_fantasia='Empresa Exemplo',
        cnpj='12.345.678/0001-90', logo_caminho=None, email='empresa@example.test',
        telefone='1133334444', endereco_rua='Rua da Empresa', endereco_numero='10',
        endereco_bairro='Centro', endereco_cidade='São Paulo', endereco_uf='SP',
        endereco_cep='01001000',
    )
    cliente = SimpleNamespace(
        nome='Cliente Exemplo S.A.', cnpj_cpf='98.765.432/0001-10',
        email='cliente@example.test', telefone='4733334444', endereco_rua='Rua do Cliente',
        endereco_numero='25', endereco_cidade='Blumenau', endereco_uf='SC',
    )
    vendedor = SimpleNamespace(nome='Vendedor Exemplo', email='vendas@example.test', telefone='11999998888')
    itens = [
        SimpleNamespace(
            tipo_item='P', produto=SimpleNamespace(codigo_interno='SKU-001', descricao_resumida='Licença cadastrada'),
            servico=None, descricao='Licença de proteção — renovação anual', quantidade=Decimal('25.000'),
            valor_unitario=Decimal('893.85'), valor_desconto=Decimal('0'), valor_total=Decimal('22346.25'),
        ),
        SimpleNamespace(
            tipo_item='S', produto=None, servico=SimpleNamespace(codigo_interno='SRV-002', descricao='Serviço cadastrado'),
            descricao='Serviço de implantação e configuração', quantidade=Decimal('1.000'),
            valor_unitario=Decimal('4153.75'), valor_desconto=Decimal('100'), valor_total=Decimal('4053.75'),
        ),
    ]
    return SimpleNamespace(
        id=42, empresa_id=7, empresa=empresa, cliente=cliente, vendedor=vendedor, filial=None,
        numero='PROP-2026-042', data_emissao=date(2026, 10, 21), data_validade=date(2026, 10, 26),
        data_aprovacao=None, itens=itens, valor_desconto=Decimal('0'), valor_total=Decimal('26400'),
        observacoes='Fornecimento das licenças e dos serviços indicados nesta proposta.',
        observacoes_internas='SEGREDO_INTERNO_NAO_EXPORTAR',
        detalhes_tecnicos='Compatibilidade e requisitos conforme ambiente do cliente.\n• Atendimento remoto.',
        validade_precos='Preços válidos até 26/10/2026, sem renovação automática.',
        condicoes_pagamento='Pagamento em duas parcelas, conforme aprovação comercial.',
        termos_compra='1. Entrega e processamento\nEntrega eletrônica após confirmação do pagamento.\n\n'
        '2. Serviços não incluídos\nServiços adicionais dependem de contratação específica.\n\n'
        '3. Confidencialidade\nAs informações desta proposta destinam-se às partes.',
    )


def ler_pdf(conteudo):
    pypdf = pytest.importorskip('pypdf', reason='Leitor opcional para inspeção do PDF nos testes locais')
    return pypdf.PdfReader(BytesIO(conteudo))


def test_conteudo_dinamico_termos_aceite_e_rodapes(tmp_path):
    proposta = proposta_exemplo()
    static_folder = Path(__file__).resolve().parents[1] / 'src' / 'static'
    leitor = ler_pdf(gerar_novo_modelo(proposta, tmp_path, static_folder=static_folder))
    assert len(leitor.pages) == 2
    paginas = [pagina.extract_text() for pagina in leitor.pages]
    conteudo = '\n'.join(paginas)
    for esperado in (
        proposta.empresa.nome, proposta.cliente.nome, proposta.empresa.cnpj, proposta.cliente.cnpj_cpf,
        'SKU-001', 'SRV-002', '26.400,00', '4.053,75', '100,00', '25',
        proposta.condicoes_pagamento, proposta.validade_precos,
        'Entrega eletrônica após confirmação do pagamento.', 'Aceite da proposta',
        'CLIENTE', 'FORNECEDORA', 'Data da assinatura:', 'proteção — renovação',
    ):
        assert esperado in conteudo
    assert proposta.observacoes_internas not in conteudo
    assert 'SKYOVI' not in conteudo
    assert 'Teka' not in conteudo
    assert 'hospedagem' not in conteudo
    for numero, pagina in enumerate(paginas, 1):
        assert f'Página {numero}/{len(paginas)}' in pagina
        assert proposta.numero in pagina
    aceite = paginas[-1].split('Aceite da proposta', 1)[1]
    assert proposta.cliente.nome in aceite
    assert proposta.cliente.cnpj_cpf in aceite
    assert 'Assinatura:' in aceite
    assert '26.400,00' in aceite


def test_muitos_itens_repetem_cabecalho_e_preservam_textos_longos(tmp_path):
    proposta = proposta_exemplo()
    proposta.itens = [SimpleNamespace(**vars(proposta.itens[0])) for _ in range(65)]
    for i, item in enumerate(proposta.itens):
        item.descricao = f'ITEM-UNICO-{i:03d} ' + ('Descrição detalhada do produto e serviço. ' * 5)
    proposta.itens[-1].descricao += 'ULTIMO_ITEM_COMPLETO'
    proposta.termos_compra = ('Condição comercial detalhada.\n' * 150) + 'FIM_DOS_TERMOS'
    leitor = ler_pdf(gerar_novo_modelo(proposta, tmp_path))
    paginas = [pagina.extract_text() for pagina in leitor.pages]
    conteudo = '\n'.join(paginas)
    for i in range(65):
        assert conteudo.count(f'ITEM-UNICO-{i:03d}') == 1
    assert 'ULTIMO_ITEM_COMPLETO' in conteudo
    assert 'FIM_DOS_TERMOS' in conteudo
    for numero, pagina in enumerate(paginas, 1):
        assert f'Página {numero}/{len(paginas)}' in pagina
        if 'ITEM-UNICO-' in pagina:
            assert 'Item / SKU' in pagina
    assert any('Aceite da proposta' in pagina and 'Assinatura:' in pagina for pagina in paginas)


def test_celula_maior_que_pagina_nao_perde_conteudo(tmp_path):
    proposta = proposta_exemplo()
    proposta.itens[0].descricao = 'Primeira linha\n' + 'Linha longa\n' * 180 + 'FIM_CELULA'
    leitor = ler_pdf(gerar_novo_modelo(proposta, tmp_path))
    conteudo = '\n'.join(p.extract_text() for p in leitor.pages)
    assert 'FIM_CELULA' in conteudo
    assert conteudo.count('Linha longa') == 180


def test_dados_opcionais_fallback_servico_total_zero_e_sem_logo_padrao(tmp_path):
    proposta = proposta_exemplo()
    proposta.vendedor = None
    proposta.observacoes = proposta.validade_precos = proposta.condicoes_pagamento = None
    proposta.termos_compra = proposta.detalhes_tecnicos = None
    proposta.itens[1].descricao = '-'
    proposta.valor_total = Decimal('0')
    leitor = ler_pdf(gerar_novo_modelo(proposta, tmp_path))
    conteudo = '\n'.join(p.extract_text() for p in leitor.pages)
    assert 'Serviço cadastrado' in conteudo
    assert 'Proposta válida até 26/10/2026.' in conteudo
    assert 'TOTAL DA PROPOSTA: R$ 0,00' in conteudo
    assert 'None' not in conteudo
    assert not list(leitor.pages[0].images)
    proposta.itens = []
    assert gerar_novo_modelo(proposta, tmp_path).startswith(b'%PDF-')


def test_cabecalho_logo_itens_total_e_condicoes_aproveitam_primeira_pagina(tmp_path):
    proposta = proposta_exemplo()
    static_folder = Path(__file__).resolve().parents[1] / 'src' / 'static'
    leitor = ler_pdf(gerar_novo_modelo(proposta, tmp_path, static_folder=static_folder))
    primeira = leitor.pages[0].extract_text()

    assert len(leitor.pages) == 2
    assert len(list(leitor.pages[0].images)) == 1
    for esperado in (
        'PROPOSTA COMERCIAL', 'CLIENTE / USUÁRIO FINAL', 'FORNECEDORA / EMITENTE',
        'Itens da proposta', 'TOTAL DA PROPOSTA: R$ 26.400,00', 'Condições comerciais',
    ):
        assert esperado in primeira


@pytest.mark.parametrize('extensao', ['png', 'webp', 'gif', 'bmp', 'jpg'])
def test_logo_cadastrado_formatos_e_confinamento(tmp_path, extensao):
    proposta = proposta_exemplo()
    pasta = tmp_path / 'logos'
    pasta.mkdir()
    arquivo = pasta / f'empresa_7_logo.{extensao}'
    Image.new('RGB', (180, 60), (181, 31, 43)).save(arquivo)
    proposta.empresa.logo_caminho = f'/uploads/logos/{arquivo.name}'
    assert localizar_logo(proposta.empresa, tmp_path) == arquivo
    leitor = ler_pdf(gerar_novo_modelo(proposta, tmp_path))
    assert len(list(leitor.pages[0].images)) == 1
    proposta.empresa.logo_caminho = '/uploads/../fora.png'
    assert localizar_logo(proposta.empresa, tmp_path) is None
    proposta.empresa.logo_caminho = 'https://example.test/logo.png'
    assert localizar_logo(proposta.empresa, tmp_path) is None


def test_logo_estatico_e_fallback_quando_upload_cadastrado_indisponivel(tmp_path):
    proposta = proposta_exemplo()
    imagens = tmp_path / 'static' / 'images'
    imagens.mkdir(parents=True)
    arquivo = imagens / 'logo.png'
    Image.new('RGB', (180, 60), (181, 31, 43)).save(arquivo)
    proposta.empresa.logo_caminho = '/uploads/logos/logo-ausente.png'

    assert localizar_logo(proposta.empresa, tmp_path, tmp_path / 'static') == arquivo
    leitor = ler_pdf(gerar_novo_modelo(proposta, tmp_path, tmp_path / 'static'))
    assert len(list(leitor.pages[0].images)) == 1


def test_logo_cadastrado_tem_prioridade_sobre_logo_estatico(tmp_path):
    proposta = proposta_exemplo()
    uploads = tmp_path / 'logos'
    estaticos = tmp_path / 'static' / 'images'
    uploads.mkdir()
    estaticos.mkdir(parents=True)
    logo_cadastrado = uploads / 'logo-cliente.png'
    logo_estatico = estaticos / 'logo.png'
    Image.new('RGB', (120, 60), (0, 0, 255)).save(logo_cadastrado)
    Image.new('RGB', (180, 60), (181, 31, 43)).save(logo_estatico)
    proposta.empresa.logo_caminho = '/uploads/logos/logo-cliente.png'

    assert localizar_logo(proposta.empresa, tmp_path, tmp_path / 'static') == logo_cadastrado


def test_aprovacao_nao_preenche_data_de_assinatura(tmp_path):
    proposta = proposta_exemplo()
    proposta.data_aprovacao = date(2026, 10, 25)
    leitor = ler_pdf(gerar_novo_modelo(proposta, tmp_path))
    conteudo = leitor.pages[-1].extract_text()
    assert 'Aprovação registrada na proposta: 25/10/2026' in conteudo
    assert 'não substitui a assinatura do cliente' in conteudo
    assert 'Data da assinatura: ______ / ______ / __________' in conteudo


def test_estilo_referencia_e_integracao_dos_menus():
    assert PDFNovoModelo.VERMELHO == (181, 31, 43)
    assert sum(PDFNovoModelo.LARGURAS_ITENS) == 182
    raiz = Path(__file__).resolve().parents[1]
    for nome in ('orcamentos_detalhe.html', 'propostas_aprovacao.html'):
        conteudo = (raiz / 'src' / 'templates' / 'comercial' / nome).read_text(encoding='utf-8')
        Environment().parse(conteudo)
        assert '>Novo Modelo</a>' in conteudo
        assert '>Completo</a>' in conteudo
        assert '>Resumido</a>' in conteudo
    from src.services.authorization import ENDPOINT_ACCESS_RULES
    regras = ENDPOINT_ACCESS_RULES
    assert regras['comercial_operacional.orcamentos_exportar_pdf_novo_modelo'] == regras[
        'comercial_operacional.orcamentos_exportar_pdf_resumido'
    ]


@pytest.fixture
def app_pdf(tmp_path):
    from src.routes.comercial_operacional import comercial_bp
    static_folder = Path(__file__).resolve().parents[1] / 'src' / 'static'
    app = Flask(__name__, static_folder=str(static_folder))
    app.config.update(TESTING=True, SECRET_KEY='test-only', UPLOAD_FOLDER=str(tmp_path))
    login = LoginManager(app)
    login.user_loader(lambda user_id: None)
    app.register_blueprint(comercial_bp)
    return app


def test_rota_exige_login(app_pdf):
    resposta = app_pdf.test_client().get('/comercial/orcamentos/42/exportar-pdf-novo-modelo')
    assert resposta.status_code == 401


def test_rota_pdf_e_isolamento_empresa(app_pdf):
    proposta = proposta_exemplo()
    app_pdf.config['LOGIN_DISABLED'] = True
    with patch('src.routes.comercial_operacional.scoped_get_or_404', return_value=proposta) as consulta, \
            patch('src.routes.comercial_operacional.tenant_id', return_value=7):
        resposta = app_pdf.test_client().get('/comercial/orcamentos/42/exportar-pdf-novo-modelo')
    assert resposta.status_code == 200
    assert resposta.mimetype == 'application/pdf'
    assert resposta.data.startswith(b'%PDF-')
    assert len(list(ler_pdf(resposta.data).pages[0].images)) == 1
    assert 'proposta_novo_modelo_PROP-2026-042.pdf' in resposta.headers['Content-Disposition']
    assert consulta.call_args.args[1] == 42
    with patch('src.routes.comercial_operacional.scoped_get_or_404', return_value=proposta), \
            patch('src.routes.comercial_operacional.tenant_id', return_value=99), \
            patch('src.services.proposta_pdf.gerar_novo_modelo') as gerar:
        resposta = app_pdf.test_client().get('/comercial/orcamentos/42/exportar-pdf-novo-modelo')
    assert resposta.status_code == 302
    gerar.assert_not_called()


def test_erro_de_geracao_nao_expoe_detalhes_internos(app_pdf):
    app_pdf.config['LOGIN_DISABLED'] = True
    with patch('src.routes.comercial_operacional.scoped_get_or_404', return_value=proposta_exemplo()), \
            patch('src.routes.comercial_operacional.tenant_id', return_value=7), \
            patch('src.services.proposta_pdf.gerar_novo_modelo', side_effect=ValueError('DETALHE_PRIVADO')):
        cliente = app_pdf.test_client()
        resposta = cliente.get('/comercial/orcamentos/42/exportar-pdf-novo-modelo')
        assert resposta.status_code == 302
        with cliente.session_transaction() as sessao:
            assert 'DETALHE_PRIVADO' not in str(sessao['_flashes'])