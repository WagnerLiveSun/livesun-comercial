from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


class AsaasApiError(RuntimeError):
    """Erro de comunicacao/negocio retornado pela API do Asaas."""


@dataclass
class AsaasClient:
    api_key: str
    base_url: str
    timeout_seconds: int = 15

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip('/')

    @property
    def _headers(self) -> dict[str, str]:
        return {
            'accept': 'application/json',
            'content-type': 'application/json',
            'access_token': self.api_key,
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f'{self.base_url}{path}'
        response = requests.request(
            method=method,
            url=url,
            headers=self._headers,
            timeout=self.timeout_seconds,
            **kwargs,
        )

        content_type = (response.headers.get('content-type') or '').lower()
        payload: dict[str, Any]
        if 'application/json' in content_type:
            payload = response.json() or {}
        else:
            payload = {'raw': response.text}

        if response.status_code >= 400:
            errors = payload.get('errors') if isinstance(payload, dict) else None
            if isinstance(errors, list) and errors:
                message = '; '.join(str(err.get('description') or err) for err in errors)
            else:
                message = str(payload)
            raise AsaasApiError(f'Asaas {response.status_code}: {message}')

        return payload

    def find_customer_by_external_reference(self, external_reference: str) -> dict[str, Any] | None:
        payload = self._request('GET', '/customers', params={'externalReference': external_reference, 'limit': 1})
        data = payload.get('data') if isinstance(payload, dict) else None
        if isinstance(data, list) and data:
            return data[0]
        return None

    def create_customer(
        self,
        *,
        name: str,
        cpf_cnpj: str | None,
        email: str | None,
        external_reference: str,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            'name': name,
            'externalReference': external_reference,
        }
        if cpf_cnpj:
            body['cpfCnpj'] = cpf_cnpj
        if email:
            body['email'] = email
        return self._request('POST', '/customers', json=body)

    def find_subscription_by_external_reference(self, external_reference: str) -> dict[str, Any] | None:
        payload = self._request('GET', '/subscriptions', params={'externalReference': external_reference, 'limit': 20})
        data = payload.get('data') if isinstance(payload, dict) else None
        if not isinstance(data, list):
            return None

        for item in data:
            status = str(item.get('status') or '').upper()
            if status not in {'INACTIVE', 'CANCELED'}:
                return item
        return data[0] if data else None

    def create_subscription(
        self,
        *,
        customer_id: str,
        billing_type: str,
        value: float,
        next_due_date: str,
        cycle: str,
        external_reference: str,
        description: str,
    ) -> dict[str, Any]:
        body = {
            'customer': customer_id,
            'billingType': billing_type,
            'value': value,
            'nextDueDate': next_due_date,
            'cycle': cycle,
            'externalReference': external_reference,
            'description': description,
        }
        return self._request('POST', '/subscriptions', json=body)

    def list_subscription_payments(self, subscription_id: str, limit: int = 20) -> list[dict[str, Any]]:
        payload = self._request('GET', '/payments', params={'subscription': subscription_id, 'limit': limit})
        data = payload.get('data') if isinstance(payload, dict) else None
        return data if isinstance(data, list) else []

    def get_payment(self, payment_id: str) -> dict[str, Any] | None:
        payment_id = (payment_id or '').strip()
        if not payment_id:
            return None
        payload = self._request('GET', f'/payments/{payment_id}')
        return payload if isinstance(payload, dict) else None

    def cancel_payment(self, payment_id: str) -> dict[str, Any]:
        payment_id = (payment_id or '').strip()
        if not payment_id:
            raise AsaasApiError('O Asaas não retornou o identificador da cobrança.')
        payload = self._request('DELETE', f'/payments/{payment_id}')
        return payload if isinstance(payload, dict) else {}

    def create_boleto_payment(
        self,
        *,
        customer_id: str,
        value: float,
        due_date: str,
        external_reference: str,
        description: str,
        interest_percent: float | None = None,
        fine_percent: float | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            'customer': customer_id,
            'billingType': 'BOLETO',
            'value': value,
            'dueDate': due_date,
            'externalReference': external_reference,
            'description': description,
        }
        if interest_percent is not None:
            body['interest'] = {'value': interest_percent}
        if fine_percent is not None:
            body['fine'] = {'value': fine_percent}
        return self._request(
            'POST',
            '/payments',
            json=body,
        )

    def get_identification_field(self, payment_id: str) -> str | None:
        payment_id = (payment_id or '').strip()
        if not payment_id:
            return None
        payload = self._request('GET', f'/payments/{payment_id}/identificationField')
        value = payload.get('identificationField') if isinstance(payload, dict) else None
        return str(value).strip() if value else None
