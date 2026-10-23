-- =====================================================================
-- MIGRACAO 037: Adicionar colunas atividade_* para o painel comercial (MySQL)
-- -------------------------------------------------------------------------
-- Adiciona as novas colunas booleanas que controlam o acesso aos módulos
-- liberados pelo Backoffice Comercial: entidades, estoque, compras,
-- pedidos, pdv, aprovação, fluxo, contas_banco, usuarios, controle_acesso.
--
-- COMPATIBILIDADE: o MySQL 8.0.31 NAO suporta ALTER TABLE ... ADD COLUMN IF
-- NOT EXISTS, entao a migration consulta information_schema e monta o ALTER
-- dinamicamente via prepared statement, executando o ADD COLUMN apenas quando
-- a coluna ainda nao existe.
--
-- A migration e IDEMPOTENTE: pode ser executada quantas vezes for necessario
-- sem falhar e sem duplicar colunas.
--
-- COLUNAS (alinhadas com src/models/__init__.py :: class Empresa):
--   atividade_entidades        BOOLEAN DEFAULT TRUE
--   atividade_estoque          BOOLEAN DEFAULT FALSE
--   atividade_compras          BOOLEAN DEFAULT FALSE
--   atividade_pedidos          BOOLEAN DEFAULT FALSE
--   atividade_pdv              BOOLEAN DEFAULT FALSE
--   atividade_aprovacao        BOOLEAN DEFAULT FALSE
--   atividade_fluxo            BOOLEAN DEFAULT TRUE
--   atividade_contas_banco     BOOLEAN DEFAULT TRUE
--   atividade_usuarios         BOOLEAN DEFAULT FALSE
--   atividade_controle_acesso  BOOLEAN DEFAULT FALSE
--
-- EXECUCAO: conectar no banco `comercial` com uma role que possua ALTER
-- sobre a tabela `empresas` (ex.: controller_owner).
-- =====================================================================

-- atividade_entidades
SET @col = 'atividade_entidades';
SET @aft = 'atividade_relatorios';
SET @dflt = 'TRUE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
-- atividade_estoque
SET @col = 'atividade_estoque';
SET @aft = 'atividade_entidades';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_compras
SET @col = 'atividade_compras';
SET @aft = 'atividade_estoque';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_pedidos
SET @col = 'atividade_pedidos';
SET @aft = 'atividade_compras';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_pdv
SET @col = 'atividade_pdv';
SET @aft = 'atividade_pedidos';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_aprovacao
SET @col = 'atividade_aprovacao';
SET @aft = 'atividade_pdv';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_fluxo
SET @col = 'atividade_fluxo';
SET @aft = 'atividade_aprovacao';
SET @dflt = 'TRUE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_contas_banco
SET @col = 'atividade_contas_banco';
SET @aft = 'atividade_fluxo';
SET @dflt = 'TRUE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_usuarios
SET @col = 'atividade_usuarios';
SET @aft = 'atividade_contas_banco';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- atividade_controle_acesso
SET @col = 'atividade_controle_acesso';
SET @aft = 'atividade_usuarios';
SET @dflt = 'FALSE';
SET @pos = (SELECT COALESCE(CONCAT(' AFTER `', COLUMN_NAME, '`'), '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@aft);
SET @sql = (SELECT IF(COUNT(*) = 0, CONCAT('ALTER TABLE `empresas` ADD COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt, @pos), CONCAT('ALTER TABLE `empresas` MODIFY COLUMN `', @col, '` BOOLEAN DEFAULT ', @dflt)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='empresas' AND COLUMN_NAME=@col);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Normalizar valores existentes (evita NULL em colunas booleanas)
UPDATE empresas
SET
    atividade_entidades        = IFNULL(atividade_entidades, TRUE),
    atividade_estoque          = IFNULL(atividade_estoque, FALSE),
    atividade_compras          = IFNULL(atividade_compras, FALSE),
    atividade_pedidos          = IFNULL(atividade_pedidos, FALSE),
    atividade_pdv              = IFNULL(atividade_pdv, FALSE),
    atividade_aprovacao        = IFNULL(atividade_aprovacao, FALSE),
    atividade_fluxo            = IFNULL(atividade_fluxo, TRUE),
    atividade_contas_banco     = IFNULL(atividade_contas_banco, TRUE),
    atividade_usuarios         = IFNULL(atividade_usuarios, FALSE),
    atividade_controle_acesso  = IFNULL(atividade_controle_acesso, FALSE);

-- Verificar resultado
SELECT COLUMN_NAME, COLUMN_DEFAULT, COLUMN_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'empresas'
  AND COLUMN_NAME LIKE 'atividade_%'
ORDER BY ORDINAL_POSITION;
