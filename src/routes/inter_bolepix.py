from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required

from src.extensions import csrf
from src.models import InterContaConfig, InterCobranca, Lancamento
from src.services.asaas_boleto import revelar_credencial
from src.services.inter_bolepix import InterBolePixError, gerar_bolepix, processar_webhook
from src.tenant import scoped_get_or_404

logger = logging.getLogger(__name__)

inter_bolepix_bp = Blueprint('inter_bolepix', __name__, url_prefix='/inter-bolepix')


@inter_bolepix_bp.route('/lancamentos/<int:id>/gerar', methods=['POST'])
@login_required
def gerar(id):
    lancamento = scoped_get_or_404(Lancamento, id)
    try:
        cobranca = gerar_bolepix(lancamento)
    except InterBolePixError as exc:
        return jsonify({'sucesso': False, 'mensagem': str(exc)}), 422
    return jsonify({
        'sucesso': True,
        'cobranca_id': cobranca.id,
        'codigo_solicitacao': cobranca.codigo_solicitacao,
        'status': cobranca.status_interno,
        'linha_digitavel': cobranca.linha_digitavel,
        'codigo_barras': cobranca.codigo_barras,
        'qr_code': cobranca.qr_code,
        'pdf_url': cobranca.pdf_url,
    }), 201


@inter_bolepix_bp.route('/webhook', methods=['POST'])
@csrf.exempt
def webhook():
    payload = request.get_json(silent=True) or {}
    codigo = str(
        payload.get('codigoSolicitacao')
        or payload.get('codigoSolicitacaoCobranca')
        or payload.get('codigo')
        or ''
    ).strip()
    cobranca = InterCobranca.query.filter_by(codigo_solicitacao=codigo).first() if codigo else None
    config = (
        InterContaConfig.query.filter_by(
            empresa_id=cobranca.empresa_id,
            conta_banco_id=cobranca.conta_banco_id,
            cobranca_habilitada=True,
            ativo=True,
        ).first()
        if cobranca
        else None
    )
    expected = revelar_credencial(config.webhook_token_criptografado) if config and config.webhook_token_criptografado else None
    supplied = (request.headers.get('x-inter-webhook-token') or request.headers.get('authorization') or '').replace('Bearer ', '').strip()
    if not expected or supplied != expected:
        return jsonify({'sucesso': False, 'mensagem': 'Token Inter inválido.'}), 401
    event_id = str(request.headers.get('x-inter-event-id') or payload.get('id') or codigo).strip()
    try:
        processed = processar_webhook(payload, event_id)
    except Exception:
        logger.exception('Erro ao processar webhook Inter de cobrança.')
        return jsonify({'sucesso': False, 'mensagem': 'Erro ao processar webhook Inter.'}), 500
    return jsonify({'sucesso': processed}), 200
