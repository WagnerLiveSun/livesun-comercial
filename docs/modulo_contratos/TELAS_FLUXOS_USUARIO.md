# Telas e Fluxos de Usuário - Módulo de Gestão de Contratos

## 1. Tela de Cadastro de Cláusulas Padrão

### Objetivo
Permitir que administradores gerenciem a biblioteca de cláusulas padrão.

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  GESTÃO DE CONTRATOS > CLÁUSULAS PADRÃO                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Nova Cláusula]  [Importar]  [Exportar]                        │
│                                                                 │
│  Filtros:                                                       │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Tipo: [Todos ▼] │ │ Categoria: [▼]  │ │ Buscar: [______] │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Código │ Título            │ Tipo        │ Editável │ Ações│   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ OBJ    │ Objeto            │ Obrigatória │ ✓       │ [✏][🗑]│   │
│  │ EXEC   │ Execução Remota   │ Obrigatória │ ✓       │ [✏][🗑]│   │
│  │ SIGILO │ Sigilo e Confid.  │ Obrigatória │ ✓       │ [✏][🗑]│   │
│  │ HONOR  │ Honorários        │ Obrigatória │ ✓       │ [✏][🗑]│   │
│  │ VIGENC │ Vigência          │ Obrigatória │ ✓       │ [✏][🗑]│   │
│  │ RESP   │ Responsabilidades  │ Opcional   │ ✓       │ [✏][🗑]│   │
│  │ VINCULO │ Vínculo Trabalhista│ Obrigatória│ ✗      │ [✏][🗑]│   │
│  │ FORO   │ Foro              │ Opcional   │ ✓       │ [✏][🗑]│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Página 1 de 1 | Mostrando 8 de 8 registros                     │
└─────────────────────────────────────────────────────────────────┘
```

### Formulário de Nova/Edição de Cláusula

```
┌─────────────────────────────────────────────────────────────────┐
│  NOVA CLÁUSULA PADRÃO                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Código:                    [OBJ____________]                   │
│  Título:                    [Objeto_________________________]  │
│                                                                 │
│  Tipo:                      ○ Obrigatória                       │
│                             ● Opcional                          │
│                             ○ Condicional                       │
│                                                                 │
│  Editável:                   [✓] Permite edição no contrato     │
│                                                                 │
│  Categoria:                 [Geral ▼]                           │
│  Tipo de Contrato:          [Prestação de Serviços ▼]           │
│                                                                 │
│  Ordem Padrão:              [1___]                              │
│                                                                 │
│  Descrição:                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Define o objeto do contrato de prestação de serviços.    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Texto Base (Editor Rich Text):                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [B] [I] [U] [H1] [H2] [List] [Link]                     │   │
│  │                                                         │   │
│  │ CLÁUSULA PRIMEIRA - DO OBJETO                            │   │
│  │                                                         │   │
│  │ 1.1. O presente contrato tem como objeto a prestação   │   │
│  │ de serviços de {CONTRATO_DESCRICAO_SERVICOS} pela      │   │
│  │ CONTRATADA em favor da CONTRATANTE.                      │   │
│  │                                                         │   │
│  │ 1.2. Os serviços serão executados de forma remota,      │   │
│  │ utilizando meios eletrônicos e digitais.                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Placeholders disponíveis:                                       │
│  {CONTRATO_DESCRICAO_SERVICOS} {CONTRATADA_RAZAO_SOCIAL} ...   │
│                                                                 │
│  [Cancelar]  [Salvar]                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Permissões
- **Administrador:** Criar, editar, excluir cláusulas
- **Gerente:** Criar, editar cláusulas da própria empresa
- **Vendedor/Operacional:** Apenas visualizar

---

## 2. Tela de Orçamentos - Botão Gerar Contrato

### Localização
No módulo de orçamentos, quando o status é "Aprovado".

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ORÇAMENTO #2026-0001                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Status: [APROVADO]                                             │
│                                                                 │
│  Cliente: Cliente Exemplo Ltda                                  │
│  Valor Total: R$ 50.400,00                                      │
│  Data Aprovação: 15/01/2026                                     │
│                                                                 │
│  [Voltar]  [Editar]  [Imprimir]  [GERAR CONTRATO]  [Cancelar]   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Fluxo ao clicar em "Gerar Contrato"

1. **Modal de Confirmação:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Gerar Contrato a partir do Orçamento #2026-0001?              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  O sistema irá:                                                 │
│  ✓ Criar um novo contrato vinculado a este orçamento            │
│  ✓ Carregar dados do cliente e da empresa                       │
│  ✓ Gerar cláusulas automáticas baseadas no tipo de serviço      │
│  ✓ O contrato nascerá com status "Rascunho"                     │
│                                                                 │
│  Contratada: LiveSun Tecnologia Ltda                            │
│  Contratante: Cliente Exemplo Ltda                               │
│                                                                 │
│  [Cancelar]  [Confirmar]                                        │
└─────────────────────────────────────────────────────────────────┘
```

2. **Após confirmação:** Redireciona para tela de edição do contrato

---

## 3. Tela de Edição de Contrato (Minuta)

### Objetivo
Permitir edição completa da minuta do contrato antes da emissão.

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  CONTRATO #CTR-2026-0001 - RASCUNHO                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Salvar]  [Prévia HTML]  [Exportar PDF]  [Exportar DOCX]     │
│  [Enviar para Assinatura]  [Cancelar]                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DADOS DO CONTRATO                                         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Número: CTR-2026-0001  | Orçamento: #2026-0001            │   │
│  │ Status: Rascunho        | Data Geração: 15/01/2026        │   │
│  │                                                         │   │
│  │ Contratada: LiveSun Tecnologia Ltda                       │   │
│  │ Contratante: Cliente Exemplo Ltda                         │   │
│  │                                                         │   │
│  │ Valor Total: [R$ 50.400,00____]  | Valor Mensal: [R$ 4.200,00__] │   │
│  │ Forma Pagamento: [Boleto bancário, vencimento dia 5______] │   │
│  │ Periodicidade: [Mensal ▼]                                 │   │
│  │ Início Vigência: [01/01/2026] | Fim Vigência: [31/12/2026]│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DESCRIÇÃO DOS SERVIÇOS                                   │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Serviços remotos de apoio à escrituração contábil,      │   │
│  │ conciliações bancárias, suporte à geração de SPED ECD/  │   │
│  │ EFD e demais obrigações acessórias.                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│  [Atualizar Orçamento]  [Apenas Contrato]                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ CLÁUSULAS DO CONTRATO                                     │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ [Adicionar Cláusula da Biblioteca]  [Reordenar]           │   │
│  │                                                         │   │
│  │ ┌───────────────────────────────────────────────────┐  │   │
│  │ │ 1. OBJETO [✏] [↑] [↓] [🗑]                        │  │   │
│  │ ├───────────────────────────────────────────────────┤  │   │
│  │ │ CLÁUSULA PRIMEIRA - DO OBJETO                     │  │   │
│  │ │                                                     │  │   │
│  │ │ 1.1. O presente contrato tem como objeto a          │  │   │
│  │ │ prestação de serviços de Serviços remotos de       │  │   │
│  │ │ apoio à escrituração contábil... pela LiveSun       │  │   │
│  │ │ Tecnologia Ltda em favor do Cliente Exemplo Ltda.   │  │   │
│  │ │                                                     │  │   │
│  │ │ 1.2. Os serviços serão executados de forma remota... │  │   │
│  │ └───────────────────────────────────────────────────┘  │   │
│  │                                                         │   │
│  │ ┌───────────────────────────────────────────────────┐  │   │
│  │ │ 2. EXECUÇÃO REMOTA [✏] [↑] [↓] [🗑]               │  │   │
│  │ ├───────────────────────────────────────────────────┤  │   │
│  │ │ CLÁUSULA SEGUNDA - DA EXECUÇÃO REMOTA             │  │   │
│  │ │                                                     │  │   │
│  │ │ 2.1. A prestação dos serviços será realizada...     │  │   │
│  │ └───────────────────────────────────────────────────┘  │   │
│  │                                                         │   │
│  │ ┌───────────────────────────────────────────────────┐  │   │
│  │ │ 3. SIGILO E CONFIDENCIALIDADE [✏] [↑] [↓] [🗑]    │  │   │
│  │ ├───────────────────────────────────────────────────┤  │   │
│  │ │ CLÁUSULA TERCEIRA - DO SIGILO E CONFIDENCIALIDADE │  │   │
│  │ │                                                     │  │   │
│  │ │ 3.1. A CONTRATADA compromete-se a manter...       │  │   │
│  │ └───────────────────────────────────────────────────┘  │   │
│  │                                                         │   │
│  │ ... (mais cláusulas)                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ HISTÓRICO DE ALTERAÇÕES                                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ 15/01/2026 14:30 - João Silva - Contrato criado         │   │
│  │ 15/01/2026 15:45 - João Silva - Cláusula 3 editada      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Edição de Cláusula (Modal)

```
┌─────────────────────────────────────────────────────────────────┐
│  Editar Cláusula: OBJETO                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Título: [Objeto____________________________]                   │
│                                                                 │
│  Texto (Editor Rich Text):                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [B] [I] [U] [H1] [H2] [List] [Link]                     │   │
│  │                                                         │   │
│  │ CLÁUSULA PRIMEIRA - DO OBJETO                            │   │
│  │                                                         │   │
│  │ 1.1. O presente contrato tem como objeto a prestação   │   │
│  │ de serviços de {CONTRATO_DESCRICAO_SERVICOS} pela      │   │
│  │ CONTRATADA em favor da CONTRATANTE.                      │   │
│  │                                                         │   │
│  │ 1.2. Os serviços serão executados de forma remota,      [EDITADO]
│  │ utilizando meios eletrônicos e digitais, conforme       │   │
│  │ especificações técnicas acordadas entre as partes.       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Placeholders: {CONTRATO_DESCRICAO_SERVICOS} {CONTRATADA} ...   │
│                                                                 │
│  [Cancelar]  [Salvar Alterações]                               │
└─────────────────────────────────────────────────────────────────┘
```

### Reordenação de Cláusulas (Drag & Drop)

```
┌─────────────────────────────────────────────────────────────────┐
│  Reordenar Cláusulas                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Arraste as cláusulas para reordenar:                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ☰ 1. OBJETO                                             │   │
│  │ ☰ 2. EXECUÇÃO REMOTA                                    │   │
│  │ ☰ 3. SIGILO E CONFIDENCIALIDADE                         │   │
│  │ ☰ 4. HONORÁRIOS                                         │   │
│  │ ☰ 5. VIGÊNCIA                                           │   │
│  │ ☰ 6. RESPONSABILIDADES                                  │   │
│  │ ☰ 7. VÍNCULO TRABALHISTA                                │   │
│  │ ☰ 8. FORO                                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Cancelar]  [Salvar Nova Ordem]                               │
└─────────────────────────────────────────────────────────────────┘
```

### Adicionar Cláusula da Biblioteca

```
┌─────────────────────────────────────────────────────────────────┐
│  Adicionar Cláusula da Biblioteca                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Buscar: [_________________]                                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Título              │ Tipo        │ Categoria │ [Adicionar]│   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Responsabilidades   │ Opcional   │ Técnico   │ [Adicionar]│   │
│  │ Garantia            │ Opcional   │ Jurídico  │ [Adicionar]│   │
│  │ Penalidades         │ Opcional   │ Financeiro│ [Adicionar]│   │
│  │ Multa Rescisória     │ Opcional   │ Financeiro│ [Adicionar]│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Fechar]                                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Tela de Prévia do Contrato (HTML)

### Objetivo
Visualização do contrato final formatado.

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  PRÉVIA DO CONTRATO #CTR-2026-0001                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Voltar à Edição]  [Imprimir]  [Exportar PDF]  [Exportar DOCX]│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │              CONTRATO DE PRESTAÇÃO DE SERVIÇOS           │   │
│  │                                                         │   │
│  │              Número: CTR-2026-0001                      │   │
│  │                                                         │   │
│  │                                                         │   │
│  │              QUALIFICAÇÃO DAS PARTES                    │   │
│  │                                                         │   │
│  │  CONTRATADA: LiveSun Tecnologia Ltda, CNPJ             │   │
│  │  12.345.678/0001-90, estabelecida em Rua Example,     │   │
│  │  123, São Paulo - SP.                                   │   │
│  │                                                         │   │
│  │  CONTRATANTE: Cliente Exemplo Ltda, CNPJ               │   │
│  │  98.765.432/0001-10, estabelecido em Av. Example,     │   │
│  │  456, Rio de Janeiro - RJ.                               │   │
│  │                                                         │   │
│  │                                                         │   │
│  │              CLÁUSULA PRIMEIRA - DO OBJETO              │   │
│  │                                                         │   │
│  │  1.1. O presente contrato tem como objeto a prestação   │   │
│  │  de serviços de Serviços remotos de apoio à            │   │
│  │  escrituração contábil, conciliações bancárias...        │   │
│  │                                                         │   │
│  │  1.2. Os serviços serão executados de forma remota...   │   │
│  │                                                         │   │
│  │                                                         │   │
│  │              CLÁUSULA SEGUNDA - DA EXECUÇÃO REMOTA      │   │
│  │                                                         │   │
│  │  2.1. A prestação dos serviços será realizada...        │   │
│  │                                                         │   │
│  │                                                         │   │
│  │              ... (demais cláusulas)                     │   │
│  │                                                         │   │
│  │                                                         │   │
│  │              ASSINATURAS                                │   │
│  │                                                         │   │
│  │  ___________________              ___________________     │   │
│  │  CONTRATADA                      CONTRATANTE            │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Tela de Gestão de Contratos

### Objetivo
Listagem e consulta de contratos.

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  GESTÃO DE CONTRATOS                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Novo Contrato]  [Importar]  [Exportar]                        │
│                                                                 │
│  Filtros:                                                       │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Status: [Todos ▼] │ │ Cliente: [▼]    │ │ Período: [▼]    │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Buscar: [____________________________________________] │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Número │ Cliente │ Status │ Vigência │ Valor │ Ações    │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ CTR-2026-0001 │ Cliente Exemplo │ Rascunho │ 01/01-31/12 │   │
│  │               │ R$ 50.400,00 │ [✏][👁][📄][🗑]            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ CTR-2026-0002 │ Outro Cliente   │ Assinado │ 01/02-31/01 │   │
│  │               │ R$ 12.000,00 │ [✏][👁][📄][🗑]            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Página 1 de 1 | Mostrando 2 de 2 registros                     │
└─────────────────────────────────────────────────────────────────┘
```

### Detalhes do Contrato (Modal)

```
┌─────────────────────────────────────────────────────────────────┐
│  Detalhes do Contrato #CTR-2026-0001                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DADOS GERAIS                                             │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Número: CTR-2026-0001                                    │   │
│  │ Orçamento: #2026-0001                                    │   │
│  │ Status: Rascunho                                         │   │
│  │ Data Geração: 15/01/2026 14:30                           │   │
│  │ Gerado por: João Silva                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ PARTES                                                   │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Contratada: LiveSun Tecnologia Ltda                      │   │
│  │ Contratante: Cliente Exemplo Ltda                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DADOS COMERCIAIS                                         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Valor Total: R$ 50.400,00                               │   │
│  │ Valor Mensal: R$ 4.200,00                                │   │
│  │ Forma Pagamento: Boleto bancário, vencimento dia 5       │   │
│  │ Periodicidade: Mensal                                    │   │
│  │ Vigência: 01/01/2026 a 31/12/2026                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ CLÁUSULAS (8)                                            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ 1. Objeto                                                │   │
│  │ 2. Execução Remota                                       │   │
│  │ 3. Sigilo e Confidencialidade                            │   │
│  │ 4. Honorários                                            │   │
│  │ 5. Vigência                                              │   │
│  │ 6. Responsabilidades                                     │   │
│  │ 7. Vínculo Trabalhista                                  │   │
│  │ 8. Foro                                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ANEXOS (0)                                              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Nenhum anexo                                             │   │
│  │ [Adicionar Anexo]                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Editar]  [Prévia]  [Exportar PDF]  [Enviar Assinatura]     │
│  [Cancelar]  [Histórico]                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Fluxo Principal: Geração de Contrato

```
┌─────────────┐
│ Orçamento   │
│ Aprovado    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Botão       │
│ "Gerar      │
│ Contrato"   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Modal de    │
│ Confirmação │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Criar       │
│ Contrato    │
│ (Rascunho)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Gerar       │
│ Cláusulas   │
│ Automáticas│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Gerar       │
│ Parâmetros  │
│ de Subst.   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Tela de     │
│ Edição da   │
│ Minuta      │
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ Editar      │   │ Adicionar   │
│ Cláusulas   │   │ Cláusulas   │
│             │   │ da Bibliot. │
└──────┬──────┘   └──────┬──────┘
       │                 │
       └────────┬────────┘
                │
                ▼
       ┌─────────────┐
       │ Reordenar   │
       │ Cláusulas   │
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │ Prévia HTML │
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │ Exportar    │
       │ PDF/DOCX    │
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │ Enviar para │
       │ Assinatura  │
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │ Status:     │
       │ Aguardando  │
       │ Assinatura  │
       └─────────────┘
```

---

## 7. Fluxo de Assinatura

```
┌─────────────┐
│ Contrato    │
│ Rascunho    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ "Enviar     │
│ para        │
│ Assinatura" │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Status:     │
│ Aguardando  │
│ Assinatura  │
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ Upload PDF  │   │ Assinatura  │
│ Assinado    │   │ Digital     │
└──────┬──────┘   └──────┬──────┘
       │                 │
       └────────┬────────┘
                │
                ▼
       ┌─────────────┐
       │ Status:     │
       │ Assinado    │
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │ Integrar    │
       │ com         │
       │ Faturamento │
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │ Gerar       │
       │ Cobranças   │
       │ Recorrentes │
       └─────────────┘
```

---

## 8. Integração com Módulos

### Integração com Faturamento

Quando contrato é assinado:
```
┌─────────────┐
│ Contrato    │
│ Assinado    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Criar       │
│ Assinatura  │
│ Empresa     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Criar       │
│ Cobrança    │
│ Recorrente  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Gerar       │
│ Boletos     │
│ Mensais     │
└─────────────┘
```

### Integração com Financeiro

```
┌─────────────┐
│ Cobrança    │
│ Gerada      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Criar       │
│ Lançamento  │
│ Financeiro  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Agendar     │
│ Vencimentos │
└─────────────┘
```

---

## 9. Boas Práticas de UX

### Editor Rich Text
- Usar biblioteca como Quill.js, TinyMCE ou CKEditor
- Suporte a formatação básica (negrito, itálico, sublinhado)
- Suporte a listas
- Suporte a links
- Preview em tempo real

### Drag & Drop
- Usar biblioteca como SortableJS para reordenação de cláusulas
- Feedback visual durante o arrastar
- Salvar automaticamente após reordenação

### Validações
- Não permitir edição de contratos assinados
- Não permitir remoção de cláusulas obrigatórias
- Validar campos obrigatórios antes de enviar para assinatura
- Alertar se houver placeholders não substituídos

### Feedback Visual
- Indicar cláusulas obrigatórias com ícone
- Indicar cláusulas não editáveis com ícone de cadeado
- Mostrar histórico de alterações em timeline
- Indicar status do contrato com cores (Rascunho=cinza, Assinado=verde, Cancelado=vermelho)

### Responsividade
- Layout adaptável para tablets e mobile
- Editor de texto responsivo
- Tabelas com scroll horizontal em telas pequenas
