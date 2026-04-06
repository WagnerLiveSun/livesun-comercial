from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Optional

from sqlalchemy import case, func

from src.models import ContaBanco, FluxoContaModel, Lancamento
from src.tenant import scoped_query, tenant_id


def _period_start(data_ref: date, agrupar_por: str) -> date:
    if agrupar_por == 'semana':
        return data_ref - timedelta(days=data_ref.weekday())
    if agrupar_por == 'mes':
        return date(data_ref.year, data_ref.month, 1)
    return data_ref


def _to_decimal(value) -> Decimal:
    return Decimal(str(value or 0))


def _build_sinteticas(linhas_periodo: list[dict], contas_fluxo: list[FluxoContaModel]) -> list[dict]:
    analiticas = [l for l in linhas_periodo if l.get('nivel_analitico') is not None]
    sinteticas = [c for c in contas_fluxo if c.nivel_analitico is None]

    for conta_sint in sinteticas:
        prefixo = f"{conta_sint.codigo}."
        filhos = [
            l for l in analiticas
            if l.get('codigo', '').startswith(prefixo)
        ]
        if not filhos:
            continue

        previsto = sum((l['previsto'] for l in filhos), Decimal('0.00'))
        realizado = sum((l['realizado'] for l in filhos), Decimal('0.00'))
        desvio = realizado - previsto
        desvio_pct = (desvio / previsto * Decimal('100')) if previsto != 0 else Decimal('0.00')

        linhas_periodo.append({
            'codigo': conta_sint.codigo,
            'descricao': conta_sint.descricao,
            'tipo': conta_sint.tipo,
            'nivel_sintetico': conta_sint.nivel_sintetico,
            'nivel_analitico': conta_sint.nivel_analitico,
            'nivel': conta_sint.nivel_sintetico or 0,
            'previsto': previsto,
            'realizado': realizado,
            'disponivel': sum((l['disponivel'] for l in filhos), Decimal('0.00')),
            'desvio': desvio,
            'desvio_pct': desvio_pct,
            'is_sintetica': True,
        })

    return linhas_periodo


def gerar_relatorio_fluxo(
    empresa_id: int,
    data_inicio: date,
    data_fim: date,
    tipo: Optional[str] = None,
    conta_banco_id: Optional[int] = None,
    entidade_id: Optional[int] = None,
    agrupar_por: str = 'dia',
) -> dict:
    empresa_scope = tenant_id() if tenant_id() else empresa_id

    data_ref_expr = func.coalesce(Lancamento.data_vencimento, Lancamento.data_evento)
    valor_previsto_expr = func.sum(
        case((Lancamento.status == 'aberto', Lancamento.valor_real), else_=0)
    )
    valor_realizado_expr = func.sum(
        case((Lancamento.status == 'pago', Lancamento.valor_pago), else_=0)
    )

    query = (
        scoped_query(Lancamento)
        .join(FluxoContaModel, FluxoContaModel.id == Lancamento.fluxo_conta_id)
        .outerjoin(ContaBanco, ContaBanco.id == Lancamento.conta_banco_id)
        .with_entities(
            data_ref_expr.label('data_ref'),
            FluxoContaModel.id.label('fluxo_id'),
            FluxoContaModel.codigo.label('codigo'),
            FluxoContaModel.descricao.label('descricao'),
            FluxoContaModel.tipo.label('tipo'),
            FluxoContaModel.nivel_sintetico.label('nivel_sintetico'),
            FluxoContaModel.nivel_analitico.label('nivel_analitico'),
            valor_previsto_expr.label('valor_previsto'),
            valor_realizado_expr.label('valor_realizado'),
            ContaBanco.id.label('conta_banco_id'),
            ContaBanco.saldo_inicial.label('valor_disponivel'),
        )
        .filter(Lancamento.empresa_id == empresa_scope)
        .filter(data_ref_expr.between(data_inicio, data_fim))
    )

    if tipo in {'R', 'P'}:
        query = query.filter(FluxoContaModel.tipo == tipo)
    if conta_banco_id:
        query = query.filter(Lancamento.conta_banco_id == conta_banco_id)
    if entidade_id:
        query = query.filter(Lancamento.entidade_id == entidade_id)

    rows = (
        query.group_by(
            data_ref_expr,
            FluxoContaModel.id,
            FluxoContaModel.codigo,
            FluxoContaModel.descricao,
            FluxoContaModel.tipo,
            FluxoContaModel.nivel_sintetico,
            FluxoContaModel.nivel_analitico,
            ContaBanco.id,
            ContaBanco.saldo_inicial,
        )
        .order_by(data_ref_expr.asc(), FluxoContaModel.codigo.asc())
        .all()
    )

    contas_fluxo = scoped_query(FluxoContaModel).filter_by(ativo=True).all()
    if tipo in {'R', 'P'}:
        contas_fluxo = [c for c in contas_fluxo if c.tipo == tipo]

    por_periodo_fluxo: dict[tuple[date, int], dict] = {}
    contas_periodo_fluxo: dict[tuple[date, int], set[tuple[int, Decimal]]] = defaultdict(set)
    contas_disponiveis_unicas: set[tuple[int, Decimal]] = set()

    for row in rows:
        data_row = row.data_ref
        if not data_row:
            continue

        periodo = _period_start(data_row, agrupar_por)
        key = (periodo, int(row.fluxo_id or 0))

        if key not in por_periodo_fluxo:
            nivel = row.nivel_analitico if row.nivel_analitico is not None else row.nivel_sintetico
            por_periodo_fluxo[key] = {
                'data_obj': periodo,
                'codigo': row.codigo or '-',
                'descricao': row.descricao or '-',
                'tipo': row.tipo or '-',
                'nivel_sintetico': row.nivel_sintetico,
                'nivel_analitico': row.nivel_analitico,
                'nivel': int(nivel or 0),
                'previsto': Decimal('0.00'),
                'realizado': Decimal('0.00'),
                'disponivel': Decimal('0.00'),
                'desvio': Decimal('0.00'),
                'desvio_pct': Decimal('0.00'),
                'is_sintetica': row.nivel_analitico is None,
            }

        item = por_periodo_fluxo[key]
        item['previsto'] += _to_decimal(row.valor_previsto)
        item['realizado'] += _to_decimal(row.valor_realizado)

        conta_id = row.conta_banco_id
        saldo_disp = _to_decimal(row.valor_disponivel)
        if conta_id is not None:
            contas_periodo_fluxo[key].add((int(conta_id), saldo_disp))
            contas_disponiveis_unicas.add((int(conta_id), saldo_disp))

    for key, item in por_periodo_fluxo.items():
        item['disponivel'] = sum((saldo for _, saldo in contas_periodo_fluxo.get(key, set())), Decimal('0.00'))
        item['desvio'] = item['realizado'] - item['previsto']
        item['desvio_pct'] = (item['desvio'] / item['previsto'] * Decimal('100')) if item['previsto'] != 0 else Decimal('0.00')

    por_periodo: dict[date, list[dict]] = defaultdict(list)
    for item in por_periodo_fluxo.values():
        por_periodo[item['data_obj']].append(item)

    linhas: list[dict] = []
    totais = {
        'total_previsto_r': Decimal('0.00'),
        'total_realizado_r': Decimal('0.00'),
        'total_previsto_p': Decimal('0.00'),
        'total_realizado_p': Decimal('0.00'),
        'saldo_previsto': Decimal('0.00'),
        'saldo_realizado': Decimal('0.00'),
        'saldo_disponivel': sum((saldo for _, saldo in contas_disponiveis_unicas), Decimal('0.00')),
        'desvio_total': Decimal('0.00'),
    }
    por_data: dict[str, dict] = {}

    for data_ref in sorted(por_periodo.keys()):
        linhas_periodo = _build_sinteticas(por_periodo[data_ref], contas_fluxo)
        linhas_periodo.sort(key=lambda x: (x.get('codigo') or ''))

        prev_data = Decimal('0.00')
        real_data = Decimal('0.00')
        disp_data = Decimal('0.00')

        for item in linhas_periodo:
            linha = {
                'data': data_ref.isoformat(),
                'codigo': item['codigo'],
                'descricao': item['descricao'],
                'tipo': item['tipo'],
                'nivel': item['nivel'],
                'nivel_sintetico': item['nivel_sintetico'],
                'nivel_analitico': item['nivel_analitico'],
                'previsto': float(item['previsto']),
                'realizado': float(item['realizado']),
                'disponivel': float(item['disponivel']),
                'desvio': float(item['desvio']),
                'desvio_pct': float(item['desvio_pct']),
                'is_sintetica': bool(item['is_sintetica']),
            }
            linhas.append(linha)

            if not item.get('is_sintetica'):
                if item['tipo'] == 'R':
                    totais['total_previsto_r'] += item['previsto']
                    totais['total_realizado_r'] += item['realizado']
                elif item['tipo'] == 'P':
                    totais['total_previsto_p'] += item['previsto']
                    totais['total_realizado_p'] += item['realizado']

                prev_data += item['previsto']
                real_data += item['realizado']
                disp_data += item['disponivel']

        por_data[data_ref.isoformat()] = {
            'previsto': float(prev_data),
            'realizado': float(real_data),
            'disponivel': float(disp_data),
        }

    totais['saldo_previsto'] = totais['total_previsto_r'] - totais['total_previsto_p']
    totais['saldo_realizado'] = totais['total_realizado_r'] - totais['total_realizado_p']
    totais['desvio_total'] = totais['saldo_realizado'] - totais['saldo_previsto']

    totais = {k: float(v) for k, v in totais.items()}

    return {
        'linhas': linhas,
        'totais': totais,
        'por_data': por_data,
    }
