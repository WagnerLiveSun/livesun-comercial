from flask import Blueprint, render_template
from flask_login import login_required, current_user
from src.models import (
    db,
    Lancamento,
    Entidade,
    ContaBanco,
    FluxoContaModel,
    FluxoCaixaPrevisto,
    FluxoCaixaRealizado,
    LocacaoPeca,
    LocacaoContrato,
    LocacaoOrcamento,
    LocacaoRetirada,
    LocacaoDevolucao,
    LocacaoManutencao,
    LocacaoRetiradaItem,
    Orcamento,
    PedidoVenda,
    Produto,
    Servico,
    User,
    Empresa,
    AssinaturaEmpresa,
    NfseNacionalEmissao,
)
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal
from src.services.assinatura import ServicoAssinatura

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard - Geral com indicadores de cadastros"""
    import logging, traceback
    try:
        hoje = datetime.now().date()
        empresa_id = current_user.empresa_id

        # Indicadores de entidades por tipo
        fornecedores = Entidade.query.filter_by(empresa_id=empresa_id, ativo=True, tipo='F').count()
        clientes = Entidade.query.filter_by(empresa_id=empresa_id, ativo=True, tipo='C').count()
        vendedores = Entidade.query.filter_by(empresa_id=empresa_id, ativo=True, tipo='V').count()
        
        total_usuarios = User.query.filter_by(empresa_id=empresa_id, is_active=True).count()
        total_produtos = Produto.query.filter_by(empresa_id=empresa_id, ativo=True).count()
        total_servicos = Servico.query.filter_by(empresa_id=empresa_id, ativo=True).count()
        
        # Dados da assinatura
        assinatura = AssinaturaEmpresa.query.filter_by(empresa_id=empresa_id).first()
        plano = assinatura.plano_codigo if assinatura else 'N/A'
        vencimento = assinatura.data_vencimento if assinatura else None
        status = assinatura.status if assinatura else 'N/A'
        add_ons = []  # Não existe campo add_ons no modelo
        tipo_cobranca = assinatura.ciclo_cobranca if assinatura else 'N/A'
        
        # Obter link de pagamento do Asaas
        link_pagamento = None
        if assinatura and assinatura.gateway == 'asaas':
            try:
                synced = ServicoAssinatura.sincronizar_cobranca_pendente_asaas(assinatura)
                if synced:
                    link_pagamento = synced.get('invoice_url') or synced.get('bank_slip_url')
            except Exception:
                pass

        return render_template(
            'dashboard_geral.html',
            fornecedores=fornecedores,
            clientes=clientes,
            vendedores=vendedores,
            total_usuarios=total_usuarios,
            total_produtos=total_produtos,
            total_servicos=total_servicos,
            plano=plano,
            vencimento=vencimento,
            status=status,
            add_ons=add_ons,
            tipo_cobranca=tipo_cobranca,
            link_pagamento=link_pagamento,
        )
    except Exception as e:
        logging.error('Erro no dashboard geral: %s\n%s', e, traceback.format_exc())
        from flask import abort
        abort(500)


@dashboard_bp.route('/comercial')
@login_required
def comercial():
    """Dashboard específico para módulo Comercial"""
    import logging, traceback
    from flask import flash
    from sqlalchemy.exc import SQLAlchemyError
    try:
        hoje = datetime.now().date()
        empresa_id = current_user.empresa_id

        # KPIs Comerciais
        total_orcamentos = Orcamento.query.filter_by(empresa_id=empresa_id).count()
        orcamentos_aprovados = Orcamento.query.filter_by(empresa_id=empresa_id, status='aprovado').count()
        orcamentos_emitidos = Orcamento.query.filter_by(empresa_id=empresa_id, status='emitido').count()
        orcamentos_convertidos = Orcamento.query.filter_by(empresa_id=empresa_id, status='convertido').count()
        
        total_pedidos = PedidoVenda.query.filter_by(empresa_id=empresa_id).count()
        pedidos_pendentes = PedidoVenda.query.filter_by(empresa_id=empresa_id, status='pendente').count()
        pedidos_faturados = PedidoVenda.query.filter_by(empresa_id=empresa_id, status='faturado').count()
        
        valor_total_orcamentos = db.session.query(func.sum(Orcamento.valor_total)).filter(
            Orcamento.empresa_id == empresa_id
        ).scalar() or 0
        valor_total_pedidos = db.session.query(func.sum(PedidoVenda.valor_total)).filter(
            PedidoVenda.empresa_id == empresa_id
        ).scalar() or 0
        
        valor_total_orcamentos = Decimal(str(valor_total_orcamentos))
        valor_total_pedidos = Decimal(str(valor_total_pedidos))

        return render_template(
            'dashboard_comercial.html',
            total_orcamentos=total_orcamentos,
            orcamentos_aprovados=orcamentos_aprovados,
            orcamentos_emitidos=orcamentos_emitidos,
            orcamentos_convertidos=orcamentos_convertidos,
            total_pedidos=total_pedidos,
            pedidos_pendentes=pedidos_pendentes,
            pedidos_faturados=pedidos_faturados,
            valor_total_orcamentos=valor_total_orcamentos,
            valor_total_pedidos=valor_total_pedidos,
        )
    except SQLAlchemyError as e:
        # Banco de produção ainda sem as tabelas/colunas do módulo (schema desatualizado)
        db.session.rollback()
        logging.error('Erro de banco no dashboard comercial (render com zeros): %s\n%s', e, traceback.format_exc())
        flash('Não foi possível carregar os indicadores comerciais: banco sem as tabelas/colunas do módulo.', 'warning')
        return render_template(
            'dashboard_comercial.html',
            total_orcamentos=0,
            orcamentos_aprovados=0,
            orcamentos_emitidos=0,
            orcamentos_convertidos=0,
            total_pedidos=0,
            pedidos_pendentes=0,
            pedidos_faturados=0,
            valor_total_orcamentos=Decimal('0.00'),
            valor_total_pedidos=Decimal('0.00'),
        )
    except Exception as e:
        logging.error('Erro no dashboard comercial: %s\n%s', e, traceback.format_exc())
        from flask import abort
        abort(500)


@dashboard_bp.route('/financeiro')
@login_required
def financeiro():
    """Dashboard específico para módulo Financeiro"""
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
        total_contas_banco = ContaBanco.query.filter_by(empresa_id=empresa_id, ativo=True).count()
        contas_ativas = ContaBanco.query.filter_by(empresa_id=empresa_id, ativo=True).all()
        saldo_total = sum(Decimal(str(c.saldo_inicial or 0)) for c in contas_ativas)
        lancamentos_pagos = Lancamento.query.join(FluxoContaModel).filter(
            Lancamento.empresa_id == empresa_id,
            Lancamento.status == 'pago'
        ).all()
        for lancamento in lancamentos_pagos:
            valor = Decimal(str(lancamento.valor_pago or 0))
            if lancamento.fluxo_conta and lancamento.fluxo_conta.is_pagamento():
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

        # Dados para gráficos de fluxo de caixa (últimos 30 dias) - separados por tipo
        grafico_labels = []
        grafico_entradas_previsto = []
        grafico_entradas_realizado = []
        grafico_saidas_previsto = []
        grafico_saidas_realizado = []

        for i in range(periodo_grafico - 1, -1, -1):
            data_ref = hoje - timedelta(days=i)
            grafico_labels.append(data_ref.strftime('%d/%m'))

            # ENTRADAS (R = Recebimentos)
            entradas_previsto = db.session.query(func.coalesce(func.sum(Lancamento.valor_real), 0)).join(FluxoContaModel).filter(
                Lancamento.empresa_id == empresa_id,
                Lancamento.data_vencimento == data_ref,
                FluxoContaModel.tipo == 'R',
                Lancamento.status.in_(['aberto', 'vencido'])
            ).scalar() or 0

            entradas_realizado = db.session.query(func.coalesce(func.sum(Lancamento.valor_pago), 0)).join(FluxoContaModel).filter(
                Lancamento.empresa_id == empresa_id,
                Lancamento.data_pagamento == data_ref,
                FluxoContaModel.tipo == 'R',
                Lancamento.status == 'pago'
            ).scalar() or 0

            # SAÍDAS (P = Pagamentos)
            saidas_previsto = db.session.query(func.coalesce(func.sum(Lancamento.valor_real), 0)).join(FluxoContaModel).filter(
                Lancamento.empresa_id == empresa_id,
                Lancamento.data_vencimento == data_ref,
                FluxoContaModel.tipo == 'P',
                Lancamento.status.in_(['aberto', 'vencido'])
            ).scalar() or 0

            saidas_realizado = db.session.query(func.coalesce(func.sum(Lancamento.valor_pago), 0)).join(FluxoContaModel).filter(
                Lancamento.empresa_id == empresa_id,
                Lancamento.data_pagamento == data_ref,
                FluxoContaModel.tipo == 'P',
                Lancamento.status == 'pago'
            ).scalar() or 0

            grafico_entradas_previsto.append(float(entradas_previsto))
            grafico_entradas_realizado.append(float(entradas_realizado))
            grafico_saidas_previsto.append(float(saidas_previsto))
            grafico_saidas_realizado.append(float(saidas_realizado))
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
            Lancamento.data_pagamento >= grafico_inicio
        ).group_by(Lancamento.data_pagamento).all()

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
            'dashboard_financeiro.html',
            contas_pagar_aberto=contas_pagar_aberto,
            contas_receber_aberto=contas_receber_aberto,
            total_contas_banco=total_contas_banco,
            saldo_total=saldo_total,
            pagar_previsto_hoje=pagar_previsto_hoje,
            receber_previsto_hoje=receber_previsto_hoje,
            disponibilidade_hoje=disponibilidade_hoje,
            grafico_labels=grafico_labels,
            grafico_entradas_previsto=grafico_entradas_previsto,
            grafico_entradas_realizado=grafico_entradas_realizado,
            grafico_saidas_previsto=grafico_saidas_previsto,
            grafico_saidas_realizado=grafico_saidas_realizado,
            ultimos_lancamentos=ultimos_lancamentos,
            resultado_por_dia=resultado_por_dia,
            previsto_a_receber=previsto_a_receber,
            previsto_a_pagar=previsto_a_pagar,
            total_pago_mes=total_pago_mes,
            total_recebido_mes=total_recebido_mes,
        )
    except Exception as e:
        logging.error('Erro no dashboard financeiro: %s\n%s', e, traceback.format_exc())
        from flask import abort
        abort(500)


@dashboard_bp.route('/locacao')
@login_required
def locacao():
    """Dashboard específico para módulo Locação"""
    import logging, traceback
    from flask import flash
    from sqlalchemy.exc import SQLAlchemyError
    try:
        empresa_id = current_user.empresa_id

        # KPIs de Locação
        total_pecas = LocacaoPeca.query.filter_by(empresa_id=empresa_id, ativo=True).count()
        pecas_disponiveis = LocacaoPeca.query.filter_by(empresa_id=empresa_id, ativo=True).filter(
            LocacaoPeca.estado_fisico.in_(['novo', 'bom'])
        ).count()
        pecas_manutencao = LocacaoManutencao.query.filter_by(empresa_id=empresa_id).filter(
            LocacaoManutencao.status == 'em_andamento'
        ).count()
        contratos_ativos = LocacaoContrato.query.filter_by(empresa_id=empresa_id).filter(
            LocacaoContrato.status.in_(['ativo', 'em_uso'])
        ).count()
        orcamentos_pendentes = LocacaoOrcamento.query.filter_by(empresa_id=empresa_id).filter(
            LocacaoOrcamento.status == 'pendente'
        ).count()
        retiradas_pendentes = LocacaoRetirada.query.filter_by(empresa_id=empresa_id).filter(
            LocacaoRetirada.status == 'pendente'
        ).count()
        devolucoes_pendentes = LocacaoDevolucao.query.filter_by(empresa_id=empresa_id).filter(
            LocacaoDevolucao.status == 'pendente'
        ).count()

        # Taxa de ocupação (peças em uso / total peças)
        pecas_em_uso = LocacaoRetiradaItem.query.join(LocacaoRetirada).filter(
            LocacaoRetirada.empresa_id == empresa_id,
            LocacaoRetirada.status == 'em_andamento'
        ).count()
        taxa_ocupacao = (pecas_em_uso / total_pecas * 100) if total_pecas > 0 else 0

        return render_template(
            'dashboard_locacao.html',
            total_pecas=total_pecas,
            pecas_disponiveis=pecas_disponiveis,
            pecas_manutencao=pecas_manutencao,
            contratos_ativos=contratos_ativos,
            orcamentos_pendentes=orcamentos_pendentes,
            retiradas_pendentes=retiradas_pendentes,
            devolucoes_pendentes=devolucoes_pendentes,
            taxa_ocupacao=round(taxa_ocupacao, 1),
        )
    except SQLAlchemyError as e:
        # Banco de produção ainda sem as tabelas/colunas do módulo (schema desatualizado)
        db.session.rollback()
        logging.error('Erro de banco no dashboard locação (render com zeros): %s\n%s', e, traceback.format_exc())
        flash('Não foi possível carregar os indicadores de locação: banco sem as tabelas/colunas do módulo.', 'warning')
        return render_template(
            'dashboard_locacao.html',
            total_pecas=0,
            pecas_disponiveis=0,
            pecas_manutencao=0,
            contratos_ativos=0,
            orcamentos_pendentes=0,
            retiradas_pendentes=0,
            devolucoes_pendentes=0,
            taxa_ocupacao=0,
        )
    except Exception as e:
        logging.error('Erro no dashboard locação: %s\n%s', e, traceback.format_exc())
        from flask import abort
        abort(500)


@dashboard_bp.route('/propostas')
@login_required
def propostas():
    """Dashboard específico para Propostas Comerciais"""
    import logging, traceback
    try:
        hoje = datetime.now().date()
        empresa_id = current_user.empresa_id

        # KPIs de Propostas
        total_propostas = Orcamento.query.filter_by(empresa_id=empresa_id).count()
        propostas_emitidas = Orcamento.query.filter_by(empresa_id=empresa_id, status='emitido').count()
        propostas_aprovadas = Orcamento.query.filter_by(empresa_id=empresa_id, status='aprovado').count()
        propostas_reprovadas = Orcamento.query.filter_by(empresa_id=empresa_id, status='reprovado').count()
        propostas_convertidas = Orcamento.query.filter_by(empresa_id=empresa_id, status='convertido').count()
        
        valor_total_emitido = db.session.query(func.sum(Orcamento.valor_total)).filter(
            Orcamento.empresa_id == empresa_id,
            Orcamento.status == 'emitido'
        ).scalar() or 0
        valor_total_aprovado = db.session.query(func.sum(Orcamento.valor_total)).filter(
            Orcamento.empresa_id == empresa_id,
            Orcamento.status == 'aprovado'
        ).scalar() or 0
        valor_total_convertido = db.session.query(func.sum(Orcamento.valor_total)).filter(
            Orcamento.empresa_id == empresa_id,
            Orcamento.status == 'convertido'
        ).scalar() or 0
        
        valor_total_emitido = Decimal(str(valor_total_emitido))
        valor_total_aprovado = Decimal(str(valor_total_aprovado))
        valor_total_convertido = Decimal(str(valor_total_convertido))
        
        # Taxa de conversão
        taxa_conversao = (propostas_convertidas / total_propostas * 100) if total_propostas > 0 else 0
        taxa_aprovacao = (propostas_aprovadas / total_propostas * 100) if total_propostas > 0 else 0

        return render_template(
            'dashboard_propostas.html',
            total_propostas=total_propostas,
            propostas_emitidas=propostas_emitidas,
            propostas_aprovadas=propostas_aprovadas,
            propostas_reprovadas=propostas_reprovadas,
            propostas_convertidas=propostas_convertidas,
            valor_total_emitido=valor_total_emitido,
            valor_total_aprovado=valor_total_aprovado,
            valor_total_convertido=valor_total_convertido,
            taxa_conversao=round(taxa_conversao, 1),
            taxa_aprovacao=round(taxa_aprovacao, 1),
        )
    except Exception as e:
        logging.error('Erro no dashboard propostas: %s\n%s', e, traceback.format_exc())
        from flask import abort
        abort(500)


@dashboard_bp.route('/fiscal')
@login_required
def fiscal():
    """Dashboard específico para módulo Fiscal - NFS-e Nacional"""
    import logging, traceback
    try:
        hoje = datetime.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        empresa_id = current_user.empresa_id

        # NFS-e emitidas no mês
        nfse_emitidas_mes = NfseNacionalEmissao.query.filter(
            NfseNacionalEmissao.empresa_id == empresa_id,
            NfseNacionalEmissao.criado_em >= primeiro_dia_mes,
            NfseNacionalEmissao.status_processamento == 'AUTORIZADA'
        ).count()

        # Valor total emitido no mês
        valor_total_mes = db.session.query(func.sum(NfseNacionalEmissao.valor_servico)).filter(
            NfseNacionalEmissao.empresa_id == empresa_id,
            NfseNacionalEmissao.criado_em >= primeiro_dia_mes,
            NfseNacionalEmissao.status_processamento == 'AUTORIZADA'
        ).scalar() or Decimal('0')

        # NFS-e canceladas no mês
        nfse_canceladas_mes = NfseNacionalEmissao.query.filter(
            NfseNacionalEmissao.empresa_id == empresa_id,
            NfseNacionalEmissao.cancelado_em >= primeiro_dia_mes
        ).count()

        # ISS total no mês
        iss_total_mes = db.session.query(func.sum(NfseNacionalEmissao.valor_iss)).filter(
            NfseNacionalEmissao.empresa_id == empresa_id,
            NfseNacionalEmissao.criado_em >= primeiro_dia_mes,
            NfseNacionalEmissao.status_processamento == 'AUTORIZADA'
        ).scalar() or Decimal('0')

        # Status das NFS-e (todas)
        total_nfse = NfseNacionalEmissao.query.filter_by(empresa_id=empresa_id).count()
        
        status_autorizadas = NfseNacionalEmissao.query.filter(
            NfseNacionalEmissao.empresa_id == empresa_id,
            NfseNacionalEmissao.situacao_fiscal == 'AUTORIZADA'
        ).count()
        
        status_canceladas = NfseNacionalEmissao.query.filter(
            NfseNacionalEmissao.empresa_id == empresa_id,
            NfseNacionalEmissao.situacao_fiscal == 'CANCELADA'
        ).count()
        
        status_pendentes = NfseNacionalEmissao.query.filter(
            NfseNacionalEmissao.empresa_id == empresa_id,
            NfseNacionalEmissao.situacao_fiscal == 'PENDENTE'
        ).count()
        
        status_rejeitadas = NfseNacionalEmissao.query.filter(
            NfseNacionalEmissao.empresa_id == empresa_id,
            NfseNacionalEmissao.situacao_fiscal.in_(['REJEITADA', 'ERRO'])
        ).count()

        # Percentuais
        percent_autorizadas = (status_autorizadas / total_nfse * 100) if total_nfse > 0 else 0
        percent_canceladas = (status_canceladas / total_nfse * 100) if total_nfse > 0 else 0
        percent_pendentes = (status_pendentes / total_nfse * 100) if total_nfse > 0 else 0
        percent_rejeitadas = (status_rejeitadas / total_nfse * 100) if total_nfse > 0 else 0

        # Últimas 5 NFS-e emitidas
        ultimas_nfse = NfseNacionalEmissao.query.filter_by(empresa_id=empresa_id).order_by(
            NfseNacionalEmissao.criado_em.desc()
        ).limit(5).all()

        return render_template(
            'dashboard_fiscal.html',
            nfse_emitidas_mes=nfse_emitidas_mes,
            valor_total_mes=valor_total_mes,
            nfse_canceladas_mes=nfse_canceladas_mes,
            iss_total_mes=iss_total_mes,
            status_autorizadas=status_autorizadas,
            status_canceladas=status_canceladas,
            status_pendentes=status_pendentes,
            status_rejeitadas=status_rejeitadas,
            percent_autorizadas=round(percent_autorizadas, 1),
            percent_canceladas=round(percent_canceladas, 1),
            percent_pendentes=round(percent_pendentes, 1),
            percent_rejeitadas=round(percent_rejeitadas, 1),
            ultimas_nfse=ultimas_nfse,
        )
    except Exception as e:
        logging.error('Erro no dashboard fiscal: %s\n%s', e, traceback.format_exc())
        from flask import abort
        abort(500)

