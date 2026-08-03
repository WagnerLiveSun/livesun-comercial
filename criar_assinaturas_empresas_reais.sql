-- Script para criar assinaturas para as empresas REAIS existentes
-- Execute isto no banco u951548013_LS_Comercial via phpMyAdmin

USE u951548013_LS_Comercial;

DELETE FROM assinatura_empresa WHERE empresa_id IN (1, 2, 3);

INSERT INTO assinatura_empresa (
    empresa_id,
    plano_codigo,
    status,
    bloqueio_nivel,
    data_inicio,
    data_vencimento,
    ciclo_cobranca,
    bloqueado_desde,
    motivo_status
) VALUES 
(1, 'premium', 'ativa', 'nenhum', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'mensal', NULL, 'Assinatura ativa'),

(2, 'premium', 'ativa', 'nenhum', DATE_SUB(CURDATE(), INTERVAL 60 DAY), DATE_ADD(CURDATE(), INTERVAL 20 DAY), 'mensal', NULL, 'Assinatura renovada - Premium'),

(3, 'basic', 'ativa', 'nenhum', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'mensal', NULL, 'Assinatura ativa - Plano Basic');

SELECT 
    ae.id,
    ae.empresa_id,
    e.nome,
    ae.plano_codigo,
    ae.status,
    ae.bloqueio_nivel,
    ae.data_vencimento
FROM assinatura_empresa ae
LEFT JOIN empresas e ON ae.empresa_id = e.id
ORDER BY ae.empresa_id;
