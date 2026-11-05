---
updatedAt: 2026-10-13T13:05:52.000Z
agentTools:
  projectIndex: https://docs.asaas.com/llms.txt
---

# Como testar as chamadas aqui na documentação

A documentação interativa da Asaas permite testar chamadas da API diretamente por ela! Veja o passo a passo abaixo.

<Callout icon="??" theme="warn">
### Antes de testar

As requisições executadas nesta documentação são enviadas para o **Sandbox** (`https://api-sandbox.asaas.com/v3`).

Use uma chave de API criada no Sandbox. Uma chave de Produção não é válida nesse ambiente e resultará em `401 Unauthorized`.

[Crie sua conta Sandbox](https://sandbox.asaas.com/) e gere uma chave de API para testes.
</Callout>

Cada endpoint da API Reference possui um console interativo. Com ele, você preenche os parâmetros, envia a requisição para o Sandbox e visualiza a resposta da API sem sair da documentação.

## 1. Escolha o endpoint

No menu lateral, selecione o endpoint que deseja testar, por exemplo [Listar clientes](https://docs.asaas.com/reference/listar-clientes).

A página mostra o método, a URL, a descrição da operação e os parâmetros aceitos.

## 2. Informe sua chave de API

No painel à direita, em **Credentials**, preencha o campo `access_token` com a sua chave de API do Sandbox.

A chave fica disponível para as próximas requisições enquanto você navega pela documentação.

[Saiba como configurar a autenticação](https://docs.asaas.com/docs/autenticação-1)

## 3. Preencha os parâmetros

Informe os parâmetros da requisição nos campos da página:

* **Path Params**: identificadores que fazem parte da URL, como o `id` de um recurso;
* **Query Params**: filtros e paginação, como `offset` e `limit`;
* **Body Params**: dados enviados no corpo da requisição em endpoints de criação e atualização.

Campos obrigatórios são indicados como **required**.

## 4. Execute a requisição

Clique em **Try It!**.

O console envia a requisição para o Sandbox e exibe a resposta em **Response**, com o status HTTP e o JSON retornado.

Antes de executar, você também pode consultar os exemplos de resposta disponíveis no mesmo painel.

## 5. Gere o código da requisição

Em **Language**, selecione a linguagem desejada, como Shell, Node, Ruby, PHP ou Python.

O exemplo de código é atualizado com os parâmetros informados e pode ser copiado para a sua aplicação.

<Callout icon="??" theme="info">
### Requisições reais no Sandbox

As requisições executadas pelo console criam, alteram ou removem dados reais na sua conta Sandbox.

Use dados fictícios e evite informar dados pessoais de terceiros.
</Callout>

## Erros comuns

| Status             | Causa provável                                        | Como resolver                                     |
| :----------------- | :---------------------------------------------------- | :------------------------------------------------ |
| `401 Unauthorized` | Chave de API ausente, inválida ou de Produção         | Informe uma chave de API válida criada no Sandbox |
| `400 Bad Request`  | Parâmetro obrigatório ausente ou com formato inválido | Revise os campos indicados em `errors`            |
| `404 Not Found`    | Identificador inexistente na conta Sandbox            | Confirme se o `id` informado pertence à sua conta |

[Consulte os Códigos HTTP das respostas](https://docs.asaas.com/reference/codigos-http-das-respostas).

## Próximos passos

* [Conheça a API Reference](https://docs.asaas.com/reference/comece-por-aqui)
* [Prepare seu ambiente Sandbox](https://docs.asaas.com/docs/sandbox)
* [Configure a autenticação da API](https://docs.asaas.com/docs/autenticação-1)
* [Entenda a listagem e paginação](https://docs.asaas.com/reference/listagem-e-paginacao)

# Sibling pages

* [Comece por aqui](https://docs.asaas.com/reference/comece-por-aqui.md)
* [Códigos HTTP das respostas](https://docs.asaas.com/reference/codigos-http-das-respostas.md)
* [Listagem e paginação](https://docs.asaas.com/reference/listagem-e-paginacao.md)
* [Limites da API](https://docs.asaas.com/reference/rate-e-quota-limit.md)