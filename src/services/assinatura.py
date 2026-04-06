from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
import logging
import re
from typing import Any

from flask import current_app
from sqlalchemy.exc import IntegrityError

from src.models import (
    AssinaturaEmpresa,
    CatalogoPlanoComercial,
    CobrancaRecorrente,
    Empresa,
    EventoCobranca,
    User,
    db,
)
from src.services.asaas_client import AsaasApiError, AsaasClient


logger = logging.getLogger(__name__)


def _today() -> date:
    return date.today()


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(text[:19], fmt).date()
        except ValueError:
            continue
    return None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip().replace('Z', '')
    if not text:
        return None
    for fmt in (
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
    ):
        try:
            return datetime.strptime(text[:26], fmt)
        except ValueError:
            continue
    return None


def _add_months(base_date: date, months: int) -> date:
    month = base_date.month - 1 + months
    year = base_date.year + month // 12
    month = month % 12 + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _next_cycle_due_date(current_due_date: date, ciclo_cobranca: str) -> date:
    ciclo = (ciclo_cobranca or 'mensal').strip().lower()
    if ciclo == 'anual':
        return _add_months(current_due_date, 12)
    return _add_months(current_due_date, 1)


class ServicoAssinatura:
    STATUS_ATIVA = 'ativa'
    STATUS_TRIAL = 'trial'
    STATUS_SUSPENSA = 'suspensa'
    STATUS_CANCELADA = 'cancelada'

    BLOQUEIO_NENHUM = 'nenhum'
    BLOQUEIO_PARCIAL = 'parcial'
    BLOQUEIO_TOTAL = 'total'

    ASAAS_STATUS_PAGO = {'RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH', 'DUNNING_RECEIVED'}
    ASAAS_STATUS_INADIMPLENTE = {'OVERDUE', 'DUNNING_REQUESTED'}
    ASAAS_STATUS_FALHA = {'REFUND_REQUESTED', 'CHARGEBACK_REQUESTED', 'CHARGEBACK_DISPUTE'}
    ASAAS_STATUS_ABERTA = {'PENDING', 'OVERDUE'}

    @staticmethod
    def _trial_days() -> int:
        value = int(current_app.config.get('ASSINATURA_TRIAL_DIAS') or 7)
        return value if value > 0 else 7

    @staticmethod
    def _digits_only(value: str | None) -> str | None:
        if not value:
            return None
        digits = re.sub(r'\D+', '', str(value))
        return digits or None

    @staticmethod
    def _is_valid_cpf(document: str) -> bool:
        if len(document) != 11 or document == document[0] * 11:
            return False

        def calc_digit(base: str, factor: int) -> int:
            total = sum(int(num) * (factor - idx) for idx, num in enumerate(base))
            rest = (total * 10) % 11
            return 0 if rest == 10 else rest

        d1 = calc_digit(document[:9], 10)
        d2 = calc_digit(document[:10], 11)
        return document[-2:] == f'{d1}{d2}'

    @staticmethod
    def _is_valid_cnpj(document: str) -> bool:
        if len(document) != 14 or document == document[0] * 14:
            return False

        def calc_digit(base: str, weights: list[int]) -> int:
            total = sum(int(num) * weight for num, weight in zip(base, weights))
            rest = total % 11
            return 0 if rest < 2 else 11 - rest

        w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        d1 = calc_digit(document[:12], w1)
        d2 = calc_digit(document[:13], w2)
        return document[-2:] == f'{d1}{d2}'

    @staticmethod
    def _valid_document_or_none(value: str | None) -> str | None:
        digits = ServicoAssinatura._digits_only(value)
        if not digits:
            return None
        if len(digits) == 11 and ServicoAssinatura._is_valid_cpf(digits):
            return digits
        if len(digits) == 14 and ServicoAssinatura._is_valid_cnpj(digits):
            return digits
        return None

    @staticmethod
    def _is_asaas_enabled() -> bool:
        return bool(current_app.config.get('ASAAS_ENABLED')) and bool(current_app.config.get('ASAAS_API_KEY'))

    @staticmethod
    def _build_asaas_client() -> AsaasClient:
        return AsaasClient(
            api_key=str(current_app.config.get('ASAAS_API_KEY') or '').strip(),
            base_url=str(current_app.config.get('ASAAS_BASE_URL') or 'https://sandbox.asaas.com/api/v3').strip(),
            timeout_seconds=int(current_app.config.get('ASAAS_TIMEOUT_SECONDS') or 15),
        )

    @staticmethod
    def _resolve_customer_email(empresa_id: int) -> str | None:
        admin_user = User.query.filter_by(empresa_id=empresa_id, is_admin=True, is_active=True).first()
        if admin_user and admin_user.email:
            return admin_user.email.strip()

        fallback_user = User.query.filter_by(empresa_id=empresa_id, is_active=True).first()
        if fallback_user and fallback_user.email:
            return fallback_user.email.strip()
        return None

    @staticmethod
    def _resolve_preco_plano(assinatura: AssinaturaEmpresa) -> Decimal:
        oferta = (
            CatalogoPlanoComercial.query
            .filter_by(
                codigo_plano=(assinatura.plano_codigo or 'premium').strip().lower(),
                periodicidade=(assinatura.ciclo_cobranca or 'mensal').strip().lower(),
                ativo=True,
            )
            .order_by(CatalogoPlanoComercial.versao_oferta.desc(), CatalogoPlanoComercial.id.desc())
            .first()
        )
        if oferta and oferta.preco is not None:
            return Decimal(str(oferta.preco))

        defaults = {
            ('basic', 'mensal'): Decimal('49.00'),
            ('intermediate', 'mensal'): Decimal('129.00'),
            ('premium', 'mensal'): Decimal('249.00'),
            ('basic', 'anual'): Decimal('490.00'),
            ('intermediate', 'anual'): Decimal('1290.00'),
            ('premium', 'anual'): Decimal('2490.00'),
        }
        return defaults.get(
            (
                (assinatura.plano_codigo or 'premium').strip().lower(),
                (assinatura.ciclo_cobranca or 'mensal').strip().lower(),
            ),
            Decimal('249.00'),
        )

    @staticmethod
    def _cycle_to_asaas(ciclo_cobranca: str) -> str:
        return 'YEARLY' if (ciclo_cobranca or '').strip().lower() == 'anual' else 'MONTHLY'

    @staticmethod
    def _payment_links(payment_data: dict[str, Any]) -> dict[str, str | None]:
        invoice_url = payment_data.get('invoiceUrl')
        bank_slip_url = payment_data.get('bankSlipUrl')
        return {
            'invoice_url': str(invoice_url).strip() if invoice_url else None,
            'bank_slip_url': str(bank_slip_url).strip() if bank_slip_url else None,
        }

    @staticmethod
    def _dump_payload(payload: dict[str, Any]) -> str:
        try:
            return json.dumps(payload, ensure_ascii=False)
        except Exception:
            return str(payload)

    @staticmethod
    def provisionar_gateway_asaas(
        assinatura: AssinaturaEmpresa,
        billing_type_override: str | None = None,
    ) -> None:
        if not assinatura or assinatura.gateway != 'asaas':
            return
        if not ServicoAssinatura._is_asaas_enabled():
            return

        empresa = Empresa.query.filter_by(id=assinatura.empresa_id).first()
        if not empresa:
            return

        external_reference = f'empresa:{assinatura.empresa_id}'

        try:
            client = ServicoAssinatura._build_asaas_client()
            documento_validado = ServicoAssinatura._valid_document_or_none(empresa.cnpj)
            if not documento_validado and ServicoAssinatura._digits_only(empresa.cnpj):
                assinatura.motivo_status = 'Aviso: CPF/CNPJ da empresa inválido para o Asaas; cliente será criado sem documento.'

            customer_id = assinatura.gateway_customer_id
            if not customer_id:
                existing_customer = client.find_customer_by_external_reference(external_reference)
                if existing_customer and existing_customer.get('id'):
                    customer_id = str(existing_customer['id'])
                else:
                    created_customer = client.create_customer(
                        name=empresa.nome,
                        cpf_cnpj=documento_validado,
                        email=ServicoAssinatura._resolve_customer_email(empresa.id),
                        external_reference=external_reference,
                    )
                    customer_id = str(created_customer.get('id') or '').strip() or None

                if customer_id:
                    assinatura.gateway_customer_id = customer_id

            if assinatura.gateway_subscription_id or not customer_id:
                db.session.flush()
                return

            existing_subscription = client.find_subscription_by_external_reference(external_reference)
            if existing_subscription and existing_subscription.get('id'):
                assinatura.gateway_subscription_id = str(existing_subscription['id'])
                db.session.flush()
                return

            preco = ServicoAssinatura._resolve_preco_plano(assinatura)
            billing_type = (billing_type_override or str(current_app.config.get('ASAAS_BILLING_TYPE') or 'BOLETO')).upper()
            created_subscription = client.create_subscription(
                customer_id=customer_id,
                billing_type=billing_type,
                value=float(preco),
                next_due_date=(assinatura.data_vencimento or _today()).isoformat(),
                cycle=ServicoAssinatura._cycle_to_asaas(assinatura.ciclo_cobranca),
                external_reference=external_reference,
                description=f'LiveSun Controller - plano {assinatura.plano_codigo}',
            )
            subscription_id = str(created_subscription.get('id') or '').strip()
            if subscription_id:
                assinatura.gateway_subscription_id = subscription_id

            db.session.flush()
        except AsaasApiError as exc:
            assinatura.motivo_status = f'Erro Asaas: {str(exc)[:220]}'
            db.session.flush()
            logger.warning('Falha ao provisionar assinatura Asaas para empresa %s: %s', assinatura.empresa_id, exc)
        except Exception as exc:
            assinatura.motivo_status = f'Erro inesperado Asaas: {str(exc)[:200]}'
            db.session.flush()
            logger.exception('Erro inesperado ao provisionar Asaas para empresa %s: %s', assinatura.empresa_id, exc)

    @staticmethod
    def sincronizar_cobranca_pendente_asaas(assinatura: AssinaturaEmpresa) -> dict[str, Any] | None:
        if not assinatura or assinatura.gateway != 'asaas':
            return None
        if not assinatura.gateway_subscription_id:
            return None
        if not ServicoAssinatura._is_asaas_enabled():
            return None

        client = ServicoAssinatura._build_asaas_client()
        payments = client.list_subscription_payments(assinatura.gateway_subscription_id, limit=20)
        if not payments:
            return None

        selected_payment = None
        for payment in payments:
            status = str(payment.get('status') or '').strip().upper()
            if status in ServicoAssinatura.ASAAS_STATUS_ABERTA:
                selected_payment = payment
                break

        if not selected_payment:
            selected_payment = payments[0]

        cobranca = ServicoAssinatura._find_or_create_cobranca(assinatura, selected_payment)
        status = str(selected_payment.get('status') or '').strip().upper()
        if status in ServicoAssinatura.ASAAS_STATUS_INADIMPLENTE:
            cobranca.status = 'vencido'
        elif status in ServicoAssinatura.ASAAS_STATUS_PAGO:
            cobranca.status = 'pago'
        else:
            cobranca.status = 'pendente'
        cobranca.payload_gateway = ServicoAssinatura._dump_payload(selected_payment)

        links = ServicoAssinatura._payment_links(selected_payment)
        return {
            'gateway_cobranca_id': str(selected_payment.get('id') or '') or None,
            'status': status,
            'valor': Decimal(str(selected_payment.get('value') or 0)),
            'vencimento': _parse_date(selected_payment.get('dueDate')),
            'invoice_url': links['invoice_url'],
            'bank_slip_url': links['bank_slip_url'],
        }

    @staticmethod
    def obter_ou_criar_assinatura(empresa_id: int) -> AssinaturaEmpresa:
        assinatura = AssinaturaEmpresa.query.filter_by(empresa_id=empresa_id).first()
        if assinatura:
            # Ajusta assinaturas em trial para refletir a regra vigente de duracao.
            if assinatura.status == ServicoAssinatura.STATUS_TRIAL and assinatura.data_inicio:
                trial_days = ServicoAssinatura._trial_days()
                novo_fim_trial = assinatura.data_inicio + timedelta(days=trial_days)
                if assinatura.data_fim_trial != novo_fim_trial:
                    assinatura.data_fim_trial = novo_fim_trial
                    assinatura.data_vencimento = novo_fim_trial
                    assinatura.data_limite_carencia = novo_fim_trial + timedelta(days=int(assinatura.carencia_dias or 7))

            if not assinatura.gateway_customer_id or not assinatura.gateway_subscription_id:
                ServicoAssinatura.provisionar_gateway_asaas(assinatura)
            return assinatura

        empresa = Empresa.query.filter_by(id=empresa_id).first()
        plano_codigo = (empresa.plano if empresa and empresa.plano else 'premium').strip().lower()

        hoje = _today()
        trial_days = ServicoAssinatura._trial_days()
        assinatura = AssinaturaEmpresa(
            empresa_id=empresa_id,
            plano_codigo=plano_codigo,
            ciclo_cobranca='mensal',
            status=ServicoAssinatura.STATUS_TRIAL,
            gateway='asaas',
            data_inicio=hoje,
            data_fim_trial=hoje + timedelta(days=trial_days),
            data_vencimento=hoje + timedelta(days=trial_days),
            data_renovacao=None,
            carencia_dias=7,
            data_limite_carencia=hoje + timedelta(days=trial_days + 7),
            bloqueio_nivel=ServicoAssinatura.BLOQUEIO_NENHUM,
            politica_efetivacao_dias=30,
        )
        db.session.add(assinatura)
        db.session.flush()

        ServicoAssinatura.provisionar_gateway_asaas(assinatura)
        return assinatura

    @staticmethod
    def recalcular_status_por_carencia(assinatura: AssinaturaEmpresa, referencia: date | None = None) -> AssinaturaEmpresa:
        if not assinatura:
            return assinatura

        if assinatura.status == ServicoAssinatura.STATUS_CANCELADA:
            return assinatura

        hoje = referencia or _today()
        vencimento = assinatura.data_vencimento
        if not vencimento:
            return assinatura

        data_limite_carencia = assinatura.data_limite_carencia
        if not data_limite_carencia:
            dias = int(assinatura.carencia_dias or 7)
            data_limite_carencia = vencimento + timedelta(days=dias)
            assinatura.data_limite_carencia = data_limite_carencia

        if hoje <= vencimento:
            if assinatura.status != ServicoAssinatura.STATUS_TRIAL:
                assinatura.status = ServicoAssinatura.STATUS_ATIVA
            assinatura.bloqueio_nivel = ServicoAssinatura.BLOQUEIO_NENHUM
            assinatura.bloqueado_desde = None
            assinatura.motivo_status = None
            return assinatura

        if hoje <= data_limite_carencia:
            if assinatura.status not in (ServicoAssinatura.STATUS_CANCELADA, ServicoAssinatura.STATUS_TRIAL):
                assinatura.status = ServicoAssinatura.STATUS_ATIVA
            assinatura.bloqueio_nivel = ServicoAssinatura.BLOQUEIO_PARCIAL
            assinatura.bloqueado_desde = assinatura.bloqueado_desde or datetime.utcnow()
            assinatura.motivo_status = 'Pagamento em atraso dentro da carencia.'
            return assinatura

        assinatura.status = ServicoAssinatura.STATUS_SUSPENSA
        assinatura.bloqueio_nivel = ServicoAssinatura.BLOQUEIO_TOTAL
        assinatura.bloqueado_desde = assinatura.bloqueado_desde or datetime.utcnow()
        assinatura.motivo_status = 'Assinatura suspensa por inadimplencia apos carencia.'
        return assinatura

    @staticmethod
    def marcar_cobranca_paga(
        assinatura: AssinaturaEmpresa,
        cobranca: CobrancaRecorrente,
        data_pagamento: datetime | None,
        valor_pago: Decimal | None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        cobranca.status = 'pago'
        cobranca.data_pagamento = data_pagamento or datetime.utcnow()
        cobranca.valor_pago = valor_pago if valor_pago is not None else cobranca.valor_previsto
        cobranca.payload_gateway = ServicoAssinatura._dump_payload(payload or {})

        due_base = cobranca.data_vencimento or assinatura.data_vencimento or _today()
        assinatura.status = ServicoAssinatura.STATUS_ATIVA
        assinatura.bloqueio_nivel = ServicoAssinatura.BLOQUEIO_NENHUM
        assinatura.bloqueado_desde = None
        assinatura.motivo_status = None
        assinatura.data_renovacao = _today()
        assinatura.data_vencimento = _next_cycle_due_date(due_base, assinatura.ciclo_cobranca)
        assinatura.data_limite_carencia = assinatura.data_vencimento + timedelta(days=int(assinatura.carencia_dias or 7))

    @staticmethod
    def marcar_cobranca_em_atraso(
        assinatura: AssinaturaEmpresa,
        cobranca: CobrancaRecorrente,
        status_cobranca: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        cobranca.status = status_cobranca
        cobranca.payload_gateway = ServicoAssinatura._dump_payload(payload or {})
        assinatura.motivo_status = f'Atualizacao de cobranca via webhook Asaas: {status_cobranca}.'
        ServicoAssinatura.recalcular_status_por_carencia(assinatura)

    @staticmethod
    def _find_assinatura_from_payload(payment_data: dict[str, Any]) -> AssinaturaEmpresa | None:
        subscription_id = payment_data.get('subscription') or payment_data.get('subscriptionId')
        if subscription_id:
            assinatura = AssinaturaEmpresa.query.filter_by(gateway_subscription_id=str(subscription_id)).first()
            if assinatura:
                return assinatura

        customer_id = payment_data.get('customer') or payment_data.get('customerId')
        if customer_id:
            assinatura = AssinaturaEmpresa.query.filter_by(gateway_customer_id=str(customer_id)).first()
            if assinatura:
                return assinatura

        external_reference = payment_data.get('externalReference') or payment_data.get('external_reference')
        if external_reference:
            text = str(external_reference).strip().lower()
            if text.startswith('empresa:'):
                empresa_text = text.split(':', 1)[1].strip()
                if empresa_text.isdigit():
                    return AssinaturaEmpresa.query.filter_by(empresa_id=int(empresa_text)).first()
            if text.isdigit():
                return AssinaturaEmpresa.query.filter_by(empresa_id=int(text)).first()

        return None

    @staticmethod
    def _find_or_create_cobranca(assinatura: AssinaturaEmpresa, payment_data: dict[str, Any]) -> CobrancaRecorrente:
        gateway_cobranca_id = payment_data.get('id')
        if gateway_cobranca_id:
            cobranca = CobrancaRecorrente.query.filter_by(gateway_cobranca_id=str(gateway_cobranca_id)).first()
            if cobranca:
                return cobranca

        external_reference = payment_data.get('externalReference') or payment_data.get('external_reference')
        reference = str(external_reference or f'asaas:{gateway_cobranca_id or "sem-id"}:{assinatura.empresa_id}')

        cobranca = CobrancaRecorrente.query.filter_by(referencia_interna=reference).first()
        if cobranca:
            return cobranca

        due_date = _parse_date(payment_data.get('dueDate')) or assinatura.data_vencimento or _today()
        value = Decimal(str(payment_data.get('value') or 0))

        cobranca = CobrancaRecorrente(
            empresa_id=assinatura.empresa_id,
            assinatura_id=assinatura.id,
            gateway='asaas',
            gateway_cobranca_id=str(gateway_cobranca_id) if gateway_cobranca_id else None,
            referencia_interna=reference,
            competencia_ano=due_date.year,
            competencia_mes=due_date.month,
            periodicidade=assinatura.ciclo_cobranca,
            valor_previsto=value,
            valor_pago=None,
            status='pendente',
            data_emissao=_parse_date(payment_data.get('dateCreated')),
            data_vencimento=due_date,
            data_pagamento=None,
            tentativas_pagamento=0,
            payload_gateway=ServicoAssinatura._dump_payload(payment_data),
        )
        db.session.add(cobranca)
        db.session.flush()
        return cobranca

    @staticmethod
    def processar_webhook_asaas(
        payload: dict[str, Any],
        event_id_externo: str | None = None,
        tipo_evento: str | None = None,
    ) -> dict[str, Any]:
        event_id = str(event_id_externo or payload.get('id') or payload.get('eventId') or '').strip()
        event_type = str(tipo_evento or payload.get('event') or payload.get('type') or 'unknown').strip()

        if not event_id:
            return {
                'sucesso': False,
                'mensagem': 'Webhook sem event_id.',
                'http_status': 400,
            }

        existing_event = EventoCobranca.query.filter_by(gateway='asaas', event_id_externo=event_id).first()
        if existing_event:
            return {
                'sucesso': True,
                'mensagem': 'Evento ja processado anteriormente (idempotente).',
                'evento_id': existing_event.id,
                'http_status': 200,
            }

        payment_data = payload.get('payment') if isinstance(payload.get('payment'), dict) else payload
        assinatura = ServicoAssinatura._find_assinatura_from_payload(payment_data)

        if not assinatura:
            evento = EventoCobranca(
                gateway='asaas',
                event_id_externo=event_id,
                tipo_evento=event_type,
                status_processamento='ignorado',
                payload=str(payload),
                mensagem_erro='Assinatura nao localizada para o evento.',
            )
            db.session.add(evento)
            db.session.commit()
            return {
                'sucesso': True,
                'mensagem': 'Evento ignorado: assinatura nao localizada.',
                'evento_id': evento.id,
                'http_status': 200,
            }

        cobranca = ServicoAssinatura._find_or_create_cobranca(assinatura, payment_data)
        asaas_status = str(payment_data.get('status') or '').strip().upper()
        valor_pago = payment_data.get('netValue', payment_data.get('value'))
        valor_pago_decimal = Decimal(str(valor_pago)) if valor_pago is not None else None
        data_pagamento = _parse_datetime(payment_data.get('paymentDate'))

        try:
            if asaas_status in ServicoAssinatura.ASAAS_STATUS_PAGO:
                ServicoAssinatura.marcar_cobranca_paga(
                    assinatura=assinatura,
                    cobranca=cobranca,
                    data_pagamento=data_pagamento,
                    valor_pago=valor_pago_decimal,
                    payload=payload,
                )
            elif asaas_status in ServicoAssinatura.ASAAS_STATUS_INADIMPLENTE:
                ServicoAssinatura.marcar_cobranca_em_atraso(
                    assinatura=assinatura,
                    cobranca=cobranca,
                    status_cobranca='vencido',
                    payload=payload,
                )
            elif asaas_status in ServicoAssinatura.ASAAS_STATUS_FALHA:
                ServicoAssinatura.marcar_cobranca_em_atraso(
                    assinatura=assinatura,
                    cobranca=cobranca,
                    status_cobranca='falhou',
                    payload=payload,
                )
            else:
                cobranca.payload_gateway = ServicoAssinatura._dump_payload(payload)
                ServicoAssinatura.recalcular_status_por_carencia(assinatura)

            assinatura.gateway = 'asaas'
            assinatura.gateway_customer_id = str(payment_data.get('customer') or assinatura.gateway_customer_id or '') or None
            assinatura.gateway_subscription_id = str(payment_data.get('subscription') or assinatura.gateway_subscription_id or '') or None

            evento = EventoCobranca(
                empresa_id=assinatura.empresa_id,
                assinatura_id=assinatura.id,
                cobranca_id=cobranca.id,
                gateway='asaas',
                event_id_externo=event_id,
                tipo_evento=event_type,
                status_processamento='processado',
                processado_em=datetime.utcnow(),
                payload=str(payload),
            )
            db.session.add(evento)
            db.session.commit()

            return {
                'sucesso': True,
                'mensagem': 'Webhook Asaas processado com sucesso.',
                'evento_id': evento.id,
                'assinatura_id': assinatura.id,
                'cobranca_id': cobranca.id,
                'http_status': 200,
            }
        except IntegrityError:
            db.session.rollback()
            return {
                'sucesso': True,
                'mensagem': 'Evento concorrente ja registrado (idempotente).',
                'http_status': 200,
            }
        except Exception as exc:
            db.session.rollback()
            evento_erro = EventoCobranca(
                empresa_id=assinatura.empresa_id,
                assinatura_id=assinatura.id,
                cobranca_id=getattr(cobranca, 'id', None),
                gateway='asaas',
                event_id_externo=event_id,
                tipo_evento=event_type,
                status_processamento='erro',
                payload=str(payload),
                mensagem_erro=str(exc)[:255],
            )
            db.session.add(evento_erro)
            db.session.commit()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao processar webhook: {exc}',
                'evento_id': evento_erro.id,
                'http_status': 500,
            }
