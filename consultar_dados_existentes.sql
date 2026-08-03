-- Script para VER as empresas já cadastradas
-- Execute isto no banco u951548013_LS_Comercial via phpMyAdmin

USE u951548013_LS_Comercial;

-- Listar todas as empresas existentes
SELECT 
    id,
    cnpj,
    razao_social,
    nome_fantasia,
    email,
    telefone,
    ativo,
    data_criacao
FROM empresas
ORDER BY id DESC;

-- Listar usuários existentes
SELECT 
    id,
    empresa_id,
    username,
    email,
    full_name,
    role,
    is_admin,
    is_active
FROM users
ORDER BY id DESC;

-- Listar assinaturas existentes
SELECT 
    id,
    empresa_id,
    plano,
    status,
    bloqueio_nivel,
    data_vencimento
FROM assinatura_empresa
ORDER BY id DESC;
