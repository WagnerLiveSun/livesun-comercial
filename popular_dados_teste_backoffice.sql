-- Script para popular dados de teste no backoffice comercial
-- Execute isto no banco u951548013_LS_Comercial via phpMyAdmin

USE u951548013_LS_Comercial;

-- 1. Inserir planos se não existirem
INSERT IGNORE INTO catalogo_plano_comercial (
    codigo_plano, 
    versao_oferta, 
    nome_plano, 
    descricao, 
    periodicidade, 
    preco, 
    limite_usuarios,
    ativo,
    data_inicio_vigencia
) VALUES 
('basic', 1, 'Plano Basic', 'Plano básico para pequenas empresas', 'mensal', 49.00, 5, 1, NOW()),
('intermediate', 1, 'Plano Intermediate', 'Plano intermediário para médias empresas', 'mensal', 129.00, 15, 1, NOW()),
('premium', 1, 'Plano Premium', 'Plano premium para grandes empresas', 'mensal', 249.00, 50, 1, NOW());

-- 2. Inserir empresas clientes de teste
INSERT IGNORE INTO empresas (
    cnpj,
    razao_social,
    nome_fantasia,
    email,
    telefone,
    ativo,
    data_criacao,
    assinante_id
) VALUES 
('12345678000100', 'Empresa Cliente 1 LTDA', 'Empresa 1', 'contato@empresa1.com.br', '1133334444', 1, NOW(), 1),
('98765432000189', 'Empresa Cliente 2 SA', 'Empresa 2', 'contato@empresa2.com.br', '1144445555', 1, NOW(), 1),
('11222333000111', 'Empresa Cliente 3 ME', 'Empresa 3', 'contato@empresa3.com.br', '1155556666', 1, NOW(), 1),
('33444555000222', 'Empresa Cliente 4 LTDA', 'Empresa 4', 'contato@empresa4.com.br', '1166667777', 1, NOW(), 1);

-- 3. Obter IDs das empresas inseridas
SET @empresa1 = (SELECT id FROM empresas WHERE cnpj = '12345678000100' LIMIT 1);
SET @empresa2 = (SELECT id FROM empresas WHERE cnpj = '98765432000189' LIMIT 1);
SET @empresa3 = (SELECT id FROM empresas WHERE cnpj = '11222333000111' LIMIT 1);
SET @empresa4 = (SELECT id FROM empresas WHERE cnpj = '33444555000222' LIMIT 1);

-- 4. Inserir assinaturas em diferentes status
INSERT IGNORE INTO assinatura_empresa (
    empresa_id,
    plano,
    status,
    bloqueio_nivel,
    data_inicio,
    data_vencimento,
    ciclo_cobranca,
    ativo,
    bloqueado_desde,
    motivo_status
) VALUES 
(@empresa1, 'basic', 'ativa', 'nenhum', NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), 'mensal', 1, NULL, 'Assinatura ativa'),
(@empresa2, 'intermediate', 'trial', 'nenhum', NOW(), DATE_ADD(NOW(), INTERVAL 14 DAY), 'mensal', 1, NULL, 'Período trial de 14 dias'),
(@empresa3, 'premium', 'suspensa', 'total', DATE_SUB(NOW(), INTERVAL 15 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY), 'mensal', 0, DATE_SUB(NOW(), INTERVAL 5 DAY), 'Falta de pagamento'),
(@empresa4, 'basic', 'ativa', 'nenhum', DATE_SUB(NOW(), INTERVAL 60 DAY), DATE_ADD(NOW(), INTERVAL 20 DAY), 'mensal', 1, NULL, 'Assinatura renovada');

-- 5. Inserir usuários para as empresas
INSERT IGNORE INTO users (
    empresa_id,
    username,
    email,
    password_hash,
    full_name,
    is_active,
    is_admin,
    role,
    dashboard_chart_days
) VALUES 
(@empresa1, 'gerente1', 'gerente@empresa1.com.br', 'pbkdf2:sha256:600000$xoYEOIqVcZ5c32i7$7f3eaa3cac7db10b87d55bd727eadefae29d563f7a0fed09326b2578db517417', 'Gerente Empresa 1', 1, 1, 'admin', 30),
(@empresa1, 'usuario1', 'usuario@empresa1.com.br', 'pbkdf2:sha256:600000$xoYEOIqVcZ5c32i7$7f3eaa3cac7db10b87d55bd727eadefae29d563f7a0fed09326b2578db517417', 'Usuário Empresa 1', 1, 0, 'operator', 30),
(@empresa2, 'gerente2', 'gerente@empresa2.com.br', 'pbkdf2:sha256:600000$xoYEOIqVcZ5c32i7$7f3eaa3cac7db10b87d55bd727eadefae29d563f7a0fed09326b2578db517417', 'Gerente Empresa 2', 1, 1, 'admin', 30),
(@empresa3, 'gerente3', 'gerente@empresa3.com.br', 'pbkdf2:sha256:600000$xoYEOIqVcZ5c32i7$7f3eaa3cac7db10b87d55bd727eadefae29d563f7a0fed09326b2578db517417', 'Gerente Empresa 3', 1, 1, 'admin', 30),
(@empresa4, 'gerente4', 'gerente@empresa4.com.br', 'pbkdf2:sha256:600000$xoYEOIqVcZ5c32i7$7f3eaa3cac7db10b87d55bd727eadefae29d563f7a0fed09326b2578db517417', 'Gerente Empresa 4', 1, 1, 'admin', 30);

-- 6. Verificar dados inseridos
SELECT 
    e.id,
    e.razao_social,
    a.plano,
    a.status,
    COUNT(u.id) as total_usuarios
FROM empresas e
LEFT JOIN assinatura_empresa a ON e.id = a.empresa_id
LEFT JOIN users u ON e.id = u.empresa_id
WHERE e.cnpj IN ('12345678000100', '98765432000189', '11222333000111', '33444555000222')
GROUP BY e.id, e.razao_social, a.plano, a.status
ORDER BY e.id;

COMMIT;
