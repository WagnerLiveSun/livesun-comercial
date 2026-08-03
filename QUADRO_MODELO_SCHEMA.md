# Quadro de compatibilidade entre modelo e schema

## Objetivo

Este quadro resume as principais diferencas encontradas entre os modelos SQLAlchemy do sistema e o schema base do banco. O foco e apontar onde a execucao pode falhar se o banco nao estiver alinhado com o codigo.

## Resumo rapido

1. A maior divergencia esta em Empresa.
2. Existe tabela auxiliar de fiscalizacao da empresa que depende de migration especifica.
3. Entidade possui campo adicional de municipio IBGE.
4. O nucleo financeiro e o comercial principal estao, em geral, alinhados com o schema base, mas dependem de migrations e scripts complementares em alguns ambientes.

## Comparacao principal

| Area | Modelo Python | Schema base | Impacto |
| --- | --- | --- | --- |
| Empresa | Possui nome fantasia, atividades da empresa, endereco completo, inscricoes, contato, logo e parametros fiscais | O schema base carrega apenas nome, cnpj, plano e timestamps | Alto. Se faltar migration, telas de empresa, fiscal e assinatura podem quebrar ou exibir dados incompletos |
| EmpresaFiscalItem | Existe no modelo como tabela auxiliar de catalogo fiscal por empresa | Nao aparece no schema base principal | Alto quando o fluxo fiscal usa itens por empresa |
| Entidade | Possui codigo_municipio_ibge e campos de comissao por cliente/fornecedor | O schema base inicial nao traz codigo_municipio_ibge, mas traz os demais campos operacionais | Medio. Pode afetar NFS-e, fiscal e filtros por municipio |
| User | Aceita empresa_id nulo para usuario backoffice e usa role, is_admin, dashboard_chart_days | O schema comercial contem esses campos | Baixo. O ponto critico e manter a migracao de login por empresa aplicada |
| FluxoContaModel | Modelo e schema seguem a mesma ideia de codigo, descricao, tipo e mascara | Estrutura compativel | Baixo |
| ContaBanco | Modelo e schema seguem a mesma estrutura, incluindo is_principal | Estrutura compativel | Baixo |
| Lancamento | Modelo e schema incluem valor_imposto, valor_outros_custos, referencia_banco e fonte | Estrutura compativel | Baixo |
| Filial | Estrutura de cadastro operacional por empresa | Estrutura compatível | Baixo |
| Produto | Estrutura operacional de produto, estoque e precificacao | Estrutura compatível | Baixo |
| Servico | Estrutura operacional de servicos e NBS | Estrutura compatível | Baixo a medio, dependendo das tabelas fiscais de apoio |
| CompraNFManual | Estrutura de compra manual com filial, fornecedor, lancamento e status | Estrutura compatível | Baixo |
| DocumentoVenda | Estrutura de venda nao fiscal com itens de produto e servico | Estrutura compatível | Baixo |

## Onde a aplicacao costuma depender de migrations

1. Campos adicionais de empresa.
2. Campo codigo_municipio_ibge em entidades.
3. Ajustes de login por empresa e isolamento de tenant.
4. Tabela auxiliar de itens fiscais da empresa.

## Principais arquivos de apoio

- src/models/__init__.py
- schema_comercial.sql
- migrations/014_add_empresa_fiscal_fields.sql
- migrations/016_add_entidades_cadastro_fields.sql
- migrations/018_add_codigo_municipio_ibge_to_entidades.sql
- migrations/019_add_codigo_municipio_ibge_to_empresas.sql
- migrations/022_add_atividade_contratos.sql
- migrations/030_add_regime_tributario.sql
- migrate_user_login_scope.py
- migrate_tenant_isolation.py

## Leitura pratica por prioridade

### Prioridade alta

1. Empresa.
2. EmpresaFiscalItem.
3. Entidade com codigo_municipio_ibge.

### Prioridade media

1. Regras de tenant e login.
2. Ajustes fiscais e de contrato por empresa.

### Prioridade baixa

1. Tabelas operacionais que ja estao alinhadas ao schema principal.

## Interpretacao para suporte

Se uma tela de cadastro empresa ou fiscal quebra, o problema quase sempre esta em migration faltante de empresa, empresa_fiscal_itens ou entidade.

Se telas financeiras e comerciais abrem, mas o usuario nao consegue gravar, o problema tende a ser permissao ou tenant, nao schema bruto.
