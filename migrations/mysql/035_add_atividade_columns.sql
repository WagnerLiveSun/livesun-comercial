-- =====================================================
-- MIGRACAO 035: Adicionar colunas atividade_* (MySQL)
-- ---------------------------------------------------------
-- COMPATIBILIDADE: o MySQL 8.0.31 NAO suporta a sintaxe
--   ALTER TABLE ... ADD COLUMN IF NOT EXISTS
-- (ela e exclusiva do MariaDB e o MySQL nunca a implementou).
-- Por isso esta migration consulta o information_schema e
-- monta o ALTER dinamicamente via prepared statement, executando
-- o ADD COLUMN apenas quando a coluna ainda nao existe.
--
-- A migration e IDEMPOTENTE: pode ser executada quantas vezes
-- for necessario sem falhar e sem duplicar colunas.
--
-- Para cada coluna atividade_*:
--   - se a coluna ainda NAO existe -> ADD COLUMN com o default
--     definido em src/models/__init__.py :: class Empresa
--   - se a coluna JA existe -> MODIFY COLUMN, realinhando o tipo
--     (BOOLEAN) e o DEFAULT ao mesmo modelo, sem perder dados.
--
-- COLUNAS (alinhadas com src/models/__init__.py :: class Empresa):
--   atividade_comercial   BOOLEAN DEFAULT TRUE
--   atividade_servicos    BOOLEAN DEFAULT TRUE
--   atividade_financeiro  BOOLEAN DEFAULT TRUE
--   atividade_locacao     BOOLEAN DEFAULT FALSE
--   atividade_contratos   BOOLEAN DEFAULT FALSE
--   atividade_propostas   BOOLEAN DEFAULT FALSE
--   atividade_dashboard   BOOLEAN DEFAULT TRUE
--   atividade_relatorios  BOOLEAN DEFAULT FALSE
--
-- EXECUCAO: conectar no banco `comercial` com uma role que possua
-- ALTER sobre a tabela `empresas` (ex.: controller_owner).
-- =====================================================

-- Verificar quais colunas existem atualmente
SELECT COLUMN_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'empresas'
  AND COLUMN_NAME LIKE 'atividade_%'
ORDER BY COLUMN_NAME;

-- ------------------------------------------------------------------
-- Cada bloco monta um prepared statement condicional a partir do
-- information_schema. Nao usa stored procedure (dispensa o
-- privilegio CREATE ROUTINE) nem DELIMITER, de modo que o arquivo
-- pode ser executado statement por statement por qualquer cliente
-- (mysql CLI, PyMySQL, SQLAlchemy, etc.).
-- ------------------------------------------------------------------

-- atividade_comercial
SET @col = 'atividade_comercial';
SET @aft = 'plano';
SET @dflt = 'TRUE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_servicos
SET @col = 'atividade_servicos';
SET @aft = 'atividade_comercial';
SET @dflt = 'TRUE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_financeiro
SET @col = 'atividade_financeiro';
SET @aft = 'atividade_servicos';
SET @dflt = 'TRUE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_locacao
SET @col = 'atividade_locacao';
SET @aft = 'atividade_financeiro';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_contratos
SET @col = 'atividade_contratos';
SET @aft = 'atividade_locacao';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_propostas
SET @col = 'atividade_propostas';
SET @aft = 'atividade_contratos';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_dashboard
SET @col = 'atividade_dashboard';
SET @aft = 'atividade_propostas';
SET @dflt = 'TRUE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_relatorios
SET @col = 'atividade_relatorios';
SET @aft = 'atividade_dashboard';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Normalizar valores existentes (evita NULL em colunas booleanas)
UPDATE empresas
SET
    atividade_comercial  = IFNULL(atividade_comercial, TRUE),
    atividade_servicos   = IFNULL(atividade_servicos, TRUE),
    atividade_financeiro = IFNULL(atividade_financeiro, TRUE),
    atividade_locacao    = IFNULL(atividade_locacao, FALSE),
    atividade_contratos  = IFNULL(atividade_contratos, FALSE),
    atividade_propostas  = IFNULL(atividade_propostas, FALSE),
    atividade_dashboard  = IFNULL(atividade_dashboard, TRUE),
    atividade_relatorios = IFNULL(atividade_relatorios, FALSE);

-- Verificar resultado
SELECT COLUMN_NAME, COLUMN_DEFAULT, COLUMN_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'empresas'
  AND COLUMN_NAME LIKE 'atividade_%'
ORDER BY ORDINAL_POSITION;
