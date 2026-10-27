-- Adiciona campos comerciais opcionais na tabela entidades.
-- Compatível com versões MySQL sem suporte a ADD COLUMN IF NOT EXISTS.
-- Script para aplicação manual: não é executado pela aplicação.

SET @schema_atual = DATABASE();

SET @existe_contato_comercial = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @schema_atual
      AND TABLE_NAME = 'entidades'
      AND COLUMN_NAME = 'contato_comercial'
);
SET @sql_contato_comercial = IF(
    @existe_contato_comercial = 0,
    'ALTER TABLE `entidades` ADD COLUMN `contato_comercial` VARCHAR(150) NULL',
    'SELECT ''Coluna contato_comercial já existe'' AS resultado'
);
PREPARE stmt_contato_comercial FROM @sql_contato_comercial;
EXECUTE stmt_contato_comercial;
DEALLOCATE PREPARE stmt_contato_comercial;

SET @existe_email_comercial = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @schema_atual
      AND TABLE_NAME = 'entidades'
      AND COLUMN_NAME = 'email_comercial'
);
SET @sql_email_comercial = IF(
    @existe_email_comercial = 0,
    'ALTER TABLE `entidades` ADD COLUMN `email_comercial` VARCHAR(120) NULL',
    'SELECT ''Coluna email_comercial já existe'' AS resultado'
);
PREPARE stmt_email_comercial FROM @sql_email_comercial;
EXECUTE stmt_email_comercial;
DEALLOCATE PREPARE stmt_email_comercial;

SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'entidades'
  AND COLUMN_NAME IN ('contato_comercial', 'email_comercial')
ORDER BY COLUMN_NAME;