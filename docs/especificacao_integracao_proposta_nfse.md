# ESPECIFICAÇÃO TÉCNICA: Integração de Propostas Comerciais com Emissão de NFS-e

## 1. REGRA DE NEGÓCIO PRINCIPAL

**Objetivo:** Permitir a conversão de propostas comerciais aprovadas (Orçamentos) em pedidos de venda, que posteriormente podem ser faturados em documentos fiscais eletrônicos, separando automaticamente itens de produto (NF-e - futuro) e itens de serviço (NFS-e - atual).

**Regra Principal:**
- Uma proposta comercial aprovada é convertida em um PedidoVenda (status 'aprovado')
- O PedidoVenda contém todos os itens da proposta (produtos e serviços mistos)
- No faturamento do pedido, o sistema separa os itens por natureza fiscal:
  - Itens do tipo Produto (tipo_item = 'P') → DocumentoVenda (pré-venda para NF-e futura)
  - Itens do tipo Serviço (tipo_item = 'S') → NfseNacionalEmissao (integração NFS-e)
- O sistema deve validar os dados obrigatórios antes do faturamento
- Cada tipo de documento deve usar seus respectivos cadastros e validações fiscais
- O faturamento deve ser atômico: ou todos os documentos são gerados, ou nenhum

## 2. FLUXO DETALHADO DO PROCESSO

### 2.1 Fluxo Principal

```
FLUXO 1: Conversão de Proposta em Pedido (JÁ EXISTE)
1. Usuário acessa proposta aprovada
   ↓
2. Sistema verifica se proposta pode ser convertida
   ↓
3. Usuário clica em "Gerar Pedido"
   ↓
4. Sistema cria PedidoVenda com todos os itens
   ↓
5. Sistema atualiza status da proposta para 'convertido'
   ↓
6. Sistema exibe detalhes do pedido gerado

FLUXO 2: Faturamento do Pedido (A IMPLEMENTAR)
1. Usuário acessa pedido aprovado
   ↓
2. Sistema verifica se pedido pode ser faturado
   ↓
3. Usuário clica em "Faturar"
   ↓
4. Sistema separa itens por natureza (Produto/Serviço)
   ↓
5. Sistema valida dados obrigatórios para cada tipo
   ↓
6. Sistema exibe prévia dos documentos a serem gerados
   ↓
7. Usuário seleciona conta bancária e fluxo financeiro
   ↓
8. Usuário confirma faturamento
   ↓
9. Sistema gera documentos:
   - DocumentoVenda para itens de produto
   - NfseNacionalEmissao para itens de serviço
   - Lancamento financeiro
   ↓
10. Sistema atualiza status do pedido para 'faturado'
   ↓
11. Sistema registra referências cruzadas
   ↓
12. Sistema exibe resultado do faturamento
```

### 2.2 Detalhamento das Etapas - Faturamento

**Etapa 1: Acesso ao Pedido**
- Usuário acessa detalhes do pedido de venda
- Botão "Faturar" aparece apenas se status in ['aprovado', 'em_producao', 'pronto']

**Etapa 2: Verificação de Pré-condições**
- Pedido deve ter status permitido para faturamento
- Pedido não pode estar faturado
- Pedido deve ter pelo menos um item

**Etapa 3: Separação de Itens**
- Agrupar itens por tipo_item:
  - Grupo Produtos: tipo_item = 'P'
  - Grupo Serviços: tipo_item = 'S'
- Calcular totais por grupo

**Etapa 4: Validação de Dados Obrigatórios**
- Para itens de produto (DocumentoVenda):
  - Cliente com cadastro completo
  - Produtos ativos com estoque disponível (opcional)
- Para itens de serviço (NFS-e):
  - Cliente com cadastro completo fiscal
  - Serviços com dados fiscais configurados
  - Empresa com configurações NFS-e válidas

**Etapa 5: Prévia dos Documentos**
- Exibir resumo dos documentos a serem gerados
- Listar itens de cada documento
- Mostrar totais parciais
- Alertar sobre validações pendentes

**Etapa 6: Seleção Financeira**
- Usuário seleciona conta bancária
- Usuário seleciona fluxo de conta
- Usuário informa data de vencimento

**Etapa 7: Confirmação**
- Usuário confirma o faturamento
- Sistema inicia transação de banco

**Etapa 8: Geração de Documentos**
- Criar Lancamento financeiro
- Se houver itens de produto: Criar DocumentoVenda
- Se houver itens de serviço: Criar NfseNacionalEmissao
- Criar itens de cada documento
- Registrar origem (pedido_id)

**Etapa 9: Atualização de Status**
- Atualizar status do pedido para 'faturado'
- Registrar data de faturamento
- Criar referências cruzadas

**Etapa 10: Exibição de Resultado**
- Mostrar documentos gerados com links
- Exibir lançamento financeiro gerado
- Exibir eventuais avisos
- Permitir acesso imediato aos documentos

## 3. VALIDAÇÕES NECESSÁRIAS

### 3.1 Validações para Documento Não Fiscal (Itens de Produto)

**Validações do Cliente:**
- Tipo = 'C' (Cliente)
- CNPJ/CPF preenchido e válido
- Nome preenchido
- Endereço completo (rua, número, bairro, cidade, UF, CEP)
- E-mail preenchido

**Validações dos Produtos:**
- Produto ativo
- Código interno preenchido
- Descrição preenchida
- Valor unitário > 0
- Quantidade > 0

**Validações da Empresa:**
- Empresa ativa
- Filial configurada (se aplicável)

### 3.2 Validações para NFS-e (Itens de Serviço)

**Validações do Cliente (Tomador):**
- Tipo = 'C' (Cliente)
- CNPJ/CPF preenchido e válido (11 ou 14 dígitos)
- Nome/Razão Social preenchido
- Endereço completo (rua, número, bairro, cidade, UF, CEP)
- E-mail preenchido
- Código IBGE do município configurado

**Validações dos Serviços:**
- Serviço ativo
- Código interno preenchido
- Descrição preenchida
- Código de serviço nacional (cTribNac) preenchido
- NBS (Nomenclatura Brasileira de Serviços) preenchido
- Natureza do serviço configurada
- Indicador de incidência configurado
- Valor unitário > 0
- Quantidade > 0

**Validações da Empresa (Prestador):**
- Empresa ativa
- Código IBGE do município configurado
- Inscrição municipal configurada (se exigida pelo município)
- Regime tributário configurado (op_simp_nac, reg_ap_trib_sn)
- Certificado digital válido e ativo
- Configuração NFS-e ativa

**Validações Fiscais Específicas:**
- Código de serviço nacional válido na tabela oficial
- NBS válido na tabela oficial
- Local de incidência do ISSQN determinado conforme regras SNNFSE
- Código de tributação municipal (cTribMun) quando incidência ≠ emitente
- Tributação ISSQN (tribISSQN) válido (1, 2, 3 ou 4)

## 4. CENÁRIOS DE ERRO E BLOQUEIO

### 4.1 Bloqueios de Faturamento

**Cenário 1: Pedido não pode ser faturado**
- Condição: status not in ['aprovado', 'em_producao', 'pronto']
- Ação: Bloquear faturamento, exibir mensagem "Pedido não pode ser faturado neste status"
- Solução: Usuário deve aguardar status adequado

**Cenário 2: Pedido já faturado**
- Condição: status = 'faturado'
- Ação: Bloquear faturamento, exibir mensagem "Este pedido já foi faturado"
- Solução: Usuário deve acessar os documentos gerados

**Cenário 3: Pedido sem itens**
- Condição: itens = []
- Ação: Bloquear faturamento, exibir mensagem "O pedido não possui itens para faturamento"
- Solução: Usuário deve adicionar itens ao pedido

**Cenário 4: Cliente sem cadastro completo**
- Condição: Campos obrigatórios faltando
- Ação: Bloquear conversão, exibir lista de campos faltantes
- Solução: Usuário deve completar cadastro do cliente

**Cenário 5: Serviço sem dados fiscais**
- Condição: Serviço sem cTribNac ou NBS
- Ação: Bloquear conversão, exibir mensagem "Serviço X não possui dados fiscais configurados"
- Solução: Usuário deve configurar dados fiscais do serviço

**Cenário 6: Empresa sem configuração NFS-e**
- Condição: Configuração NFS-e não ativa ou certificado inválido (apenas se houver serviços)
- Ação: Bloquear faturamento, exibir mensagem "Empresa não possui configuração NFS-e válida"
- Solução: Administrador deve configurar NFS-e

**Cenário 7: Erro na transação**
- Condição: Erro durante geração de documentos
- Ação: Rollback completo, exibir mensagem de erro
- Solução: Usuário deve corrigir o problema e tentar novamente

### 4.2 Avisos (Não Bloqueantes)

**Aviso 1: Estoque insuficiente**
- Condição: Produto com estoque < quantidade
- Ação: Permitir conversão com aviso
- Mensagem: "Produto X tem estoque insuficiente"

**Aviso 2: Certificado próximo ao vencimento**
- Condição: Certificado vence em < 30 dias
- Ação: Permitir conversão com aviso
- Mensagem: "Certificado digital vence em X dias"

## 5. DOCUMENTAÇÃO TÉCNICA

### 5.1 Estrutura de Dados

**Novos Campos em PedidoVenda:**
- `documento_nfse_id`: Referência à NFS-e gerada (opcional)
- `documento_nfe_id`: Referência à NF-e gerada (opcional, futuro)

**Novos Campos em PedidoVendaItem:**
- `documento_item_id`: Referência ao item do documento gerado (opcional)
- `tipo_documento`: Tipo de documento gerado ('VENDA', 'NFSE', 'NFE')

**Modificação em DocumentoVenda:**
- `pedido_id`: Referência ao pedido de venda de origem (opcional)
- `origem_tipo`: Tipo de origem ('PEDIDO', 'MANUAL')

**Modificação em NfseNacionalEmissao:**
- `pedido_id`: Referência ao pedido de venda de origem (opcional)
- `origem_tipo`: Tipo de origem ('PEDIDO', 'MANUAL')

### 5.2 Rotas Modificadas

```
POST /comercial/pedidos/<int:pedido_id>/faturar
     - ROTA EXISTENTE - Será modificada para:
     - Separar itens por natureza (Produto/Serviço)
     - Gerar DocumentoVenda para itens de produto
     - Gerar NfseNacionalEmissao para itens de serviço
     - Manter geração de Lancamento financeiro
```

### 5.3 Novos Templates

```
comercial/pedidos_faturar.html
     - Tela de faturamento com separação de itens
     - Exibe prévia dos documentos a serem gerados
     - Lista validações pendentes
     - Seleção de conta bancária e fluxo financeiro
     - Formulário de confirmação
```

### 5.4 Novas Funções de Serviço

```python
def separar_itens_por_natureza(pedido: PedidoVenda) -> dict:
    """Separa itens do pedido por natureza fiscal"""
    return {
        'produtos': [item for item in pedido.itens if item.tipo_item == 'P'],
        'servicos': [item for item in pedido.itens if item.tipo_item == 'S']
    }

def validar_faturamento_pedido(pedido: PedidoVenda) -> tuple[bool, list[str]]:
    """Valida se pedido pode ser faturado"""
    erros = []
    # Implementar validações
    return (len(erros) == 0, erros)

def faturar_pedido_com_separacao(pedido: PedidoVenda, dados_financeiros: dict) -> dict:
    """Fatura pedido separando itens por natureza fiscal"""
    # Implementar lógica de faturamento
    pass
```

### 5.5 Integração com NFS-e Existente

O faturamento deve reutilizar a infraestrutura existente de NFS-e:

- Usar `_validar_emissao_nfse()` para validações fiscais
- Usar `_build_payload()` para construção do payload
- Usar `transmitiremissao()` para envio à SEFAZ
- Usar tabelas de referência existentes (municípios, serviços nacionais, NBS)

### 5.6 Tratamento de Exceções

```python
try:
    # Iniciar transação
    db.session.begin_nested()
    
    # Validar
    valido, erros = validar_faturamento_pedido(pedido)
    if not valido:
        raise ValueError("; ".join(erros))
    
    # Separar itens
    itens_por_natureza = separar_itens_por_natureza(pedido)
    
    # Criar lançamento financeiro
    lancamento = criar_lancamento(pedido, dados_financeiros)
    
    # Gerar documentos
    documentos_gerados = []
    
    if itens_por_natureza['produtos']:
        doc_venda = gerar_documento_venda(pedido, itens_por_natureza['produtos'], lancamento)
        documentos_gerados.append(('VENDA', doc_venda))
    
    if itens_por_natureza['servicos']:
        doc_nfse = gerar_nfse(pedido, itens_por_natureza['servicos'], lancamento)
        documentos_gerados.append(('NFSE', doc_nfse))
    
    # Atualizar pedido
    pedido.status = 'faturado'
    pedido.data_faturamento = date.today()
    
    # Commit
    db.session.commit()
    
except Exception as exc:
    db.session.rollback()
    raise exc
```

## 6. CONSIDERAÇÕES DE IMPLEMENTAÇÃO

### 6.1 Fase 1: Modificação do Faturamento Existente
- Modificar rota `pedidos_faturar` para separar itens por natureza
- Implementar validações específicas para cada tipo de item
- Manter geração de lançamento financeiro existente
- Adicionar geração condicional de DocumentoVenda (produtos)
- Adicionar geração condicional de NfseNacionalEmissao (serviços)

### 6.2 Fase 2: Template de Faturamento
- Criar template `pedidos_faturar.html` para prévia de documentos
- Exibir separação de itens por tipo
- Listar validações pendentes
- Manter seleção de conta bancária e fluxo financeiro

### 6.3 Fase 3: NF-e (Futuro)
- Implementar módulo NF-e
- Substituir DocumentoVenda por NF-e para itens de produto
- Manter compatibilidade com processo existente

### 6.4 Testes Necessários
- Teste de faturamento apenas com produtos
- Teste de faturamento apenas com serviços
- Teste de faturamento misto (produtos + serviços)
- Teste de validações bloqueantes
- Teste de rollback em caso de erro
- Teste de faturamento duplicado (bloqueio)
- Teste de compatibilidade com faturamento existente (sem separação)

## 7. REFERÊNCIAS

**Modelos Existentes:**
- `Orcamento`: Modelo de proposta comercial
- `OrcamentoItem`: Itens do orçamento (tipo_item: 'P' ou 'S')
- `PedidoVenda`: Pedido de venda aprovado (JÁ EXISTE)
- `PedidoVendaItem`: Itens do pedido de venda (tipo_item: 'P' ou 'S')
- `DocumentoVenda`: Documento não fiscal de venda
- `DocumentoVendaItem`: Itens de documento não fiscal
- `NfseNacionalEmissao`: Emissão de NFS-e Nacional
- `Entidade`: Cadastro de clientes/fornecedores
- `Produto`: Cadastro de produtos
- `Servico`: Cadastro de serviços
- `Lancamento`: Lançamento financeiro

**Rotas Existentes:**
- `/comercial/orcamentos/<id>`: Detalhes do orçamento
- `/comercial/orcamentos/<id>/aprovar`: Aprovar orçamento
- `/comercial/pedidos/<id>/faturar`: Faturar pedido (EXISTENTE - será modificada)
- `/comercial/documentos`: Lista de documentos não fiscais
- `/nfse-nacional/`: Módulo de NFS-e Nacional

**Validações NFS-e Existentes:**
- `_validar_emissao_nfse()`: Validações fiscais para NFS-e
- `_determinar_local_incidencia_issqn()`: Determinação de local de incidência
- `_campos_obrigatorios_tomador_nfse()`: Validação de campos do tomador
