"""Regras de negocio para cobrancas BolePix do Banco Inter."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, date
from decimal import Decimal
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_private_key,
)
from flask import current_app
from sqlalchemy.exc import IntegrityError

from src.models import (
    ContaBanco,
    Entidade,
    InterContaConfig,
    InterCobranca,
    InterWebhookEvento,
    Lancamento,
    db,
)
from src.services.asaas_boleto import AsaasBoletoError, proteger_credencial, revelar_credencial
from src.services.inter_bolepix_client import InterApiError, InterBolePixClient

logger = logging.getLogger(__name__)

INTER_CODIGO_BANCO = '077'
INTER_SANDBOX_BASE_URL = 'https://cdpj-sandbox.partners.uatinter.co'
INTER_PRODUCTION_BASE_URL = 'https://cdpj.partners.bancointer.com.br'


class InterBolePixError(ValueError):
    """Erro de validacao ou regra de negocio do Banco Inter."""


def _validar_certificado_chave(certificado: str, chave_privada: str) -> None:
    try:
        cert = x509.load_pem_x509_certificate(certificado.encode('utf-8'))
        key = load_pem_private_key(chave_privada.encode('utf-8'), password=None)
    except (ValueError, TypeError) as exc:
        raise InterBolePixError(
            'Certificado ou chave privada inválidos. Cole os conteúdos PEM completos.'
        ) from exc
    if cert.public_key().public_bytes(
        encoding=Encoding.DER,
        format=PublicFormat.SubjectPublicKeyInfo,
    ) != key.public_key().public_bytes(
        encoding=Encoding.DER,
        format=PublicFormat.SubjectPublicKeyInfo,
    ):
        raise InterBolePixError(
            'O certificado e a chave privada não pertencem ao mesmo par. '
            'Use o .crt/.pem e .key gerados juntos pelo Banco Inter.'
        )


def _percentual(value: str | float | Decimal | None, label: str) -> Decimal | None:
    if value in (None, ''):
        return None
    try:
        parsed = Decimal(str(value).replace(',', '.'))
    except Exception as exc:
        raise InterBolePixError(f'{label} inválido.') from exc
    if parsed < 0 or parsed > 100:
        raise InterBolePixError(f'{label} deve estar entre 0 e 100%.')
    return parsed


def configurar_conta_inter(
    *,
    conta_banco_id: int,
    empresa_id: int,
    habilitada: bool,
    ambiente: str | None,
    client_id: str | None,
    client_secret: str | None,
    certificado: str | None,
    chave_privada: str | None,
    webhook_token: str | None,
    juros_mensal_percentual: str | float | Decimal | None = None,
    multa_percentual: str | float | Decimal | None = None,
) -> InterContaConfig | None:
    config = InterContaConfig.query.filter_by(
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
        raise InterBolePixError('Selecione o ambiente do Banco Inter.')
    values = {
        'Client ID': client_id,
        'Client Secret': client_secret,
        'certificado .crt': certificado,
        'chave privada .key': chave_privada,
    }
    if config is None and any(not str(value or '').strip() for value in values.values()):
        raise InterBolePixError('As credenciais e certificados do Banco Inter são obrigatórios ao habilitar a cobrança.')
    if config is None:
        config = InterContaConfig(empresa_id=empresa_id, conta_banco_id=conta_banco_id)
        db.session.add(config)
    try:
        saved_certificate = revelar_credencial(config.certificado_criptografado) if config.certificado_criptografado else ''
        saved_private_key = revelar_credencial(config.chave_privada_criptografada) if config.chave_privada_criptografada else ''
    except AsaasBoletoError as exc:
        raise InterBolePixError(str(exc)) from exc
    effective_certificate = str(certificado or '').strip() or saved_certificate
    effective_private_key = str(chave_privada or '').strip() or saved_private_key
    if (
        effective_certificate
        and effective_private_key
        and '-----END ' in effective_certificate
        and '-----END ' in effective_private_key
    ):
        _validar_certificado_chave(effective_certificate, effective_private_key)
    encrypted_fields = {
        'client_id_criptografado': client_id,
        'client_secret_criptografado': client_secret,
        'certificado_criptografado': certificado,
        'chave_privada_criptografada': chave_privada,
        'webhook_token_criptografado': webhook_token,
    }
    for field, value in encrypted_fields.items():
        if value and str(value).strip():
            setattr(config, field, proteger_credencial(str(value)))
    required_fields = (
        'client_id_criptografado',
        'client_secret_criptografado',
        'certificado_criptografado',
        'chave_privada_criptografada',
    )
    if any(not getattr(config, field) for field in required_fields):
        raise InterBolePixError('A configuração do Banco Inter está incompleta.')
    config.cobranca_habilitada = True
    config.ativo = True
    config.ambiente = ambiente
    config.juros_mensal_percentual = _percentual(juros_mensal_percentual, 'Juros mensal')
    config.multa_percentual = _percentual(multa_percentual, 'Multa')
    return config


def _documento(value: str | None) -> str:
    digits = ''.join(char for char in str(value or '') if char.isdigit())
    if len(digits) not in {11, 14}:
        raise InterBolePixError('O pagador precisa ter CPF ou CNPJ válido.')
    return digits


def _telefone(value: str | None) -> tuple[str, str] | None:
    digits = ''.join(char for char in str(value or '') if char.isdigit())
    if digits.startswith('55') and len(digits) in {12, 13}:
        digits = digits[2:]
    if len(digits) in {10, 11}:
        return digits[:2], digits[2:]
    return None


def _validar_pagador(entidade: Entidade) -> None:
    required = {
        'nome': entidade.nome,
        'endereço': entidade.endereco_rua,
        'cidade': entidade.endereco_cidade,
        'UF': entidade.endereco_uf,
        'CEP': entidade.endereco_cep,
        'número': entidade.endereco_numero,
    }
    missing = [label for label, value in required.items() if not str(value or '').strip()]
    if missing:
        raise InterBolePixError(
            f'Complete os dados do pagador antes de emitir: {", ".join(missing)}.'
        )
    if not _telefone(entidade.telefone) and entidade.telefone:
        raise InterBolePixError('O telefone do pagador deve conter DDD e número válidos.')


def _client(config: InterContaConfig) -> tuple[InterBolePixClient, list[str]]:
    try:
        client_id = revelar_credencial(config.client_id_criptografado)
        client_secret = revelar_credencial(config.client_secret_criptografado)
        certificate = revelar_credencial(config.certificado_criptografado)
        private_key = revelar_credencial(config.chave_privada_criptografada)
    except AsaasBoletoError as exc:
        raise InterBolePixError(str(exc)) from exc
    if not all((client_id, client_secret, certificate, private_key)):
        raise InterBolePixError('Conta Inter habilitada sem credenciais ou certificados configurados.')
    base_url = (
        INTER_PRODUCTION_BASE_URL
        if config.ambiente == 'PRODUCAO'
        else INTER_SANDBOX_BASE_URL
    )
    paths: list[str] = []
    for suffix, content in (('.crt', certificate), ('.key', private_key)):
        handle = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8')
        try:
            handle.write(content or '')
        finally:
            handle.close()
        paths.append(handle.name)
    return InterBolePixClient(
        client_id=client_id or '',
        client_secret=client_secret or '',
        certificate_path=paths[0],
        private_key_path=paths[1],
        base_url=base_url,
        conta_corrente=(
            ''.join(char for char in str(config.conta_banco.numero_conta or '') if char.isdigit())
            if config.ambiente == 'PRODUCAO'
            else None
        ),
        timeout_seconds=int(current_app.config.get('INTER_TIMEOUT_SECONDS') or 20),
    ), paths


def gerar_bolepix(
    lancamento: Lancamento,
    *,
    origem: str = 'lancamento',
    nfse_emissao_id: int | None = None,
    juros_mensal_percentual: Decimal | float | None = None,
    multa_percentual: Decimal | float | None = None,
) -> InterCobranca:
    if lancamento.status != 'aberto':
        raise InterBolePixError('Somente lançamentos em aberto podem gerar cobrança.')
    conta = ContaBanco.query.filter_by(id=lancamento.conta_banco_id, empresa_id=lancamento.empresa_id).first()
    if not conta or str(conta.codigo_banco or '').zfill(3) != INTER_CODIGO_BANCO:
        raise InterBolePixError('A conta selecionada não é uma conta do Banco Inter (código 077).')
    config = InterContaConfig.query.filter_by(
        conta_banco_id=conta.id,
        empresa_id=lancamento.empresa_id,
    ).first()
    if not config or not config.habilitada:
        raise InterBolePixError('A cobrança bancária do Banco Inter não está habilitada nesta conta.')
    existing = InterCobranca.query.filter_by(
        empresa_id=lancamento.empresa_id,
        lancamento_id=lancamento.id,
    ).filter(InterCobranca.status_interno.notin_(['cancelado', 'falhou'])).first()
    if existing:
        raise InterBolePixError('Este lançamento já possui uma cobrança Inter ativa.')
    entidade = Entidade.query.filter_by(id=lancamento.entidade_id, empresa_id=lancamento.empresa_id).first()
    if not entidade:
        raise InterBolePixError('Pagador do lançamento não encontrado.')
    _validar_pagador(entidade)
    if lancamento.data_vencimento <= date.today():
        raise InterBolePixError('A data de vencimento deve ser posterior à data atual.')
    juros = _percentual(
        juros_mensal_percentual if juros_mensal_percentual is not None else config.juros_mensal_percentual,
        'Juros mensal',
    )
    multa = _percentual(
        multa_percentual if multa_percentual is not None else config.multa_percentual,
        'Multa',
    )
    seu_numero = f'LS{lancamento.empresa_id}-{lancamento.id}'
    try:
        client, paths = _client(config)
    except InterBolePixError:
        raise
    try:
        pagador: dict[str, Any] = {
            'cpfCnpj': _documento(entidade.cnpj_cpf),
            'tipoPessoa': 'FISICA' if len(_documento(entidade.cnpj_cpf)) == 11 else 'JURIDICA',
            'nome': entidade.nome,
            'endereco': entidade.endereco_rua or '',
            'numero': entidade.endereco_numero or 'S/N',
            'bairro': entidade.endereco_bairro or '',
            'cidade': entidade.endereco_cidade or '',
            'uf': entidade.endereco_uf or '',
            'cep': entidade.endereco_cep or '',
        }
        if entidade.email:
            pagador['email'] = entidade.email
        telefone = _telefone(entidade.telefone)
        if telefone:
            pagador['ddd'], pagador['telefone'] = telefone
        body: dict[str, Any] = {
            'seuNumero': seu_numero,
            'valorNominal': f'{Decimal(str(lancamento.valor_real)):.2f}',
            'dataVencimento': lancamento.data_vencimento.isoformat(),
            'numDiasAgenda': '30',
            'pagador': pagador,
        }
        if multa is not None:
            body['multa'] = {'codigo': 'PERCENTUAL', 'taxa': f'{multa:.2f}'}
        if juros is not None:
            body['mora'] = {'codigo': 'TAXAMENSAL', 'taxa': f'{juros:.2f}'}
        response = client.emitir_cobranca(body)
        codigo = str(response.get('codigoSolicitacao') or response.get('codigoSolicitacaoCobranca') or '').strip()
        if not codigo:
            raise InterBolePixError('O Banco Inter não retornou o código da cobrança.')
        cobranca = InterCobranca(
            empresa_id=lancamento.empresa_id,
            conta_banco_id=conta.id,
            lancamento_id=lancamento.id,
            entidade_id=entidade.id,
            codigo_solicitacao=codigo,
            seu_numero=seu_numero,
            nosso_numero=str(response.get('nossoNumero') or '') or None,
            valor=lancamento.valor_real,
            data_vencimento=lancamento.data_vencimento,
            status_inter=str(response.get('situacao') or response.get('status') or 'EMITIDA'),
            status_interno='pendente',
            linha_digitavel=response.get('linhaDigitavel') or response.get('codBarraLinhaDigitavel'),
            codigo_barras=response.get('codigoBarras') or response.get('codBarras'),
            qr_code=response.get('qrCode') or response.get('pixCopiaECola'),
            pdf_url=response.get('pdf') or response.get('pdfUrl'),
            origem=origem,
            nfse_emissao_id=nfse_emissao_id,
            juros_mensal_percentual=juros,
            multa_percentual=multa,
            payload=json.dumps(response, ensure_ascii=False),
        )
        db.session.add(cobranca)
        db.session.commit()
        return cobranca
    except InterApiError as exc:
        db.session.rollback()
        raise InterBolePixError(str(exc)) from exc
    except InterBolePixError:
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        logger.exception('Erro ao gerar BolePix para lançamento %s', lancamento.id)
        raise InterBolePixError('Não foi possível registrar a cobrança Inter.') from exc
    finally:
        for path in paths:
            try:
                os.unlink(path)
            except OSError:
                logger.warning('Não foi possível remover arquivo temporário do certificado Inter.')


def processar_webhook(payload: dict[str, Any], event_id: str) -> bool:
    codigo = str(
        payload.get('codigoSolicitacao')
        or payload.get('codigoSolicitacaoCobranca')
        or payload.get('codigo')
        or ''
    ).strip()
    if not codigo:
        return False
    cobranca = InterCobranca.query.filter_by(codigo_solicitacao=codigo).first()
    if not cobranca:
        return False
    evento = InterWebhookEvento(
        empresa_id=cobranca.empresa_id,
        evento_id=event_id,
        codigo_solicitacao=codigo,
        payload=json.dumps(payload, ensure_ascii=False),
    )
    db.session.add(evento)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return True
    status = str(payload.get('situacao') or payload.get('status') or '').upper()
    cobranca.status_inter = status or cobranca.status_inter
    cobranca.payload = json.dumps(payload, ensure_ascii=False)
    if status in {'PAGA', 'PAGO', 'LIQUIDADA', 'RECEBIDA'}:
        cobranca.status_interno = 'pago'
        cobranca.lancamento.status = 'pago'
        cobranca.lancamento.data_pagamento = datetime.utcnow().date()
        cobranca.lancamento.valor_pago = payload.get('valorPago') or cobranca.valor
    elif status in {'VENCIDA', 'OVERDUE'}:
        cobranca.status_interno = 'vencido'
    elif status in {'CANCELADA', 'CANCELED'}:
        cobranca.status_interno = 'cancelado'
    evento.status_processamento = 'processado'
    evento.processado_em = datetime.utcnow()
    db.session.commit()
    return True
