# Módulo de Locação de Roupas e Fantasias - LiveSun Comercial

## Visão Geral

O módulo de **Locação de Roupas e Fantasias** é um sistema completo para gerenciamento de aluguel de peças, fantasias, acessórios e kits em boutiques, locadoras e eventos. O módulo integra-se perfeitamente ao LiveSun Comercial, reutilizando cadastros de empresas, entidades, fluxo de caixa e lançamentos financeiros.

---

## 1. Estrutura de Dados

### 1.1 Acervo (Cadastro de Peças)

#### **LocacaoPeca**
Representa uma peça individual no acervo de locação.

**Campos principais:**
- `codigo_interno`: Identificador único da peça
- `codigo_barras` / `qr_code`: Para rastreamento
- `descricao`, `categoria`, `tema`: Classificação
- `tamanho`, `cor`, `tecido`, `marca_colecao`: Características físicas
- `valor_aquisicao`, `valor_reposicao`, `preco_aluguel_diario`, `preco_venda`: Precificação
- `estado_fisico`: novo, bom, regular, ruim, descartado
- `serializado`: True = item único; False = por grade
- `ativo`: Controle de disponibilidade

**Relacionamentos:**
- `empresa_id`: Multi-tenant
- `filial_id`: Opcional, para filiais
- `disponibilidades`: Lista de períodos bloqueados
- `manutencoes`: Histórico de manutenção

---

#### **LocacaoKit**
Conjunto/combo de peças para aluguel (ex: fantasia completa).

**Campos principais:**
- `codigo_interno`, `descricao`, `tema`
- `preco_aluguel_diario`, `preco_venda`
- `itens`: Peças que compõem o kit (via `LocacaoKitItem`)

**Relacionamentos:**
- `empresa_id`, `filial_id`
- `itens`: Muitos-para-muitos com `LocacaoPeca`

---

#### **LocacaoKitItem**
Relacionamento entre kit e peças.

**Campos:**
- `kit_id`, `peca_id`
- `quantidade`: Quantas peças deste tipo no kit
- `observacoes`

---

### 1.2 Disponibilidade e Agenda

#### **LocacaoDisponibilidade**
Controla períodos em que uma peça está indisponível (reservada, em manutenção, etc).

**Campos principais:**
- `peca_id`: Peça afetada
- `data_inicio`, `data_fim`: Período de bloqueio
- `motivo`: reserva, manutencao, limpeza, avaria, extravio
- `reserva_id`: Se bloqueio é por reserva
- `manutencao_id`: Se bloqueio é por manutenção

**Índices:**
- `idx_locacao_disp_peca_data`: Para consultas rápidas de disponibilidade
- `idx_locacao_disp_empresa_data`: Para relatórios por empresa

---

#### **LocacaoParametro**
Parâmetros configuráveis por empresa (buffers, multas, etc).

**Exemplos de chaves:**
- `dias_buffer_antes`: Dias de buffer antes da locação
- `dias_buffer_depois`: Dias de buffer depois da locação
- `multa_atraso_diaria_percentual`: % de multa por dia de atraso
- `multa_avaria_percentual`: % de multa por avaria
- `multa_perda_percentual`: % de multa por perda
- `percentual_caucao`: % de caução sobre o valor de aluguel
- `percentual_sinal`: % de sinal sobre o valor de aluguel

---

### 1.3 Comercial - Orçamento, Reserva e Contrato

#### **LocacaoEvento**
Evento associado a uma locação (casamento, festa, carnaval, etc).

**Campos:**
- `cliente_id`: Quem está alugando
- `tipo_evento`, `data_evento`, `local`
- `observacoes`

---

#### **LocacaoOrcamento**
Orçamento inicial com validade.

**Campos principais:**
- `numero`: Identificador único
- `cliente_id`, `evento_id`
- `data_emissao`, `data_validade`
- `data_retirada_prevista`, `data_devolucao_prevista`
- `dias_locacao`: Calculado automaticamente
- `valor_aluguel`, `valor_desconto`, `valor_acrescimo`, `valor_total`
- `valor_sinal`, `percentual_sinal`: Sinal configurável
- `valor_caucao`, `percentual_caucao`: Caução configurável
- `status`: rascunho, enviado, aprovado, rejeitado, convertido
- `itens`: Via `LocacaoOrcamentoItem`

**Fluxo:**
1. Criar orçamento (status = rascunho)
2. Enviar para cliente (status = enviado)
3. Cliente aprova (status = aprovado)
4. Converter em reserva (status = convertido)

---

#### **LocacaoOrcamentoItem**
Itens do orçamento (peças avulsas ou kits).

**Campos:**
- `tipo_item`: P (peça) ou K (kit)
- `peca_id` / `kit_id`: Referência
- `descricao`, `quantidade`
- `valor_unitario`, `valor_total`

---

#### **LocacaoReserva**
Reserva confirmada (conversão de orçamento aprovado).

**Campos principais:**
- `numero`: Identificador único
- `cliente_id`, `evento_id`
- `orcamento_id`: Referência ao orçamento original
- `data_reserva`: Quando foi feita
- `data_retirada`, `data_devolucao`: Período de locação
- `dias_locacao`
- `valor_aluguel`, `valor_desconto`, `valor_acrescimo`, `valor_total`
- `valor_sinal_pago`, `valor_caucao_retida`
- `status`: confirmada, retirada, devolvida, cancelada

**Bloqueio de disponibilidade:**
- Ao confirmar reserva, criar `LocacaoDisponibilidade` com motivo = "reserva"

---

#### **LocacaoContrato**
Contrato formal com cláusulas e termos.

**Campos principais:**
- `numero`: Identificador único
- `cliente_id`, `evento_id`
- `reserva_id`: Referência (1:1)
- `data_contrato`
- `data_retirada`, `data_devolucao`
- `valor_aluguel`, `valor_sinal`, `valor_caucao`, `valor_total`
- `multa_atraso_diaria`: Valor fixo ou % por dia de atraso
- `multa_avaria_percentual`: % sobre valor de reposição
- `multa_perda_percentual`: % sobre valor de reposição
- `condicoes_gerais`: Texto com cláusulas
- `status`: assinado, ativo, finalizado, cancelado
- `assinado_em`, `assinado_por_cliente`, `assinado_por_empresa`

**Geração de títulos:**
- Ao confirmar contrato, gerar automaticamente títulos financeiros (sinal, caução, saldo)

---

### 1.4 Operação - Retirada e Devolução

#### **LocacaoRetirada**
Registro de retirada de peças.

**Campos:**
- `numero`: Identificador único
- `contrato_id`: Qual contrato
- `data_retirada`: Quando foi retirado
- `responsavel_retirada`, `user_retirada_id`: Quem retirou
- `modo_retirada`: balcao ou entrega
- `status`: registrada, confirmada
- `itens`: Via `LocacaoRetiradaItem`

---

#### **LocacaoRetiradaItem**
Itens retirados.

**Campos:**
- `peca_id` / `kit_id`
- `quantidade`
- `observacoes`

---

#### **LocacaoDevolucao**
Registro de devolução de peças.

**Campos principais:**
- `numero`: Identificador único
- `contrato_id`
- `data_devolucao`: Quando foi devolvido
- `data_devolucao_prevista`: Data prevista
- `dias_atraso`: Calculado automaticamente
- `multa_atraso`: Calculada automaticamente
- `tipo_devolucao`: total ou parcial
- `status`: registrada, inspecionada, liberada
- `inspecoes`: Via `LocacaoInspecao`

**Cálculo de atraso:**
```
dias_atraso = max(0, data_devolucao - data_devolucao_prevista)
multa_atraso = dias_atraso * multa_atraso_diaria_do_contrato
```

---

#### **LocacaoInspecao**
Inspeção de peça devolvida.

**Campos principais:**
- `devolucao_id`
- `peca_id`
- `classificacao`: ok, sujo, avariado, faltante, perdido
- `valor_limpeza`, `valor_reparo`, `valor_reposicao`: Cobranças
- `valor_total_cobranca`: Soma das cobranças
- `encaminhamento`: higienizacao, manutencao, descarte
- `manutencao_id`: Se encaminhado para manutenção

**Regras de classificação:**
- **ok**: Sem cobranças adicionais
- **sujo**: Gerar cobrança de limpeza
- **avariado**: Gerar cobrança de reparo
- **faltante/perdido**: Gerar cobrança de reposição (valor_reposicao da peça)

---

### 1.5 Manutenção e Higienização

#### **LocacaoManutencao**
Registro de manutenção, limpeza ou reparo.

**Campos:**
- `peca_id`
- `tipo_servico`: higienizacao, reparo, manutencao_preventiva
- `data_entrada`, `data_saida_prevista`, `data_saida`
- `valor_servico`, `valor_material`, `valor_total`
- `status`: pendente, em_andamento, concluida, cancelada

**Bloqueio de disponibilidade:**
- Ao criar manutenção, criar `LocacaoDisponibilidade` com motivo = "manutencao"

---

### 1.6 Financeiro - Títulos e Cobranças

#### **LocacaoTitulo**
Título financeiro gerado a partir de contrato.

**Campos principais:**
- `numero`: Identificador único
- `contrato_id`
- `cliente_id`
- `lancamento_id`: Integração com `Lancamento` do módulo financeiro
- `tipo_titulo`: sinal, caucao, saldo, multa, avaria, venda_complementar, estorno
- `data_emissao`, `data_vencimento`, `data_pagamento`
- `valor_original`, `valor_pago`, `valor_aberto`
- `status`: aberto, pago, vencido, cancelado, estornado

**Geração automática:**
1. **Sinal**: Ao confirmar contrato, se `valor_sinal > 0`
2. **Caução**: Ao confirmar contrato, se `valor_caucao > 0`
3. **Saldo**: Ao confirmar contrato, valor restante = `valor_total - valor_sinal - valor_caucao`
4. **Multa**: Ao processar devolução com atraso
5. **Avaria**: Ao processar inspeção com classificação != ok
6. **Venda complementar**: Se cliente comprar peça alugada
7. **Estorno**: Se cancelar ou devolver caução

**Integração com Lancamento:**
- Cada título gera um `Lancamento` correspondente
- `Lancamento.fonte = 'locacao'`
- `Lancamento.numero_documento = LocacaoTitulo.numero`

---

#### **LocacaoCobranca**
Cobrança adicional por atraso, avaria, perda ou limpeza.

**Campos:**
- `contrato_id`
- `inspecao_id`: Se originária de inspeção
- `titulo_id`: Título financeiro associado
- `tipo_cobranca`: atraso, avaria, perda, limpeza, outro
- `valor_cobranca`, `valor_pago`
- `status`: pendente, pago, cancelado

---

#### **LocacaoDevolucaoCaucao**
Registro de devolução de caução ao cliente.

**Campos:**
- `contrato_id`
- `cliente_id`
- `titulo_id`: Título de devolução de caução
- `valor_caucao_original`
- `valor_descontos`: Descontos por avaria, etc
- `valor_devolucao`: Valor efetivamente devolvido
- `data_devolucao_prevista`, `data_devolucao_efetiva`
- `status`: pendente, processando, devolvida, cancelada

**Cálculo:**
```
valor_devolucao = valor_caucao_original - valor_descontos
```

---

### 1.7 Faturamento

#### **LocacaoFaturamento**
Registro de faturamento de locação.

**Campos principais:**
- `numero_documento`: Identificador único
- `contrato_id`
- `cliente_id`
- `data_faturamento`
- `evento_faturamento`: reserva, retirada, devolucao, fechamento
- `valor_aluguel`, `valor_venda`, `valor_multa`, `valor_avaria`, `valor_caucao_retida`
- `valor_total`
- `memoria_calculo`: Detalhamento do cálculo
- `status`: emitido, refaturado, cancelado

**Eventos de faturamento:**
1. **Na reserva**: Se política = "na_reserva"
2. **Na retirada**: Se política = "na_retirada"
3. **Na devolução**: Se política = "na_devolucao"
4. **No fechamento**: Se política = "no_fechamento"

**Memória de cálculo (exemplo):**
```json
{
  "dias_locacao": 3,
  "valor_diario": 50.00,
  "valor_aluguel": 150.00,
  "valor_desconto": 0.00,
  "valor_acrescimo": 0.00,
  "dias_atraso": 1,
  "multa_atraso_diaria": 25.00,
  "multa_atraso_total": 25.00,
  "avarias": [
    {"peca": "Vestido Vermelho", "valor": 75.00}
  ],
  "valor_avaria_total": 75.00,
  "valor_caucao_retida": 0.00,
  "valor_total": 250.00
}
```

---

### 1.8 Auditoria

#### **LocacaoAuditoria**
Log completo de todas as ações.

**Campos:**
- `user_id`: Quem fez a ação
- `tipo_entidade`: contrato, retirada, devolucao, inspecao, etc
- `id_entidade`: ID do registro afetado
- `tipo_acao`: criacao, atualizacao, cancelamento, etc
- `descricao`: Descrição legível
- `dados_anteriores`, `dados_novos`: JSON com mudanças
- `data_acao`: Quando aconteceu

---

## 2. Fluxos de Negócio

### 2.1 Fluxo de Locação Completo

```
1. ORÇAMENTO
   ├─ Criar LocacaoOrcamento (status = rascunho)
   ├─ Adicionar LocacaoOrcamentoItem (peças/kits)
   ├─ Calcular valores (aluguel, desconto, caução, sinal)
   └─ Enviar para cliente (status = enviado)

2. APROVAÇÃO
   ├─ Cliente aprova orçamento (status = aprovado)
   └─ Opção: Rejeitar (status = rejeitado)

3. RESERVA
   ├─ Converter orçamento em LocacaoReserva (status = confirmada)
   ├─ Criar LocacaoDisponibilidade para cada peça (motivo = reserva)
   ├─ Gerar LocacaoContrato
   └─ Gerar LocacaoTitulo (sinal, caução, saldo)

4. RETIRADA
   ├─ Criar LocacaoRetirada
   ├─ Adicionar LocacaoRetiradaItem
   ├─ Registrar responsável e modo (balcão/entrega)
   └─ Confirmar retirada (status = confirmada)

5. DEVOLUÇÃO
   ├─ Criar LocacaoDevolucao
   ├─ Calcular dias de atraso
   ├─ Calcular multa de atraso (se houver)
   └─ Registrar responsável

6. INSPEÇÃO
   ├─ Para cada peça devolvida, criar LocacaoInspecao
   ├─ Classificar: ok, sujo, avariado, faltante, perdido
   ├─ Calcular cobranças (limpeza, reparo, reposição)
   ├─ Gerar LocacaoCobranca se necessário
   ├─ Encaminhar para manutenção se necessário
   └─ Liberar peça (status = liberada)

7. FATURAMENTO
   ├─ Gerar LocacaoFaturamento
   ├─ Incluir aluguel, multas, avarias, etc
   ├─ Gerar LocacaoTitulo para cobranças adicionais
   └─ Integrar com Lancamento (módulo financeiro)

8. FECHAMENTO
   ├─ Processar pagamentos
   ├─ Devolver caução (LocacaoDevolucaoCaucao)
   ├─ Encerrar contrato (status = finalizado)
   └─ Arquivar documentos
```

---

### 2.2 Máquina de Estados do Contrato

```
LocacaoContrato.status:
  assinado ──→ ativo ──→ finalizado
       ↓
   cancelado
```

**Transições permitidas:**
- `assinado` → `ativo`: Quando retirada é confirmada
- `assinado` → `cancelado`: Cancelamento antes de retirada
- `ativo` → `finalizado`: Quando devolução é liberada
- `ativo` → `cancelado`: Cancelamento durante locação (com penalidades)

---

### 2.3 Regras de Disponibilidade

**Consulta de disponibilidade:**
```sql
SELECT p.* FROM locacao_pecas p
WHERE p.empresa_id = :empresa_id
  AND p.ativo = TRUE
  AND NOT EXISTS (
    SELECT 1 FROM locacao_disponibilidade d
    WHERE d.peca_id = p.id
      AND d.data_inicio <= :data_fim
      AND d.data_fim >= :data_inicio
  )
```

**Buffers:**
- Antes da locação: `dias_buffer_antes` dias sem disponibilidade
- Depois da locação: `dias_buffer_depois` dias sem disponibilidade

**Exemplo:**
```
Locação: 10 a 15 de janeiro
Buffer antes: 2 dias
Buffer depois: 1 dia
Bloqueio efetivo: 8 a 16 de janeiro
```

---

## 3. Integração com Módulos Existentes

### 3.1 Integração com Entidades

- **Cliente**: Referência em `LocacaoReserva`, `LocacaoContrato`, `LocacaoTitulo`
- Reutilizar cadastro de clientes existente
- Suportar múltiplos contatos por cliente

### 3.2 Integração com Financeiro

**Geração de Lançamentos:**
1. Ao gerar `LocacaoTitulo`, criar `Lancamento` correspondente
2. `Lancamento.fonte = 'locacao'`
3. `Lancamento.numero_documento = LocacaoTitulo.numero`
4. `Lancamento.entidade_id = cliente_id`
5. `Lancamento.fluxo_conta_id = conta de recebimento de aluguel`
6. `Lancamento.data_evento = data_emissao`
7. `Lancamento.data_vencimento = data_vencimento`
8. `Lancamento.valor_real = valor_original`

**Regra de não duplicação:**
- Verificar se `Lancamento` com mesmo `numero_documento` já existe
- Se existir, não criar novo (idempotência)

### 3.3 Integração com Relatórios

**Relatórios propostos:**
1. **Disponibilidade por período**: Peças disponíveis em data range
2. **Itens reservados**: Peças com reservas ativas
3. **Itens em atraso**: Devoluções atrasadas
4. **Itens em manutenção**: Peças em higienização/reparo
5. **Agenda diária**: Retiradas e devoluções do dia
6. **Contratos abertos e encerrados**: Por período
7. **Ranking por peça**: Mais alugadas, receita, etc
8. **Ranking por cliente**: Maior volume, receita, etc
9. **Receita por período**: Aluguel, multas, avarias
10. **Multas e avarias**: Por período, cliente, peça
11. **Contas a receber**: Integrado com módulo financeiro
12. **Fluxo de caixa**: Previsto x realizado
13. **Giro e ocupação**: Dias alugados vs dias totais
14. **ROI do acervo**: Receita vs valor de aquisição

---

## 4. Parâmetros de Configuração

**Chaves de LocacaoParametro:**

| Chave | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `dias_buffer_antes` | numeric | 2 | Dias de buffer antes da locação |
| `dias_buffer_depois` | numeric | 1 | Dias de buffer depois da locação |
| `multa_atraso_diaria_valor` | numeric | 0.00 | Valor fixo de multa por dia de atraso |
| `multa_atraso_diaria_percentual` | numeric | 0.00 | % de multa por dia de atraso (sobre valor diário) |
| `multa_avaria_percentual` | numeric | 50.00 | % de multa por avaria (sobre valor de reposição) |
| `multa_perda_percentual` | numeric | 100.00 | % de multa por perda (sobre valor de reposição) |
| `percentual_caucao` | numeric | 20.00 | % de caução sobre valor de aluguel |
| `percentual_sinal` | numeric | 30.00 | % de sinal sobre valor de aluguel |
| `politica_faturamento` | string | "no_fechamento" | Quando faturar: na_reserva, na_retirada, na_devolucao, no_fechamento |
| `dias_retencao_caucao` | numeric | 7 | Dias para reter caução antes de devolver |
| `valor_limpeza_padrao` | numeric | 25.00 | Valor padrão de cobrança por limpeza |
| `valor_reparo_padrao` | numeric | 50.00 | Valor padrão de cobrança por reparo |

---

## 5. Casos de Uso Principais

### 5.1 Aluguel Simples (1 peça, 3 dias)

```
Cliente: João Silva
Peça: Vestido Vermelho (código: VR-001)
Período: 10 a 13 de janeiro
Valor diário: R$ 50,00
Valor total: R$ 150,00
Sinal (30%): R$ 45,00
Caução (20%): R$ 30,00
Saldo: R$ 75,00

Títulos gerados:
1. Sinal: R$ 45,00 (vencimento: 5 de janeiro)
2. Caução: R$ 30,00 (vencimento: 5 de janeiro)
3. Saldo: R$ 75,00 (vencimento: 13 de janeiro)
```

### 5.2 Kit Completo (5 peças, 1 dia)

```
Cliente: Maria Santos
Kit: Fantasia Carnaval Completa (código: FC-001)
Peças: Vestido, Sapato, Coroa, Maquiagem, Acessórios
Período: 25 de fevereiro
Valor do kit: R$ 200,00
Sinal: R$ 60,00
Caução: R$ 40,00
Saldo: R$ 100,00

Devolução:
- Vestido: OK
- Sapato: Sujo (limpeza: R$ 25,00)
- Coroa: Avariada (reparo: R$ 50,00)
- Maquiagem: OK
- Acessórios: Faltante (reposição: R$ 30,00)

Cobranças adicionais: R$ 105,00
Caução retida: R$ 40,00 (descontar cobranças)
Devolução de caução: R$ 0,00 (R$ 40,00 - R$ 105,00 = -R$ 65,00, cliente deve)
```

### 5.3 Atraso de Devolução

```
Cliente: Pedro Costa
Contrato: Vestido Azul
Período previsto: 10 a 12 de janeiro (2 dias)
Devolução real: 15 de janeiro (5 dias)
Dias de atraso: 3 dias
Multa diária: R$ 25,00
Multa total: R$ 75,00

Título gerado:
- Multa por atraso: R$ 75,00 (vencimento: 20 de janeiro)
```

### 5.4 Conversão de Aluguel em Venda

```
Cliente: Ana Silva
Vestido Branco (aluguel: R$ 100,00)
Período: 10 a 12 de janeiro
Cliente deseja comprar: Valor de venda = R$ 300,00

Cálculo:
- Aluguel já pago: R$ 100,00 (desconto)
- Valor de venda: R$ 300,00
- Saldo a pagar: R$ 200,00

Título gerado:
- Venda complementar: R$ 200,00
```

---

## 6. Status e Transições

### LocacaoOrcamento
- `rascunho` → `enviado` → `aprovado` → `convertido`
- `rascunho` → `enviado` → `rejeitado`

### LocacaoReserva
- `confirmada` → `retirada` → `devolvida`
- `confirmada` → `cancelada`

### LocacaoContrato
- `assinado` → `ativo` → `finalizado`
- `assinado` → `cancelado`
- `ativo` → `cancelado`

### LocacaoRetirada
- `registrada` → `confirmada`

### LocacaoDevolucao
- `registrada` → `inspecionada` → `liberada`

### LocacaoTitulo
- `aberto` → `pago`
- `aberto` → `vencido`
- `aberto` → `cancelado`
- `aberto` → `estornado`

### LocacaoManutencao
- `pendente` → `em_andamento` → `concluida`
- `pendente` → `cancelada`
- `em_andamento` → `cancelada`

---

## 7. Segurança e Auditoria

### 7.1 Isolamento de Dados (Multi-tenant)

Todos os modelos incluem `empresa_id` para isolamento automático.

### 7.2 Rastreabilidade

Todos os modelos incluem:
- `criado_em`: Timestamp de criação
- `atualizado_em`: Timestamp de última atualização
- `criado_por_user_id`: Quem criou (quando aplicável)

### 7.3 Auditoria Completa

Tabela `LocacaoAuditoria` registra:
- Quem fez a ação
- O quê foi modificado
- Quando foi modificado
- Dados anteriores e novos

---

## 8. Próximas Etapas

1. **Criar rotas e views** para cada funcionalidade
2. **Implementar lógica de negócio** (cálculos, validações)
3. **Criar templates** para interface web
4. **Integrar com financeiro** (geração de lançamentos)
5. **Implementar relatórios**
6. **Testes unitários e de integração**
7. **Documentação de API**
8. **Treinamento de usuários**

---

## 9. Referências

- **Escopo original**: Aluguel de Roupas e Fantasias
- **Arquitetura**: Padrão LiveSun Comercial (SQLAlchemy, Flask, Multi-tenant)
- **Integração**: Módulo Financeiro (Lançamentos), Relatórios, Auditoria
