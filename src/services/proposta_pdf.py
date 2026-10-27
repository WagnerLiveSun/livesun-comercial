"""Novo Modelo: apresentação resumida com dados e termos da própria proposta."""

from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import re

from fpdf import FPDF
from PIL import Image


def texto(valor, padrao=''):
    if valor is None:
        return padrao
    valor = str(valor).strip().replace('\r\n', '\n').replace('\r', '\n')
    return valor or padrao


def moeda(valor):
    numero = f'{Decimal(str(valor or 0)):,.2f}'
    return 'R$ ' + numero.replace(',', 'X').replace('.', ',').replace('X', '.')


def documento(entidade):
    return texto(getattr(entidade, 'cnpj_cpf', None) or getattr(entidade, 'cnpj', None), '-')


def endereco(entidade):
    partes = [texto(getattr(entidade, campo, None)) for campo in (
        'endereco_rua', 'endereco_numero', 'endereco_bairro', 'endereco_cidade', 'endereco_uf',
    )]
    cep = texto(getattr(entidade, 'endereco_cep', None))
    if re.fullmatch(r'\d{8}', cep):
        cep = f'{cep[:5]}-{cep[5:]}'
    if cep:
        partes.append(f'CEP: {cep}')
    return ', '.join(parte for parte in partes if parte) or '-'


def data_formatada(valor):
    return valor.strftime('%d/%m/%Y') if valor else '-'


def localizar_logo(empresa, upload_folder, static_folder=None):
    """Prioriza o logo cadastrado e usa o logo estático do app como fallback."""
    caminho = texto(getattr(empresa, 'logo_caminho', None))
    if caminho.startswith('/uploads/'):
        raiz = Path(upload_folder).resolve()
        arquivo = (raiz / caminho[len('/uploads/'):]).resolve()
        if arquivo.is_relative_to(raiz) and arquivo.is_file():
            return arquivo

    if static_folder:
        raiz_estatica = Path(static_folder).resolve()
        candidatos = (
            raiz_estatica / 'images' / 'logo_sem fundo2.png',
            raiz_estatica / 'images' / 'logo_sem_fundo2.png',
            raiz_estatica / 'images' / 'logo.png',
            raiz_estatica / 'img' / 'logo.png',
        )
        for candidato in candidatos:
            if candidato.is_file():
                return candidato
    return None


class PDFNovoModelo(FPDF):
    VERMELHO = (181, 31, 43)
    CINZA = (242, 244, 247)
    LARGURAS_ITENS = (30, 64, 15, 26, 22, 25)
    CABECALHO_ITENS = ('Item / SKU', 'Descrição', 'Qtd.', 'Unitário', 'Desconto', 'Total (R$)')

    def __init__(self, empresa, numero):
        super().__init__('P', 'mm', 'A4')
        self.set_margins(14, 16, 14)
        self.set_auto_page_break(True, 20)
        self.alias_nb_pages()
        self.empresa_nome = texto(getattr(empresa, 'nome_fantasia', None) or getattr(empresa, 'nome', None))
        self.numero = texto(numero, '-')
        self.set_title(self.codificar(f'Proposta {self.numero} - Novo Modelo'))
        self.set_author(self.codificar(self.empresa_nome))

    @staticmethod
    def codificar(valor):
        # As fontes PDF básicas usam WinAnsi; mantém acentos, bullets e travessões.
        return texto(valor).expandtabs(4).encode('cp1252', 'replace').decode('latin-1')

    def fonte(self, negrito=False, tamanho=10):
        self.set_font('Helvetica', 'B' if negrito else '', tamanho)
        self.set_text_color(0, 0, 0)

    def linhas(self, valor, largura):
        return self.multi_cell(largura, 5, self.codificar(valor), split_only=True) or ['']

    def garantir_espaco(self, altura):
        if self.get_y() + altura > self.page_break_trigger:
            self.add_page()

    def footer(self):
        self.set_y(-13)
        self.fonte(tamanho=7)
        rodape = self.codificar(
            f'{self.empresa_nome} | Proposta {self.numero} | Página {self.page_no()}/{{nb}}'
        )
        while self.get_string_width(rodape) > 182 and self.font_size_pt > 5:
            self.set_font_size(self.font_size_pt - 0.5)
        self.cell(182, 5, rodape, align='R')

    def titulo(self, valor):
        self.fonte(True, 12)
        linhas = self.linhas(valor, 182)
        self.garantir_espaco(len(linhas) * 6 + 12)
        self.set_text_color(*self.VERMELHO)
        for linha in linhas:
            self.cell(182, 6, linha, ln=1)
        self.ln(2)

    def paragrafo(self, valor, negrito=False, tamanho=10):
        self.fonte(negrito, tamanho)
        self.multi_cell(182, 4.8, self.codificar(valor), align='L')
        self.ln(1)

    def topico(self, titulo, conteudo):
        self.fonte(tamanho=9)
        linhas = self.linhas(conteudo, 182)
        self.garantir_espaco(8 + min(len(linhas), 3) * 4.8)
        self.paragrafo(titulo, negrito=True, tamanho=9.5)
        self.paragrafo(conteudo, tamanho=9)

    def linha_tabela(self, valores, larguras, cabecalho=False, fundo=False):
        """Quebra linhas por largura real e divide células muito extensas entre páginas."""
        tamanho_fonte = 8 if cabecalho else 8.5
        altura_linha = 4.2
        self.fonte(cabecalho, tamanho_fonte)
        colunas = [self.multi_cell(largura - 4, altura_linha, self.codificar(valor), split_only=True) or ['']
                   for valor, largura in zip(valores, larguras)]
        restantes = max(map(len, colunas))
        altura_total = restantes * altura_linha + 4
        limite_pagina = self.page_break_trigger - self.t_margin - 22
        if altura_total <= limite_pagina and self.get_y() + altura_total > self.page_break_trigger:
            self.add_page()
            if tuple(larguras) == self.LARGURAS_ITENS and not cabecalho:
                self.cabecalho_itens()
        deslocamento = 0
        while restantes:
            capacidade = int((self.page_break_trigger - self.get_y() - 4) / altura_linha)
            if capacidade < 1:
                self.add_page()
                if tuple(larguras) == self.LARGURAS_ITENS and not cabecalho:
                    self.cabecalho_itens()
                capacidade = int((self.page_break_trigger - self.get_y() - 4) / altura_linha)
            quantidade = min(restantes, capacidade)
            altura = quantidade * altura_linha + 4
            x, y = self.l_margin, self.get_y()
            self.set_draw_color(0, 0, 0)
            self.set_line_width(0.25)
            self.set_fill_color(*(self.VERMELHO if cabecalho else self.CINZA))
            self.fonte(cabecalho, tamanho_fonte)
            if cabecalho:
                self.set_text_color(255, 255, 255)
            for indice, (largura, linhas) in enumerate(zip(larguras, colunas)):
                self.rect(x, y, largura, altura, 'DF' if cabecalho or fundo else 'D')
                for posicao, linha in enumerate(linhas[deslocamento:deslocamento + quantidade]):
                    self.set_xy(x + 2, y + 2 + posicao * altura_linha)
                    alinhamento = 'R' if len(larguras) == 6 and indice >= 3 and not cabecalho else 'L'
                    self.cell(largura - 4, altura_linha, linha, align=alinhamento)
                x += largura
            self.set_xy(self.l_margin, y + altura)
            deslocamento += quantidade
            restantes -= quantidade

    def cabecalho_itens(self):
        self.garantir_espaco(22)
        self.linha_tabela(self.CABECALHO_ITENS, self.LARGURAS_ITENS, cabecalho=True)


def gerar_novo_modelo(orcamento, upload_folder, static_folder=None):
    """Retorna PDF sem alterar proposta, aprovação, cadastros ou banco de dados."""
    empresa = orcamento.empresa
    cliente = orcamento.cliente
    vendedor = orcamento.vendedor
    pdf = PDFNovoModelo(empresa, orcamento.numero)
    pdf.add_page()
    logo = localizar_logo(empresa, upload_folder, static_folder=static_folder)
    if logo:
        # Normaliza os formatos aceitos no cadastro (inclusive WEBP/GIF/BMP).
        with TemporaryDirectory(prefix='proposta_logo_') as temporario:
            with Image.open(logo) as imagem:
                imagem = imagem.convert('RGBA')
                imagem.thumbnail((1200, 600))
                arquivo = Path(temporario) / 'logo.png'
                imagem.save(arquivo)
                largura = min(48, 25 * imagem.width / imagem.height)
                altura = largura * imagem.height / imagem.width
            pdf.image(str(arquivo), x=14, y=16, w=largura, h=altura)
    pdf.set_xy(91, 15)
    pdf.set_text_color(*pdf.VERMELHO)
    pdf.set_font('Helvetica', 'B', 19)
    pdf.cell(97, 9, pdf.codificar('PROPOSTA COMERCIAL'), align='R', ln=1)
    pdf.set_x(91)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(97, 7, pdf.codificar(f'Nº {orcamento.numero}'), align='R', ln=1)
    pdf.set_x(91)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(97, 5, pdf.codificar(f'Emissão: {data_formatada(orcamento.data_emissao)}'), align='R', ln=1)
    pdf.set_x(91)
    pdf.cell(97, 5, pdf.codificar(f'Validade: {data_formatada(orcamento.data_validade)}'), align='R', ln=1)

    # Identificação compacta e de altura dinâmica, sem sobrepor endereços longos.
    endereco_emitente = f'CNPJ/CPF: {documento(empresa)}  |  {endereco(empresa)}'
    contato_empresa = ' | '.join(filter(None, [
        texto(getattr(empresa, 'email', None)), texto(getattr(empresa, 'telefone', None)),
    ]))
    pdf.fonte(tamanho=8.5)
    linhas_endereco = pdf.multi_cell(174, 4.2, pdf.codificar(endereco_emitente), split_only=True) or ['']
    pdf.fonte(tamanho=8)
    linhas_contato = pdf.multi_cell(174, 4, pdf.codificar(contato_empresa), split_only=True) if contato_empresa else []
    altura_emitente = 11 + len(linhas_endereco) * 4.2 + len(linhas_contato) * 4
    topo_emitente = 46
    pdf.set_xy(14, topo_emitente + 1)
    pdf.set_draw_color(215, 219, 225)
    pdf.set_fill_color(*pdf.CINZA)
    pdf.rect(14, topo_emitente, 182, altura_emitente, 'DF')
    pdf.set_xy(18, 49)
    pdf.fonte(True, 9.5)
    pdf.cell(174, 5, pdf.codificar(texto(getattr(empresa, 'nome', None), 'Emitente não informado')), ln=1)
    pdf.set_x(18)
    pdf.fonte(tamanho=8.5)
    pdf.multi_cell(174, 4.2, pdf.codificar(endereco_emitente))
    if contato_empresa:
        pdf.set_x(18)
        pdf.fonte(tamanho=8)
        pdf.multi_cell(174, 4, pdf.codificar(contato_empresa))

    linhas_cliente = [
        'CLIENTE / USUÁRIO FINAL', texto(getattr(cliente, 'nome', None), '-'),
        f'CNPJ/CPF: {documento(cliente)}', endereco(cliente),
        ' | '.join(filter(None, [texto(getattr(cliente, 'email', None)), texto(getattr(cliente, 'telefone', None))])),
    ]
    if texto(getattr(cliente, 'contato_comercial', None)):
        linhas_cliente.append(f"Contato comercial: {texto(cliente.contato_comercial)}")
    if texto(getattr(cliente, 'email_comercial', None)):
        linhas_cliente.append(f"E-mail comercial: {texto(cliente.email_comercial)}")
    bloco_cliente = '\n'.join(linhas_cliente)
    bloco_fornecedor = '\n'.join(filter(None, [
        'FORNECEDORA / EMITENTE', texto(getattr(empresa, 'nome', None), '-'),
        f'CNPJ/CPF: {documento(empresa)}',
        f'Responsável comercial: {texto(getattr(vendedor, "nome", None), "Não informado")}',
        texto(getattr(vendedor, 'email', None)), texto(getattr(vendedor, 'telefone', None)),
        f'Filial: {orcamento.filial.nome}' if getattr(orcamento, 'filial', None) else '',
    ]))
    pdf.set_y(topo_emitente + altura_emitente + 3)
    pdf.linha_tabela((bloco_cliente, bloco_fornecedor), (91, 91), fundo=True)
    pdf.ln(3)
    pdf.titulo('Itens da proposta')
    itens = list(orcamento.itens)
    pdf.garantir_espaco(22 if itens else 7)
    pdf.cabecalho_itens()
    for indice, item in enumerate(itens, 1):
        cadastro = item.produto if item.tipo_item == 'P' else item.servico
        descricao = texto(item.descricao)
        if descricao in ('', '-'):
            descricao = texto(getattr(cadastro, 'descricao_resumida', None) or getattr(cadastro, 'descricao', None), '-')
        quantidade = Decimal(str(item.quantidade or 0))
        qtd = format(quantidade, 'f').rstrip('0').rstrip('.') if '.' in format(quantidade, 'f') else str(quantidade)
        pdf.linha_tabela((
            f'{indice}\n{texto(getattr(cadastro, "codigo_interno", None), "-")}',
            descricao, qtd.replace('.', ','), moeda(item.valor_unitario).removeprefix('R$ '),
            moeda(item.valor_desconto).removeprefix('R$ '), moeda(item.valor_total).removeprefix('R$ '),
        ), pdf.LARGURAS_ITENS)
    if not itens:
        pdf.paragrafo('Nenhum item cadastrado nesta proposta.')
    pdf.ln(2)
    pdf.garantir_espaco(18)
    if getattr(orcamento, 'valor_desconto', None):
        pdf.set_x(14)
        pdf.fonte(tamanho=9)
        pdf.cell(182, 5, pdf.codificar(f'Desconto da proposta: {moeda(orcamento.valor_desconto)}'), align='R', ln=1)
    # O valor salvo é a fonte de verdade; não descontar novamente os descontos dos itens.
    pdf.set_fill_color(*pdf.CINZA)
    pdf.rect(108, pdf.get_y(), 88, 10, 'F')
    pdf.set_xy(110, pdf.get_y() + 1)
    pdf.set_text_color(*pdf.VERMELHO)
    pdf.fonte(True, 12)
    pdf.cell(84, 7, pdf.codificar(f'TOTAL DA PROPOSTA: R$ {Decimal(str(orcamento.valor_total or 0)):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')), align='R', ln=1)
    pdf.ln(4)

    pdf.titulo('Condições comerciais')
    numero_topico = 0
    for titulo, conteudo in (
        ('Objeto e escopo', getattr(orcamento, 'observacoes', None)),
        ('Informações técnicas / serviços', getattr(orcamento, 'detalhes_tecnicos', None)),
        ('Validade dos preços', getattr(orcamento, 'validade_precos', None)
         or f'Proposta válida até {data_formatada(orcamento.data_validade)}.'),
        ('Pagamento', getattr(orcamento, 'condicoes_pagamento', None)),
    ):
        if texto(conteudo):
            numero_topico += 1
            pdf.topico(f'{numero_topico}. {titulo}', conteudo)

    termos = texto(getattr(orcamento, 'termos_compra', None))
    if termos:
        pdf.titulo('Termos de fornecimento e contratação')
        # Preserva os tópicos, as quebras e as condições informadas, sem cláusulas fixas.
        for linha in termos.splitlines():
            if re.match(r'^\s*\d+[.)]\s+', linha):
                pdf.garantir_espaco(18)
                pdf.paragrafo(linha, negrito=True)
            elif linha.strip():
                pdf.paragrafo(linha)
            else:
                pdf.ln(2)
        pdf.ln(4)

    aceite = (
        f'Confirmamos o aceite dos produtos, serviços, valores e condições da proposta '
        f'{orcamento.numero}, emitida em {data_formatada(orcamento.data_emissao)}, '
        f'no valor total de {moeda(orcamento.valor_total)}, entre '
        f'{texto(getattr(cliente, "nome", None), "cliente não informado")} '
        f'(CNPJ/CPF: {documento(cliente)}) e '
        f'{texto(getattr(empresa, "nome", None), "emitente não informado")} '
        f'(CNPJ/CPF: {documento(empresa)}).'
    )
    pdf.fonte(tamanho=10)
    altura_aceite = len(pdf.linhas(aceite, 182)) * 5.2 + 68
    pdf.garantir_espaco(altura_aceite)
    pdf.titulo('Aceite da proposta')
    pdf.paragrafo(aceite)
    pdf.linha_tabela((
        f'CLIENTE\n{texto(getattr(cliente, "nome", None), "-")}\nCNPJ/CPF: {documento(cliente)}\n\nAssinatura: ______________________\nData da assinatura: ______ / ______ / __________',
        f'FORNECEDORA\n{texto(getattr(empresa, "nome", None), "-")}\nCNPJ/CPF: {documento(empresa)}\n\nAssinatura: ______________________\nData da assinatura: ______ / ______ / __________',
    ), (91, 91))
    pdf.ln(3)
    if getattr(orcamento, 'data_aprovacao', None):
        pdf.paragrafo(
            f'Aprovação registrada na proposta: {data_formatada(orcamento.data_aprovacao)} '
            '(não substitui a assinatura do cliente).', tamanho=9,
        )
    pdf.paragrafo(' | '.join(filter(None, [
        texto(getattr(empresa, 'nome', None)), texto(getattr(vendedor, 'nome', None)),
        texto(getattr(vendedor, 'email', None)),
    ])), tamanho=9)
    return pdf.output(dest='S').encode('latin-1')