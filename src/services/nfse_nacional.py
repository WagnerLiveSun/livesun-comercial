from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET


def _decimal(value, default: Decimal = Decimal('0.00')) -> Decimal:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, ValueError, TypeError):
        return default


def _date(value) -> date | None:
    if value in (None, ''):
        return None
    if isinstance(value, date):
        return value
    text = str(value)
    try:
        return datetime.strptime(text[:10], '%Y-%m-%d').date()
    except Exception:
        return None


def generate_internal_number(empresa_id: int) -> str:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    suffix = uuid.uuid4().hex[:8].upper()
    return f'NFSE-{empresa_id}-{stamp}-{suffix}'


def build_idempotency_hash(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def build_dps_xml(payload: dict) -> str:
    root = ET.Element('DPSNacional')
    meta = ET.SubElement(root, 'metadados')
    ET.SubElement(meta, 'ambiente').text = str(payload.get('ambiente') or '')
    ET.SubElement(meta, 'numero_interno').text = str(payload.get('numero_interno') or '')
    ET.SubElement(meta, 'hash_idempotencia').text = str(payload.get('hash_idempotencia') or '')

    prestador = ET.SubElement(root, 'prestador')
    for key in ('empresa_id', 'empresa_nome', 'empresa_cnpj', 'inscricao_municipal', 'codigo_municipio', 'regime_tributario'):
        ET.SubElement(prestador, key).text = str(payload.get(key) or '')

    tomador = ET.SubElement(root, 'tomador')
    for key in ('tomador_id', 'tomador_nome', 'tomador_documento', 'tomador_tipo'):
        ET.SubElement(tomador, key).text = str(payload.get(key) or '')

    servico = ET.SubElement(root, 'servico')
    for key in ('servico_id', 'servico_codigo_interno', 'servico_codigo_nacional', 'servico_nbs', 'servico_descricao'):
        ET.SubElement(servico, key).text = str(payload.get(key) or '')

    valores = ET.SubElement(root, 'valores')
    for key in ('valor_servico', 'valor_deducoes', 'valor_iss'):
        ET.SubElement(valores, key).text = f"{_decimal(payload.get(key)):0.2f}"

    origem = ET.SubElement(root, 'origem')
    for key in ('origem_tipo', 'origem_id', 'origem_referencia', 'canal_origem'):
        ET.SubElement(origem, key).text = str(payload.get(key) or '')

    return ET.tostring(root, encoding='unicode')


def _response_payload(response) -> dict:
    try:
        content_type = (response.headers.get('content-type') or '').lower()
        if 'json' in content_type:
            return response.json()
    except Exception:
        pass
    return {'raw': response.text}


def transmitir_emissao(payload: dict, configuracao=None) -> dict:
    endpoint_base = (getattr(configuracao, 'endpoint_base', '') or '').strip().rstrip('/')
    if endpoint_base:
        import requests

        response = requests.post(
            f'{endpoint_base}/emissoes',
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'X-Idempotency-Key': payload.get('hash_idempotencia', ''),
                'X-NFSe-Layout-Version': str(payload.get('versao_layout') or ''),
            },
            timeout=30,
        )
        retorno = _response_payload(response)
        nfse_info = retorno.get('nfse') if isinstance(retorno, dict) else None
        return {
            'sucesso': response.ok,
            'status': retorno.get('status') or ('AUTORIZADA' if response.ok else 'REJEITADA'),
            'situacao_fiscal': retorno.get('situacao_fiscal') or retorno.get('status') or ('AUTORIZADA' if response.ok else 'REJEITADA'),
            'protocolo': retorno.get('protocolo'),
            'numero_nfse': (nfse_info or {}).get('numero') if isinstance(nfse_info, dict) else retorno.get('numero_nfse'),
            'codigo_verificacao': (nfse_info or {}).get('codigo_verificacao') if isinstance(nfse_info, dict) else retorno.get('codigo_verificacao'),
            'chave_nfse': (nfse_info or {}).get('chave') if isinstance(nfse_info, dict) else retorno.get('chave_nfse'),
            'xml_nfse': (nfse_info or {}).get('xml_armazenado') if isinstance(nfse_info, dict) else retorno.get('xml_nfse'),
            'payload_retorno': retorno,
            'mensagem': retorno.get('mensagem') or response.reason,
            'http_status': response.status_code,
        }

    numero_nfse = payload.get('numero_nfse_sugerido') or payload.get('numero_interno')
    codigo = payload.get('hash_idempotencia', '')[:8].upper()
    protocolo = f'LOCAL-{payload.get("hash_idempotencia", "")[:12].upper()}'
    xml_nfse = build_dps_xml(payload).replace('DPSNacional', 'NFSeNacional')
    retorno = {
        'simulado': True,
        'status': 'AUTORIZADA',
        'situacao_fiscal': 'AUTORIZADA',
        'protocolo': protocolo,
        'numero_nfse': numero_nfse,
        'codigo_verificacao': codigo,
        'chave_nfse': payload.get('hash_idempotencia'),
        'xml_nfse': xml_nfse,
        'mensagem': 'Emissão simulada por ausência de endpoint oficial configurado.',
    }
    return {
        'sucesso': True,
        'status': 'AUTORIZADA_LOCALMENTE',
        'situacao_fiscal': 'AUTORIZADA',
        'protocolo': protocolo,
        'numero_nfse': numero_nfse,
        'codigo_verificacao': codigo,
        'chave_nfse': payload.get('hash_idempotencia'),
        'xml_nfse': xml_nfse,
        'payload_retorno': retorno,
        'mensagem': retorno['mensagem'],
        'http_status': 200,
    }


def cancelar_emissao(payload: dict, configuracao=None) -> dict:
    endpoint_base = (getattr(configuracao, 'endpoint_base', '') or '').strip().rstrip('/')
    if endpoint_base:
        import requests

        response = requests.post(
            f'{endpoint_base}/cancelamentos',
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'X-Idempotency-Key': payload.get('hash_idempotencia', ''),
            },
            timeout=30,
        )
        retorno = _response_payload(response)
        return {
            'sucesso': response.ok,
            'status': retorno.get('status') or ('CANCELADA' if response.ok else 'REJEITADA'),
            'situacao_fiscal': retorno.get('situacao_fiscal') or ('CANCELADA' if response.ok else 'REJEITADA'),
            'protocolo': retorno.get('protocolo'),
            'payload_retorno': retorno,
            'mensagem': retorno.get('mensagem') or response.reason,
            'http_status': response.status_code,
        }

    retorno = {
        'simulado': True,
        'status': 'CANCELADA',
        'situacao_fiscal': 'CANCELADA',
        'protocolo': f'CANCEL-{payload.get("hash_idempotencia", "")[:12].upper()}',
        'mensagem': 'Cancelamento simulado por ausência de endpoint oficial configurado.',
    }
    return {
        'sucesso': True,
        'status': 'CANCELADA_LOCALMENTE',
        'situacao_fiscal': 'CANCELADA',
        'protocolo': retorno['protocolo'],
        'payload_retorno': retorno,
        'mensagem': retorno['mensagem'],
        'http_status': 200,
    }