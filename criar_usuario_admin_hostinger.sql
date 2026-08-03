-- Script para criar usuário admin na Hostinger
-- Execute isto no banco u951548013_LS_Comercial via phpMyAdmin

USE u951548013_LS_Comercial;

-- Limpar admin anterior se existir (opcional)
DELETE FROM users WHERE username = 'admin' AND empresa_id IS NULL;

-- Inserir novo usuário admin
INSERT INTO users (
    username, 
    email, 
    password_hash, 
    full_name, 
    is_active, 
    is_admin, 
    role, 
    empresa_id,
    dashboard_chart_days
) VALUES (
    'admin',
    'admin@livesun.local',
    'pbkdf2:sha256:600000$xoYEOIqVcZ5c32i7$7f3eaa3cac7db10b87d55bd727eadefae29d563f7a0fed09326b2578db517417',
    'Administrador',
    1,
    1,
    'admin',
    NULL,
    30
);

-- Verificar se foi criado
SELECT id, username, email, role, is_admin, empresa_id FROM users WHERE username = 'admin';
