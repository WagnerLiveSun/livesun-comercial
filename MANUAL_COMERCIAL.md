# Manual do Modulo Comercial

## Visao geral
O modulo comercial do LiveSun Comercial organiza a operacao de cadastro, estoque, compra manual e documentos de venda nao fiscais, sempre respeitando o isolamento por empresa.

## O que existe hoje
- Filiais por empresa
- Cadastro de produtos e servicos
- Movimentacao simples de estoque
- Entrada manual de NF de compra, com itens e parcelamento
- Documento nao fiscal de venda, com itens de produto e servico
- Vinculo com lancamentos financeiros e fluxo de caixa

## Cadastros base
### Filiais
Cada filial pertence a uma empresa e pode ter codigo, nome, CNPJ e endereco.

### Produtos
Use para itens que controlam estoque. O cadastro permite codigo interno, descricao, NCM, unidade, codigo de barras, estoque atual e estoque minimo.

### Servicos
Use para itens sem controle de estoque. O cadastro permite codigo interno, descricao, NBS e informacoes fiscais de apoio.

## Estoque
Toda movimentacao de produto deve ser registrada como entrada, saida ou ajuste.
- Origem: manual, compra, venda ou ajuste
- Pode ser vinculada a filial
- Deve ser coerente com o produto e a empresa

## Compra manual de NF
A entrada manual de compra registra:
- numero do documento
- serie
- data de emissao
- data de entrada
- fornecedor
- valor total
- observacoes
- itens da nota

### Parcelamento
Quando a compra for parcelada, o sistema cria lancamentos separados e registra a vinculacao entre a compra e cada parcela.

## Documento nao fiscal de venda
O documento de venda registra:
- cliente
- filial opcional
- numero do documento
- datas de emissao, vencimento e pagamento
- itens de produto ou servico
- valor total

### Impressao
A tela de detalhe usa layout de impressao estilo DANFE para facilitar conferencia e apresentacao ao cliente.

## Boas praticas
- Sempre cadastre a empresa correta antes de operar
- Nunca reutilize produto ou servico de outra empresa
- Use estoque apenas para itens com controle habilitado
- Use lancamentos para manter rastreabilidade financeira

## Observacao
Este manual cobre apenas o que esta implementado no sistema atual. Recursos de PDV, orcamentos e tabelas de preco ficam fora deste escopo por enquanto.
