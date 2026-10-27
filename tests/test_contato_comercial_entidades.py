from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment
import pytest

from src.services.proposta_pdf import gerar_novo_modelo


def test_proposta_novo_modelo_inclui_contato_e_email_comercial(tmp_path):
    pypdf = pytest.importorskip('pypdf', reason='Leitor opcional usado para inspecionar o PDF')
    cliente = SimpleNamespace(
        nome='Cliente Exemplo', cnpj_cpf='12345678000199', email='fiscal@example.test',
        email_comercial='comercial@example.test', contato_comercial='Maria Comercial',
        telefone='1133334444', endereco_rua='Rua Exemplo', endereco_numero='10',
        endereco_bairro='Centro', endereco_cidade='São Paulo', endereco_uf='SP',
        endereco_cep='01001000',
    )
    empresa = SimpleNamespace(
        id=1, nome='Empresa Exemplo', nome_fantasia='Empresa', cnpj='98765432000199',
        logo_caminho=None, email='empresa@example.test', telefone='1133334444',
        endereco_rua='Rua Empresa', endereco_numero='20', endereco_bairro='Centro',
        endereco_cidade='São Paulo', endereco_uf='SP', endereco_cep='01001000',
    )
    proposta = SimpleNamespace(
        id=1, empresa_id=1, empresa=empresa, cliente=cliente, vendedor=None, filial=None,
        numero='PROP-TESTE', data_emissao=date(2026, 10, 27), data_validade=date(2026, 11, 3),
        data_aprovacao=None, itens=[], valor_desconto=Decimal('0'), valor_total=Decimal('0'),
        observacoes='', observacoes_internas='', detalhes_tecnicos='', validade_precos='',
        condicoes_pagamento='', termos_compra='',
    )

    conteudo_pdf = gerar_novo_modelo(proposta, tmp_path)
    leitor = pypdf.PdfReader(BytesIO(conteudo_pdf))
    texto = '\n'.join(pagina.extract_text() or '' for pagina in leitor.pages)

    assert 'Contato comercial: Maria Comercial' in texto
    assert 'E-mail comercial: comercial@example.test' in texto


def test_campos_comerciais_sao_restritos_a_cliente_no_cadastro_e_detalhe():
    raiz = Path(__file__).resolve().parents[1]
    formulario = (raiz / 'src/templates/entidades/form.html').read_text(encoding='utf-8')
    detalhes = (raiz / 'src/templates/entidades/details.html').read_text(encoding='utf-8')

    Environment().parse(formulario)
    Environment().parse(detalhes)
    assert "entidade.tipo == 'C'" in formulario
    assert "entidade.tipo == 'C'" in detalhes
    assert 'disabled' in formulario


def test_migracoes_sao_separadas_e_usam_schema_corretos():
    raiz = Path(__file__).resolve().parents[1]
    mysql = (raiz / 'migrations/mysql/038_add_contato_comercial_entidades_mysql.sql').read_text(encoding='utf-8')
    postgres = (raiz / 'migrations/postgresql/035_add_contato_comercial_entidades_postgresql.sql').read_text(encoding='utf-8')

    assert "TABLE_NAME = 'entidades'" in mysql
    assert 'ADD COLUMN `contato_comercial` VARCHAR(150) NULL' in mysql
    assert 'ADD COLUMN `email_comercial` VARCHAR(120) NULL' in mysql
    assert 'ALTER TABLE app.entidades' in postgres
    assert 'ADD COLUMN IF NOT EXISTS contato_comercial VARCHAR(150)' in postgres
    assert 'ADD COLUMN IF NOT EXISTS email_comercial VARCHAR(120)' in postgres


def test_mensagem_danfse_preserva_texto_existente_e_acrescenta_contato():
    from src.routes.nfse_nacional import MENSAGEM_PADRAO_NFSE, _acrescentar_contato_comercial

    mensagem = MENSAGEM_PADRAO_NFSE.format(numero='123', data_emissao='27/10/2026')
    mensagem = _acrescentar_contato_comercial(mensagem, 'Maria Comercial')

    assert mensagem.startswith('Prezado cliente, segue em anexo nossa NFS-e Nº 123 emitida em 27/10/2026.')
    assert mensagem.endswith('Aos cuidados de Maria Comercial.')
    assert _acrescentar_contato_comercial(mensagem, 'Maria Comercial') == mensagem