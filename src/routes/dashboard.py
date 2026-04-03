from flask import Blueprint, render_template
from flask_login import login_required, current_user
from src.models import db, Lancamento, Entidade, ContaBanco, FluxoContaModel, FluxoCaixaPrevisto, FluxoCaixaRealizado
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal
from decimal import Decimal

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard"""
    import logging, traceback
    try:
        hoje = datetime.now().date()
        empresa_id = current_user.empresa_id

        contas_pagar_aberto = Lancamento.query.join(FluxoContaModel).filter(
            Lancamento.empresa_id == empresa_id,
            FluxoContaModel.tipo == 'P',
            Lancamento.status == 'aberto',
            Lancamento.data_vencimento <= hoje
        ).count()
        contas_receber_aberto = Lancamento.query.join(FluxoContaModel).filter(
            Lancamento.empresa_id == empresa_id,
            FluxoContaModel.tipo == 'R',
            Lancamento.status == 'aberto',
            Lancamento.data_vencimento <= hoje
        ).count()
        total_entidades = Entidade.query.filter_by(empresa_id=empresa_id, ativo=True).count()
        total_contas_banco = ContaBanco.query.filter_by(empresa_id=empresa_id, ativo=True).count()
        contas_ativas = ContaBanco.query.filter_by(empresa_id=empresa_id, ativo=True).all()
        saldo_total = sum(Decimal(str(c.saldo_inicial or 0)) for c in contas_ativas)
        lancamentos_pagos = Lancamento.query.join(FluxoContaModel).filter(
            Lancamento.empresa_id == empresa_id,
            Lancamento.status == 'pago'
        ).all()
        for lancamento in lancamentos_pagos:
            valor = Decimal(str(lancamento.valor_pago or 0))
            if lancamento.fluxo_conta and lancamento.fluxo_conta.tipo == 'P':
                saldo_total -= valor
            else:
                saldo_total += valor
        pagar_previsto_hoje = db.session.query(
            func.sum(Lancamento.valor_real)
        ).join(FluxoContaModel).filter(
            Lancamento.empresa_id == empresa_id,
            FluxoContaModel.tipo == 'P',
            Lancamento.data_vencimento == hoje
        ).scalar() or 0
        receber_previsto_hoje = db.session.query(
            func.sum(Lancamento.valor_real)
        ).join(FluxoContaModel).filter(
            Lancamento.empresa_id == empresa_id,
            FluxoContaModel.tipo == 'R',
            Lancamento.data_vencimento == hoje
        ).scalar() or 0
        pagar_previsto_hoje = Decimal(str(pagar_previsto_hoje))
        receber_previsto_hoje = Decimal(str(receber_previsto_hoje))
        disponibilidade_hoje = saldo_total + receber_previsto_hoje - pagar_previsto_hoje
        necessidade_hoje = max(Decimal('0.00'), pagar_previsto_hoje - (saldo_total + receber_previsto_hoje))
        ultimos_lancamentos = Lancamento.query.filter_by(empresa_id=empresa_id).order_by(Lancamento.data_evento.desc()).limit(10).all()
        data_inicial = hoje - timedelta(days=7)
        resultado_por_dia = db.session.query(
            Lancamento.data_evento,
            func.sum(Lancamento.valor_pago).label('pago'),
            func.sum(Lancamento.valor_real).label('previsto')
        ).filter(
            Lancamento.empresa_id == empresa_id,
            Lancamento.data_evento >= data_inicial,
            Lancamento.status == 'pago'
        ).group_by(Lancamento.data_evento).all()
        periodo_grafico = int(current_user.dashboard_chart_days or 30)
        periodo_grafico = min(max(periodo_grafico, 7), 365)
        grafico_inicio = hoje - timedelta(days=periodo_grafico - 1)
        dias = [grafico_inicio + timedelta(days=i) for i in range(periodo_grafico)]
        previsto_rows = db.session.query(
            Lancamento.data_vencimento,
            func.sum(Lancamento.valor_real)
        ).join(FluxoContaModel).filter(
            Lancamento.empresa_id == empresa_id,
            Lancamento.data_vencimento >= grafico_inicio
        ).group_by(Lancamento.data_vencimento).all()
        realizado_rows = db.session.query(
            Lancamento.data_pagamento,
            func.sum(Lancamento.valor_pago)
        ).join(FluxoContaModel).filter(
            Lancamento.empresa_id == empresa_id,
            Lancamento.data_pagamento >= grafico_inicio,
            Lancamento.status == 'pago'
        ).group_by(Lancamento.data_pagamento).all()
        previsto_por_dia = {row[0]: Decimal(str(row[1] or 0)) for row in previsto_rows}
        realizado_por_dia = {row[0]: Decimal(str(row[1] or 0)) for row in realizado_rows}
        grafico_labels = [d.strftime('%d/%m') for d in dias]
        grafico_previsto = [float(previsto_por_dia.get(d, 0)) for d in dias]
        grafico_realizado = [float(realizado_por_dia.get(d, 0)) for d in dias]
        previsto_inicio = hoje
        previsto_fim = hoje + timedelta(days=periodo_grafico - 1)
        previsto_a_receber = db.session.query(
            func.sum(FluxoCaixaPrevisto.valor_previsto_recebido)
        ).filter(
            FluxoCaixaPrevisto.empresa_id == empresa_id,
            FluxoCaixaPrevisto.data >= previsto_inicio,
            FluxoCaixaPrevisto.data <= previsto_fim
        ).scalar() or 0
        previsto_a_pagar = db.session.query(
            func.sum(FluxoCaixaPrevisto.valor_previsto_pago)
        ).filter(
            FluxoCaixaPrevisto.empresa_id == empresa_id,
            FluxoCaixaPrevisto.data >= previsto_inicio,
            FluxoCaixaPrevisto.data <= previsto_fim
        ).scalar() or 0
        previsto_a_receber = Decimal(str(previsto_a_receber))
        previsto_a_pagar = Decimal(str(previsto_a_pagar))
        mes_inicio = hoje.replace(day=1)
        total_pago_mes = db.session.query(
            func.sum(FluxoCaixaRealizado.valor_pago)
        ).filter(
            FluxoCaixaRealizado.empresa_id == empresa_id,
            FluxoCaixaRealizado.data >= mes_inicio,
            FluxoCaixaRealizado.data <= hoje
        ).scalar() or 0
        total_recebido_mes = db.session.query(
            func.sum(FluxoCaixaRealizado.valor_recebido)
        ).filter(
            FluxoCaixaRealizado.empresa_id == empresa_id,
            FluxoCaixaRealizado.data >= mes_inicio,
            FluxoCaixaRealizado.data <= hoje
        ).scalar() or 0
        total_pago_mes = Decimal(str(total_pago_mes))
        total_recebido_mes = Decimal(str(total_recebido_mes))
        return render_template(
            'dashboard.html',
            contas_pagar_aberto=contas_pagar_aberto,
            contas_receber_aberto=contas_receber_aberto,
            total_entidades=total_entidades,
            total_contas_banco=total_contas_banco,
            saldo_total=saldo_total,
            pagar_previsto_hoje=pagar_previsto_hoje,
            receber_previsto_hoje=receber_previsto_hoje,
            disponibilidade_hoje=disponibilidade_hoje,
            necessidade_hoje=necessidade_hoje,
            grafico_labels=grafico_labels,
            grafico_previsto=grafico_previsto,
            grafico_realizado=grafico_realizado,
            ultimos_lancamentos=ultimos_lancamentos,
            resultado_por_dia=resultado_por_dia,
            previsto_a_receber=previsto_a_receber,
            previsto_a_pagar=previsto_a_pagar,
            total_pago_mes=total_pago_mes,
            total_recebido_mes=total_recebido_mes
        )
    except Exception as e:
        logging.error('Erro no dashboard: %s\n%s', e, traceback.format_exc())
        from flask import abort
        abort(500)
