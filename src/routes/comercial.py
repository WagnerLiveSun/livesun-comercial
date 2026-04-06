from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.extensions import csrf
from src.services.assinatura import ServicoAssinatura


comercial_webhook_bp = Blueprint('comercial_webhook', __name__, url_prefix='/webhooks')


@comercial_webhook_bp.route('/asaas', methods=['POST'])
@csrf.exempt
def webhook_asaas():
    payload = request.get_json(silent=True) or {}
    event_id = (
        request.headers.get('Asaas-Event-Id')
        or request.headers.get('X-Asaas-Event-Id')
        or payload.get('id')
        or payload.get('eventId')
    )
    event_type = payload.get('event') or payload.get('type') or 'unknown'

    resultado = ServicoAssinatura.processar_webhook_asaas(
        payload=payload,
        event_id_externo=event_id,
        tipo_evento=event_type,
    )
    http_status = int(resultado.get('http_status', 200))
    return jsonify(resultado), http_status
