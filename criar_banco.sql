-- Script SQL para criar o banco de dados LiveSun Financeiro
-- MySQL 5.7+ / MariaDB 10.3+

-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS livesun_financeiro 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Usar o banco de dados
USE livesun_financeiro;

-- Criar usuário (opcional)
-- CREATE USER 'livesun'@'localhost' IDENTIFIED BY 'livesun2026';
-- GRANT ALL PRIVILEGES ON livesun_financeiro.* TO 'livesun'@'localhost';
-- FLUSH PRIVILEGES;

-- As tabelas serão criadas automaticamente pelo SQLAlchemy
-- ao executar a aplicação pela primeira vez
