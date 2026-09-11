-- =====================================================================
-- SCRIPT DE MIGRAÇÃO: LiveSun Financeiro → LiveSun Comercial
-- =====================================================================
-- Origem: u951548013_gfinanceiro (MySQL - Hostinger)
-- Destino: u951548013_LS_Comercial (MySQL - Hostinger)
-- 
-- ATENÇÃO: Este script deve ser executado MANUALMENTE após revisão
-- Execute via phpMyAdmin ou cliente MySQL com as credenciais corretas
-- =====================================================================
--
-- CREDENCIAIS ORIGEM:
-- Host: 195.35.61.111:3306
-- Database: u951548013_gfinanceiro
-- Password: quemsabe123!A
--
-- CREDENCIAIS DESTINO:
-- Host: 195.35.61.111:3306
-- Database: u951548013_LS_Comercial
-- Password: quemsabe123!
-- =====================================================================

-- =====================================================================
-- INSTRUÇÕES DE EXECUÇÃO
-- =====================================================================
-- 1. Faça backup do banco de destino ANTES de executar
-- 2. Execute este script no banco de DESTINO (u951548013_LS_Comercial)
-- 3. O script assume que as tabelas já existem no destino (criadas pelo install_hostinger_comercial.sql)
-- 4. Se houver erro, verifique a mensagem e corrija antes de prosseguir
-- =====================================================================

USE `u951548013_LS_Comercial`;

SET NAMES utf8mb4;
SET time_zone = '+00:00';
SET FOREIGN_KEY_CHECKS = 0;
SET AUTOCOMMIT = 0;

-- =====================================================================
-- INÍCIO DA MIGRAÇÃO
-- =====================================================================

-- =====================================================================
-- 1. MIGRAR TABELA: empresas
-- =====================================================================
INSERT INTO empresas (
    id, nome, cnpj, 
    nome_fantasia, plano,
    atividade_comercial, atividade_servicos, atividade_financeiro,
    atividade_locacao, atividade_contratos, atividade_propostas, atividade_dashboard,
    endereco_rua, endereco_numero, endereco_bairro, codigo_municipio_ibge,
    endereco_cidade, endereco_uf, endereco_cep,
    inscricao_municipal, inscricao_estadual, telefone, email,
    op_simp_nac, reg_ap_trib_sn,
    criado_em, atualizado_em
)
SELECT 
    id, nome, cnpj,
    NULL AS nome_fantasia,
    'premium' AS plano,
    TRUE AS atividade_comercial,
    TRUE AS atividade_servicos,
    TRUE AS atividade_financeiro,
    FALSE AS atividade_locacao,
    FALSE AS atividade_contratos,
    FALSE AS atividade_propostas,
    TRUE AS atividade_dashboard,
    NULL AS endereco_rua,
    NULL AS endereco_numero,
    NULL AS endereco_bairro,
    NULL AS codigo_municipio_ibge,
    NULL AS endereco_cidade,
    NULL AS endereco_uf,
    NULL AS endereco_cep,
    NULL AS inscricao_municipal,
    NULL AS inscricao_estadual,
    NULL AS telefone,
    NULL AS email,
    3 AS op_simp_nac,
    1 AS reg_ap_trib_sn,
    criado_em,
    atualizado_em
FROM `u951548013_gfinanceiro`.empresas;

SELECT CONCAT('✓ empresas: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 2. MIGRAR TABELA: users
-- =====================================================================
INSERT INTO users (
    id, empresa_id, username, email, password_hash, full_name,
    is_active, is_admin, role,
    dashboard_chart_days,
    created_at, updated_at
)
SELECT 
    id, empresa_id, username, email, password_hash, full_name,
    is_active, is_admin,
    CASE 
        WHEN is_admin = 1 THEN 'admin'
        ELSE 'viewer'
    END AS role,
    dashboard_chart_days,
    created_at, updated_at
FROM `u951548013_gfinanceiro`.users;

SELECT CONCAT('✓ users: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 3. MIGRAR TABELA: fluxo_contas_modelo
-- =====================================================================
INSERT INTO fluxo_contas_modelo (
    id, empresa_id, codigo, descricao, tipo, mascara,
    nivel_sintetico, nivel_analitico, ativo,
    criado_em, atualizado_em
)
SELECT 
    id, empresa_id, codigo, descricao, tipo, mascara,
    nivel_sintetico, nivel_analitico, ativo,
    criado_em, atualizado_em
FROM `u951548013_gfinanceiro`.fluxo_contas_modelo;

SELECT CONCAT('✓ fluxo_contas_modelo: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 4. MIGRAR TABELA: entidades
-- =====================================================================
INSERT INTO entidades (
    id, empresa_id, nome, nome_fantasia, cnpj_cpf,
    inscricao_estadual, inscricao_municipal,
    tipo, fluxo_conta_id,
    endereco_rua, endereco_numero, endereco_bairro, codigo_municipio_ibge,
    endereco_cidade, endereco_uf, endereco_cep,
    telefone, email, contrato_produto,
    aliquota_comissao_especifica, valor_repasse, vendedor_id,
    ativo, criado_em, atualizado_em
)
SELECT 
    id, empresa_id, nome, NULL AS nome_fantasia, cnpj_cpf,
    NULL AS inscricao_estadual,
    NULL AS inscricao_municipal,
    tipo, fluxo_conta_id,
    NULL AS endereco_rua,
    NULL AS endereco_numero,
    NULL AS endereco_bairro,
    NULL AS codigo_municipio_ibge,
    NULL AS endereco_cidade,
    NULL AS endereco_uf,
    NULL AS endereco_cep,
    NULL AS telefone,
    NULL AS email,
    NULL AS contrato_produto,
    aliquota_comissao_especifica, valor_repasse, vendedor_id,
    ativo, criado_em, atualizado_em
FROM `u951548013_gfinanceiro`.entidades;

SELECT CONCAT('✓ entidades: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 5. MIGRAR TABELA: contas_banco
-- =====================================================================
INSERT INTO contas_banco (
    id, empresa_id, nome, banco, agencia, numero_conta, dv, tipo,
    fluxo_conta_id, saldo_inicial, is_principal, ativo,
    criado_em, atualizado_em
)
SELECT 
    id, empresa_id, nome, banco, agencia, numero_conta, dv, tipo,
    fluxo_conta_id, saldo_inicial,
    0 AS is_principal,
    ativo, criado_em, atualizado_em
FROM `u951548013_gfinanceiro`.contas_banco;

SELECT CONCAT('✓ contas_banco: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 6. MIGRAR TABELA: lancamentos
-- =====================================================================
INSERT INTO lancamentos (
    id, empresa_id,
    data_evento, data_vencimento, data_pagamento, status,
    entidade_id, fluxo_conta_id, conta_banco_id,
    valor_real, valor_pago, valor_imposto, valor_outros_custos,
    numero_documento, observacoes,
    referencia_banco, fonte,
    criado_em, atualizado_em
)
SELECT 
    id, empresa_id,
    data_evento, data_vencimento, data_pagamento, status,
    entidade_id, fluxo_conta_id, conta_banco_id,
    valor_real, valor_pago, valor_imposto, valor_outros_custos,
    numero_documento, observacoes,
    NULL AS referencia_banco,
    'migracao' AS fonte,
    criado_em, atualizado_em
FROM `u951548013_gfinanceiro`.lancamentos;

SELECT CONCAT('✓ lancamentos: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 7. MIGRAR TABELA: fluxo_caixa_realizado
-- =====================================================================
INSERT INTO fluxo_caixa_realizado (
    id, empresa_id, data,
    fluxo_conta_id, conta_banco_id,
    saldo_anterior, valor_pago, valor_recebido, saldo_atual,
    criado_em, atualizado_em
)
SELECT 
    id, empresa_id, data,
    fluxo_conta_id, conta_banco_id,
    saldo_anterior, valor_pago, valor_recebido, saldo_atual,
    criado_em, atualizado_em
FROM `u951548013_gfinanceiro`.fluxo_caixa_realizado;

SELECT CONCAT('✓ fluxo_caixa_realizado: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 8. MIGRAR TABELA: fluxo_caixa_previsto
-- =====================================================================
INSERT INTO fluxo_caixa_previsto (
    id, empresa_id, data,
    fluxo_conta_id, conta_banco_id,
    saldo_anterior, valor_previsto_pago, valor_previsto_recebido, saldo_previsto,
    criado_em, atualizado_em
)
SELECT 
    id, empresa_id, data,
    fluxo_conta_id, conta_banco_id,
    saldo_anterior, valor_previsto_pago, valor_previsto_recebido, saldo_previsto,
    criado_em, atualizado_em
FROM `u951548013_gfinanceiro`.fluxo_caixa_previsto;

SELECT CONCAT('✓ fluxo_caixa_previsto: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 9. MIGRAR TABELA: parametros_sistema
-- =====================================================================
INSERT INTO parametros_sistema (
    id, empresa_id, chave, valor, tipo, descricao,
    criado_em, atualizado_em
)
SELECT 
    id, empresa_id, chave, valor, tipo, descricao,
    criado_em, atualizado_em
FROM `u951548013_gfinanceiro`.parametros_sistema;

SELECT CONCAT('✓ parametros_sistema: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 10. MIGRAR TABELA: comissoes
-- =====================================================================
INSERT INTO comissoes (
    id, empresa_id, id_apuracao,
    lancamento_id, entidade_cliente_id, entidade_vendedor_id,
    dt_lancamento, dt_vencimento, dt_pagamento_recebimento,
    vl_nota, vl_imposto, vl_outros_custos, vl_repasse, vl_liquido,
    aliquota_aplicada, vl_comissao, situacao,
    criado_em, atualizado_em
)
SELECT 
    id, empresa_id, id_apuracao,
    lancamento_id, entidade_cliente_id, entidade_vendedor_id,
    dt_lancamento, dt_vencimento, dt_pagamento_recebimento,
    vl_nota, vl_imposto, vl_outros_custos, vl_repasse, vl_liquido,
    aliquota_aplicada, vl_comissao, situacao,
    criado_em, atualizado_em
FROM `u951548013_gfinanceiro`.comissoes;

SELECT CONCAT('✓ comissoes: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- 11. MIGRAR TABELA: importacao_nfse
-- =====================================================================
INSERT INTO importacao_nfse (
    id, empresa_id, chave_nota, numero_nota, data_emissao, cnpj_tomador,
    entidade_id, lancamento_id,
    valor_bruto, valor_impostos, descricao_servico,
    status_importacao, mensagem_erro, data_importacao,
    endereco_rua, endereco_numero, endereco_bairro, endereco_cidade,
    endereco_uf, endereco_cep, telefone, email, contrato_produto,
    aliquota_iss, aliquota_comissao_especifica, valor_repasse,
    entidade_vendedor_padrao_id, ativo, criado_em, atualizado_em
)
SELECT 
    id, empresa_id, chave_nota, numero_nota, data_emissao, cnpj_tomador,
    entidade_id, lancamento_id,
    valor_bruto, valor_impostos, descricao_servico,
    status_importacao, mensagem_erro, data_importacao,
    endereco_rua, endereco_numero, endereco_bairro, endereco_cidade,
    endereco_uf, endereco_cep, telefone, email, contrato_produto,
    aliquota_iss, aliquota_comissao_especifica, valor_repasse,
    entidade_vendedor_padrao_id, ativo, criado_em, atualizado_em
FROM `u951548013_gfinanceiro`.importacao_nfse;

SELECT CONCAT('✓ importacao_nfse: ', ROW_COUNT(), ' registros migrados') AS status;

-- =====================================================================
-- FIM DA MIGRAÇÃO
-- =====================================================================

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- VERIFICAÇÃO DE INTEGRIDADE
-- =====================================================================
SELECT '=== RESUMO DA MIGRAÇÃO ===' AS status;

SELECT 
    'empresas' AS tabela,
    COUNT(*) AS total
FROM empresas
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'fluxo_contas_modelo', COUNT(*) FROM fluxo_contas_modelo
UNION ALL
SELECT 'entidades', COUNT(*) FROM entidades
UNION ALL
SELECT 'contas_banco', COUNT(*) FROM contas_banco
UNION ALL
SELECT 'lancamentos', COUNT(*) FROM lancamentos
UNION ALL
SELECT 'fluxo_caixa_realizado', COUNT(*) FROM fluxo_caixa_realizado
UNION ALL
SELECT 'fluxo_caixa_previsto', COUNT(*) FROM fluxo_caixa_previsto
UNION ALL
SELECT 'parametros_sistema', COUNT(*) FROM parametros_sistema
UNION ALL
SELECT 'comissoes', COUNT(*) FROM comissoes
UNION ALL
SELECT 'importacao_nfse', COUNT(*) FROM importacao_nfse;

-- =====================================================================
-- COMMIT
-- =====================================================================
COMMIT;

SELECT '=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===' AS status;
SELECT 'Revise os dados e, se estiver tudo correto, o processo está completo.' AS observacao;
SELECT 'Lembre-se de ajustar manualmente o campo is_principal em contas_banco se necessário.' AS proximo_passo;

-- =====================================================================
-- EM CASO DE ERRO, EXECUTE:
-- ROLLBACK;
-- =====================================================================
