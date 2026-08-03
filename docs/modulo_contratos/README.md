# Módulo de Gestão de Contratos - Documentação Completa

## Visão Geral

Este módulo permite a geração automática de contratos de prestação de serviços a partir de orçamentos aprovados, com biblioteca de cláusulas padrão, edição de minuta e exportação em múltiplos formatos.

## Documentação Criada

### 1. Modelo de Dados
**Arquivo:** `MODELO_DADOS_CONTRATOS.md`

Define 7 tabelas principais:
- `clausulas_contrato_padrao` - Biblioteca de cláusulas
- `contratos` - Contratos gerados
- `contrato_clausulas` - Instâncias de cláusulas nos contratos
- `contrato_historico` - Versionamento e auditoria
- `contrato_anexos` - Arquivos anexados
- `contrato_parametros` - Definição de placeholders
- `contrato_parametros_valores` - Valores por contrato

### 2. Serviços e APIs
**Arquivo:** `SERVICOS_APIS_CONTRATOS.md`

Define 5 serviços principais:
- `ContratoService` - Geração e ciclo de vida de contratos
- `ClausulaService` - Gerenciamento de cláusulas
- `PlaceholderService` - Substituição de variáveis
- `ExportacaoService` - Exportação HTML/PDF/DOCX
- `HistoricoService` - Auditoria e versionamento

Endpoints REST para todas as operações.

### 3. Telas e Fluxos de Usuário
**Arquivo:** `TELAS_FLUXOS_USUARIO.md`

Define 6 telas principais:
- Cadastro de cláusulas padrão
- Geração de contrato a partir de orçamento
- Edição de minuta (com editor rich text)
- Prévia do contrato
- Gestão de contratos
- Detalhes do contrato

Fluxos completos de geração, edição e assinatura.

### 4. Boas Práticas
**Arquivo:** `BOAS_PRATICAS_CONTRATOS.md`

Cobre:
- Integridade de dados (evitar duplicação)
- Parametrização de variáveis (placeholders)
- Preparação para integração (faturamento, financeiro, serviços)
- Controle de permissões
- Versionamento e histórico
- Performance e escalabilidade
- Segurança
- Testes
- Monitoramento

### 5. Scripts SQL
**Arquivos:**
- `migrations/mysql/014_create_contratos_tables.sql` - MySQL
- `migrations/postgresql/014_create_contratos_tables_postgresql.sql` - PostgreSQL

Ambos incluem:
- Criação de todas as tabelas
- Índices de performance
- Triggers para auto-update (PostgreSQL)
- Dados iniciais (9 cláusulas padrão + 19 parâmetros)
- Constraints e FKs

## Funcionalidades Principais

### Geração de Contrato
- Botão "Gerar Contrato" em orçamentos aprovados
- Criação automática de cláusulas
- Substituição de placeholders
- Status inicial: Rascunho

### Edição de Minuta
- Editor rich text para cláusulas
- Reordenação (drag & drop)
- Adição/remoção de cláusulas
- Validação de placeholders

### Exportação
- HTML (prévia)
- PDF
- DOCX

### Integrações
- Faturamento recorrente
- Financeiro (lançamentos)
- Gestão de serviços/projetos

## Próximos Passos

1. Executar scripts de migração SQL
2. Criar modelos SQLAlchemy
3. Implementar serviços de negócio
4. Criar endpoints REST
5. Desenvolver interface do usuário
6. Implementar integrações
7. Escrever testes
8. Documentar API

## Requisitos de Dependências

```python
# requirements.txt (adicional)
weasyprint>=52.0  # Para geração de PDF
python-docx>=0.8.11  # Para geração de DOCX
bleach>=6.0.0  # Para sanitização de HTML
```

## Permissões Necessárias

Adicionar ao RBAC:
- `contratos.view`
- `contratos.create`
- `contratos.edit`
- `contratos.delete`
- `contratos.sign`
- `contratos.export`
- `clausulas.view`
- `clausulas.create`
- `clausulas.edit`
- `clausulas.delete`
- `clausulas.edit_critical`
