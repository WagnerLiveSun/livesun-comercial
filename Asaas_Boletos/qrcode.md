---
updatedAt: 2026-08-13T19:11:53.000Z
agentTools:
  projectIndex: https://docs.asaas.com/llms.txt
---

# Criando um QR Code estático

# Receba pagamentos com QR Code Pix estático

O QR Code Pix estático permite receber múltiplos pagamentos usando a mesma chave Pix. Ele só expira quando uma data de expiração é definida.

Esse formato pode ser utilizado em cenários em que o mesmo QR Code fica disponível para diferentes pagadores, como em um estabelecimento comercial.

<Callout icon="??" theme="info">
  Ao concluir este guia, você saberá criar um QR Code Pix estático, identificar os pagamentos recebidos e consultar as cobranças geradas a partir dele.
</Callout>

## 1. Crie o QR Code estático

Tenha em mãos a chave Pix que receberá os pagamentos e envie a requisição:

```http
POST /v3/pix/qrCodes/static
```

```json
{
  "addressKey": "b6295ee1-f054-47d1-9e90-ee57b74f60d9",
  "description": "Churrasco",
  "value": 50.00,
  "format": "ALL",
  "expirationDate": "2023-05-17 14:20:50",
  "expirationSeconds": null
}
```

<Anchor target="_blank" href="https://docs.asaas.com/reference/criar-qrcode-estatico">Consulte o endpoint: Criar QR Code estático</Anchor>.

A resposta disponibiliza o `id` do QR Code e o `payload` com os dados do QR Code em Base64.

Não é necessário criar previamente uma cobrança ou definir o cliente. Quando o pagamento for realizado, os dados do pagador serão importados e uma cobrança será criada automaticamente.

## 2. Identifique o pagamento

Acompanhe os eventos do <Anchor target="_blank" href="https://docs.asaas.com/docs/webhook-para-cobrancas">Webhook para cobranças</Anchor>.

Quando receber um evento de pagamento recebido, o campo `pixQrCodeId` identificará o QR Code estático utilizado.

## 3. Consulte as cobranças geradas

Utilize o `pixQrCodeId` para listar as cobranças criadas a partir do QR Code:

```http
GET /v3/payments?pixQrCodeId=9bea9bcd226b45c7980065f598be54d5
```

<Anchor target="_blank" href="https://docs.asaas.com/reference/listar-cobrancas">Consulte o endpoint: Listar cobranças</Anchor>.

## Próximos passos

* <Anchor target="_blank" href="https://docs.asaas.com/docs/webhook-para-cobrancas">Configure o Webhook para cobranças</Anchor>
* <Anchor target="_blank" href="https://docs.asaas.com/reference/listar-cobrancas">Consulte as cobranças geradas pelo QR Code</Anchor>

# Sibling pages

* [Introdução - Pix](https://docs.asaas.com/docs/pix.md)
* [Cobranças via Pix / QR Code dinâmico](https://docs.asaas.com/docs/cobrancas-via-pix.md)
* [Pix Recorrente](https://docs.asaas.com/docs/pix-recorrente.md)
* [Diferença entre Pix Recorrente e Pix Automático](https://docs.asaas.com/docs/diferença-entre-pix-recorrente-e-pix-automático.md)
* [Consultar Chave Pix](https://docs.asaas.com/docs/consultar-chave-pix.md)