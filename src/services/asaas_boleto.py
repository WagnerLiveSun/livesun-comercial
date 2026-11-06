"""Regras de negocio para cobrancas de boleto do Asaas."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app
from sqlalchemy.exc import IntegrityError

from src.models import (
    AsaasCliente,
    AsaasCobranca,
    AsaasContaConfig,
    AsaasWebhookEvento,
    Entidade,
    Lancamento,
    NfseNacionalEmissao,
    db,
)
from src.services.asaas_client import AsaasApiError, AsaasClient

logger = logging.getLogger(__name__)


class AsaasBoletoError(ValueError):
    """Erro de validacao ou regra de negocio de boleto."""


def _fernet() -> Fernet:
    configured_key = str(current_app.config.get('ASAAS_ENCRYPTION_KEY') or '').strip()
    if configured_key:
        try:
            return Fernet(configured_key.encode())
        except ValueError as exc:
            raise AsaasBoletoError('ASAAS_ENCRYPTION_KEY inválida.') from exc

    secret = str(current_app.config.get('SECRET_KEY') or '').encode()
    if not secret:
        raise AsaasBoletoError('SECRET_KEY deve estar configurada para proteger credenciais Asaas.')
    digest = hashlib.sha256(secret).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def proteger_credencial(value: str) -> str:
    return _fernet().encrypt(value.strip().encode()).decode()


def revelar_credencial(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise AsaasBoletoError('Não foi possível descriptografar a credencial Asaas.') from exc


def configurar_conta_asaas(
    *,
    conta_banco_id: int,
    empresa_id: int,
    habilitada: bool,
    ambiente: str | None,
    api_key: str | None,
    webhook_token: str | None,
    juros_mensal_percentual: str | float | Decimal | None = None,
    multa_percentual: str | float | Decimal | None = None,
) -> AsaasContaConfig | None:
    config = AsaasContaConfig.query.filter_by(
        conta_banco_id=conta_banco_id,
        empresa_id=empresa_id,
    ).first()

    if not habilitada:
        if config:
            config.cobranca_habilitada = False
            config.ativo = False
        return config

    ambiente = (ambiente or '').strip().upper()
    if ambiente not in {'SANDBOX', 'PRODUCAO'}:
        raise AsaasBoletoError('Selecione o ambiente do Asaas.')

    api_key = (api_key or '').strip()
    webhook_token = (webhook_token or '').strip()
    if not config and (not api_key or not webhook_token):
        raise AsaasBoletoError('API Key e token do webhook são obrigatórios ao habilitar a cobrança.')
    if not config:
        config = AsaasContaConfig(empresa_id=empresa_id, conta_banco_id=conta_banco_id)
        db.session.add(config)

    if api_key:
        config.api_key_criptografada = proteger_credencial(api_key)
    if webhook_token:
        config.webhook_token_criptografado = proteger_credencial(webhook_token)
    if not config.api_key_criptografada or not config.webhook_token_criptografado:
        raise AsaasBoletoError('API Key e token do webhook são obrigatórios ao habilitar a cobrança.')

    config.cobranca_habilitada = True
    config.ativo = True
    config.ambiente = ambiente
    config.juros_mensal_percentual = _percentual_or_none(juros_mensal_percentual, 'Juros mensal')
    config.multa_percentual = _percentual_or_none(multa_percentual, 'Multa')
    return config


def _percentual_or_none(value: str | float | Decimal | None, label: str) -> Decimal | None:
    if value in (None, ''):
        return None
    try:
        decimal_value = Decimal(str(value).replace(',', '.'))
    except Exception as exc:
        raise AsaasBoletoError(f'{label} inválido.') from exc
    if decimal_value < 0 or decimal_value > 100:
        raise AsaasBoletoError(f'{label} deve estar entre 0 e 100%.')
    return decimal_value


def _client(config: AsaasContaConfig) -> AsaasClient:
    api_key = revelar_credencial(config.api_key_criptografada)
    if not api_key:
        raise AsaasBoletoError('Conta Asaas habilitada sem API Key configurada.')
    base_url = (
        'https://api.asaas.com/v3'
        if config.ambiente == 'PRODUCAO'
        else 'https://api-sandbox.asaas.com/v3'
    )
    return AsaasClient(
        api_key=api_key,
        base_url=base_url,
        timeout_seconds=int(current_app.config.get('ASAAS_TIMEOUT_SECONDS') or 15),
    )


def _documento(value: str | None) -> str:
    digits = ''.join(char for char in str(value or '') if char.isdigit())
    if len(digits) not in {11, 14}:
        raise AsaasBoletoError('O cliente precisa ter CPF ou CNPJ válido para gerar o boleto.')
    return digits


def _payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def gerar_boleto(
    lancamento: Lancamento,
    *,
    origem: str = 'lancamento',
    nfse_emissao_id: int | None = None,
    juros_mensal_percentual: Decimal | float | None = None,
    multa_percentual: Decimal | float | None = None,
) -> AsaasCobranca:
    if lancamento.status != 'aberto':
        raise AsaasBoletoError('Somente lançamentos em aberto podem gerar boleto.')
    if not lancamento.valor_real or Decimal(str(lancamento.valor_real)) <= 0:
        raise AsaasBoletoError('O valor do lançamento deve ser maior que zero.')
    if not lancamento.data_vencimento:
        raise AsaasBoletoError('O vencimento do lançamento é obrigatório.')

    config = AsaasContaConfig.query.filter_by(
        conta_banco_id=lancamento.conta_banco_id,
        empresa_id=lancamento.empresa_id,
    ).first()
    if not config or not config.habilitada:
        raise AsaasBoletoError('A cobrança bancária Asaas não está habilitada nesta conta.')

    existing = AsaasCobranca.query.filter_by(
        empresa_id=lancamento.empresa_id,
        lancamento_id=lancamento.id,
    ).filter(AsaasCobranca.status_interno.notin_(['cancelado', 'falhou'])).first()
    if existing:
        raise AsaasBoletoError('Este lançamento já possui uma cobrança Asaas ativa.')

    entidade = Entidade.query.filter_by(
        id=lancamento.entidade_id,
        empresa_id=lancamento.empresa_id,
    ).first()
    if not entidade:
        raise AsaasBoletoError('Cliente do lançamento não encontrado.')
    documento = _documento(entidade.cnpj_cpf)
    client = _client(config)
    juros = (
        Decimal(str(juros_mensal_percentual))
        if juros_mensal_percentual is not None
        else config.juros_mensal_percentual
    )
    multa = (
        Decimal(str(multa_percentual))
        if multa_percentual is not None
        else config.multa_percentual
    )
    for label, value in (('Juros mensal', juros), ('Multa', multa)):
        if value is not None and (value < 0 or value > 100):
            raise AsaasBoletoError(f'{label} deve estar entre 0 e 100%.')

    customer = AsaasCliente.query.filter_by(
        empresa_id=lancamento.empresa_id,
        entidade_id=entidade.id,
    ).first()
    if customer:
        customer_id = customer.asaas_customer_id
    else:
        external_customer = f'LIVESUN:{lancamento.empresa_id}:CLIENTE:{entidade.id}'
        customer_data = client.find_customer_by_external_reference(external_customer)
        if not customer_data:
            customer_data = client.create_customer(
                name=entidade.nome,
                cpf_cnpj=documento,
                email=entidade.email,
                external_reference=external_customer,
            )
        customer_id = str(customer_data.get('id') or '').strip()
        if not customer_id:
            raise AsaasBoletoError('O Asaas não retornou o identificador do cliente.')
        customer = AsaasCliente(
            empresa_id=lancamento.empresa_id,
            entidade_id=entidade.id,
            asaas_customer_id=customer_id,
            cpf_cnpj=documento,
            nome_razao_social=entidade.nome,
            email=entidade.email,
        )
        db.session.add(customer)
        db.session.flush()

    emissao = (
        NfseNacionalEmissao.query.filter_by(
            id=nfse_emissao_id,
            empresa_id=lancamento.empresa_id,
        ).first()
        if nfse_emissao_id
        else None
    )
    identificacao = (
        f'NFS-e {emissao.numero_nfse}'
        if emissao and emissao.numero_nfse
        else f'Documento {lancamento.numero_documento or lancamento.id}'
    )
    reference = f'LIVESUN:{lancamento.empresa_id}:LANCAMENTO:{lancamento.id}'
    try:
        payment = client.create_boleto_payment(
            customer_id=customer_id,
            value=float(lancamento.valor_real),
            due_date=lancamento.data_vencimento.isoformat(),
            external_reference=reference,
            description=f'LiveSun Comercial - {identificacao}',
            interest_percent=float(juros) if juros is not None else None,
            fine_percent=float(multa) if multa is not None else None,
        )
        payment_id = str(payment.get('id') or '').strip()
        if not payment_id:
            raise AsaasBoletoError('O Asaas não retornou o identificador da cobrança.')
        identification_field = client.get_identification_field(payment_id)
        cobranca = AsaasCobranca(
            empresa_id=lancamento.empresa_id,
            conta_banco_id=lancamento.conta_banco_id,
            lancamento_id=lancamento.id,
            entidade_id=entidade.id,
            asaas_payment_id=payment_id,
            asaas_customer_id=customer_id,
            external_reference=reference,
            valor=lancamento.valor_real,
            data_vencimento=lancamento.data_vencimento,
            status_asaas=payment.get('status') or 'PENDING',
            status_interno='pendente',
            invoice_url=payment.get('invoiceUrl'),
            bank_slip_url=payment.get('bankSlipUrl'),
            identification_field=identification_field,
            origem=origem,
            nfse_emissao_id=nfse_emissao_id,
            juros_mensal_percentual=juros,
            multa_percentual=multa,
            payload=_payload_json(payment),
        )
        db.session.add(cobranca)
        db.session.commit()
        return cobranca
    except (AsaasApiError, AsaasBoletoError):
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        logger.exception('Erro inesperado ao gerar boleto para lançamento %s', lancamento.id)
        raise AsaasBoletoError('Não foi possível registrar o boleto. Consulte os logs técnicos.')


def cancelar_boleto(cobranca: AsaasCobranca) -> AsaasCobranca:
    if not cobranca.asaas_payment_id:
        raise AsaasBoletoError('A cobrança não possui identificador no Asaas.')
    if cobranca.status_interno in {'pago', 'cancelado'}:
        raise AsaasBoletoError('Este boleto não pode ser cancelado no status atual.')

    config = AsaasContaConfig.query.filter_by(
        conta_banco_id=cobranca.conta_banco_id,
        empresa_id=cobranca.empresa_id,
    ).first()
    if not config or not config.cobranca_habilitada:
        raise AsaasBoletoError('A conta Asaas desta cobrança não está habilitada.')
    client = _client(config)
    payment = client.get_payment(cobranca.asaas_payment_id)
    if payment and str(payment.get('status') or '').upper() in {'RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH'}:
        raise AsaasBoletoError('Boleto já pago não pode ser cancelado.')
    result = client.cancel_payment(cobranca.asaas_payment_id)
    cobranca.status_asaas = str(result.get('status') or 'CANCELED').upper()
    cobranca.status_interno = 'cancelado'
    cobranca.mensagem_erro = None
    db.session.commit()
    return cobranca


def processar_webhook(payload: dict[str, Any], event_id: str, event_type: str) -> bool:
    payment = payload.get('payment') if isinstance(payload.get('payment'), dict) else payload
    reference = str(payment.get('externalReference') or '').strip()
    payment_id = str(payment.get('id') or '').strip() or None
    if not reference.startswith('LIVESUN:'):
        return False
    parts = reference.split(':')
    if len(parts) != 4 or parts[2] != 'LANCAMENTO' or not parts[1].isdigit():
        return False
    empresa_id = int(parts[1])
    evento = AsaasWebhookEvento(
        empresa_id=empresa_id,
        evento_id=event_id,
        evento=event_type,
        asaas_payment_id=payment_id,
        external_reference=reference,
        payload=_payload_json(payload),
        status_processamento='recebido',
    )
    db.session.add(evento)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return True

    cobranca = AsaasCobranca.query.filter_by(
        empresa_id=empresa_id,
        external_reference=reference,
    ).first()
    if not cobranca:
        evento.status_processamento = 'ignorado'
        evento.mensagem_erro = 'Cobrança não localizada.'
        db.session.commit()
        return True

    status = str(payment.get('status') or '').upper()
    cobranca.status_asaas = status or cobranca.status_asaas
    cobranca.payload = _payload_json(payload)
    if status in {'RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH'}:
        cobranca.status_interno = 'pago'
        cobranca.lancamento.status = 'pago'
        cobranca.lancamento.data_pagamento = datetime.utcnow().date()
        cobranca.lancamento.valor_pago = payment.get('netValue') or payment.get('value') or cobranca.valor
    elif status in {'OVERDUE'}:
        cobranca.status_interno = 'vencido'
    elif status in {'CANCELED', 'REFUNDED', 'REFUND_REQUESTED'}:
        cobranca.status_interno = 'cancelado'
    evento.status_processamento = 'processado'
    evento.processado_em = datetime.utcnow()
    db.session.commit()
    return True
