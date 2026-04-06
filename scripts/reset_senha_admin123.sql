-- Reset de senha para admin123 (hash Werkzeug)
-- Data: 2026-04-06
-- Observacao: ajuste o filtro WHERE para o usuario correto antes de executar.

UPDATE users
SET password_hash = 'scrypt:32768:8:1$mPJ7I2qQOPxks4U4$34b0a02b277d77397d5d91462a43f51bf90fc44e6460ce75fbc82cb2ca1caddb833f30768728ccc114e4d09a5f7be7f32de4d862c4401ddfdeea938c8bf9a56d',
    updated_at = NOW()
WHERE username = 'livesun';

-- Opcional: reset por email em vez de username
-- UPDATE users
-- SET password_hash = 'scrypt:32768:8:1$mPJ7I2qQOPxks4U4$34b0a02b277d77397d5d91462a43f51bf90fc44e6460ce75fbc82cb2ca1caddb833f30768728ccc114e4d09a5f7be7f32de4d862c4401ddfdeea938c8bf9a56d',
--     updated_at = NOW()
-- WHERE email = 'wagner@livesun.com.br';

SELECT id, empresa_id, username, email, is_active
FROM users
WHERE username = 'livesun';
