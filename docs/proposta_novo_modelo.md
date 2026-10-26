# Proposta resumida — Novo Modelo

## Acesso

Na tela de detalhes da proposta ou na lista de propostas para aprovação, abrir
**PDF → Novo Modelo**. As opções **Completo** e **Resumido** continuam disponíveis
sem alterações nos respectivos geradores.

## Apresentação

O modelo utiliza a referência visual de `Proposta_LiveSun_Teka_Backup_Exec.pdf`:
logo à esquerda, identificação à direita, blocos de cliente e fornecedora,
tabela com cabeçalho vermelho `#B51F2B`, condições comerciais, termos e quadro
de aceite. O rodapé identifica empresa, proposta e página atual/total.

As colunas são adaptadas aos dados existentes: item/SKU, descrição, quantidade,
unitário, desconto e total. Não se presume vigência individual de licenças,
distribuidora ou entitlement, pois não são campos próprios dos itens atuais.
Essas informações podem ser descritas nos itens e nas informações técnicas.

## Origem das informações

| Conteúdo | Origem |
| --- | --- |
| Emitente / fornecedora | Empresa vinculada à proposta |
| Logo | `empresa.logo_caminho`, dentro do diretório de uploads configurado |
| Cliente e documento | Cliente vinculado à proposta |
| Responsável comercial | Vendedor vinculado à proposta |
| Itens | Descrição da proposta, com fallback para cadastro de produto/serviço |
| Total | `orcamento.valor_total`, sem reaplicar descontos |
| Objeto e escopo | Escopo do Projeto / `observacoes` |
| Informações técnicas | `detalhes_tecnicos` |
| Validade dos preços | `validade_precos`, ou data de validade quando vazio |
| Pagamento | `condicoes_pagamento` |
| Termos de fornecimento e contratação | `termos_compra` |
| Aceite | Número, emissão, total, empresa e cliente da proposta |

Os termos de compra mantêm as quebras de linha; títulos numerados recebem
destaque. Condições específicas de entrega, licenciamento, sigilo, despesas,
cancelamento ou renovação devem ser informadas na proposta. Nenhuma condição
comercial do PDF de referência é imposta automaticamente a outras propostas.
Observações internas não são exportadas.

Sem logo cadastrado, o documento usa a identificação textual da empresa e não
substitui o logo por uma marca fixa. PNG, JPEG, GIF, BMP e WEBP cadastrados são
normalizados temporariamente para inclusão no PDF.

## Aceite e aprovação

Cliente, CNPJ/CPF e identificação da negociação são preenchidos automaticamente.
Representante legal, cargo, assinatura e data da assinatura permanecem para
preenchimento, pois não possuem campos próprios no cadastro atual. O vendedor
não é tratado como representante legal do cliente. Uma data de aprovação já
registrada é exibida separadamente e não substitui a assinatura.

A exportação não aprova, altera ou converte a proposta. A rota exige login,
consulta restrita à empresa e a mesma permissão dos modelos atuais.

## Validação local

Na raiz do projeto, executar com o ambiente virtual existente:

```powershell
python -m pytest tests/test_proposta_novo_modelo.py -q
```

Os testes geram PDFs com dados fictícios, verificam conteúdo, paginação,
formatos de logo, total, aceite, menus e proteção da rota. A inspeção do
conteúdo usa `pypdf` quando disponível no ambiente de desenvolvimento;
essa biblioteca não é dependência de produção do gerador.

Não há migração de banco ou novas dependências de produção.