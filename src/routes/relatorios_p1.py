"""Relatórios P1 — LiveSun Comercial.

Blueprint unificado com os relatórios de prioridade P1 (operação, auditoria e
gestão), organizados por módulo. Todos aplicam isolamento por ID_EMPRESA a
partir do usuário logado (nunca acessam dados de outra empresa) e permitem
exportação CSV.
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, Response, render_template, request
from flask_login import current_user, login_required

from src.models import (
    CompraNFManual,
    ContaBanco,
    Entidade,
    ImportacaoNFSe,
    Lancamento,
    Orcamento,
    PedidoVenda,
    Produto,
    User,
)
from src.models.contratos import Contrato
from src.models.locacao import LocacaoContrato, LocacaoManutencao, LocacaoPeca
from src.access_control import require_permission

relatorios_p1_bp = Blueprint('relatorios_p1', __name__, url_prefix='/relatorios-p1')


# =============================================================================
# Utilitários
# =============================================================================

def _empresa_id() -> int | None:
    """Empresa do usuário logado (nunca de outro tenant)."""
    return getattr(current_user, 'empresa_id', None)


def _brl(value) -> str:
    try:
        dec = Decimal(str(value or 0)).quantize(Decimal('0.01'))
    except Exception:
        dec = Decimal('0.00')
    s = f'{dec:,.2f}'
    return 'R$ ' + s.replace(',', 'X').replace('.', ',').replace('X', '.')


def _numero(value: Decimal) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal('0')


def _datad(value) -> str:
    return value.strftime('%d/%m/%Y') if value else '-'


def _parse_date(value) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except ValueError:
        return None


def _is_pagamento(lancamento) -> bool:
    fluxo = getattr(lancamento, 'fluxo_conta', None)
    if fluxo is not None and hasattr(fluxo, 'is_pagamento'):
        try:
            return bool(fluxo.is_pagamento())
        except Exception:
            return False
    return False


def _csv_response(filename: str, headers, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([('' if c is None else str(c)) for c in row])
    return Response(
        buffer.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )


def _render(report_key, title, subtitle, headers, rows,
            filter_fields=None, totals=None):
    """Renderiza HTML ou CSV conforme parâmetro `formato`."""
    if (request.args.get('formato') or '').strip().lower() == 'csv':
        return _csv_response(f'{report_key}.csv', headers, rows)
    return render_template(
        'relatorios/p1_generic.html',
        report_key=report_key,
        title=title,
        subtitle=subtitle,
        headers=headers,
        rows=rows,
        filter_fields=filter_fields or [],
        totals=totals or [],
    )


# =============================================================================
# 1. ADMINISTRAÇÃO
# =============================================================================

@relatorios_p1_bp.route('/usuarios')
@login_required
@require_permission('relatorios')
def usuarios():
    """Usuários ativos e inativos da empresa."""
    eid = _empresa_id()
    if not eid:
        return _render('usuarios', 'Usuários', 'Sem empresa vinculada.',
                       ['Usuário'], [])

    query = User.query.filter_by(empresa_id=eid)
    status_f = (request.args.get('status') or '').strip().lower()
    role_f = (request.args.get('role') or '').strip()
    if status_f == 'ativos':
        query = query.filter(User.is_active.is_(True))
    elif status_f == 'inativos':
        query = query.filter(User.is_active.is_(False))
    if role_f:
        query = query.filter(User.role == role_f)

    usuarios = query.order_by(User.full_name.asc(), User.username.asc()).all()

    headers = ['Usuário', 'Nome', 'E-mail', 'Perfil', 'Status', 'Criado em']
    rows = [[
        u.username,
        u.full_name or '-',
        u.email or '-',
        (u.role or '-').capitalize(),
        'Ativo' if u.is_active else 'Inativo',
        _datad(u.created_at.date() if u.created_at else None),
    ] for u in usuarios]

    total = len(usuarios)
    ativos = sum(1 for u in usuarios if u.is_active)
    totals = [
        ('Total', str(total)),
        ('Ativos', str(ativos)),
        ('Inativos', str(total - ativos)),
    ]
    fields = [
        {'name': 'status', 'label': 'Status', 'type': 'select',
         'value': status_f, 'options': [
             ('', 'Todos'), ('ativos', 'Ativos'),
             ('inativos', 'Inativos')]},
        {'name': 'role', 'label': 'Perfil', 'type': 'select',
         'value': role_f, 'options': [
             ('', 'Todos'), ('admin', 'Admin'), ('operator', 'Operador'),
             ('viewer', 'Visualizador')]},
    ]
    return _render('usuarios', 'Relatório — Usuários Ativos e Inativos',
                   'Administração · Todos os dados restritos à empresa logada.',
                   headers, rows, fields, totals)


# =============================================================================
# 2. CADASTROS
# =============================================================================

@relatorios_p1_bp.route('/entidades')
@login_required
@require_permission('relatorios')
def entidades():
    """Entidades por tipo, cidade/UF e status."""
    eid = _empresa_id()
    query = Entidade.query.filter_by(empresa_id=eid)
    tipo_f = (request.args.get('tipo') or '').strip().upper()
    uf_f = (request.args.get('uf') or '').strip().upper()
    status_f = (request.args.get('status') or '').strip().lower()
    if tipo_f:
        query = query.filter(Entidade.tipo == tipo_f)
    if uf_f:
        query = query.filter(Entidade.endereco_uf == uf_f)
    if status_f == 'ativos':
        query = query.filter(Entidade.ativo.is_(True))
    elif status_f == 'inativos':
        query = query.filter(Entidade.ativo.is_(False))

    entidades = query.order_by(Entidade.nome.asc()).all()
    headers = ['Nome', 'Documento', 'Tipo', 'Cidade', 'UF', 'Vendedor', 'Status']
    rows = [[
        e.nome,
        e.cnpj_cpf or '-',
        e.get_tipo_descricao(),
        e.endereco_cidade or '-',
        e.endereco_uf or '-',
        e.vendedor.nome if e.vendedor else '-',
        'Ativo' if e.ativo else 'Inativo',
    ] for e in entidades]

    qtd_c = sum(1 for e in entidades if e.tipo == 'C')
    qtd_f = sum(1 for e in entidades if e.tipo == 'F')
    totals = [
        ('Total', str(len(entidades))),
        ('Clientes', str(qtd_c)),
        ('Fornecedores', str(qtd_f)),
    ]
    fields = [
        {'name': 'tipo', 'label': 'Tipo', 'type': 'select',
         'value': tipo_f, 'options': [
             ('', 'Todos'), ('C', 'Cliente'), ('F', 'Fornecedor'),
             ('V', 'Vendedor'), ('L', 'Funcionário')]},
        {'name': 'uf', 'label': 'UF', 'type': 'text', 'value': uf_f},
        {'name': 'status', 'label': 'Status', 'type': 'select',
         'value': status_f, 'options': [
             ('', 'Todos'), ('ativos', 'Ativos'), ('inativos', 'Inativos')]},
    ]
    return _render('entidades', 'Relatório — Entidades',
                   'Cadastros · Tipo, cidade, UF e status.',
                   headers, rows, fields, totals)


@relatorios_p1_bp.route('/clientes-comissao')
@login_required
@require_permission('relatorios')
def clientes_comissao():
    """Clientes com vendedor e comissão configurados (base de apuração)."""
    eid = _empresa_id()
    query = Entidade.query.filter(Entidade.empresa_id == eid, Entidade.tipo == 'C')
    vendedor_f = request.args.get('vendedor', type=int)
    if vendedor_f:
        query = query.filter(Entidade.vendedor_id == vendedor_f)

    clientes = query.order_by(Entidade.nome.asc()).all()
    headers = ['Cliente', 'Documento', 'Vendedor', 'Alíquota %', 'Repasse', 'Status']
    rows = []
    for c in clientes:
        sem_comissao = (c.aliquota_comissao_especifica is None and
                        _numero(c.valor_repasse) <= 0)
        rows.append([
            c.nome,
            c.cnpj_cpf or '-',
            c.vendedor.nome if c.vendedor else '—',
            f'{_numero(c.aliquota_comissao_especifica)}%' if c.aliquota_comissao_especifica is not None else '—',
            _brl(c.valor_repasse) if _numero(c.valor_repasse) > 0 else '—',
            'SEM CONFIG.' if sem_comissao else 'OK',
        ])

    ok = sum(1 for c in clientes
             if c.aliquota_comissao_especifica is not None or _numero(c.valor_repasse) > 0)
    sem = len(clientes) - ok
    totals = [
        ('Total clientes', str(len(clientes))),
        ('Com comissão', str(ok)),
        ('Sem config.', str(sem)),
    ]
    fields = [
        {'name': 'vendedor', 'label': 'Vendedor (ID)', 'type': 'number',
         'value': str(vendedor_f) if vendedor_f else ''},
    ]
    return _render('clientes-comissao', 'Relatório — Clientes com Vendedor e Comissão',
                   'Cadastros · Base para apuração de comissão.',
                   headers, rows, fields, totals)


# =============================================================================
# 3. COMERCIAL
# =============================================================================

@relatorios_p1_bp.route('/orcamentos')
@login_required
@require_permission('relatorios')
def orcamentos():
    """Orçamentos por status, conversão e validade."""
    eid = _empresa_id()
    query = Orcamento.query.filter_by(empresa_id=eid)
    status_f = (request.args.get('status') or '').strip()
    d_ini = _parse_date(request.args.get('data_inicio'))
    d_fim = _parse_date(request.args.get('data_fim'))
    if status_f:
        query = query.filter(Orcamento.status == status_f)
    if d_ini:
        query = query.filter(Orcamento.data_emissao >= d_ini)
    if d_fim:
        query = query.filter(Orcamento.data_emissao <= d_fim)

    items = query.order_by(Orcamento.data_emissao.desc()).all()
    headers = ['N°', 'Data', 'Cliente', 'Vendedor', 'Status', 'Validade', 'Valor Total']
    hoje = date.today()
    rows = []
    for o in items:
        val = 'Expirado' if o.data_validade and o.data_validade < hoje else _datad(o.data_validade)
        rows.append([
            o.numero,
            _datad(o.data_emissao),
            o.cliente.nome if o.cliente else '-',
            o.vendedor.nome if o.vendedor else '-',
            (o.status or '-').replace('_', ' ').capitalize(),
            val,
            _brl(o.valor_total),
        ])
    convertidos = sum(1 for o in items if o.status == 'convertido')
    totals = [
        ('Total', str(len(items))),
        ('Convertidos', str(convertidos)),
        ('Valor total', _brl(sum((_numero(o.valor_total) for o in items), Decimal('0')))),
    ]
    fields = [
        {'name': 'status', 'label': 'Status', 'type': 'select',
         'value': status_f, 'options': [
             ('', 'Todos'), ('emitido', 'Emitido'), ('aprovado', 'Aprovado'),
             ('rejeitado', 'Rejeitado'), ('convertido', 'Convertido'),
             ('expirado', 'Expirado'), ('cancelado', 'Cancelado')]},
        {'name': 'data_inicio', 'label': 'De', 'type': 'date',
         'value': request.args.get('data_inicio', '')},
        {'name': 'data_fim', 'label': 'Até', 'type': 'date',
         'value': request.args.get('data_fim', '')},
    ]
    return _render('orcamentos', 'Relatório — Orçamentos',
                   'Comercial · Status, conversão e validade.',
                   headers, rows, fields, totals)


@relatorios_p1_bp.route('/pedidos')
@login_required
@require_permission('relatorios')
def pedidos():
    """Pedidos por status, atendimento e faturamento."""
    eid = _empresa_id()
    query = PedidoVenda.query.filter_by(empresa_id=eid)
    status_f = (request.args.get('status') or '').strip()
    d_ini = _parse_date(request.args.get('data_inicio'))
    d_fim = _parse_date(request.args.get('data_fim'))
    if status_f:
        query = query.filter(PedidoVenda.status == status_f)
    if d_ini:
        query = query.filter(PedidoVenda.data_emissao >= d_ini)
    if d_fim:
        query = query.filter(PedidoVenda.data_emissao <= d_fim)

    items = query.order_by(PedidoVenda.data_emissao.desc()).all()
    headers = ['N°', 'Data', 'Cliente', 'Vendedor', 'Status',
               'Data Faturamento', 'Valor Total']
    rows = [[
        p.numero,
        _datad(p.data_emissao),
        p.cliente.nome if p.cliente else '-',
        p.vendedor.nome if p.vendedor else '-',
        (p.status or '-').replace('_', ' ').capitalize(),
        _datad(p.data_faturamento),
        _brl(p.valor_total),
    ] for p in items]

    nao_faturados = sum(1 for p in items if not p.data_faturamento and p.status != 'cancelado')
    totals = [
        ('Total pedidos', str(len(items))),
        ('Não faturados', str(nao_faturados)),
        ('Valor total', _brl(sum((_numero(p.valor_total) for p in items), Decimal('0')))),
    ]
    fields = [
        {'name': 'status', 'label': 'Status', 'type': 'select',
         'value': status_f, 'options': [
             ('', 'Todos'), ('aprovado', 'Aprovado'),
             ('em_producao', 'Em produção'), ('pronto', 'Pronto'),
             ('faturado', 'Faturado'), ('entregue', 'Entregue'),
             ('cancelado', 'Cancelado')]},
        {'name': 'data_inicio', 'label': 'De', 'type': 'date',
         'value': request.args.get('data_inicio', '')},
        {'name': 'data_fim', 'label': 'Até', 'type': 'date',
         'value': request.args.get('data_fim', '')},
    ]
    return _render('pedidos', 'Relatório — Pedidos',
                   'Comercial · Status, atendimento parcial e faturamento.',
                   headers, rows, fields, totals)


@relatorios_p1_bp.route('/estoque')
@login_required
@require_permission('relatorios')
def estoque():
    """Estoque atual, mínimo e situação por produto."""
    eid = _empresa_id()
    query = Produto.query.filter_by(empresa_id=eid)
    abaixo = (request.args.get('abaixo') or '').strip() == '1'
    if abaixo:
        query = query.filter(Produto.controla_estoque.is_(True),
                             Produto.estoque_atual < Produto.estoque_minimo)

    items = query.order_by(Produto.descricao_resumida.asc()).all()
    headers = ['Código', 'Descrição', 'Contr. Estoque', 'Est. Atual', 'Mínimo',
               'Custo', 'Venda', 'Situação']
    rows = []
    abaixo_qtd = 0
    for p in items:
        situacao = 'Ativo'
        if not p.ativo:
            situacao = 'Inativo'
        elif p.controla_estoque and _numero(p.estoque_atual) < _numero(p.estoque_minimo):
            situacao = 'ABAIXO DO MÍN.'
            abaixo_qtd += 1
        rows.append([
            p.codigo_interno,
            p.descricao_resumida,
            'Sim' if p.controla_estoque else 'Não',
            f'{float(_numero(p.estoque_atual)):g}',
            f'{float(_numero(p.estoque_minimo)):g}',
            _brl(p.valor_custo),
            _brl(p.valor_venda_padrao),
            situacao,
        ])
    totals = [
        ('Produtos', str(len(items))),
        ('Abaixo do mínimo', str(abaixo_qtd)),
    ]
    fields = [
        {'name': 'abaixo', 'label': 'Filtrar', 'type': 'select',
         'value': request.args.get('abaixo', ''), 'options': [
             ('', 'Todos'), ('1', 'Apenas abaixo do mínimo')]},
    ]
    return _render('estoque', 'Relatório — Estoque Atual',
                   'Comercial · Posição, mínimo e alertas.',
                   headers, rows, fields, totals)


@relatorios_p1_bp.route('/compras')
@login_required
@require_permission('relatorios')
def compras():
    """Compras manuais por fornecedor, data e total."""
    eid = _empresa_id()
    query = CompraNFManual.query.filter_by(empresa_id=eid)
    fornecedor_f = request.args.get('fornecedor', type=int)
    status_f = (request.args.get('status') or '').strip()
    d_ini = _parse_date(request.args.get('data_inicio'))
    d_fim = _parse_date(request.args.get('data_fim'))
    if fornecedor_f:
        query = query.filter(CompraNFManual.fornecedor_id == fornecedor_f)
    if status_f:
        query = query.filter(CompraNFManual.status == status_f)
    if d_ini:
        query = query.filter(CompraNFManual.data_emissao >= d_ini)
    if d_fim:
        query = query.filter(CompraNFManual.data_emissao <= d_fim)

    items = query.order_by(CompraNFManual.data_emissao.desc()).all()
    headers = ['N°', 'Data', 'Fornecedor', 'Status', 'Valor Total']
    rows = [[
        c.numero_documento,
        _datad(c.data_emissao),
        c.fornecedor.nome if c.fornecedor else '-',
        (c.status or 'registrada').replace('_', ' ').capitalize(),
        _brl(c.valor_total),
    ] for c in items]

    totals = [
        ('Compras', str(len(items))),
        ('Valor total', _brl(sum((_numero(c.valor_total) for c in items), Decimal('0')))),
    ]
    fields = [
        {'name': 'fornecedor', 'label': 'Fornecedor (ID)', 'type': 'number',
         'value': str(fornecedor_f) if fornecedor_f else ''},
        {'name': 'data_inicio', 'label': 'De', 'type': 'date',
         'value': request.args.get('data_inicio', '')},
        {'name': 'data_fim', 'label': 'Até', 'type': 'date',
         'value': request.args.get('data_fim', '')},
        {'name': 'status', 'label': 'Status', 'type': 'select',
         'value': status_f, 'options': [
             ('', 'Todos'), ('registrada', 'Registrada'),
             ('cancelada', 'Cancelada')]},
    ]
    return _render('compras', 'Relatório — Compras Manuais',
                   'Comercial · Por fornecedor, data e total.',
                   headers, rows, fields, totals)


# =============================================================================
# 4. FINANCEIRO
# =============================================================================

@relatorios_p1_bp.route('/saldo-contas')
@login_required
@require_permission('relatorios')
def saldo_contas():
    """Saldo por conta bancária (saldo inicial + movimentações realizadas)."""
    eid = _empresa_id()
    conta_f = request.args.get('conta', type=int)
    query = ContaBanco.query.filter_by(empresa_id=eid)
    if conta_f:
        query = query.filter(ContaBanco.id == conta_f)

    contas = query.order_by(ContaBanco.nome.asc()).all()
    headers = ['Conta', 'Banco', 'Saldo Inicial', 'Entradas', 'Saídas',
               'Saldo Atual', 'Principal']
    rows = []
    for c in contas:
        lanc = Lancamento.query.filter_by(empresa_id=eid, conta_banco_id=c.id).all()
        entradas = Decimal('0')
        saidas = Decimal('0')
        for l in lanc:
            if l.status != 'pago':
                continue
            valor = _numero(l.valor_pago)
            if _is_pagamento(l):
                saidas += valor
            else:
                entradas += valor
        saldo = _numero(c.saldo_inicial) + entradas - saidas
        rows.append([
            c.nome,
            c.banco,
            _brl(c.saldo_inicial),
            _brl(entradas),
            _brl(saidas),
            _brl(saldo),
            'Sim' if c.is_principal else 'Não',
        ])
    saldo_total = sum((_numero(c.saldo_inicial) for c in contas), Decimal('0'))
    totals = [('Contas', str(len(contas))), ('Saldo inicial total', _brl(saldo_total))]
    fields = [
        {'name': 'conta', 'label': 'Conta (ID)', 'type': 'number',
         'value': str(conta_f) if conta_f else ''},
    ]
    return _render('saldo-contas', 'Relatório — Saldo por Conta Bancária',
                   'Financeiro · Saldo inicial + movimentações realizadas.',
                   headers, rows, fields, totals)


@relatorios_p1_bp.route('/fluxo-categorias')
@login_required
@require_permission('relatorios')
def fluxo_categorias():
    """Receitas e despesas analíticas por categoria do fluxo."""
    eid = _empresa_id()
    d_ini = _parse_date(request.args.get('data_inicio'))
    d_fim = _parse_date(request.args.get('data_fim'))

    query = Lancamento.query.filter_by(empresa_id=eid)
    if d_ini:
        query = query.filter(Lancamento.data_vencimento >= d_ini)
    if d_fim:
        query = query.filter(Lancamento.data_vencimento <= d_fim)
    lancamentos = query.all()

    grupos = {}
    for l in lancamentos:
        fluxo = getattr(l, 'fluxo_conta', None)
        key = getattr(fluxo, 'id', 0) or 0
        if key not in grupos:
            grupos[key] = {
                'codigo': getattr(fluxo, 'codigo', None) or '-',
                'descricao': getattr(fluxo, 'descricao', None) or 'Sem categoria',
                'tipo': fluxo.get_tipo_descricao() if fluxo else '-',
                'previsto': Decimal('0'),
                'realizado': Decimal('0'),
            }
        g = grupos[key]
        if l.status == 'pago':
            g['realizado'] += _numero(l.valor_pago)
        else:
            g['previsto'] += _numero(l.valor_real)

    headers = ['Código', 'Categoria', 'Tipo', 'Previsto', 'Realizado', 'Saldo']
    rows = []
    total_r = Decimal('0')
    total_p = Decimal('0')
    for g in sorted(grupos.values(), key=lambda x: (x['codigo'], x['descricao'])):
        saldo = g['realizado'] - g['previsto']
        total_r += g['realizado']
        total_p += g['previsto']
        rows.append([
            g['codigo'],
            g['descricao'],
            g['tipo'],
            _brl(g['previsto']),
            _brl(g['realizado']),
            _brl(saldo),
        ])
    totals = [
        ('Previsto', _brl(total_p)),
        ('Realizado', _brl(total_r)),
        ('Saldo', _brl(total_r - total_p)),
    ]
    fields = [
        {'name': 'data_inicio', 'label': 'De', 'type': 'date',
         'value': request.args.get('data_inicio', '')},
        {'name': 'data_fim', 'label': 'Até', 'type': 'date',
         'value': request.args.get('data_fim', '')},
    ]
    return _render('fluxo-categorias', 'Relatório — Receitas e Despesas por Categoria',
                   'Financeiro · Previsto x realizado agrupado por conta de fluxo.',
                   headers, rows, fields, totals)


# =============================================================================
# 5. FISCAL / SERVIÇOS
# =============================================================================

@relatorios_p1_bp.route('/nfse')
@login_required
@require_permission('relatorios')
def nfse():
    """NFS-e importadas por período, status, tomador e serviço."""
    eid = _empresa_id()
    query = ImportacaoNFSe.query.filter_by(empresa_id=eid)
    status_f = (request.args.get('status') or '').strip()
    d_ini = _parse_date(request.args.get('data_inicio'))
    d_fim = _parse_date(request.args.get('data_fim'))
    if status_f:
        query = query.filter(ImportacaoNFSe.status_importacao == status_f)
    if d_ini:
        query = query.filter(ImportacaoNFSe.data_emissao >= d_ini)
    if d_fim:
        query = query.filter(ImportacaoNFSe.data_emissao <= d_fim)

    notas = query.order_by(ImportacaoNFSe.data_emissao.desc()).all()
    headers = ['N° Nota', 'Emissão', 'Tomador', 'Serviço', 'Valor Bruto',
               'Status', 'Importada em']
    rows = [[
        n.numero_nota,
        _datad(n.data_emissao),
        n.entidade.nome if n.entidade else (n.cnpj_tomador or '-'),
        (n.descricao_servico or '-')[:80],
        _brl(n.valor_bruto),
        (n.status_importacao or 'sucesso').replace('_', ' ').capitalize(),
        _datad(n.data_importacao.date() if n.data_importacao else None),
    ] for n in notas]

    totals = [
        ('Notas', str(len(notas))),
        ('Valor total', _brl(sum((_numero(n.valor_bruto) for n in notas), Decimal('0')))),
    ]
    fields = [
        {'name': 'data_inicio', 'label': 'De', 'type': 'date',
         'value': request.args.get('data_inicio', '')},
        {'name': 'data_fim', 'label': 'Até', 'type': 'date',
         'value': request.args.get('data_fim', '')},
        {'name': 'status', 'label': 'Status', 'type': 'select',
         'value': status_f, 'options': [
             ('', 'Todos'), ('sucesso', 'Sucesso'),
             ('pendente', 'Pendente'), ('erro', 'Erro')]},
    ]
    return _render('nfse', 'Relatório — NFS-e Importadas',
                   'Fiscal/Serviços · Por período, status, tomador e serviço.',
                   headers, rows, fields, totals)


# =============================================================================
# 6. LOCAÇÃO
# =============================================================================

@relatorios_p1_bp.route('/locacao-pecas')
@login_required
@require_permission('relatorios')
def locacao_pecas():
    """Peças e kits cadastrados no acervo de locação."""
    eid = _empresa_id()
    query = LocacaoPeca.query.filter_by(empresa_id=eid)
    cat_f = (request.args.get('categoria') or '').strip()
    estado_f = (request.args.get('estado') or '').strip()
    if cat_f:
        query = query.filter(LocacaoPeca.categoria == cat_f)
    if estado_f:
        query = query.filter(LocacaoPeca.estado_fisico == estado_f)

    items = query.order_by(LocacaoPeca.codigo_interno.asc()).all()
    headers = ['Código', 'Descrição', 'Categoria', 'Tamanho', 'Preço Aluguel',
               'Estado', 'Ativo']
    rows = [[
        p.codigo_interno,
        p.descricao,
        p.categoria,
        p.tamanho or '-',
        _brl(p.preco_aluguel_diario),
        (p.estado_fisico or 'novo').capitalize(),
        'Sim' if p.ativo else 'Não',
    ] for p in items]
    catalogo = sum(1 for p in items if p.ativo)
    totals = [
        ('Itens', str(len(items))),
        ('Catálogo ativo', str(catalogo)),
    ]
    fields = [
        {'name': 'categoria', 'label': 'Categoria', 'type': 'text', 'value': cat_f},
        {'name': 'estado', 'label': 'Estado', 'type': 'select',
         'value': estado_f, 'options': [
             ('', 'Todos'), ('novo', 'Novo'), ('bom', 'Bom'),
             ('regular', 'Regular'), ('ruim', 'Ruim'), ('descartado', 'Descartado')]},
    ]
    return _render('locacao-pecas', 'Relatório — Peças e Kits (Acervo)',
                   'Locação · Cadastro do acervo.',
                   headers, rows, fields, totals)


@relatorios_p1_bp.route('/locacao-contratos')
@login_required
@require_permission('relatorios')
def locacao_contratos():
    """Contratos de locação por status."""
    eid = _empresa_id()
    query = LocacaoContrato.query.filter_by(empresa_id=eid)
    status_f = (request.args.get('status') or '').strip()
    if status_f:
        query = query.filter(LocacaoContrato.status == status_f)

    items = query.order_by(LocacaoContrato.data_contrato.desc()).all()
    headers = ['N°', 'Data', 'Cliente', 'Retirada', 'Devolução', 'Valor Total', 'Status']
    rows = [[
        c.numero,
        _datad(c.data_contrato),
        c.cliente.nome if c.cliente else '-',
        _datad(c.data_retirada),
        _datad(c.data_devolucao),
        _brl(c.valor_total),
        (c.status or 'assinado').replace('_', ' ').capitalize(),
    ] for c in items]

    hoje = date.today()
    atrasados = sum(1 for c in items
                    if c.status in ('assinado', 'ativo') and c.data_devolucao and c.data_devolucao < hoje)
    totals = [
        ('Contratos', str(len(items))),
        ('Atrasados', str(atrasados)),
        ('Valor total', _brl(sum((_numero(c.valor_total) for c in items), Decimal('0')))),
    ]
    fields = [
        {'name': 'status', 'label': 'Status', 'type': 'select',
         'value': status_f, 'options': [
             ('', 'Todos'), ('assinado', 'Assinado'), ('ativo', 'Ativo'),
             ('finalizado', 'Finalizado'), ('cancelado', 'Cancelado')]},
    ]
    return _render('locacao-contratos', 'Relatório — Contratos de Locação',
                   'Locação · Contratos por status e atraso de devolução.',
                   headers, rows, fields, totals)


@relatorios_p1_bp.route('/locacao-manutencao')
@login_required
@require_permission('relatorios')
def locacao_manutencao():
    """Peças em manutenção / reparo."""
    eid = _empresa_id()
    query = LocacaoManutencao.query.filter_by(empresa_id=eid)
    status_f = (request.args.get('status') or '').strip()
    if status_f:
        query = query.filter(LocacaoManutencao.status == status_f)

    items = query.order_by(LocacaoManutencao.data_entrada.desc()).all()
    headers = ['Item', 'Tipo de Serviço', 'Entrada', 'Saída Prevista', 'Saída',
               'Valor', 'Status']
    rows = [[
        m.peca.descricao if m.peca else '-',
        (m.tipo_servico or '-').replace('_', ' ').capitalize(),
        _datad(m.data_entrada),
        _datad(m.data_saida_prevista),
        _datad(m.data_saida),
        _brl(m.valor_total),
        (m.status or 'pendente').replace('_', ' ').capitalize(),
    ] for m in items]

    em_aberto = sum(1 for m in items if m.status in ('pendente', 'em_andamento'))
    hoje = date.today()
    atrasada = sum(1 for m in items
                   if m.status in ('pendente', 'em_andamento') and m.data_saida_prevista and m.data_saida_prevista < hoje)
    totals = [
        ('Manutenções', str(len(items))),
        ('Em aberto', str(em_aberto)),
        ('Atrasadas', str(atrasada)),
    ]
    fields = [
        {'name': 'status', 'label': 'Status', 'type': 'select',
         'value': status_f, 'options': [
             ('', 'Todos'), ('pendente', 'Pendente'),
             ('em_andamento', 'Em andamento'), ('concluida', 'Concluída'),
             ('cancelada', 'Cancelada')]},
    ]
    return _render('locacao-manutencao', 'Relatório — Peças em Manutenção',
                   'Locação · Disponibilidade do acervo.',
                   headers, rows, fields, totals)


# =============================================================================
# 7. CONTRATOS
# =============================================================================

@relatorios_p1_bp.route('/contratos')
@login_required
@require_permission('relatorios')
def contratos():
    """Contratos de serviços por status, vigência e valor."""
    eid = _empresa_id()
    query = Contrato.query.filter_by(empresa_id=eid)
    status_f = (request.args.get('status') or '').strip()
    if status_f:
        query = query.filter(Contrato.status == status_f)

    items = query.order_by(Contrato.data_inicio_vigencia.desc()).all()
    headers = ['N°', 'Título', 'Cliente', 'Início', 'Fim', 'Valor Mensal',
               'Valor Total', 'Status']
    hoje = date.today()
    rows = []
    for c in items:
        vig = _datad(c.data_fim_vigencia)
        if c.data_fim_vigencia and c.status in ('assinado', 'aguardando_assinatura') and c.data_fim_vigencia < hoje:
            vig = f'{vig} (expirado)'
        rows.append([
            f'{c.serie}-{c.numero}' if c.serie else c.numero,
            c.titulo or '-',
            c.cliente.nome if c.cliente else '-',
            _datad(c.data_inicio_vigencia),
            vig,
            _brl(c.valor_mensal) if c.valor_mensal else '—',
            _brl(c.valor_total),
            (c.status or 'rascunho').replace('_', ' ').capitalize(),
        ])
    totals = [
        ('Contratos', str(len(items))),
        ('Valor total', _brl(sum((_numero(c.valor_total) for c in items), Decimal('0')))),
    ]
    fields = [
        {'name': 'status', 'label': 'Status', 'type': 'select',
         'value': status_f, 'options': [
             ('', 'Todos'), ('rascunho', 'Rascunho'),
             ('aguardando_assinatura', 'Aguardando assinatura'),
             ('assinado', 'Assinado'), ('cancelado', 'Cancelado'),
             ('rescindido', 'Rescindido')]},
    ]
    return _render('contratos', 'Relatório — Contratos de Serviços',
                   'Contratos · Por status, vigência e valor.',
                   headers, rows, fields, totals)
