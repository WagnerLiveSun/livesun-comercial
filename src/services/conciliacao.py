from decimal import Decimal

from sqlalchemy import or_

from src.models import db, ContaBanco, ConciliacaoBancaria, ConciliacaoItem, Lancamento
from src.services.ofx_parser import OFXParser


def _as_decimal(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal('0.01'))


def _normalizar_descricao(texto: str) -> str:
    return ' '.join((texto or '').strip().lower().split())


def _digits_only(value: str | None) -> str:
    return ''.join(ch for ch in (value or '') if ch.isdigit())


def _encontrar_lancamento_correspondente(empresa_id: int, conta_banco_id: int, transacao: dict):
    """Busca um lançamento correspondente à transação do extrato."""
    data_movimento = transacao.get('data')
    referencia = (transacao.get('transaction_id') or '').strip()
    descricao = _normalizar_descricao(transacao.get('descricao') or '')
    valor_extrato = _as_decimal(transacao.get('valor'))
    tipo_movimento = transacao.get('tipo_movimento')

    base_query = Lancamento.query.filter_by(empresa_id=empresa_id, conta_banco_id=conta_banco_id)

    if referencia:
        lancamento = base_query.filter(Lancamento.referencia_banco == referencia).first()
        if lancamento:
            return lancamento, 'referencia_banco'

    candidatos = base_query.filter(
        or_(
            Lancamento.data_pagamento == data_movimento,
            Lancamento.data_vencimento == data_movimento,
            Lancamento.data_evento == data_movimento,
        )
    ).all()

    for lancamento in candidatos:
        if tipo_movimento == 'saida' and lancamento.fluxo_conta and lancamento.fluxo_conta.tipo != 'P':
            continue
        if tipo_movimento == 'entrada' and lancamento.fluxo_conta and lancamento.fluxo_conta.tipo != 'R':
            continue

        valor_base = lancamento.valor_pago if lancamento.status == 'pago' and lancamento.valor_pago else lancamento.valor_real
        if _as_decimal(valor_base) == abs(valor_extrato):
            return lancamento, 'valor_data'

        if descricao and _normalizar_descricao(lancamento.observacoes or '') == descricao:
            return lancamento, 'descricao'

    return None, None


def criar_conciliacao_ofx(empresa_id: int, conta_banco_id: int, ofx_content: str, criado_por_user_id: int | None = None):
    """Parte 1: cria a sessão de conciliação e importa as transações do OFX."""
    conta = ContaBanco.query.filter_by(id=conta_banco_id, empresa_id=empresa_id).first()
    if not conta:
        raise ValueError('Conta bancária não encontrada para a empresa informada.')

    parser = OFXParser(ofx_content)
    if not parser.parse():
        raise ValueError('; '.join(parser.get_errors()) or 'Não foi possível processar o OFX.')

    conta_extrato = _digits_only(parser.account_id)
    conta_sistema = _digits_only(conta.numero_conta)
    dv_sistema = _digits_only(conta.dv)

    conta_sistema_candidatas = {conta_sistema}
    if conta_sistema and dv_sistema:
        conta_sistema_candidatas.add(f'{conta_sistema}{dv_sistema}')

    if conta_extrato and conta_sistema and conta_extrato not in conta_sistema_candidatas:
        raise ValueError(
            'Conta do extrato não corresponde à conta selecionada no sistema. '
            f'Extrato: {conta_extrato} | Sistema: {conta.numero_conta}'
            + (f'-{conta.dv}' if conta.dv else '')
        )

    transacoes = parser.get_transactions()
    if not transacoes:
        raise ValueError('Nenhuma transação encontrada no arquivo OFX.')

    datas = [txn['data'] for txn in transacoes if txn.get('data')]
    periodo_inicio = min(datas)
    periodo_fim = max(datas)

    conciliacao = ConciliacaoBancaria(
        empresa_id=empresa_id,
        conta_banco_id=conta_banco_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        status='aberta',
        criado_por_user_id=criado_por_user_id,
    )
    db.session.add(conciliacao)
    db.session.flush()

    for transacao in transacoes:
        item = ConciliacaoItem(
            empresa_id=empresa_id,
            conciliacao_id=conciliacao.id,
            data_movimento=transacao['data'],
            descricao_extrato=transacao.get('descricao'),
            referencia_banco=transacao.get('transaction_id') or transacao.get('referencia'),
            valor_extrato=transacao.get('valor'),
            status='pendente',
        )
        db.session.add(item)

    db.session.commit()
    return conciliacao


def reconciliar_conciliacao(conciliacao_id: int, empresa_id: int):
    """Parte 2: tenta casar os itens importados com lançamentos internos."""
    conciliacao = ConciliacaoBancaria.query.filter_by(id=conciliacao_id, empresa_id=empresa_id).first()
    if not conciliacao:
        raise ValueError('Conciliação não encontrada para a empresa informada.')

    conciliados = 0
    pendentes = 0
    divergentes = 0

    for item in conciliacao.itens:
        lancamento, regra = _encontrar_lancamento_correspondente(
            empresa_id=empresa_id,
            conta_banco_id=conciliacao.conta_banco_id,
            transacao={
                'data': item.data_movimento,
                'transaction_id': item.referencia_banco,
                'descricao': item.descricao_extrato,
                'valor': item.valor_extrato,
                'tipo_movimento': 'saida' if _as_decimal(item.valor_extrato) < 0 else 'entrada',
            },
        )

        if lancamento:
            item.lancamento_id = lancamento.id
            item.status = 'conciliado'
            item.motivo_divergencia = f'casado_por={regra}'
            lancamento.status = 'pago'
            lancamento.data_pagamento = item.data_movimento
            lancamento.valor_pago = abs(_as_decimal(item.valor_extrato))
            lancamento.referencia_banco = item.referencia_banco or lancamento.referencia_banco
            lancamento.fonte = 'ofx'
            conciliados += 1
        else:
            item.status = 'pendente'
            item.motivo_divergencia = 'Nenhum lançamento correspondente encontrado.'
            if item.valor_extrato == 0:
                item.status = 'divergente'
                divergentes += 1
            else:
                pendentes += 1

    conciliacao.status = 'fechada' if pendentes == 0 and divergentes == 0 else 'revisao'
    db.session.commit()

    return {
        'conciliacao_id': conciliacao.id,
        'conciliados': conciliados,
        'pendentes': pendentes,
        'divergentes': divergentes,
        'status': conciliacao.status,
    }
