---
updatedAt: 2026-10-13T13:40:17.000Z
agentTools:
  projectIndex: https://docs.asaas.com/llms.txt
---

# Cobranças via Pix / QR Code dinâmico

A forma mais rápida de ter o dinheiro na conta.

# Crie cobranças via Pix

Crie cobranças com `billingType` igual a `PIX` e disponibilize o QR Code dinâmico para pagamento.

<Callout icon="??" theme="info">
  Ao concluir este guia, você saberá criar uma cobrança via Pix e recuperar o QR Code e o código copia e cola.
</Callout>

## 1. Crie a cobrança

Envie a cobrança com a forma de pagamento `PIX`.

```http
POST /v3/lean/payments
```

```json
{
  "customer": "cus_000005219613",
  "billingType": "PIX",
  "value": 100.90,
  "dueDate": "2023-07-21"
}
```

<Anchor target="_blank" href="https://docs.asaas.com/reference/criar-nova-cobranca-com-dados-resumidos-na-resposta">Consulte o endpoint: Criar nova cobrança com dados resumidos na resposta</Anchor>.

Recomendamos manter uma <Anchor target="_blank" href="https://docs.asaas.com/reference/criar-uma-chave">chave Pix cadastrada</Anchor> na conta.

## 2. Obtenha o QR Code

Após criar a cobrança, envie o ID retornado para recuperar os dados do QR Code.

```http
GET /v3/payments/{id}/pixQrCode
```

<Anchor target="_blank" href="https://docs.asaas.com/reference/obter-qr-code-para-pagamentos-via-pix">Consulte o endpoint: Obter QR Code para pagamentos via Pix</Anchor>.

A resposta disponibiliza:

| Campo            | Descrição                    |
| ---------------- | ---------------------------- |
| `encodedImage`   | Imagem do QR Code em Base64  |
| `payload`        | Código Pix copia e cola      |
| `expirationDate` | Data de expiração do QR Code |

<Callout icon="??" theme="info">
  O QR Code é dinâmico, possui vencimento e pode ser pago uma única vez.

  Ele expira 12 meses após a data de vencimento da cobrança e pode ser impresso ou incluído em documentos, como boletos e carnês.
</Callout>

<Callout icon="??" theme="warn">
  ### Cobranças sem chave Pix cadastrada

  Atualmente, é possível gerar um QR Code Pix dinâmico de pagamento imediato sem uma chave Pix cadastrada no Asaas. Nesse caso, o QR Code é vinculado a uma instituição parceira e pode ser pago até 23:59 do mesmo dia.

  Se a cobrança for atualizada, obtenha um novo QR Code.

  Essa funcionalidade será descontinuada futuramente, com comunicação 30 dias antes. Por isso, recomendamos <Anchor target="_blank" href="https://docs.asaas.com/reference/criar-uma-chave">cadastrar uma chave Pix</Anchor>.
</Callout>

## Próximos passos

* <Anchor target="_blank" href="https://docs.asaas.com/reference/criar-uma-chave">Cadastre uma chave Pix</Anchor>
* <Anchor target="_blank" href="https://docs.asaas.com/reference/obter-qr-code-para-pagamentos-via-pix">Consulte os dados do QR Code Pix</Anchor>

# Sibling pages

* [Introdução - Pix](https://docs.asaas.com/docs/pix.md)
* [Criando um QR Code estático](https://docs.asaas.com/docs/o-que-e-qr-code-estatico.md)
* [Pix Recorrente](https://docs.asaas.com/docs/pix-recorrente.md)
* [Diferença entre Pix Recorrente e Pix Automático](https://docs.asaas.com/docs/diferença-entre-pix-recorrente-e-pix-automático.md)
* [Consultar Chave Pix](https://docs.asaas.com/docs/consultar-chave-pix.md)