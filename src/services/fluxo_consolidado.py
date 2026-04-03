from decimal import Decimal
from collections import defaultdict
from src.models import db, Lancamento, FluxoContaModel, ContaBanco, FluxoCaixaRealizado, FluxoCaixaPrevisto, Empresa
from datetime import datetime, timezone


def consolidar_fluxo_caixa(empresa_id=None):
    """Consolidate cash flow per company.

    If `empresa_id` is provided, only that company's consolidated rows are
    recalculated. Otherwise the function iterates all companies present in
    `Lancamento`.
    """
    # Determine companies to process
    if empresa_id:
        empresa_ids = [empresa_id]
    else:
        empresa_ids = [row[0] for row in db.session.query(Lancamento.empresa_id).distinct().all()]

    if not empresa_ids:
        return

    for empresa_id in empresa_ids:
        # Remove previous consolidated rows only for this company
        FluxoCaixaRealizado.query.filter_by(empresa_id=empresa_id).delete()
        FluxoCaixaPrevisto.query.filter_by(empresa_id=empresa_id).delete()
        db.session.commit()

        # Load only active accounts/flows for this company
        contas_fluxo = FluxoContaModel.query.filter_by(ativo=True, empresa_id=empresa_id).all()
        contas_banco = ContaBanco.query.filter_by(ativo=True, empresa_id=empresa_id).all()

        saldos_realizado = defaultdict(lambda: {
            'valor_pago': Decimal('0.00'),
            'valor_recebido': Decimal('0.00'),
            'datas': []
        })
        saldos_previsto = defaultdict(lambda: {
            'valor_previsto_pago': Decimal('0.00'),
            'valor_previsto_recebido': Decimal('0.00'),
            'datas': []
        })

        lancamentos = Lancamento.query.filter_by(empresa_id=empresa_id).all()

        for lanc in lancamentos:
            key = (lanc.fluxo_conta_id, lanc.conta_banco_id)
            if lanc.status == 'pago':
                if lanc.fluxo_conta and lanc.fluxo_conta.tipo == 'P':
                    saldos_realizado[key]['valor_pago'] += lanc.valor_pago or Decimal('0.00')
                else:
                    saldos_realizado[key]['valor_recebido'] += lanc.valor_pago or Decimal('0.00')
                saldos_realizado[key]['datas'].append(lanc.data_pagamento or lanc.data_evento)
            else:
                if lanc.fluxo_conta and lanc.fluxo_conta.tipo == 'P':
                    saldos_previsto[key]['valor_previsto_pago'] += lanc.valor_real or Decimal('0.00')
                else:
                    saldos_previsto[key]['valor_previsto_recebido'] += lanc.valor_real or Decimal('0.00')
                saldos_previsto[key]['datas'].append(lanc.data_vencimento or lanc.data_evento)

        # Grava realizado
        for (fluxo_conta_id, conta_banco_id), valores in saldos_realizado.items():
            conta_banco = ContaBanco.query.get(conta_banco_id)
            saldo_anterior = conta_banco.saldo_inicial if conta_banco else Decimal('0.00')
            saldo_atual = saldo_anterior + valores['valor_recebido'] - valores['valor_pago']
            data_consolidado = valores['datas'][-1] if valores['datas'] else datetime.now(timezone.utc).date()
            consolidado = FluxoCaixaRealizado(
                empresa_id=empresa_id,
                data=data_consolidado,
                fluxo_conta_id=fluxo_conta_id,
                conta_banco_id=conta_banco_id,
                saldo_anterior=saldo_anterior,
                valor_pago=valores['valor_pago'],
                valor_recebido=valores['valor_recebido'],
                saldo_atual=saldo_atual
            )
            db.session.add(consolidado)

        # Grava previsto
        for (fluxo_conta_id, conta_banco_id), valores in saldos_previsto.items():
            conta_banco = ContaBanco.query.get(conta_banco_id)
            saldo_anterior = conta_banco.saldo_inicial if conta_banco else Decimal('0.00')
            saldo_previsto = saldo_anterior + valores['valor_previsto_recebido'] - valores['valor_previsto_pago']
            data_consolidado = valores['datas'][-1] if valores['datas'] else datetime.now(timezone.utc).date()
            previsto = FluxoCaixaPrevisto(
                empresa_id=empresa_id,
                data=data_consolidado,
                fluxo_conta_id=fluxo_conta_id,
                conta_banco_id=conta_banco_id,
                saldo_anterior=saldo_anterior,
                valor_previsto_pago=valores['valor_previsto_pago'],
                valor_previsto_recebido=valores['valor_previsto_recebido'],
                saldo_previsto=saldo_previsto
            )
            db.session.add(previsto)

        db.session.commit()

# Para uso: from src.services.fluxo_consolidado import consolidar_fluxo_caixa
# consolidar_fluxo_caixa()