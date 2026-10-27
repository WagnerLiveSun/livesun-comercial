-- Adiciona campos comerciais opcionais na tabela operacional app.entidades.
-- Executar manualmente como role autorizada para ALTER em app.entidades;
-- livesun_api é uma role de runtime e não deve executar este DDL.

BEGIN;

ALTER TABLE app.entidades
    ADD COLUMN IF NOT EXISTS contato_comercial VARCHAR(150),
    ADD COLUMN IF NOT EXISTS email_comercial VARCHAR(120);

COMMENT ON COLUMN app.entidades.contato_comercial IS
    'Nome do contato comercial da entidade cliente; opcional.';
COMMENT ON COLUMN app.entidades.email_comercial IS
    'Email comercial, distinto do email de envio de DANFS-e; opcional.';

COMMIT;

SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_schema = 'app'
  AND table_name = 'entidades'
  AND column_name IN ('contato_comercial', 'email_comercial')
ORDER BY column_name;