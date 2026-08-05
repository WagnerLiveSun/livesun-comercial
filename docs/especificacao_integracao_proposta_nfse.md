# ESPECIFICAÇÃO TÉCNICA: Integração de Propostas Comerciais com Emissão de NFS-e

## 1. REGRA DE NEGÓCIO PRINCIPAL

**Objetivo:** Permitir a conversão de propostas comerciais aprovadas (Orçamentos) em documentos fiscais eletrônicos, separando automaticamente itens de produto (NF-e - futuro) e itens de serviço (NFS-e - atual).

**Regra Principal:**
- Uma proposta comercial aprovada pode ser convertida em um ou mais documentos fiscais
- Itens do tipo Produto (tipo_item = 'P') devem ser direcionados para NF-e (usar DocumentoVenda como pré-venda enquanto NF-e não implementada)
- Itens do tipo Serviço (tipo_item = 'S') devem ser direcionados para NFS-e
- O sistema deve validar os dados obrigatórios antes da conversão
- Cada tipo de documento deve usar seus respectivos cadastros e validações fiscais
- A conversão deve ser atômica: ou todos os documentos são gerados, ou nenhum

## 2. FLUXO DETALHADO DO PROCESSO

### 2.1 Fluxo Principal

```
1. Usuário acessa proposta aprovada
   ↓
2. Sistema verifica se proposta pode ser convertida
   ↓
3. Usuário clica em "Converter em Documentos Fiscais"
   ↓
4. Sistema separa itens por natureza (Produto/Serviço)
   ↓
5. Sistema valida dados obrigatórios para cada tipo
   ↓
6. Sistema exibe prévia dos documentos a serem gerados
   ↓
7. Usuário confirma conversão
   ↓
8. Sistema gera documentos:
   - DocumentoVenda para itens de produto
   - NfseNacionalEmissao para itens de serviço
   ↓
9. Sistema atualiza status da proposta para 'convertido'
   ↓
10. Sistema registra referências cruzadas
   ↓
11. Sistema exibe resultado da conversão
```

### 2.2 Detalhamento das Etapas

**Etapa 1: Acesso à Proposta**
- Usuário acessa detalhes do orçamento aprovado
- Botão "Converter em Documentos Fiscais" aparece apenas se status = 'aprovado'

**Etapa 2: Verificação de Pré-condições**
- Proposta deve ter status 'aprovado'
- Proposta não pode ter sido convertida anteriormente
- Proposta deve ter pelo menos um item

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

**Etapa 6: Confirmação**
- Usuário confirma a conversão
- Sistema inicia transação de banco

**Etapa 7: Geração de Documentos**
- Criar DocumentoVenda para itens de produto
- Criar NfseNacionalEmissao para itens de serviço
- Criar itens de cada documento
- Registrar origem (orcamento_id)

**Etapa 8: Atualização de Status**
- Atualizar status do orçamento para 'convertido'
- Registrar data de conversão
- Criar referências cruzadas

**Etapa 9: Exibição de Resultado**
- Mostrar documentos gerados com links
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

### 4.1 Bloqueios de Conversão

**Cenário 1: Proposta não aprovada**
- Condição: status ≠ 'aprovado'
- Ação: Bloquear conversão, exibir mensagem "Apenas propostas aprovadas podem ser convertidas"
- Solução: Usuário deve aprovar a proposta primeiro

**Cenário 2: Proposta já convertida**
- Condição: status = 'convertido'
- Ação: Bloquear conversão, exibir mensagem "Esta proposta já foi convertida em documentos"
- Solução: Usuário deve acessar os documentos gerados

**Cenário 3: Proposta sem itens**
- Condição: itens = []
- Ação: Bloquear conversão, exibir mensagem "A proposta não possui itens para conversão"
- Solução: Usuário deve adicionar itens à proposta

**Cenário 4: Cliente sem cadastro completo**
- Condição: Campos obrigatórios faltando
- Ação: Bloquear conversão, exibir lista de campos faltantes
- Solução: Usuário deve completar cadastro do cliente

**Cenário 5: Serviço sem dados fiscais**
- Condição: Serviço sem cTribNac ou NBS
- Ação: Bloquear conversão, exibir mensagem "Serviço X não possui dados fiscais configurados"
- Solução: Usuário deve configurar dados fiscais do serviço

**Cenário 6: Empresa sem configuração NFS-e**
- Condição: Configuração NFS-e não ativa ou certificado inválido
- Ação: Bloquear conversão, exibir mensagem "Empresa não possui configuração NFS-e válida"
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

**Novos Campos em Orcamento:**
- `documento_nfse_id`: Referência à NFS-e gerada (opcional)
- `documento_nfe_id`: Referência à NF-e gerada (opcional, futuro)
- `documento_venda_id`: Referência ao documento não fiscal gerado (opcional)
- `data_conversao`: Data da conversão em documentos (opcional)

**Novos Campos em OrcamentoItem:**
- `documento_item_id`: Referência ao item do documento gerado (opcional)
- `tipo_documento`: Tipo de documento gerado ('VENDA', 'NFSE', 'NFE')

**Modificação em DocumentoVenda:**
- `orcamento_id`: Referência ao orçamento de origem (opcional)
- `origem_tipo`: Tipo de origem ('ORCAMENTO', 'MANUAL')

**Modificação em NfseNacionalEmissao:**
- `orcamento_id`: Referência ao orçamento de origem (opcional)
- `origem_tipo`: Tipo de origem ('ORCAMENTO', 'MANUAL')

### 5.2 Novas Rotas

```
GET  /comercial/orcamentos/<int:orcamento_id>/converter
     - Exibe tela de prévia de conversão

POST /comercial/orcamentos/<int:orcamento_id>/converter
     - Processa a conversão em documentos
```

### 5.3 Novos Templates

```
comercial/orcamentos_converter.html
     - Tela de prévia de conversão
     - Exibe separação de itens por tipo
     - Lista validações pendentes
     - Formulário de confirmação
```

### 5.4 Novas Funções de Serviço

```python
def separar_itens_por_natureza(orcamento: Orcamento) -> dict:
    """Separa itens do orçamento por natureza fiscal"""
    return {
        'produtos': [item for item in orcamento.itens if item.tipo_item == 'P'],
        'servicos': [item for item in orcamento.itens if item.tipo_item == 'S']
    }

def validar_conversao_orcamento(orcamento: Orcamento) -> tuple[bool, list[str]]:
    """Valida se orçamento pode ser convertido em documentos"""
    erros = []
    # Implementar validações
    return (len(erros) == 0, erros)

def converter_orcamento_em_documentos(orcamento: Orcamento) -> dict:
    """Converte orçamento em documentos fiscais"""
    # Implementar lógica de conversão
    pass
```

### 5.5 Integração com NFS-e Existente

A conversão deve reutilizar a infraestrutura existente de NFS-e:

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
    valido, erros = validar_conversao_orcamento(orcamento)
    if not valido:
        raise ValueError("; ".join(erros))
    
    # Separar itens
    itens_por_natureza = separar_itens_por_natureza(orcamento)
    
    # Gerar documentos
    documentos_gerados = []
    
    if itens_por_natureza['produtos']:
        doc_venda = gerar_documento_venda(orcamento, itens_por_natureza['produtos'])
        documentos_gerados.append(('VENDA', doc_venda))
    
    if itens_por_natureza['servicos']:
        doc_nfse = gerar_nfse(orcamento, itens_por_natureza['servicos'])
        documentos_gerados.append(('NFSE', doc_nfse))
    
    # Atualizar orçamento
    orcamento.status = 'convertido'
    orcamento.data_conversao = date.today()
    
    # Commit
    db.session.commit()
    
except Exception as exc:
    db.session.rollback()
    raise exc
```

## 6. CONSIDERAÇÕES DE IMPLEMENTAÇÃO

### 6.1 Fase 1: Documento Não Fiscal (Itens de Produto)
- Reutilizar modelo `DocumentoVenda` existente
- Implementar separação de itens
- Implementar validações básicas
- Implementar geração de documento não fiscal

### 6.2 Fase 2: NFS-e (Itens de Serviço)
- Integrar com módulo NFS-e existente
- Implementar validações fiscais específicas
- Implementar geração de NFS-e
- Implementar tratamento de erros de envio

### 6.3 Fase 3: NF-e (Futuro)
- Implementar módulo NF-e
- Substituir DocumentoVenda por NF-e para itens de produto
- Manter compatibilidade com processo existente

### 6.4 Testes Necessários
- Teste de conversão apenas com produtos
- Teste de conversão apenas com serviços
- Teste de conversão mista (produtos + serviços)
- Teste de validações bloqueantes
- Teste de rollback em caso de erro
- Teste de conversão duplicada (bloqueio)

## 7. REFERÊNCIAS

**Modelos Existentes:**
- `Orcamento`: Modelo de proposta comercial
- `OrcamentoItem`: Itens do orçamento (tipo_item: 'P' ou 'S')
- `DocumentoVenda`: Documento não fiscal de venda
- `DocumentoVendaItem`: Itens de documento não fiscal
- `NfseNacionalEmissao`: Emissão de NFS-e Nacional
- `Entidade`: Cadastro de clientes/fornecedores
- `Produto`: Cadastro de produtos
- `Servico`: Cadastro de serviços

**Rotas Existentes:**
- `/comercial/orcamentos/<id>`: Detalhes do orçamento
- `/comercial/orcamentos/<id>/aprovar`: Aprovar orçamento
- `/comercial/documentos`: Lista de documentos não fiscais
- `/nfse-nacional/`: Módulo de NFS-e Nacional

**Validações NFS-e Existentes:**
- `_validar_emissao_nfse()`: Validações fiscais para NFS-e
- `_determinar_local_incidencia_issqn()`: Determinação de local de incidência
- `_campos_obrigatorios_tomador_nfse()`: Validação de campos do tomador
