from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required

from src.extensions import csrf
from src.models import AsaasContaConfig, Lancamento
from src.services.asaas_boleto import AsaasBoletoError, gerar_boleto, processar_webhook, revelar_credencial
from src.tenant import scoped_get_or_404

logger = logging.getLogger(__name__)

asaas_boleto_bp = Blueprint('asaas_boleto', __name__, url_prefix='/asaas-boletos')


@asaas_boleto_bp.route('/lancamentos/<int:id>/gerar', methods=['POST'])
@login_required
def gerar(id):
    lancamento = scoped_get_or_404(Lancamento, id)
    try:
        cobranca = gerar_boleto(lancamento)
    except AsaasBoletoError as exc:
        return jsonify({'sucesso': False, 'mensagem': str(exc)}), 422

    return jsonify({
        'sucesso': True,
        'cobranca_id': cobranca.id,
        'payment_id': cobranca.asaas_payment_id,
        'status': cobranca.status_interno,
        'invoice_url': cobranca.invoice_url,
        'bank_slip_url': cobranca.bank_slip_url,
        'identification_field': cobranca.identification_field,
    }), 201


@asaas_boleto_bp.route('/webhook', methods=['POST'])
@csrf.exempt
def webhook():
    token = (request.headers.get('asaas-access-token') or '').strip()
    if not token:
        return jsonify({'sucesso': False, 'mensagem': 'Token Asaas ausente.'}), 401

    payload = request.get_json(silent=True) or {}
    payment = payload.get('payment') if isinstance(payload.get('payment'), dict) else payload
    reference = str(payment.get('externalReference') or '').strip()
    parts = reference.split(':')
    empresa_id = int(parts[1]) if len(parts) == 4 and parts[0] == 'LIVESUN' and parts[1].isdigit() else None
    config = (
        AsaasContaConfig.query.filter_by(
            empresa_id=empresa_id,
            cobranca_habilitada=True,
            ativo=True,
        ).first()
        if empresa_id is not None
        else None
    )
    authorized = bool(
        config
        and config.webhook_token_criptografado
        and revelar_credencial(config.webhook_token_criptografado) == token
    )
    if not authorized:
        logger.warning('Webhook Asaas rejeitado por token inválido.')
        return jsonify({'sucesso': False, 'mensagem': 'Token Asaas inválido.'}), 401

    event_id = str(
        request.headers.get('Asaas-Event-Id')
        or request.headers.get('X-Asaas-Event-Id')
        or payload.get('id')
        or payload.get('eventId')
        or ''
    ).strip()
    if not event_id:
        return jsonify({'sucesso': False, 'mensagem': 'Evento Asaas sem identificador.'}), 400

    try:
        processado = processar_webhook(
            payload=payload,
            event_id=event_id,
            event_type=str(payload.get('event') or payload.get('type') or 'unknown'),
        )
    except Exception:
        logger.exception('Erro ao processar webhook Asaas de boleto.')
        return jsonify({'sucesso': False, 'mensagem': 'Erro ao processar webhook Asaas.'}), 500
    return jsonify({'sucesso': processado}), 200
