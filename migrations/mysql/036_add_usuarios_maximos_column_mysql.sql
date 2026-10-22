-- =====================================================
-- MIGRACAO 036: Adicionar coluna usuarios_maximos (MySQL)
-- ---------------------------------------------------------
-- Regra comercial vigente: cada empresa tem um limite de usuários
-- ativos definido pelo Backoffice Comercial (coluna
-- `empresas.usuarios_maximos`, valor padrão 5, espelhando o plano
-- intermediate). Esta migration:
--   - ADD COLUMN apenas quando a coluna ainda nao existe
--     (MySQL 8.0.31 nao suporta `ADD COLUMN IF NOT EXISTS`, entao se
--     consulta o information_schema e monta o ALTER via prepared stmt).
--   - MODIFY COLUMN quando ja existe, realinhando tipo/DEFAULT ao modelo
--     src/models/__init__.py :: class Empresa.
-- A migration e IDEMPOTENTE.
--
-- EXECUCAO: conectar no banco `comercial` com role com ALTER sobre
-- `empresas` (ex.: controller_owner).
-- =====================================================

SET @col   = 'usuarios_maximos';
SET @dflt  = '5';
SET @type  = 'INTEGER DEFAULT 5 NOT NULL';
SET @pos   = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '')
              FROM information_schema.COLUMNS
              WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME   = 'empresas'
                AND COLUMN_NAME  = 'plano');
SET @exists = (SELECT COUNT(*)
              FROM information_schema.COLUMNS
              WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME   = 'empresas'
                AND COLUMN_NAME  = @col);
SET @sql = IF(@exists = 0,
    CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` ', @type, @pos),
    CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` ', @type)
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Garantir valores definidos (evita NULL em linhas pre-existentes)
UPDATE empresas SET usuarios_maximos = IFNULL(usuarios_maximos, 5) WHERE usuarios_maximos IS NULL OR usuarios_maximos < 1;

-- Verificar resultado
SELECT COLUMN_NAME, COLUMN_DEFAULT, COLUMN_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'empresas'
  AND COLUMN_NAME = 'usuarios_maximos';
