"""Cliente HTTP da API de cobranca BolePix do Banco Inter."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class InterApiError(RuntimeError):
    """Erro retornado pela API do Banco Inter."""


@dataclass
class InterBolePixClient:
    client_id: str
    client_secret: str
    certificate_path: str
    private_key_path: str
    base_url: str
    conta_corrente: str | None = None
    timeout_seconds: int = 20

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip('/')
        self._access_token: str | None = None

    @property
    def _certificate(self) -> tuple[str, str]:
        return self.certificate_path, self.private_key_path

    def _request_token(self) -> str:
        try:
            response = requests.post(
                f'{self.base_url}/oauth/v2/token',
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'client_credentials',
                    'scope': 'boleto-cobranca.read boleto-cobranca.write',
                },
                cert=self._certificate,
                timeout=self.timeout_seconds,
            )
        except requests.exceptions.SSLError as exc:
            raise InterApiError(
                'Certificado e chave privada do Banco Inter não correspondem ou estão inválidos.'
            ) from exc
        payload = _response_payload(response)
        if response.status_code >= 400:
            raise InterApiError(f'Inter OAuth {response.status_code}: {_error_message(payload)}')
        token = str(payload.get('access_token') or '').strip()
        if not token:
            raise InterApiError('O Banco Inter não retornou o token de acesso.')
        self._access_token = token
        return token

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        token = self._access_token or self._request_token()
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'Authorization': f'Bearer {token}',
        }
        if self.conta_corrente:
            headers['x-conta-corrente'] = self.conta_corrente
        response = requests.request(
            method,
            f'{self.base_url}{path}',
            headers=headers,
            cert=self._certificate,
            timeout=self.timeout_seconds,
            **kwargs,
        )
        if response.status_code == 401 and self._access_token:
            self._access_token = self._request_token()
            headers['Authorization'] = f'Bearer {self._access_token}'
            response = requests.request(
                method,
                f'{self.base_url}{path}',
                headers=headers,
                cert=self._certificate,
                timeout=self.timeout_seconds,
                **kwargs,
            )
        payload = _response_payload(response)
        if response.status_code >= 400:
            logger.warning(
                'API Inter rejeitou %s %s: status=%s, chaves_resposta=%s, tamanho_resposta=%s',
                method,
                path,
                response.status_code,
                sorted(payload.keys()),
                len(response.content),
            )
            raise InterApiError(f'Inter {response.status_code}: {_error_message(payload)}')
        return payload

    def emitir_cobranca(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request('POST', '/cobranca/v3/cobrancas', json=body)

    def consultar_cobranca(self, codigo_solicitacao: str) -> dict[str, Any]:
        return self._request('GET', f'/cobranca/v3/cobrancas/{codigo_solicitacao}')

    def baixar_pdf(self, codigo_solicitacao: str) -> bytes:
        token = self._access_token or self._request_token()
        response = requests.get(
            f'{self.base_url}/cobranca/v3/cobrancas/{codigo_solicitacao}/pdf',
            headers={'Authorization': f'Bearer {token}'},
            cert=self._certificate,
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise InterApiError(f'Inter PDF {response.status_code}: {response.text[:500]}')
        return response.content

    def cancelar_cobranca(self, codigo_solicitacao: str) -> dict[str, Any]:
        return self._request(
            'POST',
            f'/cobranca/v3/cobrancas/{codigo_solicitacao}/cancelar',
        )


def _response_payload(response: requests.Response) -> dict[str, Any]:
    if 'application/json' in (response.headers.get('content-type') or '').lower():
        payload = response.json()
        return payload if isinstance(payload, dict) else {'data': payload}
    return {'raw': response.text}


def _error_message(payload: dict[str, Any]) -> str:
    messages = _collect_error_messages(payload)
    correlation_id = (
        payload.get('correlationId')
        or payload.get('correlationID')
        or payload.get('correlation_id')
    )
    if correlation_id:
        messages.append(f'Código de correlação: {correlation_id}')
    if messages:
        return '; '.join(messages)
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))


def _collect_error_messages(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        messages: list[str] = []
        for item in value:
            messages.extend(_collect_error_messages(item))
        return messages
    if not isinstance(value, dict):
        return []
    messages: list[str] = []
    for key in ('message', 'mensagem', 'title', 'detail', 'error_description'):
        if key in value:
            messages.extend(_collect_error_messages(value[key]))
    for key in (
        'errors',
        'erros',
        'violacoes',
        'violations',
        'mensagens',
        'details',
        'data',
    ):
        if key in value:
            messages.extend(_collect_error_details(value[key]))
    return messages


def _collect_error_details(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        messages: list[str] = []
        for item in value:
            messages.extend(_collect_error_details(item))
        return messages
    if isinstance(value, dict):
        messages: list[str] = []
        for item in value.values():
            messages.extend(_collect_error_details(item))
        return messages
    return []
