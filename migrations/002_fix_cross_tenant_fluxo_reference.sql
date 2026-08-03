-- Manutenção manual para o caso residual de referência cruzada
-- entre lancamentos e fluxo_contas_modelo de empresas diferentes.
--
-- Objetivo:
-- 1. Identificar o(s) lançamento(s) ainda inconsistentes.
-- 2. Localizar a conta de fluxo correta dentro da mesma empresa.
-- 3. Atualizar o fluxo_conta_id com segurança.

-- ============================================================
-- 1) Diagnóstico: listar lançamentos inconsistentes
-- ============================================================

SELECT
    l.id AS lancamento_id,
    l.numero_documento,
    l.empresa_id AS empresa_lancamento,
    l.fluxo_conta_id AS fluxo_atual_id,
    f_atual.empresa_id AS empresa_fluxo_atual,
    f_atual.codigo AS fluxo_atual_codigo,
    f_atual.descricao AS fluxo_atual_descricao,
    e.id AS entidade_id,
    e.nome AS entidade_nome,
    cb.id AS conta_banco_id,
    cb.nome AS conta_banco_nome
FROM lancamentos l
JOIN fluxo_contas_modelo f_atual ON f_atual.id = l.fluxo_conta_id
LEFT JOIN entidades e ON e.id = l.entidade_id
LEFT JOIN contas_banco cb ON cb.id = l.conta_banco_id
WHERE l.empresa_id <> f_atual.empresa_id
ORDER BY l.id;

-- ============================================================
-- 2) Sugestão automática: procurar conta equivalente por código
--    dentro da empresa correta do lançamento
-- ============================================================

SELECT
    l.id AS lancamento_id,
    l.empresa_id AS empresa_lancamento,
    l.fluxo_conta_id AS fluxo_atual_id,
    f_atual.codigo AS codigo_fluxo,
    f_atual.descricao AS descricao_fluxo_atual,
    f_correto.id AS fluxo_correto_id,
    f_correto.descricao AS descricao_fluxo_correto
FROM lancamentos l
JOIN fluxo_contas_modelo f_atual ON f_atual.id = l.fluxo_conta_id
LEFT JOIN fluxo_contas_modelo f_correto
    ON f_correto.empresa_id = l.empresa_id
   AND f_correto.codigo = f_atual.codigo
WHERE l.empresa_id <> f_atual.empresa_id
ORDER BY l.id, f_correto.id;

-- ============================================================
-- 3) Correção manual segura
--
-- Instruções:
-- - Defina @lancamento_id com o id do lançamento inconsistente.
-- - Defina @fluxo_correto_id com o id correto da conta de fluxo
--   pertencente à mesma empresa do lançamento.
-- - Execute primeiro o SELECT de conferência e só depois o UPDATE.
-- ============================================================

SET @lancamento_id = 0;
SET @fluxo_correto_id = 0;

START TRANSACTION;

SELECT
    l.id AS lancamento_id,
    l.empresa_id AS empresa_lancamento,
    l.fluxo_conta_id AS fluxo_atual_id,
    f_atual.empresa_id AS empresa_fluxo_atual,
    f_atual.codigo AS codigo_fluxo_atual,
    f_atual.descricao AS descricao_fluxo_atual
FROM lancamentos l
JOIN fluxo_contas_modelo f_atual ON f_atual.id = l.fluxo_conta_id
WHERE l.id = @lancamento_id
FOR UPDATE;

SELECT
    f.id,
    f.empresa_id,
    f.codigo,
    f.descricao,
    f.tipo,
    f.ativo
FROM fluxo_contas_modelo f
WHERE f.id = @fluxo_correto_id
FOR UPDATE;

UPDATE lancamentos
SET fluxo_conta_id = @fluxo_correto_id
WHERE id = @lancamento_id;

SELECT
    l.id AS lancamento_id,
    l.empresa_id AS empresa_lancamento,
    l.fluxo_conta_id AS fluxo_novo_id,
    f.empresa_id AS empresa_fluxo_novo,
    f.codigo AS codigo_fluxo_novo,
    f.descricao AS descricao_fluxo_novo
FROM lancamentos l
JOIN fluxo_contas_modelo f ON f.id = l.fluxo_conta_id
WHERE l.id = @lancamento_id;

-- Se estiver correto:
COMMIT;

-- Se precisar desfazer em vez de gravar:
-- ROLLBACK;

-- ============================================================
-- 4) Validação final global
-- ============================================================

SELECT COUNT(*) AS inconsistencias_restantes
FROM lancamentos l
JOIN fluxo_contas_modelo f ON f.id = l.fluxo_conta_id
WHERE l.empresa_id <> f.empresa_id;