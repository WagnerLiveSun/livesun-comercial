-- MySQL dump 10.13  Distrib 8.0.31, for Win64 (x86_64)
--
-- Host: 195.35.61.111    Database: u951548013_gfinanceiro
-- ------------------------------------------------------
-- Server version	11.8.8-MariaDB-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `comissoes`
--

DROP TABLE IF EXISTS `comissoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comissoes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `id_apuracao` int(11) NOT NULL,
  `lancamento_id` int(11) NOT NULL,
  `entidade_cliente_id` int(11) NOT NULL,
  `entidade_vendedor_id` int(11) NOT NULL,
  `dt_lancamento` date NOT NULL,
  `dt_vencimento` date NOT NULL,
  `dt_pagamento_recebimento` date NOT NULL,
  `vl_nota` decimal(15,2) NOT NULL,
  `vl_imposto` decimal(15,2) DEFAULT 0.00,
  `vl_outros_custos` decimal(15,2) DEFAULT 0.00,
  `vl_repasse` decimal(15,2) DEFAULT 0.00,
  `vl_liquido` decimal(15,2) NOT NULL,
  `aliquota_aplicada` decimal(5,2) NOT NULL,
  `vl_comissao` decimal(15,2) NOT NULL,
  `situacao` varchar(20) DEFAULT 'ativo',
  `criado_em` datetime DEFAULT current_timestamp(),
  `atualizado_em` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_comissao_unica` (`lancamento_id`,`entidade_cliente_id`,`entidade_vendedor_id`,`situacao`),
  KEY `idx_comissao_empresa` (`empresa_id`),
  KEY `idx_comissao_apuracao` (`empresa_id`,`id_apuracao`),
  KEY `idx_comissao_datas` (`dt_pagamento_recebimento`),
  KEY `idx_comissao_lancamento` (`lancamento_id`),
  KEY `idx_comissao_cliente` (`entidade_cliente_id`),
  KEY `idx_comissao_vendedor` (`entidade_vendedor_id`),
  CONSTRAINT `comissoes_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  CONSTRAINT `comissoes_ibfk_2` FOREIGN KEY (`lancamento_id`) REFERENCES `lancamentos` (`id`),
  CONSTRAINT `comissoes_ibfk_3` FOREIGN KEY (`entidade_cliente_id`) REFERENCES `entidades` (`id`),
  CONSTRAINT `comissoes_ibfk_4` FOREIGN KEY (`entidade_vendedor_id`) REFERENCES `entidades` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comissoes`
--

LOCK TABLES `comissoes` WRITE;
/*!40000 ALTER TABLE `comissoes` DISABLE KEYS */;
INSERT INTO `comissoes` VALUES (1,1,1,2,7,23,'2026-03-11','2026-03-01','2026-03-11',175.00,11.69,0.00,55.00,108.31,25.00,27.08,'ativo','2026-03-31 19:53:38','2026-03-31 19:53:38'),(2,1,1,3,8,23,'2026-03-11','2026-03-01','2026-03-11',409.68,26.75,0.00,194.00,188.93,25.00,47.23,'ativo','2026-03-31 19:53:38','2026-03-31 19:53:38'),(3,1,1,4,5,23,'2026-03-11','2026-03-05','2026-03-11',357.70,23.38,0.00,65.50,268.82,25.00,67.20,'ativo','2026-03-31 19:53:38','2026-03-31 19:53:38'),(4,1,1,5,4,23,'2026-03-12','2026-03-10','2026-03-12',317.00,21.17,0.00,137.00,158.83,25.00,39.71,'ativo','2026-03-31 19:53:39','2026-03-31 19:53:39'),(5,1,1,6,6,23,'2026-03-05','2026-03-05','2026-03-05',69.21,4.62,0.00,0.00,64.59,25.00,16.15,'ativo','2026-03-31 19:53:39','2026-03-31 19:53:39'),(6,1,1,7,26,23,'2026-03-10','2026-03-10','2026-03-10',337.14,22.52,0.00,0.00,314.62,25.00,78.66,'ativo','2026-03-31 19:53:39','2026-03-31 19:53:39'),(7,1,1,11,11,23,'2026-03-02','2026-03-09','2026-03-09',5500.00,367.40,0.00,517.00,4615.60,10.00,461.56,'ativo','2026-03-31 19:53:40','2026-03-31 19:53:40'),(8,1,1,18,10,23,'2026-02-02','2026-03-02','2026-03-02',5585.11,373.08,0.00,0.00,5212.03,10.00,521.20,'ativo','2026-03-31 19:53:40','2026-03-31 19:53:40'),(9,1,1,41,3,23,'2026-03-20','2026-03-27','2026-03-20',308.96,20.64,0.00,166.85,121.47,25.00,30.37,'ativo','2026-03-31 19:53:41','2026-03-31 19:53:41'),(16,1,4,51,10,23,'2026-04-01','2026-05-01','2026-05-06',5585.11,335.11,0.00,0.00,5250.00,10.00,525.00,'ativo','2026-06-02 17:42:57','2026-06-02 17:42:57'),(17,1,4,86,11,23,'2026-05-01','2026-05-01','2026-05-08',5500.00,330.00,0.00,517.00,4653.00,10.00,465.30,'ativo','2026-06-02 17:42:58','2026-06-02 17:42:58'),(18,1,4,87,37,28,'2026-05-01','2026-05-01','2026-05-05',2405.83,360.87,0.00,0.00,2044.96,35.00,715.74,'ativo','2026-06-02 17:42:58','2026-06-02 17:42:58'),(19,1,4,94,6,23,'2026-05-08','2026-05-08','2026-05-07',69.21,4.15,0.00,0.00,65.06,25.00,16.26,'ativo','2026-06-02 17:42:58','2026-06-02 17:42:58'),(20,1,4,95,7,23,'2026-05-12','2026-05-12','2026-05-12',175.00,10.50,0.00,55.00,109.50,25.00,27.38,'ativo','2026-06-02 17:42:59','2026-06-02 17:42:59'),(21,1,4,96,8,23,'2026-05-12','2026-05-12','2026-05-12',400.48,24.03,0.00,194.00,182.45,25.00,45.61,'ativo','2026-06-02 17:42:59','2026-06-02 17:42:59'),(22,1,4,97,26,23,'2026-05-12','2026-05-12','2026-05-11',337.14,20.23,0.00,0.00,316.91,25.00,79.23,'ativo','2026-06-02 17:42:59','2026-06-02 17:42:59'),(23,1,4,102,4,23,'2026-05-13','2026-05-13','2026-05-13',333.00,19.98,0.00,137.00,176.02,25.00,44.00,'ativo','2026-06-02 17:43:00','2026-06-02 17:43:00'),(24,1,4,107,3,23,'2026-05-21','2026-05-21','2026-05-21',308.96,18.54,0.00,166.85,123.57,25.00,30.89,'ativo','2026-06-02 17:43:01','2026-06-02 17:43:01'),(33,1,6,88,10,23,'2026-05-01','2026-06-01','2026-06-01',5585.11,335.11,0.00,0.00,5250.00,10.00,525.00,'ativo','2026-07-06 18:58:36','2026-07-06 18:58:36'),(34,1,6,112,11,23,'2026-06-02','2026-06-10','2026-06-08',5500.00,330.00,0.00,517.00,4653.00,10.00,465.30,'ativo','2026-07-06 18:58:36','2026-07-06 18:58:36'),(35,1,6,114,6,23,'2026-06-05','2026-06-05','2026-06-05',69.21,4.15,0.00,0.00,65.06,25.00,16.26,'ativo','2026-07-06 18:58:37','2026-07-06 18:58:37'),(36,1,6,117,8,23,'2026-06-08','2026-06-08','2026-06-05',400.48,24.54,0.00,194.00,181.94,25.00,45.48,'ativo','2026-07-06 18:58:37','2026-07-06 18:58:37'),(37,1,6,118,7,23,'2026-06-08','2026-06-08','2026-06-05',175.00,10.72,0.00,55.00,109.28,25.00,27.32,'ativo','2026-07-06 18:58:37','2026-07-06 18:58:37'),(38,1,6,128,26,23,'2026-06-12','2026-06-12','2026-06-11',337.14,20.63,0.00,0.00,316.51,25.00,79.13,'ativo','2026-07-06 18:58:38','2026-07-06 18:58:38'),(39,1,6,129,4,23,'2026-06-12','2026-06-12','2026-06-12',333.00,19.98,0.00,137.00,176.02,25.00,44.00,'ativo','2026-07-06 18:58:38','2026-07-06 18:58:38'),(40,1,6,132,3,23,'2026-06-18','2026-06-18','2026-06-18',308.96,20.63,0.00,166.85,121.48,25.00,30.37,'ativo','2026-07-06 18:58:39','2026-07-06 18:58:39'),(48,1,8,111,10,23,'2026-06-01','2026-07-01','2026-07-01',5585.11,335.10,0.00,0.00,5250.01,10.00,525.00,'ativo','2026-08-07 19:11:23','2026-08-07 19:11:23'),(49,1,8,127,10,23,'2026-06-12','2026-06-12','2026-07-12',1396.00,83.76,0.00,0.00,1312.24,10.00,131.22,'ativo','2026-08-07 19:11:23','2026-08-07 19:11:23'),(50,1,8,141,6,23,'2026-07-07','2026-07-07','2026-07-07',69.00,4.14,0.00,0.00,64.86,25.00,16.22,'ativo','2026-08-07 19:11:23','2026-08-07 19:11:23'),(51,1,8,151,26,23,'2026-07-14','2026-07-14','2026-07-13',337.14,20.23,0.00,0.00,316.91,25.00,79.23,'ativo','2026-08-07 19:11:24','2026-08-07 19:11:24'),(52,1,8,152,4,23,'2026-07-14','2026-07-14','2026-07-13',333.00,19.98,0.00,137.00,176.02,25.00,44.00,'ativo','2026-08-07 19:11:24','2026-08-07 19:11:24'),(53,1,8,154,7,23,'2026-07-13','2026-07-13','2026-07-10',575.48,34.53,0.00,55.00,485.95,25.00,121.49,'ativo','2026-08-07 19:11:24','2026-08-07 19:11:24'),(54,1,8,159,3,23,'2026-07-23','2026-07-23','2026-07-22',308.96,18.54,0.00,166.85,123.57,25.00,30.89,'ativo','2026-08-07 19:11:25','2026-08-07 19:11:25'),(55,1,9,138,10,23,'2026-07-01','2026-07-01','2026-08-01',5585.11,335.11,0.00,0.00,5250.00,10.00,525.00,'ativo','2026-08-27 19:44:06','2026-08-27 19:44:06'),(56,1,9,165,11,23,'2026-08-03','2026-08-03','2026-08-03',5500.00,330.00,0.00,517.00,4653.00,10.00,465.30,'ativo','2026-08-27 19:44:06','2026-08-27 19:44:06'),(57,1,9,166,11,23,'2026-08-03','2026-08-03','2026-08-05',900.00,54.00,0.00,517.00,329.00,10.00,32.90,'ativo','2026-08-27 19:44:06','2026-08-27 19:44:06'),(58,1,9,173,8,23,'2026-08-06','2026-08-06','2026-08-06',400.48,24.03,0.00,194.00,182.45,25.00,45.61,'ativo','2026-08-27 19:44:07','2026-08-27 19:44:07'),(59,1,9,174,7,23,'2026-08-06','2026-08-06','2026-08-06',175.00,10.50,0.00,55.00,109.50,25.00,27.38,'ativo','2026-08-27 19:44:07','2026-08-27 19:44:07'),(60,1,9,175,6,23,'2026-08-07','2026-08-07','2026-08-06',69.21,4.15,0.00,0.00,65.06,25.00,16.26,'ativo','2026-08-27 19:44:08','2026-08-27 19:44:08'),(61,1,9,181,26,23,'2026-08-12','2026-08-12','2026-08-12',337.14,20.23,0.00,0.00,316.91,25.00,79.23,'ativo','2026-08-27 19:44:08','2026-08-27 19:44:08'),(62,1,9,182,4,23,'2026-08-12','2026-08-12','2026-08-12',333.00,19.98,0.00,137.00,176.02,25.00,44.00,'ativo','2026-08-27 19:44:09','2026-08-27 19:44:09'),(63,1,9,188,3,23,'2026-08-24','2026-08-24','2026-08-24',308.96,18.54,0.00,166.85,123.57,25.00,30.89,'ativo','2026-08-27 19:44:09','2026-08-27 19:44:09');
/*!40000 ALTER TABLE `comissoes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contas_banco`
--

DROP TABLE IF EXISTS `contas_banco`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contas_banco` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `nome` varchar(150) NOT NULL,
  `banco` varchar(50) NOT NULL,
  `agencia` varchar(10) NOT NULL,
  `numero_conta` varchar(20) NOT NULL,
  `dv` varchar(2) DEFAULT NULL,
  `tipo` varchar(20) DEFAULT NULL,
  `fluxo_conta_id` int(11) DEFAULT NULL,
  `saldo_inicial` decimal(15,2) DEFAULT 0.00,
  `ativo` tinyint(1) DEFAULT 1,
  `criado_em` datetime DEFAULT current_timestamp(),
  `atualizado_em` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `is_principal` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `empresa_id` (`empresa_id`),
  KEY `fluxo_conta_id` (`fluxo_conta_id`),
  KEY `idx_contas_banco_is_principal` (`is_principal`),
  CONSTRAINT `contas_banco_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  CONSTRAINT `contas_banco_ibfk_2` FOREIGN KEY (`fluxo_conta_id`) REFERENCES `fluxo_contas_modelo` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contas_banco`
--

LOCK TABLES `contas_banco` WRITE;
/*!40000 ALTER TABLE `contas_banco` DISABLE KEYS */;
INSERT INTO `contas_banco` VALUES (1,1,'Inter Empresa','Inter','0001','7201890','9','Conta corrente',6,9570.64,1,'2026-02-26 20:32:57','2026-03-25 19:58:16',1);
/*!40000 ALTER TABLE `contas_banco` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `empresas`
--

DROP TABLE IF EXISTS `empresas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `empresas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(150) NOT NULL,
  `cnpj` varchar(18) DEFAULT NULL,
  `criado_em` datetime DEFAULT current_timestamp(),
  `atualizado_em` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `nome` (`nome`),
  UNIQUE KEY `cnpj` (`cnpj`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `empresas`
--

LOCK TABLES `empresas` WRITE;
/*!40000 ALTER TABLE `empresas` DISABLE KEYS */;
INSERT INTO `empresas` VALUES (1,'LiveSun','27907386000176','2026-02-26 19:44:24','2026-02-26 19:44:24'),(2,'Empresa Padrão','00000000000000','2026-02-26 19:50:19','2026-03-10 20:02:15'),(4,'Teste','00941812766','2026-03-10 20:42:27','2026-03-10 20:42:27');
/*!40000 ALTER TABLE `empresas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entidades`
--

DROP TABLE IF EXISTS `entidades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `entidades` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `tipo` varchar(1) NOT NULL,
  `cnpj_cpf` varchar(18) NOT NULL,
  `inscricao_estadual` varchar(20) DEFAULT NULL,
  `inscricao_municipal` varchar(20) DEFAULT NULL,
  `nome` varchar(150) NOT NULL,
  `nome_fantasia` varchar(150) DEFAULT NULL,
  `endereco_rua` varchar(150) DEFAULT NULL,
  `endereco_numero` varchar(10) DEFAULT NULL,
  `endereco_bairro` varchar(100) DEFAULT NULL,
  `endereco_cidade` varchar(100) DEFAULT NULL,
  `endereco_uf` varchar(2) DEFAULT NULL,
  `endereco_cep` varchar(8) DEFAULT NULL,
  `telefone` varchar(20) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `contrato_produto` text DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT 1,
  `criado_em` datetime DEFAULT current_timestamp(),
  `atualizado_em` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `aliquota_comissao_especifica` decimal(5,2) DEFAULT NULL,
  `percentual_repasse` decimal(5,2) DEFAULT 0.00,
  `entidade_vendedor_padrao_id` int(11) DEFAULT NULL,
  `valor_repasse` decimal(10,2) DEFAULT 0.00,
  `fluxo_conta_id` int(11) DEFAULT NULL,
  `vendedor_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `cnpj_cpf` (`cnpj_cpf`),
  KEY `idx_entidade_empresa_tipo` (`empresa_id`,`tipo`),
  KEY `idx_entidades_cnpj_cpf` (`cnpj_cpf`),
  KEY `fk_entidades_fluxo_conta` (`fluxo_conta_id`),
  CONSTRAINT `entidades_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  CONSTRAINT `fk_entidades_fluxo_conta` FOREIGN KEY (`fluxo_conta_id`) REFERENCES `fluxo_contas_modelo` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entidades`
--

LOCK TABLES `entidades` WRITE;
/*!40000 ALTER TABLE `entidades` DISABLE KEYS */;
INSERT INTO `entidades` VALUES (1,1,'L','00941812766','','','Wagner de Carlos','','','','','','','','','wagmer.carlos@Livesun.com.br','Colaborador',1,'2026-02-26 20:08:16','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(2,1,'F','01436204798','','','Nelci Vallotto','','','','','','','','','nelci.vallotto@livesun.com.br','Colaborador fornecedor',1,'2026-02-26 20:09:07','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(3,1,'C','06871247000160','','','Arte da Terra Fantasias Ltda','Arte da Terra','','','','','','','','','',1,'2026-03-10 19:05:32','2026-03-31 19:50:54',NULL,0.00,23,166.85,6,23),(4,1,'C','54349011000100','','','Bia Brand Roupas Ltda','Biaritz','','','','','','','','','',1,'2026-03-10 19:07:36','2026-03-31 19:52:43',NULL,0.00,23,137.00,6,23),(5,1,'C','57823777000173','','','Decente Transportes Ltda','Decente Transportes','','','','','','','','','',1,'2026-03-10 19:14:31','2026-03-31 19:52:43',NULL,0.00,23,65.50,6,23),(6,1,'C','03430981000103','','','Mega Star Comércio e Serviços Ltda','Mega Star','','','','','','','','','',1,'2026-03-10 19:16:47','2026-03-31 19:52:43',NULL,0.00,23,0.00,6,23),(7,1,'C','35159867000179','','','Zé Palito industria de Gelados Comestiveis Ltda','Zé Palito fabrica','','','','','','','','','',1,'2026-03-10 19:18:48','2026-03-31 19:52:43',NULL,0.00,23,55.00,6,23),(8,1,'C','49035013000195','','','Zé Palito Comércio de Gelados Comestiveis Ltda','Zé Palito Loja','','','','','','','','','',1,'2026-03-10 19:21:38','2026-03-31 19:52:43',NULL,0.00,23,194.00,6,23),(9,1,'F','48628778500','','','Silvio Fernando Viana Nogueira','Aluguel Stella','','','','','','','','','Aluguel',1,'2026-03-10 19:26:08','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(10,1,'C','00624964000100','','','CIGAS - Companhia de Gás do Amazonas','Cigas','','','','','','','','','',1,'2026-03-10 20:11:42','2026-03-31 19:52:43',10.00,0.00,23,0.00,6,23),(11,1,'C','02750988000131','','','Termonorte ','Termonorte','','','','','','','','','',1,'2026-03-10 20:12:36','2026-03-31 19:52:43',10.00,0.00,23,517.00,6,23),(12,1,'F','00000000000000','','010218000496001','Prefeitura Municipal de Simoes Filho','Prefeitura Simões Filho','','','','','','','','','',1,'2026-03-11 17:32:01','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(14,1,'F','15139629000194','','','Coelba - Neoenergia','Coelba','','','','','','','','','',1,'2026-03-11 17:39:25','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(16,1,'F','12605982000124','','','Hiper Software S/A','Hiper','','','','','','','','','',1,'2026-03-11 17:40:32','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(17,1,'F','43965081000177','','','Associação dos Moradores do Fazenda Real Residence','Associaçao Fazenda Real','','','','','','','','','',1,'2026-03-11 17:46:16','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(18,1,'F','01685053000156','','','Sulamerica Companhia de Seguros','Sulamerica Odonto','','','','','','','','','',1,'2026-03-11 17:54:43','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(19,1,'F','40432544000147','','','Claro Brasil','Claro','','','','','','','','','',1,'2026-03-11 17:56:56','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(20,1,'F','02558157000162','','','Telefônica Brasil S/A','Vivo','','','','','','','','','',1,'2026-03-11 17:58:06','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(21,1,'F','13504675000110','','','Empresa Baiana de Aguas e Saneamento S/A','Embasa','','','','','','','','','',1,'2026-03-11 18:01:18','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(22,1,'F','02351877001124','','','Bling Sistemas','Bling','','','','','','','','','',1,'2026-03-11 18:21:14','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(23,1,'V','12211922724','','','Felipe Wagner Gomes de Carlos','Felipe','','','','','','','','','',1,'2026-03-11 18:26:18','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(24,1,'F','00394460005887','','','Receita Federal - Impostos','DAS Simples Nacional','','','','','','','','','',1,'2026-03-11 18:48:34','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(25,1,'F','29979036000140','','','Instituto Nacional Seguridade Social','INSS','','','','','','','','','',1,'2026-03-13 18:00:01','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(26,1,'C','01605168000274','','','Rita de Cassia Lopes Iberti','Casa da Baiana','','','','','','','','','',1,'2026-03-13 18:58:32','2026-03-31 19:52:43',NULL,0.00,23,0.00,6,23),(27,1,'F','00416968000101','','','Banco Inter -Cartao Empresarial','Cartão Empresarial','','','','','','','','','',1,'2026-03-13 19:32:37','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(28,1,'V','04601365422','','','Magno Almeida Ramos','Magno','','','','','','','','','',1,'2026-03-16 19:17:15','2026-05-05 14:32:20',NULL,0.00,NULL,0.00,NULL,23),(31,1,'F','00000000066','','','Lucas Abelar','Tv Box','','','','','','','','','',1,'2026-03-16 20:56:40','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(32,1,'F','86329834580','','','Davi Wagner Vallotto de Carlos','Davi','','','','','','','','','Filhote',1,'2026-03-19 19:43:12','2026-03-31 19:52:43',NULL,0.00,NULL,0.00,NULL,23),(33,1,'F','00000000000002',NULL,NULL,'Posto Bike Stella Mares',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-04-03 18:57:47','2026-04-03 18:57:47',NULL,0.00,NULL,0.00,NULL,NULL),(34,1,'F','00000000000003',NULL,NULL,'KFC Lanches',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-04-03 18:58:59','2026-04-03 18:58:59',NULL,0.00,NULL,0.00,NULL,NULL),(35,1,'F','00000000000004',NULL,NULL,'Estacionamento Shopping',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-04-03 19:00:21','2026-04-03 19:00:21',NULL,0.00,NULL,0.00,NULL,NULL),(36,1,'F','00000000000005',NULL,NULL,'Redemix Supermercados Ltda',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-04-03 19:01:11','2026-04-03 19:01:11',NULL,0.00,NULL,0.00,NULL,NULL),(37,1,'C','24413094000199',NULL,NULL,'Aplex Distribuidora de Produtos de Tecnologia Eireli - ME',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-05-01 15:07:06','2026-05-05 14:34:06',35.00,0.00,NULL,0.00,3,28),(38,1,'C','20215683000101',NULL,NULL,'CLICK DIGITAL SOLUTIONS LTDA',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-06-08 21:19:14','2026-06-12 18:12:06',NULL,0.00,NULL,0.00,6,NULL),(39,1,'F','00000000000007',NULL,NULL,'Casa do Frango',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-06-15 18:29:19','2026-06-15 18:29:19',NULL,0.00,NULL,0.00,NULL,NULL),(40,1,'C','27907386000176',NULL,NULL,'Tomador 27907386000176',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,'2026-07-12 21:31:41','2026-07-12 21:34:37',NULL,0.00,NULL,0.00,3,NULL),(41,1,'C','00000000000008',NULL,NULL,'Hiper Ideal Supermercados Ltda',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-07-27 17:55:23','2026-07-27 17:55:23',NULL,0.00,NULL,0.00,NULL,NULL),(42,1,'F','00000000000009',NULL,NULL,'Total Supermercados Ltda',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-07-27 17:56:35','2026-07-27 17:56:35',NULL,0.00,NULL,0.00,NULL,NULL),(43,1,'F','27119334000135',NULL,NULL,'Qipu Contabilidade',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-07-28 18:32:41','2026-07-28 18:32:41',NULL,0.00,NULL,0.00,NULL,NULL),(44,1,'F','14336330000167',NULL,NULL,'VALE SAUDE ADM DE CARTOES LTDA',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2026-09-07 13:49:01','2026-09-07 13:49:30',NULL,0.00,NULL,0.00,118,NULL);
/*!40000 ALTER TABLE `entidades` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fluxo_caixa_previsto`
--

DROP TABLE IF EXISTS `fluxo_caixa_previsto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fluxo_caixa_previsto` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `data` date NOT NULL,
  `fluxo_conta_id` int(11) NOT NULL,
  `conta_banco_id` int(11) NOT NULL,
  `saldo_anterior` decimal(15,2) DEFAULT 0.00,
  `valor_previsto_pago` decimal(15,2) DEFAULT 0.00,
  `valor_previsto_recebido` decimal(15,2) DEFAULT 0.00,
  `saldo_previsto` decimal(15,2) DEFAULT 0.00,
  `criado_em` datetime DEFAULT current_timestamp(),
  `atualizado_em` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `empresa_id` (`empresa_id`),
  KEY `fluxo_conta_id` (`fluxo_conta_id`),
  KEY `conta_banco_id` (`conta_banco_id`),
  CONSTRAINT `fluxo_caixa_previsto_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  CONSTRAINT `fluxo_caixa_previsto_ibfk_2` FOREIGN KEY (`fluxo_conta_id`) REFERENCES `fluxo_contas_modelo` (`id`),
  CONSTRAINT `fluxo_caixa_previsto_ibfk_3` FOREIGN KEY (`conta_banco_id`) REFERENCES `contas_banco` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=338 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fluxo_caixa_previsto`
--

LOCK TABLES `fluxo_caixa_previsto` WRITE;
/*!40000 ALTER TABLE `fluxo_caixa_previsto` DISABLE KEYS */;
INSERT INTO `fluxo_caixa_previsto` VALUES (337,1,'2026-09-02',6,1,9570.64,0.00,17570.22,27140.86,'2026-09-07 13:52:24','2026-09-07 13:52:24');
/*!40000 ALTER TABLE `fluxo_caixa_previsto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fluxo_caixa_realizado`
--

DROP TABLE IF EXISTS `fluxo_caixa_realizado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fluxo_caixa_realizado` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `data` date NOT NULL,
  `fluxo_conta_id` int(11) NOT NULL,
  `conta_banco_id` int(11) NOT NULL,
  `saldo_anterior` decimal(15,2) DEFAULT 0.00,
  `valor_pago` decimal(15,2) DEFAULT 0.00,
  `valor_recebido` decimal(15,2) DEFAULT 0.00,
  `saldo_atual` decimal(15,2) DEFAULT 0.00,
  `criado_em` datetime DEFAULT current_timestamp(),
  `atualizado_em` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `empresa_id` (`empresa_id`),
  KEY `fluxo_conta_id` (`fluxo_conta_id`),
  KEY `conta_banco_id` (`conta_banco_id`),
  CONSTRAINT `fluxo_caixa_realizado_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  CONSTRAINT `fluxo_caixa_realizado_ibfk_2` FOREIGN KEY (`fluxo_conta_id`) REFERENCES `fluxo_contas_modelo` (`id`),
  CONSTRAINT `fluxo_caixa_realizado_ibfk_3` FOREIGN KEY (`conta_banco_id`) REFERENCES `contas_banco` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4594 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fluxo_caixa_realizado`
--

LOCK TABLES `fluxo_caixa_realizado` WRITE;
/*!40000 ALTER TABLE `fluxo_caixa_realizado` DISABLE KEYS */;
INSERT INTO `fluxo_caixa_realizado` VALUES (4568,1,'2026-08-24',6,1,9570.64,0.00,85496.08,95066.72,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4569,1,'2026-08-25',112,1,9570.64,25732.64,0.00,-16162.00,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4570,1,'2026-08-07',27,1,9570.64,17586.04,0.00,-8015.40,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4571,1,'2026-07-27',36,1,9570.64,11038.00,0.00,-1467.36,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4572,1,'2026-08-20',31,1,9570.64,7003.49,0.00,2567.15,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4573,1,'2026-08-20',26,1,9570.64,2139.72,0.00,7430.92,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4574,1,'2026-06-05',20,1,9570.64,12800.00,0.00,-3229.36,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4575,1,'2026-08-01',113,1,9570.64,626.00,0.00,8944.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4576,1,'2026-03-16',23,1,9570.64,173.00,0.00,9397.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4577,1,'2026-05-27',22,1,9570.64,519.00,0.00,9051.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4578,1,'2026-03-20',114,1,9570.64,87.00,0.00,9483.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4579,1,'2026-08-07',29,1,9570.64,3887.34,0.00,5683.30,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4580,1,'2026-06-03',21,1,9570.64,436.97,0.00,9133.67,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4581,1,'2026-03-09',115,1,9570.64,176.00,0.00,9394.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4582,1,'2026-03-09',116,1,9570.64,30.00,0.00,9540.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4583,1,'2026-08-17',15,1,9570.64,1520.00,0.00,8050.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4584,1,'2026-05-04',37,1,9570.64,1834.00,0.00,7736.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4585,1,'2026-08-03',16,1,9570.64,459.18,0.00,9111.46,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4586,1,'2026-08-05',117,1,9570.64,802.40,0.00,8768.24,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4587,1,'2026-05-05',3,1,9570.64,0.00,2405.83,11976.47,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4588,1,'2026-06-08',35,1,9570.64,1348.00,0.00,8222.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4589,1,'2026-07-03',32,1,9570.64,4495.00,0.00,5075.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4590,1,'2026-07-15',17,1,9570.64,194.00,0.00,9376.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4591,1,'2026-08-03',34,1,9570.64,6.40,0.00,9564.24,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4592,1,'2026-08-04',28,1,9570.64,4533.00,0.00,5037.64,'2026-09-07 13:52:24','2026-09-07 13:52:24'),(4593,1,'2026-09-07',118,1,9570.64,31.80,0.00,9538.84,'2026-09-07 13:52:24','2026-09-07 13:52:24');
/*!40000 ALTER TABLE `fluxo_caixa_realizado` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fluxo_contas_modelo`
--

DROP TABLE IF EXISTS `fluxo_contas_modelo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fluxo_contas_modelo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `codigo` varchar(20) NOT NULL,
  `descricao` varchar(200) NOT NULL,
  `tipo` varchar(1) NOT NULL,
  `mascara` varchar(50) DEFAULT NULL,
  `nivel_sintetico` int(11) DEFAULT NULL,
  `nivel_analitico` int(11) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT 1,
  `criado_em` datetime DEFAULT current_timestamp(),
  `atualizado_em` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_codigo_empresa` (`empresa_id`,`codigo`),
  CONSTRAINT `fluxo_contas_modelo_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=119 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fluxo_contas_modelo`
--

LOCK TABLES `fluxo_contas_modelo` WRITE;
/*!40000 ALTER TABLE `fluxo_contas_modelo` DISABLE KEYS */;
INSERT INTO `fluxo_contas_modelo` VALUES (1,1,'1','Entradas de Caixa','R',NULL,1,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(2,1,'1.1','Receitas Operacionais','R',NULL,2,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(3,1,'1.1.1','Vendas à vista','R',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(4,1,'1.1.2','Vendas cartão crédito','R',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(5,1,'1.1.3','Vendas cartão débito','R',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(6,1,'1.1.4','Recebimento mensalidades/serviços','R',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(7,1,'1.2','Receitas Financeiras','R',NULL,2,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(8,1,'1.2.1','Juros recebidos','R',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(9,1,'1.2.2','Descontos obtidos','R',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(10,1,'1.3','Outras Entradas','R',NULL,2,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(11,1,'1.3.1','Empréstimos recebidos','R',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(12,1,'1.3.2','Aporte de sócios','R',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(13,1,'1.3.3','Reembolsos diversos','R',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(14,1,'2','Saídas de Caixa','P',NULL,1,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(15,1,'2.1','Custos Operacionais','P',NULL,2,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(16,1,'2.1.1','Compra de mercadorias','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(17,1,'2.1.2','Matéria-prima/insumos','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(18,1,'2.1.3','Fretes sobre compras','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(19,1,'2.2','Despesas Fixas','P',NULL,2,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(20,1,'2.2.1','Aluguel','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(21,1,'2.2.2','Energia elétrica','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(22,1,'2.2.3','Água','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(23,1,'2.2.4','Internet e telefone','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(24,1,'2.3','Despesas com Pessoal','P',NULL,2,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(25,1,'2.3.1','Salários','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(26,1,'2.3.2','Encargos (INSS, FGTS)','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(27,1,'2.3.3','Pró-labore','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(28,1,'2.4','Despesas Variáveis','P',NULL,2,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(29,1,'2.4.1','Comissões sobre vendas','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(30,1,'2.4.2','Taxas de cartão/maquininha','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(31,1,'2.4.3','Impostos sobre vendas','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(32,1,'2.5','Despesas Financeiras','P',NULL,2,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(33,1,'2.5.1','Juros e multas pagas','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(34,1,'2.5.2','Tarifas bancárias','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(35,1,'2.6','Outras Saídas','P',NULL,2,NULL,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(36,1,'2.6.1','Distribuição de lucros','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(37,1,'2.6.2','Adiantamentos a sócios','P',NULL,3,1,1,'2026-02-26 19:44:24','2026-02-26 19:44:24'),(75,4,'1','Entradas de Caixa','R',NULL,1,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(76,4,'1.1','Receitas Operacionais','R',NULL,2,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(77,4,'1.1.1','Vendas à vista','R',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(78,4,'1.1.2','Vendas cartão crédito','R',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(79,4,'1.1.3','Vendas cartão débito','R',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(80,4,'1.1.4','Recebimento mensalidades/serviços','R',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(81,4,'1.2','Receitas Financeiras','R',NULL,2,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(82,4,'1.2.1','Juros recebidos','R',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(83,4,'1.2.2','Descontos obtidos','R',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(84,4,'1.3','Outras Entradas','R',NULL,2,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(85,4,'1.3.1','Empréstimos recebidos','R',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(86,4,'1.3.2','Aporte de sócios','R',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(87,4,'1.3.3','Reembolsos diversos','R',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(88,4,'2','Saídas de Caixa','P',NULL,1,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(89,4,'2.1','Custos Operacionais','P',NULL,2,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(90,4,'2.1.1','Compra de mercadorias','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(91,4,'2.1.2','Matéria-prima/insumos','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(92,4,'2.1.3','Fretes sobre compras','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(93,4,'2.2','Despesas Fixas','P',NULL,2,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(94,4,'2.2.1','Aluguel','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(95,4,'2.2.2','Energia elétrica','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(96,4,'2.2.3','Água','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(97,4,'2.2.4','Internet e telefone','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(98,4,'2.3','Despesas com Pessoal','P',NULL,2,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(99,4,'2.3.1','Salários','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(100,4,'2.3.2','Encargos (INSS, FGTS)','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(101,4,'2.3.3','Pró-labore','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(102,4,'2.4','Despesas Variáveis','P',NULL,2,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(103,4,'2.4.1','Comissões sobre vendas','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(104,4,'2.4.2','Taxas de cartão/maquininha','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(105,4,'2.4.3','Impostos sobre vendas','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(106,4,'2.5','Despesas Financeiras','P',NULL,2,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(107,4,'2.5.1','Juros e multas pagas','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(108,4,'2.5.2','Tarifas bancárias','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(109,4,'2.6','Outras Saídas','P',NULL,2,NULL,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(110,4,'2.6.1','Distribuição de lucros','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(111,4,'2.6.2','Adiantamentos a sócios','P',NULL,3,1,1,'2026-03-10 20:42:27','2026-03-10 20:42:27'),(112,1,'2.6.3','Despesas com cartao','P','',3,1,1,'2026-03-13 19:24:14','2026-03-13 19:24:14'),(113,1,'2.4.7','Condominio','P','',3,1,1,'2026-03-16 19:22:54','2026-09-07 13:48:18'),(114,1,'2.4.4','Das MEI','P','',NULL,NULL,1,'2026-03-16 19:47:59','2026-03-16 19:47:59'),(115,1,'2.4.5','Seguro dental','P','',NULL,NULL,1,'2026-03-16 20:11:04','2026-03-16 20:11:04'),(116,1,'2.4.6','Tv Box','P','',NULL,NULL,1,'2026-03-16 20:18:09','2026-03-16 20:18:09'),(117,1,'2.6.4','Compras de marcado','P','9.9.9',1,3,1,'2026-03-23 19:27:12','2026-03-23 19:27:50'),(118,1,'2.3.4','Despesas com Pessoal - Beneficios','P','9.9.9',2,NULL,1,'2026-09-07 13:46:37','2026-09-07 13:46:37');
/*!40000 ALTER TABLE `fluxo_contas_modelo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `importacao_nfse`
--

DROP TABLE IF EXISTS `importacao_nfse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `importacao_nfse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `chave_nota` varchar(60) NOT NULL,
  `numero_nota` varchar(30) NOT NULL,
  `data_emissao` date NOT NULL,
  `cnpj_tomador` varchar(20) NOT NULL,
  `valor_bruto` decimal(15,2) NOT NULL,
  `valor_impostos` decimal(15,2) DEFAULT NULL,
  `descricao_servico` varchar(255) DEFAULT NULL,
  `status_importacao` varchar(20) DEFAULT NULL,
  `mensagem_erro` varchar(255) DEFAULT NULL,
  `data_importacao` datetime DEFAULT NULL,
  `endereco_rua` varchar(150) DEFAULT NULL,
  `endereco_numero` varchar(10) DEFAULT NULL,
  `endereco_bairro` varchar(100) DEFAULT NULL,
  `endereco_cidade` varchar(100) DEFAULT NULL,
  `endereco_uf` varchar(2) DEFAULT NULL,
  `endereco_cep` varchar(8) DEFAULT NULL,
  `telefone` varchar(20) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `contrato_produto` text DEFAULT NULL,
  `aliquota_comissao_especifica` decimal(5,2) DEFAULT NULL,
  `valor_repasse` decimal(10,2) DEFAULT NULL,
  `entidade_vendedor_padrao_id` int(11) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  `entidade_id` int(11) DEFAULT NULL,
  `lancamento_id` int(11) DEFAULT NULL,
  `aliquota_iss` decimal(5,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `entidade_vendedor_padrao_id` (`entidade_vendedor_padrao_id`),
  KEY `ix_importacao_nfse_chave_nota` (`chave_nota`),
  KEY `ix_importacao_nfse_empresa_id` (`empresa_id`),
  KEY `idx_importacao_nfse_entidade_id` (`entidade_id`),
  KEY `idx_importacao_nfse_lancamento_id` (`lancamento_id`),
  CONSTRAINT `fk_importacao_nfse_entidade_id` FOREIGN KEY (`entidade_id`) REFERENCES `entidades` (`id`),
  CONSTRAINT `fk_importacao_nfse_lancamento_id` FOREIGN KEY (`lancamento_id`) REFERENCES `lancamentos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `importacao_nfse_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  CONSTRAINT `importacao_nfse_ibfk_2` FOREIGN KEY (`entidade_vendedor_padrao_id`) REFERENCES `entidades` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `importacao_nfse`
--

LOCK TABLES `importacao_nfse` WRITE;
/*!40000 ALTER TABLE `importacao_nfse` DISABLE KEYS */;
INSERT INTO `importacao_nfse` VALUES (27,1,'NFS33045572227907386000176000000000003226048123021963','32','2026-04-01','02750988000131',5500.00,NULL,'Serviços de suporte Mensal','sucesso',NULL,'2026-04-01 18:49:37',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-04-01 18:49:37','2026-04-01 18:49:37',11,50,6.00),(28,1,'NFS33045572227907386000176000000000003326048558881447','33','2026-04-01','00624964000100',5585.11,NULL,'Prestação de serviços de suporte Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação de serviço de suportetécnico em informática ERP MXM Execução conforme previsto: - Contrato nº 030/2025 - Termo de Referência nº 02','sucesso',NULL,'2026-04-01 23:40:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-04-01 23:40:28','2026-04-01 23:40:28',10,51,6.00),(29,1,'NFS33045572227907386000176000000000002426036912644781','24','2026-03-02','00624964000100',5585.11,NULL,'Prestação de serviços de suporte Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação de serviço de suporte técnico em informática ERP MXM Execução conforme previsto: - Contrato nº 030/2025 - Termo de Referência nº 0','sucesso',NULL,'2026-04-03 18:35:12',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-04-03 18:35:12','2026-04-03 18:35:12',10,54,6.68),(30,1,'NFS33045572227907386000176000000000003426043859772569','34','2026-04-06','03430981000103',69.21,NULL,'Serviço de suporte remoto  - Conforme Lei 12.741/2012, o percentual total de impostos incidentes neste serviço prestado é de aproximadamente 6,80%','sucesso',NULL,'2026-04-08 19:14:46',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-04-08 19:14:46','2026-04-08 19:14:46',6,67,6.80),(31,1,'NFS33045572227907386000176000000000003526048462083113','35','2026-04-08','57823777000173',350.00,NULL,'Serviço de suporte remoto  - Conforme Lei 12.741/2012, o percentual total de impostos incidentes neste serviço prestado é de aproximadamente 6,80%','sucesso',NULL,'2026-04-08 19:15:24',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-04-08 19:15:24','2026-04-08 19:15:24',5,68,6.80),(32,1,'NFS33045572227907386000176000000000003826040062536221','38','2026-04-14','01605168000274',337.14,NULL,'Suporte remoto Mensal','sucesso',NULL,'2026-04-14 18:59:22',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-04-14 18:59:22','2026-04-14 18:59:22',26,76,6.00),(33,1,'NFS33045572227907386000176000000000003926040043871170','39','2026-04-15','54349011000100',333.00,NULL,'Suporte remoto mensal','sucesso',NULL,'2026-04-15 18:48:45',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-04-15 18:48:45','2026-04-15 18:48:45',4,77,6.00),(34,1,'NFS33045572227907386000176000000000004026049548640129','40','2026-04-23','06871247000160',308.96,NULL,'Serviço de suporte mensal','sucesso',NULL,'2026-04-23 17:57:40',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-04-23 17:57:40','2026-04-23 17:57:40',3,82,6.00),(35,1,'NFS33045572227907386000176000000000004126055715432294','41','2026-05-01','02750988000131',5500.00,NULL,'Serviço de apoio/suporte remoto','sucesso',NULL,'2026-05-01 15:06:58',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-05-01 15:06:58','2026-05-01 15:06:58',11,86,6.00),(36,1,'NFS33045572227907386000176000000000004226050524079614','42','2026-05-01','24413094000199',2405.83,NULL,'Serviços de Intermediação comercial no licenciamento\\Renovação do Kaspersky Next EDR 20-24 user - 12 mesesNúmero do processo interno Aplex: P26-93138ACliente: Termo Norte Energia LtdaDados para recebimento:Chave pix CNPJ. LiveSun: 27.907.386/0001-76','sucesso',NULL,'2026-05-01 15:07:16',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-05-01 15:07:16','2026-05-01 15:07:16',37,87,6.00),(37,1,'NFS33045572227907386000176000000000004326052588244675','43','2026-05-01','00624964000100',5585.11,NULL,'Apoio Administrativo  - Prestação de serviços de suporte Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação de serviço de suportetécnico em informática ERP MXM Execução conforme previsto: - Contrato nº 030/2025 - T','sucesso',NULL,'2026-05-01 15:25:43',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-05-01 15:25:43','2026-05-01 15:25:43',10,88,6.00),(38,1,'NFS33045572227907386000176000000000004426055122219290','44','2026-05-08','03430981000103',69.21,NULL,'Suporte remoto mensal','sucesso',NULL,'2026-05-08 23:43:56',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-05-08 23:43:56','2026-05-08 23:43:56',6,94,6.00),(39,1,'NFS33045572227907386000176000000000004726050471819455','47','2026-05-12','35159867000179',175.00,NULL,'Suporte Remoto','sucesso',NULL,'2026-05-13 00:38:43',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-05-13 00:38:43','2026-05-13 00:38:43',7,95,6.00),(40,1,'NFS33045572227907386000176000000000004626051043489265','46','2026-05-12','49035013000195',400.48,NULL,'Suporte remoto','sucesso',NULL,'2026-05-13 00:39:04',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-05-13 00:39:04','2026-05-13 00:39:04',8,96,6.00),(41,1,'NFS33045572227907386000176000000000004526053073056068','45','2026-05-12','01605168000274',337.14,NULL,'Suporte remoto','sucesso',NULL,'2026-05-13 00:39:29',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-05-13 00:39:29','2026-05-13 00:39:29',26,97,6.00),(42,1,'NFS33045572227907386000176000000000004826056605632276','48','2026-05-13','54349011000100',333.00,NULL,'Suporte remoto','sucesso',NULL,'2026-05-13 23:16:35',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-05-13 23:16:35','2026-05-13 23:16:35',4,102,6.00),(43,1,'NFS33045572227907386000176000000000004926059789652001','49','2026-05-21','06871247000160',308.96,NULL,'Suporte Remoto','sucesso',NULL,'2026-05-21 17:57:25',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-05-21 17:57:25','2026-05-21 17:57:25',3,107,6.00),(44,1,'NFS33045572227907386000176000000000005026069396955570','50','2026-06-01','00624964000100',5585.11,NULL,'Serviços combinados de escritório e suporte operacional no monitoramento de fluxos de processos administrativos. Prestação de serviços de suporte Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação deserviço de supo','sucesso',NULL,'2026-06-02 20:30:29',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-02 20:30:29','2026-06-02 20:30:29',10,111,2.00),(45,1,'NFS33045572227907386000176000000000005126065153596273','51','2026-06-02','02750988000131',5500.00,NULL,'Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas','sucesso',NULL,'2026-06-02 20:31:04',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-02 20:31:04','2026-06-02 20:31:04',11,112,2.00),(46,1,'NFS33045572227907386000176000000000005226067338672588','52','2026-06-05','03430981000103',69.21,NULL,'Serviço Suporte Mensal','sucesso',NULL,'2026-06-05 20:27:51',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-05 20:27:51','2026-06-05 20:27:51',6,114,2.00),(47,1,'NFS33045572227907386000176000000000005326060431451622','53','2026-06-08','49035013000195',400.48,NULL,'Serviço de Suporte mensal','sucesso',NULL,'2026-06-08 18:07:44',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-08 18:07:44','2026-06-08 18:07:44',8,117,2.00),(48,1,'NFS33045572227907386000176000000000005426069165585305','54','2026-06-08','35159867000179',175.00,NULL,'Serviço de Suporte mensal','sucesso',NULL,'2026-06-08 18:07:57',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-08 18:07:57','2026-06-08 18:07:57',7,118,2.00),(49,1,'NFS33045572227907386000176000000000005526060804532328','55','2026-06-08','20215683000101',383.72,NULL,'Serviços de intermediação comercial na licença de uso do sistema de gestão ERP - Gestão Click em SaaS','sucesso',NULL,'2026-06-08 21:19:33',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-08 21:19:33','2026-06-08 21:19:33',38,120,6.00),(50,1,'NFS33045572227907386000176000000000005626060030589497','56','2026-06-12','00624964000100',1396.00,NULL,'Serviços de apoio administrativo e suporte operacional na parametrização e validação de rotinas de processos internos. De acordo com o Pedido de Compra CIGAS N. 034649;Renovação de hospedagem WIX Plano Essencial por 36 meses','sucesso',NULL,'2026-06-12 18:07:35',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-12 18:07:35','2026-06-12 18:07:35',10,127,2.00),(51,1,'NFS33045572227907386000176000000000005726062480766365','57','2026-06-12','01605168000274',337.14,NULL,'Serviço de suporte mensal','sucesso',NULL,'2026-06-12 18:07:49',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-12 18:07:49','2026-06-12 18:07:49',26,128,2.00),(52,1,'NFS33045572227907386000176000000000005826069998222863','58','2026-06-12','54349011000100',333.00,NULL,'Serviço de suporte mensal','sucesso',NULL,'2026-06-12 19:35:44',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-12 19:35:44','2026-06-12 19:35:44',4,129,2.00),(53,1,'NFS33045572227907386000176000000000005926064039278099','59','2026-06-18','06871247000160',308.96,NULL,'Serviço de suporte mensal','sucesso',NULL,'2026-06-19 16:33:00',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-06-19 16:33:00','2026-06-19 16:33:00',3,132,2.00),(54,1,'NFS33045572227907386000176000000000006026072156366009','60','2026-07-01','02750988000131',10900.00,NULL,'Serviço de apoio administrativo e suporte a sistema','sucesso',NULL,'2026-07-02 22:18:23',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-07-02 22:18:23','2026-07-02 22:18:23',11,137,6.00),(55,1,'NFS33045572227907386000176000000000006126077157980465','61','2026-07-01','00624964000100',5585.11,NULL,'Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas Prestação de serviços de suporteFerramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação','sucesso',NULL,'2026-07-02 22:18:37',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-07-02 22:18:37','2026-07-02 22:18:37',10,138,6.00),(56,1,'NFS33045572227907386000176000000000006326070863348123','63','2026-07-07','03430981000103',69.00,NULL,'Serviço suporte remoto','sucesso',NULL,'2026-07-07 18:38:31',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-07-07 18:38:31','2026-07-07 18:38:31',6,141,6.00),(57,1,'NFS33045572227907386000176000000000006226075431766132','62','2026-07-06','20215683000101',376.76,NULL,'Serviços de intermediação comercial na licença de uso do sistema de gestão ERP - Gestão Click em SaaS','sucesso',NULL,'2026-07-07 18:38:43',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-07-07 18:38:43','2026-07-07 18:38:43',38,142,6.00),(58,1,'NFS42029092212605982000124000000004131026072443663811','41310','2026-07-07','27907386000176',194.00,NULL,'LICENCIAMENTO OU CESSAO DE DIREITO DE USO DE PROGRAMAS DE COMPUTACAO','sucesso',NULL,'2026-07-12 21:31:50',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-07-12 21:31:50','2026-07-12 21:31:50',40,148,6.00),(59,1,'NFS33045572227907386000176000000000006626077008345472','66','2026-07-14','01605168000274',337.14,NULL,'Serviço de suporte remoto','sucesso',NULL,'2026-07-14 19:13:48',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-07-14 19:13:48','2026-07-14 19:13:48',26,151,6.00),(60,1,'NFS33045572227907386000176000000000006526079313644804','65','2026-07-14','54349011000100',333.00,NULL,'Serviço de suporte remoto','sucesso',NULL,'2026-07-14 19:13:58',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-07-14 19:13:58','2026-07-14 19:13:58',4,152,6.00),(62,1,'NFS33045572227907386000176000000000006426079645214840','64','2026-07-13','35159867000179',575.48,NULL,'Serviços prestados','sucesso',NULL,'2026-07-14 19:28:50',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-07-14 19:28:50','2026-07-14 19:28:50',7,154,6.00),(63,1,'NFS33045572227907386000176000000000006726072962688861','67','2026-07-23','06871247000160',308.96,NULL,'Suporte remoto mensal','sucesso',NULL,'2026-07-24 17:24:31',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-07-24 17:24:31','2026-07-24 17:24:31',3,159,6.00),(65,1,'NFS33045572227907386000176000000000007126086408711534','71','2026-08-03','02750988000131',5500.00,NULL,'Suporte mensal','sucesso',NULL,'2026-08-03 12:40:31',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-08-03 12:40:31','2026-08-03 12:40:31',11,165,6.00),(66,1,'NFS33045572227907386000176000000000007226083353712983','72','2026-08-03','02750988000131',900.00,NULL,'Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas.- Escritório Salvador','sucesso',NULL,'2026-08-03 12:40:46',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-08-03 12:40:46','2026-08-03 12:40:46',11,166,6.00),(67,1,'NFS33045572227907386000176000000000007326081501921892','73','2026-08-06','49035013000195',400.48,NULL,'Serviço de suporte mensal','sucesso',NULL,'2026-08-07 17:47:29',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-08-07 17:47:29','2026-08-07 17:47:29',8,173,6.00),(68,1,'NFS33045572227907386000176000000000007426081907373642','74','2026-08-06','35159867000179',175.00,NULL,'Serviço de suporte mensal','sucesso',NULL,'2026-08-07 17:47:41',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-08-07 17:47:41','2026-08-07 17:47:41',7,174,6.00),(69,1,'NFS33045572227907386000176000000000007526080238528993','75','2026-08-07','03430981000103',69.21,NULL,'Serviço suporte mensal','sucesso',NULL,'2026-08-07 17:47:55',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-08-07 17:47:55','2026-08-07 17:47:55',6,175,6.00),(70,1,'NFS33045572227907386000176000000000007626086468821369','76','2026-08-12','01605168000274',337.14,NULL,'Serviço suporte mensal','sucesso',NULL,'2026-08-12 18:14:01',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-08-12 18:14:01','2026-08-12 18:14:01',26,181,6.00),(71,1,'NFS33045572227907386000176000000000007726080165527620','77','2026-08-12','54349011000100',333.00,NULL,'Serviço de Suporte Remoto','sucesso',NULL,'2026-08-12 18:15:26',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-08-12 18:15:26','2026-08-12 18:15:26',4,182,6.00),(72,1,'NFS33045572227907386000176000000000007826083127724820','78','2026-08-20','00624964000100',5585.11,NULL,'Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas - Prestação de serviçosde suporte em Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Pres','sucesso',NULL,'2026-08-20 14:11:57',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-08-20 14:11:57','2026-08-20 14:11:57',10,185,6.00),(73,1,'NFS33045572227907386000176000000000007926087247049557','79','2026-08-24','06871247000160',308.96,NULL,'Serviço de suporte mensal','sucesso',NULL,'2026-08-25 13:49:42',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-08-25 13:49:42','2026-08-25 13:49:42',3,188,6.00),(74,1,'NFS33045572227907386000176000000000008026096664968820','80','2026-09-01','00624964000100',5585.11,NULL,'Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas - Prestação de serviçosde suporte em Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Pres','sucesso',NULL,'2026-09-01 16:56:53',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-09-01 16:56:53','2026-09-01 16:56:53',10,190,6.00),(75,1,'NFS33045572227907386000176000000000008126097286310113','81','2026-09-01','02750988000131',5500.00,NULL,'Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas.-','sucesso',NULL,'2026-09-01 16:57:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-09-01 16:57:10','2026-09-01 16:57:10',11,191,6.00),(76,1,'NFS33045572227907386000176000000000008226093419718240','82','2026-09-02','02750988000131',900.00,NULL,'Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas','sucesso',NULL,'2026-09-02 14:07:38',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,NULL,1,'2026-09-02 14:07:38','2026-09-02 14:07:38',11,192,6.00);
/*!40000 ALTER TABLE `importacao_nfse` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lancamentos`
--

DROP TABLE IF EXISTS `lancamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lancamentos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `data_evento` date NOT NULL,
  `data_vencimento` date NOT NULL,
  `data_pagamento` date DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'aberto',
  `fluxo_conta_id` int(11) NOT NULL,
  `conta_banco_id` int(11) NOT NULL,
  `entidade_id` int(11) NOT NULL,
  `valor_real` decimal(15,2) NOT NULL,
  `valor_pago` decimal(15,2) DEFAULT 0.00,
  `numero_documento` varchar(50) DEFAULT NULL,
  `observacoes` text DEFAULT NULL,
  `criado_em` datetime DEFAULT current_timestamp(),
  `atualizado_em` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `valor_imposto` decimal(15,2) DEFAULT 0.00,
  `valor_outros_custos` decimal(15,2) DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `fluxo_conta_id` (`fluxo_conta_id`),
  KEY `conta_banco_id` (`conta_banco_id`),
  KEY `entidade_id` (`entidade_id`),
  KEY `idx_lancamento_empresa_datas` (`empresa_id`,`data_evento`),
  CONSTRAINT `lancamentos_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  CONSTRAINT `lancamentos_ibfk_2` FOREIGN KEY (`fluxo_conta_id`) REFERENCES `fluxo_contas_modelo` (`id`),
  CONSTRAINT `lancamentos_ibfk_3` FOREIGN KEY (`conta_banco_id`) REFERENCES `contas_banco` (`id`),
  CONSTRAINT `lancamentos_ibfk_4` FOREIGN KEY (`entidade_id`) REFERENCES `entidades` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=194 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lancamentos`
--

LOCK TABLES `lancamentos` WRITE;
/*!40000 ALTER TABLE `lancamentos` DISABLE KEYS */;
INSERT INTO `lancamentos` VALUES (2,1,'2026-03-11','2026-03-01','2026-03-11','pago',6,1,7,175.00,179.03,'29','','2026-03-13 18:43:22','2026-03-21 00:28:17',11.69,0.00),(3,1,'2026-03-11','2026-03-01','2026-03-11','pago',6,1,8,409.68,409.68,'28','','2026-03-13 18:45:33','2026-03-19 19:22:17',26.75,0.00),(4,1,'2026-03-11','2026-03-05','2026-03-11','pago',6,1,5,357.70,357.70,'27','','2026-03-13 18:47:42','2026-03-19 19:19:16',23.38,0.00),(5,1,'2026-03-12','2026-03-10','2026-03-12','pago',6,1,4,317.00,317.00,'30','','2026-03-13 18:49:46','2026-03-13 18:49:46',21.17,0.00),(6,1,'2026-03-05','2026-03-05','2026-03-05','pago',6,1,6,69.21,69.21,'25','','2026-03-13 18:54:23','2026-03-13 18:54:23',4.62,0.00),(7,1,'2026-03-10','2026-03-10','2026-03-10','pago',6,1,26,337.14,337.14,'26','','2026-03-13 19:06:24','2026-03-13 19:06:24',22.52,0.00),(9,1,'2026-03-09','2026-03-10','2026-03-09','pago',112,1,27,2669.31,2669.31,'Março 26','','2026-03-13 19:34:39','2026-03-13 19:34:39',0.00,0.00),(10,1,'2026-03-10','2026-03-10','2026-03-10','pago',27,1,1,1442.69,1442.69,'Fev/26','','2026-03-13 19:39:17','2026-03-19 18:19:37',0.00,0.00),(11,1,'2026-03-02','2026-03-09','2026-03-09','pago',6,1,11,5500.00,5500.00,'23','','2026-03-13 19:43:56','2026-03-13 19:43:56',367.40,0.00),(13,1,'2026-03-06','2026-03-06','2026-03-06','pago',27,1,23,1716.45,1716.45,'Fev26','Pro labore ref. Fev26\r\n2001,10  -  178,31(INSS)  - 106,34','2026-03-13 19:46:30','2026-03-19 18:25:19',0.00,0.00),(14,1,'2026-03-05','2026-03-05','2026-03-05','pago',36,1,1,1516.00,1516.00,'05 de Março','Pagamento cartões Gian','2026-03-13 19:51:25','2026-03-19 18:26:44',0.00,0.00),(16,1,'2026-03-05','2026-03-05','2026-03-05','pago',36,1,1,200.00,200.00,'05 de Março','Pago Eletricista Dona Dinora','2026-03-13 19:53:07','2026-03-19 18:33:38',0.00,0.00),(18,1,'2026-02-02','2026-03-02','2026-03-02','pago',6,1,10,5585.11,5585.11,'13','','2026-03-16 18:23:00','2026-03-19 18:37:35',373.08,0.00),(20,1,'2026-03-02','2026-03-02','2026-03-02','pago',36,1,1,750.00,750.00,'02 de março','Pago 1 parcela obra Dona Dinora','2026-03-16 18:25:09','2026-03-16 18:28:57',0.00,0.00),(21,1,'2026-03-16','2026-03-20','2026-03-20','pago',31,1,24,2665.10,2665.10,'Impostos','','2026-03-16 18:45:00','2026-03-20 18:32:33',0.00,0.00),(22,1,'2026-03-16','2026-03-20','2026-03-20','pago',26,1,25,356.62,356.62,'Ref. Fev26','','2026-03-16 18:52:02','2026-03-20 18:33:17',0.00,0.00),(23,1,'2026-03-10','2026-03-10','2026-03-19','pago',20,1,9,3200.00,3200.00,'Ref. Mar26','Pago aluguel Stella ref. Fev26  - Pix 03/03','2026-03-16 19:07:18','2026-03-19 18:21:43',0.00,0.00),(24,1,'2026-03-10','2026-03-10','2026-03-10','pago',113,1,17,326.00,326.00,'Ref. Março 26','','2026-03-16 19:31:28','2026-03-16 19:31:28',0.00,0.00),(25,1,'2026-03-16','2026-03-17','2026-03-19','pago',23,1,20,41.00,41.00,'Março 26','','2026-03-16 19:33:07','2026-03-19 18:22:14',0.00,0.00),(26,1,'2026-03-16','2026-03-16','2026-03-16','pago',23,1,19,132.00,132.00,'Março 26','','2026-03-16 19:34:22','2026-03-16 19:34:22',0.00,0.00),(27,1,'2026-03-09','2026-03-09','2026-03-09','pago',22,1,21,269.00,269.00,'Março 26','','2026-03-16 19:35:44','2026-03-16 19:35:44',0.00,0.00),(28,1,'2026-03-16','2026-03-20','2026-03-20','pago',114,1,2,87.00,87.00,'Março 26','','2026-03-16 19:50:32','2026-03-20 18:33:51',0.00,0.00),(29,1,'2026-03-09','2026-03-09','2026-03-09','pago',29,1,28,517.00,517.00,'Março 26','','2026-03-16 19:56:19','2026-03-16 19:56:19',0.00,0.00),(30,1,'2026-03-03','2026-03-03','2026-03-03','pago',21,1,14,182.00,182.00,'Março 26','','2026-03-16 19:59:00','2026-03-16 19:59:00',0.00,0.00),(31,1,'2026-03-09','2026-03-09','2026-03-09','pago',115,1,18,176.00,176.00,'Março 26','','2026-03-16 20:12:35','2026-03-16 20:12:35',0.00,0.00),(32,1,'2026-03-09','2026-03-09','2026-03-09','pago',116,1,31,30.00,30.00,'Março 26','','2026-03-16 20:58:57','2026-03-16 20:58:57',0.00,0.00),(33,1,'2026-03-16','2026-03-16','2026-03-16','pago',15,1,16,259.50,259.50,'Março 26','Repasse Hiper Sistemas','2026-03-19 18:45:03','2026-03-19 18:45:03',0.00,0.00),(34,1,'2026-03-16','2026-03-16','2026-03-16','pago',15,1,16,300.00,300.00,'Março 26 - Certificados 03/3','Compra de 10 certificados digitais parcela 3/3','2026-03-19 18:49:26','2026-03-19 18:49:26',0.00,0.00),(35,1,'2026-03-16','2026-03-16','2026-03-16','pago',37,1,1,600.00,600.00,'Março 26','Pix conserto carro 1','2026-03-19 18:54:01','2026-03-19 18:54:01',0.00,0.00),(36,1,'2026-03-17','2026-03-17','2026-03-17','pago',37,1,1,850.00,850.00,'Conserto carro 2','Pix conserto carro - Lauro','2026-03-19 18:58:26','2026-03-19 18:58:26',0.00,0.00),(37,1,'2026-03-17','2026-03-17','2026-03-17','pago',16,1,2,150.00,150.00,'Março 17','Complemento pago despesas diversas','2026-03-19 19:06:08','2026-03-19 19:06:08',0.00,0.00),(38,1,'2026-03-02','2026-03-02','2026-03-02','pago',16,1,2,55.00,55.00,'02 de março','Pix enviado Nelci - Pagto cartao Gian','2026-03-19 19:11:23','2026-03-19 19:11:23',0.00,0.00),(39,1,'2026-03-05','2026-03-05','2026-03-05','pago',16,1,32,75.00,75.00,'Refeiçao','Pix enviado Davi - iFood','2026-03-19 20:41:12','2026-03-19 20:41:12',0.00,0.00),(41,1,'2026-03-20','2026-03-27','2026-03-20','pago',6,1,3,308.96,308.96,'NF 31','','2026-03-23 19:23:57','2026-03-23 20:10:13',20.64,0.00),(42,1,'2026-03-20','2026-03-20','2026-03-20','pago',112,1,1,376.24,376.24,'Março 20','Total Atacado','2026-03-23 19:29:58','2026-03-23 19:44:06',0.00,0.00),(43,1,'2026-03-25','2026-03-25','2026-03-25','pago',36,1,1,1700.00,1700.00,'Março25','','2026-03-25 19:23:05','2026-03-25 19:23:05',0.00,0.00),(46,1,'2026-03-25','2026-03-25','2026-03-25','pago',36,1,1,1000.00,1000.00,'Março25','','2026-03-26 17:41:50','2026-03-26 17:41:50',0.00,0.00),(48,1,'2026-03-31','2026-03-31','2026-04-01','pago',36,1,1,280.00,280.00,'Março 31','Obra D.Dinora - pia','2026-03-31 17:56:33','2026-04-01 18:36:51',0.00,0.00),(50,1,'2026-04-01','2026-04-07','2026-04-07','pago',6,1,11,5500.00,5500.00,'32','Serviços de suporte Mensal','2026-04-01 18:49:37','2026-04-07 18:32:13',330.00,517.00),(51,1,'2026-04-01','2026-05-01','2026-05-06','pago',6,1,10,5585.11,5585.11,'33','Prestação de serviços de suporte Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação de serviço de suportetécnico em informática ERP MXM Execução conforme previsto: - Contrato nº 030/2025 - Termo de Referência nº 024/2025 - Ordem de fornecimento nº001/2025 Abrange atividades de manutenção corretiva e preventiva, apoio à operação, análise de log, ajustes e suporte relativos ao processo de apuração decontribuições federais (PIS/COFINS) e integração aos sistemas SGA/TCE','2026-04-01 23:40:28','2026-05-06 23:45:55',335.11,0.00),(52,1,'2026-04-01','2026-04-01','2026-04-01','pago',112,1,2,188.00,188.00,'01 Abril','Cartão bradesco Gian','2026-04-03 18:27:50','2026-04-03 18:27:50',0.00,0.00),(53,1,'2026-04-01','2026-04-01','2026-04-01','pago',21,1,14,120.00,120.00,'Coelba mar26','','2026-04-03 18:29:41','2026-04-03 18:29:41',0.00,0.00),(54,1,'2026-03-02','2026-03-02','2026-04-03','pago',6,1,10,5585.11,5585.11,'24','Prestação de serviços de suporte Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação de serviço de suporte técnico em informática ERP MXM Execução conforme previsto: - Contrato nº 030/2025 - Termo de Referência nº 024/2025 - Ordem de fornecimento nº 001/2025 Abrange atividades de manutenção corretiva e preventiva, apoio à operação, análise de log, ajustes e suporte relativos ao processo de apuração de contribuições federais (PIS/COFINS) e integração aos sistemas SGA/TCE - Conforme Lei 12.741/2012, o percentual total de impostos incidentes neste serviço prestado é de aproximadamente 6.26% - Conforme Lei 12.741/2012, o percentual total de impostos incidentes neste serviço prestado é de aproximadamente 6,68%','2026-04-03 18:35:12','2026-04-03 18:37:45',373.09,0.00),(55,1,'2026-04-02','2026-04-02','2026-04-02','pago',112,1,33,50.00,50.00,'02 de Abril','','2026-04-03 19:04:25','2026-04-03 19:04:25',0.00,0.00),(56,1,'2026-04-02','2026-04-02','2026-04-02','pago',112,1,34,39.80,39.80,'02 de Abril','','2026-04-03 19:06:02','2026-04-03 19:06:02',0.00,0.00),(57,1,'2026-04-02','2026-04-02','2026-04-02','pago',112,1,35,15.00,15.00,'02 de Abril','','2026-04-03 19:08:09','2026-04-03 19:08:09',0.00,0.00),(58,1,'2026-04-02','2026-04-02','2026-04-02','pago',16,1,36,117.79,117.79,'02 de Abril','','2026-04-03 19:10:03','2026-04-03 19:10:03',0.00,0.00),(59,1,'2026-04-03','2026-04-03','2026-04-03','pago',36,1,1,1200.00,1200.00,'03 de Abril','Pagto  saldo obra','2026-04-06 17:36:07','2026-04-06 17:36:07',0.00,0.00),(60,1,'2026-04-04','2026-04-04','2026-04-04','pago',36,1,1,50.00,50.00,'04 de Abril','Farmácia ','2026-04-06 17:42:05','2026-04-06 17:42:05',0.00,0.00),(62,1,'2026-04-06','2026-04-06','2026-04-06','pago',36,1,1,343.00,343.00,'06 de Abril','Cartão Gian - Pic Pay','2026-04-07 18:00:26','2026-04-07 18:00:26',0.00,0.00),(63,1,'2026-04-06','2026-04-06','2026-04-06','pago',27,1,23,1442.69,1442.69,'Março 26','Pro-Labore ref. março26','2026-04-07 18:07:08','2026-04-07 18:07:08',0.00,0.00),(64,1,'2026-04-08','2026-04-08','2026-04-08','pago',112,1,35,15.00,15.00,'07 de Abril','','2026-04-08 18:24:46','2026-04-08 18:24:46',0.00,0.00),(65,1,'2026-04-08','2026-04-08','2026-04-08','pago',20,1,9,3200.00,3200.00,'07 de Abril','Aluguel ref. março26','2026-04-08 18:27:50','2026-04-08 18:27:50',0.00,0.00),(66,1,'2026-04-08','2026-04-08','2026-04-08','pago',29,1,28,517.00,517.00,'08 de Abril','','2026-04-08 18:30:52','2026-04-08 18:30:52',0.00,0.00),(67,1,'2026-04-06','2026-04-06','2026-04-05','pago',6,1,6,69.21,69.21,'34','Serviço de suporte remoto  - Conforme Lei 12.741/2012, o percentual total de impostos incidentes neste serviço prestado é de aproximadamente 6,80%','2026-04-08 19:14:46','2026-04-08 19:20:01',4.71,0.00),(68,1,'2026-04-08','2026-04-08','2026-04-08','pago',6,1,5,350.00,357.23,'35','Serviço de suporte remoto  - Conforme Lei 12.741/2012, o percentual total de impostos incidentes neste serviço prestado é de aproximadamente 6,80%','2026-04-08 19:15:24','2026-04-08 19:22:44',23.80,0.00),(69,1,'2026-04-09','2026-04-09','2026-04-09','pago',27,1,1,1442.69,1442.69,'09 de Abril','Pro Labore ref. março26','2026-04-13 17:47:19','2026-04-13 17:47:19',0.00,0.00),(70,1,'2026-04-09','2026-04-09','2026-04-09','pago',112,1,27,774.97,774.97,'09 de Abril','Fatura parcelada em 1 + 2','2026-04-13 17:50:10','2026-04-13 17:50:10',0.00,0.00),(71,1,'2026-04-09','2026-04-09','2026-04-09','pago',36,1,1,325.00,325.00,'Complem. Obra','Complemento da Obra d.Dinora','2026-04-13 17:53:48','2026-04-13 17:53:48',0.00,0.00),(72,1,'2026-04-01','2026-04-01','2026-04-10','pago',6,1,8,400.48,409.68,'NF 37','','2026-04-13 17:58:07','2026-04-13 18:11:39',26.75,0.00),(73,1,'2026-04-01','2026-04-01','2026-04-10','pago',6,1,7,175.00,179.03,'NF 36','','2026-04-13 18:00:35','2026-04-13 18:13:54',11.69,0.00),(74,1,'2026-04-10','2026-04-10','2026-04-10','pago',36,1,1,640.00,640.00,'10 de Abril','Pagto cartões Gianlucca','2026-04-13 18:04:53','2026-04-13 18:04:53',0.00,0.00),(75,1,'2026-04-12','2026-04-12','2026-04-12','pago',117,1,36,15.59,15.59,'12 de Abril','','2026-04-13 18:08:42','2026-04-13 18:08:42',0.00,0.00),(76,1,'2026-04-14','2026-04-10','2026-04-13','pago',6,1,26,337.14,344.22,'38','Suporte remoto Mensal','2026-04-14 18:59:21','2026-04-14 19:01:58',20.23,0.00),(77,1,'2026-04-15','2026-04-15','2026-04-15','pago',6,1,4,333.00,333.00,'39','Suporte remoto mensal','2026-04-15 18:48:45','2026-04-15 18:51:21',19.98,0.00),(78,1,'2026-04-15','2026-04-15','2026-04-15','pago',15,1,16,259.50,259.50,'Abril','Repasse Hiper Sistemas','2026-04-15 20:02:23','2026-04-15 20:02:23',0.00,0.00),(79,1,'2026-04-14','2026-04-14','2026-04-14','pago',36,1,1,100.00,100.00,'14 de Abril','Repasse Gianlucca','2026-04-15 20:08:27','2026-04-15 20:08:27',0.00,0.00),(80,1,'2026-04-20','2026-04-20','2026-04-20','pago',31,1,24,871.10,871.10,'Março 26','','2026-04-20 18:33:39','2026-04-20 18:33:39',0.00,0.00),(81,1,'2026-04-20','2026-04-20','2026-04-20','pago',26,1,25,356.62,356.62,'Março 26','INSS Wagner e Felipe','2026-04-20 18:35:32','2026-04-20 18:35:32',0.00,0.00),(82,1,'2026-04-23','2026-04-23','2026-04-23','pago',6,1,3,308.96,308.96,'40','Serviço de suporte mensal','2026-04-23 17:57:39','2026-04-23 18:06:06',18.54,0.00),(83,1,'2026-04-26','2026-04-26','2026-04-26','pago',37,1,1,100.00,100.00,'26 de Abril','','2026-04-29 22:49:05','2026-04-29 22:49:05',0.00,0.00),(84,1,'2026-04-27','2026-04-27','2026-04-27','pago',112,1,35,30.00,30.00,'27 de Abril','Estacionamento Aeroporto','2026-04-29 22:50:54','2026-04-29 22:50:54',0.00,0.00),(85,1,'2026-04-27','2026-04-27','2026-04-27','pago',112,1,1,1500.00,1500.00,'27 de Março','Adiantamento Wagner Pagto Cartão ','2026-04-29 22:53:52','2026-04-29 22:53:52',0.00,0.00),(86,1,'2026-05-01','2026-05-01','2026-05-08','pago',6,1,11,5500.00,5500.00,'41','Serviço de apoio/suporte remoto','2026-05-01 15:06:58','2026-05-08 23:23:39',330.00,0.00),(87,1,'2026-05-01','2026-05-01','2026-05-05','pago',3,1,37,2405.83,2405.83,'42','Serviços de Intermediação comercial no licenciamento\\Renovação do Kaspersky Next EDR 20-24 user - 12 mesesNúmero do processo interno Aplex: P26-93138ACliente: Termo Norte Energia LtdaDados para recebimento:Chave pix CNPJ. LiveSun: 27.907.386/0001-76','2026-05-01 15:07:16','2026-05-05 14:36:09',360.87,0.00),(88,1,'2026-05-01','2026-06-01','2026-06-01','pago',6,1,10,5585.11,5585.11,'43','Apoio Administrativo  - Prestação de serviços de suporte Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação de serviço de suportetécnico em informática ERP MXM Execução conforme previsto: - Contrato nº 030/2025 - Termo de Referência nº 024/2025 - Ordem de fornecimento nº001/2025 Abrange atividades de manutenção corretiva e preventiva, apoio à operação, análise de log, ajustes e suporte relativos ao processo de apuração decontribuições federais (PIS/COFINS) e integração aos sistemas SGA/TCE','2026-05-01 15:25:43','2026-06-01 18:12:17',335.11,0.00),(89,1,'2026-05-04','2026-05-04','2026-05-04','pago',37,1,1,284.00,284.00,'04 de Maio','Saldo Pagto pedreiro','2026-05-06 23:48:39','2026-05-06 23:48:39',0.00,0.00),(90,1,'2026-05-04','2026-05-04','2026-05-04','pago',112,1,1,932.00,932.00,'04 de Maio','Cartões Gian (Bradesco e Pic Pay)','2026-05-06 23:50:28','2026-05-06 23:50:28',0.00,0.00),(91,1,'2026-05-04','2026-05-04','2026-05-04','pago',36,1,1,500.00,500.00,'04 de Maio','Aplicação Gian - enviado Nelci)','2026-05-06 23:53:39','2026-05-06 23:53:39',0.00,0.00),(92,1,'2026-05-06','2026-05-06','2026-05-06','pago',27,1,23,1442.69,1442.69,'Abril 26','Pro labore ref. Abril 26','2026-05-06 23:59:35','2026-05-06 23:59:35',0.00,0.00),(93,1,'2026-05-06','2026-05-06','2026-05-06','pago',27,1,1,1442.69,1442.69,'Abril 26','Pro Labore ref. Abril 26','2026-05-07 00:01:57','2026-05-07 00:01:57',0.00,0.00),(94,1,'2026-05-08','2026-05-08','2026-05-07','pago',6,1,6,69.21,70.63,'44','Suporte remoto mensal','2026-05-08 23:43:56','2026-05-13 00:47:39',4.15,0.00),(95,1,'2026-05-12','2026-05-12','2026-05-12','pago',6,1,7,175.00,178.97,'47','Suporte Remoto','2026-05-13 00:38:43','2026-05-13 00:55:55',10.50,0.00),(96,1,'2026-05-12','2026-05-12','2026-05-12','pago',6,1,8,400.48,409.55,'46','Suporte remoto','2026-05-13 00:39:04','2026-05-13 00:55:24',24.03,0.00),(97,1,'2026-05-12','2026-05-12','2026-05-11','pago',6,1,26,337.14,337.14,'45','Suporte remoto','2026-05-13 00:39:29','2026-05-13 00:46:45',20.23,0.00),(98,1,'2026-05-08','2026-05-08','2026-05-08','pago',20,1,9,3200.00,3200.00,'Aluguel Maio','Aluguel ref. Abril 26','2026-05-13 00:43:19','2026-05-13 00:43:19',0.00,0.00),(99,1,'2026-05-11','2026-05-11','2026-05-11','pago',36,1,1,844.00,844.00,'11 de Maio','Pagto cartões Gian - inter e Nubank','2026-05-13 00:50:10','2026-05-13 00:54:50',0.00,0.00),(100,1,'2026-05-11','2026-05-11','2026-05-11','pago',112,1,27,2091.80,2091.80,'Maio 26','Cartão empresarial ref. abr26','2026-05-13 00:54:01','2026-05-13 00:54:01',0.00,0.00),(101,1,'2026-05-08','2026-05-08','2026-05-08','pago',29,1,28,1232.74,1232.74,'Maio 26','Comissao Termonorte e Aplex','2026-05-13 01:00:02','2026-05-13 01:00:02',0.00,0.00),(102,1,'2026-05-13','2026-05-13','2026-05-13','pago',6,1,4,333.00,333.00,'48','Suporte remoto','2026-05-13 23:16:35','2026-05-13 23:17:15',19.98,0.00),(103,1,'2026-05-15','2026-05-15','2026-05-15','pago',15,1,16,194.00,194.00,'Maio 26 ','Repasse Hiper Sistemas ','2026-05-20 18:37:52','2026-05-20 18:37:52',0.00,0.00),(104,1,'2026-05-20','2026-05-20','2026-05-20','pago',26,1,25,356.62,356.62,'DARF Maio','INSS ref. Abril 26 - Wagner e Felipe','2026-05-20 18:40:23','2026-05-20 18:40:23',0.00,0.00),(105,1,'2026-05-20','2026-05-20','2026-05-20','pago',31,1,24,888.16,888.16,'DAS maio26','DAS ref. Abr26','2026-05-20 18:48:13','2026-05-20 18:48:13',0.00,0.00),(106,1,'2026-05-20','2026-05-20','2026-05-20','pago',112,1,2,1082.00,1082.00,'Maio 26','Cartão Nelci ref. Maio 26','2026-05-20 18:50:51','2026-05-20 18:50:51',0.00,0.00),(107,1,'2026-05-21','2026-05-21','2026-05-21','pago',6,1,3,308.96,308.96,'49','Suporte Remoto','2026-05-21 17:57:25','2026-05-26 17:38:39',18.54,0.00),(108,1,'2026-05-26','2026-05-26','2026-05-26','pago',112,1,1,300.00,300.00,'25 de Maio','','2026-05-26 17:43:56','2026-05-26 17:43:56',0.00,0.00),(109,1,'2026-05-27','2026-05-27','2026-05-27','pago',22,1,2,250.00,250.00,'Embasa Maio','Pagto Embasa ref. Maio 26','2026-06-01 18:05:30','2026-06-01 18:05:30',0.00,0.00),(110,1,'2026-06-01','2026-06-01','2026-06-01','pago',112,1,2,275.00,275.00,'Cartao Gian Pic Py','','2026-06-01 18:09:13','2026-06-01 18:09:13',0.00,0.00),(111,1,'2026-06-01','2026-07-01','2026-07-01','pago',6,1,10,5585.11,5585.11,'50','Serviços combinados de escritório e suporte operacional no monitoramento de fluxos de processos administrativos. Prestação de serviços de suporte Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação deserviço de suportetécnico em informática ERP MXM Execução conforme previsto: - Contrato nº 030/2025 - Termo de Referência nº 024/2025 - Ordem de fornecimento nº001/2025 Abrange atividades de manutenção corretiva e preventiva, apoio à operação, análise de log, ajustes e suporte relativos ao processo de apuração decontribuições federais (PIS/COFINS) e integração aos sistemas SGA/TCE','2026-06-02 20:30:28','2026-07-01 18:25:41',335.10,0.00),(112,1,'2026-06-02','2026-06-10','2026-06-08','pago',6,1,11,5500.00,5500.00,'51','Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas','2026-06-02 20:31:04','2026-06-12 19:42:12',330.00,0.00),(113,1,'2026-06-03','2026-06-03','2026-06-03','pago',21,1,1,134.97,134.97,'Junho 26','Pagto Coelba ref. maio26','2026-06-05 20:19:35','2026-06-05 20:19:35',0.00,0.00),(114,1,'2026-06-05','2026-06-05','2026-06-05','pago',6,1,6,69.21,69.21,'52','Serviço Suporte Mensal','2026-06-05 20:27:50','2026-06-12 19:44:26',4.15,0.00),(115,1,'2026-06-05','2026-06-05','2026-06-05','pago',16,1,1,1.39,1.39,'05 de junho','Compra na Master Parafusos - Lauro','2026-06-05 20:32:46','2026-06-09 18:44:21',0.00,0.00),(116,1,'2026-06-05','2026-06-05','2026-06-05','pago',36,1,1,90.00,90.00,'05 de Junho','Compra em Itapuã ','2026-06-05 20:34:38','2026-06-05 20:34:38',0.00,0.00),(117,1,'2026-06-08','2026-06-08','2026-06-05','pago',6,1,8,400.48,409.01,'53','Serviço de Suporte mensal','2026-06-08 18:07:44','2026-06-12 19:42:59',24.54,0.00),(118,1,'2026-06-08','2026-06-08','2026-06-05','pago',6,1,7,175.00,178.73,'54','Serviço de Suporte mensal','2026-06-08 18:07:57','2026-06-12 19:43:42',10.72,0.00),(119,1,'2026-06-05','2026-06-05','2026-06-05','pago',27,1,23,1442.69,1442.69,'Maio 26','Pro Labore referente a Maio 26','2026-06-08 18:21:38','2026-06-08 18:21:38',0.00,0.00),(120,1,'2026-06-08','2026-06-08','2026-06-18','pago',6,1,38,383.72,383.72,'55','Serviços de intermediação comercial na licença de uso do sistema de gestão ERP - Gestão Click em SaaS','2026-06-08 21:19:33','2026-06-18 18:45:39',23.02,0.00),(121,1,'2026-06-05','2026-06-05','2026-06-05','pago',20,1,9,3200.00,3200.00,'05 de Junho','','2026-06-09 18:33:07','2026-06-09 18:33:07',0.00,0.00),(122,1,'2026-06-05','2026-06-05','2026-06-05','pago',112,1,2,550.00,550.00,'05 de Junho','Pagto cartão Gian','2026-06-09 18:35:33','2026-06-09 18:35:33',0.00,0.00),(123,1,'2026-06-05','2026-06-05','2026-06-05','pago',112,1,2,100.00,100.00,'05 de Junho','Pix enviado  Evelyn Pagto despesas d. Dinora\r\n','2026-06-09 18:37:17','2026-06-09 18:37:17',0.00,0.00),(124,1,'2026-06-08','2026-06-08','2026-06-08','pago',27,1,1,1442.69,1442.69,'Junho','Pro Labore ref. a Maio 26','2026-06-09 18:38:57','2026-06-09 18:38:57',0.00,0.00),(125,1,'2026-06-08','2026-06-08','2026-06-08','pago',35,1,2,1348.00,1348.00,'Diversos','Despesas Diversas (Condominio/Magno/SulAmérica/Tv Box/Vivo Celular/Internet Claro/Das Mei)','2026-06-09 18:42:32','2026-06-09 18:42:32',0.00,0.00),(126,1,'2026-06-10','2026-06-10','2026-06-10','pago',112,1,27,1700.58,1700.58,'10 de Junho','Pagto cartão empresa ref. Maio 26','2026-06-11 19:27:15','2026-06-11 19:27:15',0.00,0.00),(127,1,'2026-06-12','2026-06-12','2026-07-12','pago',6,1,10,1396.00,1396.00,'56','Serviços de apoio administrativo e suporte operacional na parametrização e validação de rotinas de processos internos. De acordo com o Pedido de Compra CIGAS N. 034649;Renovação de hospedagem WIX Plano Essencial por 36 meses','2026-06-12 18:07:35','2026-07-13 17:06:35',83.76,0.00),(128,1,'2026-06-12','2026-06-12','2026-06-11','pago',6,1,26,337.14,343.99,'57','Serviço de suporte mensal','2026-06-12 18:07:49','2026-06-12 19:40:02',20.63,0.00),(129,1,'2026-06-12','2026-06-12','2026-06-12','pago',6,1,4,333.00,333.00,'58','Serviço de suporte mensal','2026-06-12 19:35:44','2026-06-12 19:41:13',19.98,0.00),(130,1,'2026-06-13','2026-06-13','2026-06-13','pago',117,1,39,39.99,39.99,'13 junho','','2026-06-15 18:34:03','2026-06-15 18:34:03',0.00,0.00),(131,1,'2026-06-15','2026-06-15','2026-06-15','pago',15,1,16,194.00,194.00,'Julho','Repasse Hiper Sistemas ref. Maio26','2026-06-15 18:36:10','2026-06-15 18:36:10',0.00,0.00),(132,1,'2026-06-18','2026-06-18','2026-06-18','pago',6,1,3,308.96,308.96,'59','Serviço de suporte mensal','2026-06-19 16:33:00','2026-06-19 16:42:17',20.63,0.00),(133,1,'2026-06-19','2026-06-19','2026-06-19','pago',26,1,25,356.62,356.62,'Maio 26','Pagto DARF INSS ref. Maio 26','2026-06-19 16:46:04','2026-06-19 16:46:04',0.00,0.00),(134,1,'2026-06-22','2026-06-22','2026-06-22','pago',31,1,24,1042.22,1042.22,'Maio 26','DAS Simples Nacional ref. Maio 26','2026-06-22 18:14:32','2026-06-22 18:14:32',0.00,0.00),(135,1,'2026-06-25','2026-06-25','2026-06-25','pago',112,1,1,600.00,600.00,'Junho','Pagto cartão Wagner - parte','2026-06-30 18:00:32','2026-06-30 18:00:32',0.00,0.00),(136,1,'2026-07-01','2026-07-01','2026-07-01','pago',112,1,2,132.00,132.00,'01 Julho','Cartão Gian','2026-07-01 18:28:35','2026-07-01 18:28:35',0.00,0.00),(137,1,'2026-07-01','2026-07-01','2028-07-07','pago',6,1,11,10900.00,10900.00,'60','Serviço de apoio administrativo e suporte a sistema','2026-07-02 22:18:23','2026-07-08 18:34:57',654.00,0.00),(138,1,'2026-07-01','2026-07-01','2026-08-01','pago',6,1,10,5585.11,5585.11,'61','Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas Prestação de serviços de suporteFerramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação de serviço de suporte técnico em informática ERP MXM Execução conforme previsto: - Contrato nº 030/2025 - Termo de Referência nº 024/2025 - Ordem de fornecimento nº001/2025 Abrange atividades de manutenção corretiva e preventiva, apoio à operação, análise de log, ajustes e suporte relativos ao processo de apuração decontribuições federais (PIS/COFINS) e integração aos sistemas SGA/TCE','2026-07-02 22:18:37','2026-08-03 18:58:49',335.11,0.00),(139,1,'2026-07-03','2026-07-03','2026-07-03','pago',32,1,2,4495.00,4495.00,'Despesas Julho','Despesas Diversas Julho 26','2026-07-06 17:24:38','2026-07-06 17:41:16',0.00,0.00),(140,1,'2026-07-03','2026-07-03','2026-07-03','pago',117,1,1,400.00,400.00,'03 Julho','Despesas compras mercado','2026-07-06 17:26:56','2026-07-06 17:26:56',0.00,0.00),(141,1,'2026-07-07','2026-07-07','2026-07-07','pago',6,1,6,69.00,69.00,'63','Serviço suporte remoto','2026-07-07 18:38:31','2026-07-07 18:44:40',4.14,0.00),(142,1,'2026-07-06','2026-07-06','2026-07-09','pago',6,1,38,376.76,376.76,'62','Serviços de intermediação comercial na licença de uso do sistema de gestão ERP - Gestão Click em SaaS','2026-07-07 18:38:43','2026-07-09 17:50:40',22.61,0.00),(143,1,'2026-07-06','2026-07-06','2026-07-06','pago',112,1,1,1034.00,1034.00,'06 de Julho','Cartões Gian','2026-07-09 17:34:26','2026-07-09 17:34:26',0.00,0.00),(144,1,'2026-07-07','2026-07-07','2026-07-07','pago',27,1,1,1442.69,1442.69,'Junho 26','Pro Labore ref. Junho26','2026-07-09 17:38:04','2026-07-09 17:38:04',0.00,0.00),(145,1,'2026-07-07','2026-07-07','2026-07-07','pago',27,1,23,1442.69,1442.69,'Junho 26','Pro Labore ref. Junho 26','2026-07-09 17:42:24','2026-07-09 17:42:24',0.00,0.00),(146,1,'2026-07-08','2026-07-08','2026-07-08','pago',29,1,1,1024.60,1024.60,'Magno','Valor ref. A comissões de R$ 517,00 e R$ 507,60','2026-07-09 17:47:31','2026-07-09 17:47:31',0.00,0.00),(147,1,'2026-07-10','2026-07-10','2026-07-10','pago',112,1,27,1932.23,1932.23,'Julho 26','Pagto cartão empresarial ref. Jun26','2026-07-10 17:50:29','2026-07-10 17:50:29',0.00,0.00),(148,1,'2026-07-07','2026-07-15','2026-07-15','pago',17,1,16,194.00,194.00,'41310','LICENCIAMENTO OU CESSAO DE DIREITO DE USO DE PROGRAMAS DE COMPUTACAO','2026-07-12 21:31:50','2026-07-15 18:00:47',11.64,0.00),(150,1,'2026-07-13','2026-07-13','2026-07-13','pago',112,1,1,1054.00,1054.00,'Cartões Gian','Pagto cartões Gian dos dias 12 e 13','2026-07-14 18:02:44','2026-07-14 18:02:44',0.00,0.00),(151,1,'2026-07-14','2026-07-14','2026-07-13','pago',6,1,26,337.14,344.22,'66','Serviço de suporte remoto','2026-07-14 19:13:48','2026-07-14 19:30:02',20.23,0.00),(152,1,'2026-07-14','2026-07-14','2026-07-13','pago',6,1,4,333.00,333.00,'65','Serviço de suporte remoto','2026-07-14 19:13:58','2026-07-14 19:31:52',19.98,0.00),(154,1,'2026-07-13','2026-07-13','2026-07-10','pago',6,1,7,575.48,575.48,'64','Serviços prestados','2026-07-14 19:28:50','2026-07-14 19:32:44',34.53,0.00),(155,1,'2026-07-15','2026-07-15','2026-07-15','pago',112,1,1,783.00,783.00,'15 de Julho','Pagamento Boleto Bernardo','2026-07-16 17:12:13','2026-07-16 17:12:13',0.00,0.00),(156,1,'2026-07-20','2026-07-20','2026-07-20','pago',31,1,24,883.14,883.14,'Julho 26','DAS Imposto ref. Junho 26','2026-07-20 18:29:31','2026-07-20 18:29:31',0.00,0.00),(157,1,'2026-07-20','2026-07-20','2026-07-20','pago',26,1,25,356.62,356.62,'Julho 26','Pagto INSS ref. Junho 26','2026-07-20 18:32:21','2026-07-20 18:32:21',0.00,0.00),(158,1,'2026-07-20','2026-07-20','2026-07-20','pago',112,1,2,1600.00,1600.00,'Julho 26','Cartao Nelci','2026-07-23 18:41:29','2026-07-23 18:41:29',0.00,0.00),(159,1,'2026-07-23','2026-07-23','2026-07-22','pago',6,1,3,308.96,308.96,'67','Suporte remoto mensal','2026-07-24 17:24:31','2026-07-24 17:27:24',18.54,0.00),(160,1,'2026-07-27','2026-07-27','2026-07-27','pago',36,1,1,1500.00,1500.00,'Cartao Wagner','Parte Pagto cartão Wagner','2026-07-27 17:39:59','2026-07-27 17:39:59',0.00,0.00),(161,1,'2026-07-25','2026-07-25','2026-07-25','pago',117,1,41,40.40,40.40,'25 de Julho','','2026-07-27 17:58:48','2026-07-27 17:58:48',0.00,0.00),(162,1,'2026-07-24','2026-07-24','2026-07-24','pago',117,1,42,284.94,284.94,'24 de Julho','','2026-07-27 18:02:05','2026-07-27 18:02:05',0.00,0.00),(163,1,'2026-07-28','2026-07-28','2026-07-28','pago',15,1,43,119.00,119.00,'Julho 26','','2026-07-28 18:37:48','2026-07-28 18:37:48',0.00,0.00),(165,1,'2026-08-03','2026-08-03','2026-08-03','pago',6,1,11,5500.00,5500.00,'71','Suporte mensal','2026-08-03 12:40:31','2026-08-07 18:37:13',330.00,0.00),(166,1,'2026-08-03','2026-08-03','2026-08-05','pago',6,1,11,900.00,900.00,'72','Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas.- Escritório Salvador','2026-08-03 12:40:46','2026-08-05 18:45:39',54.00,0.00),(167,1,'2026-08-01','2026-08-01','2026-08-01','pago',113,1,1,300.00,300.00,'Terreno','Limpeza terreno fazenda','2026-08-03 18:52:45','2026-08-03 18:52:45',0.00,0.00),(168,1,'2026-08-03','2026-08-03','2026-08-03','pago',112,1,1,535.00,535.00,'Gian - Bradesco','Cartão Bradesco Gian','2026-08-03 18:57:06','2026-08-03 18:57:06',0.00,0.00),(169,1,'2026-08-03','2026-08-03','2026-08-03','pago',16,1,27,60.00,60.00,'B 24H','Saque Banco 24 horas','2026-08-05 18:16:07','2026-08-05 18:16:07',0.00,0.00),(170,1,'2026-08-03','2026-08-03','2026-08-03','pago',34,1,27,6.40,6.40,'Tarifa','Tarifa saque Bco 24 horas','2026-08-05 18:21:33','2026-08-05 18:21:33',0.00,0.00),(171,1,'2026-08-04','2026-08-04','2026-08-04','pago',28,1,2,4533.00,4533.00,'Agosto','Despesas Diversas Agosto (Cond., Aluguel, celular,Mei,Tv Box, Embasa, Coelba,Sulamerica, Iptu 5)','2026-08-05 18:25:39','2026-08-05 18:25:39',0.00,0.00),(172,1,'2026-08-05','2026-08-05','2026-08-05','pago',117,1,42,21.48,21.48,'05 Agosto','Despesas Mercado','2026-08-05 18:42:42','2026-08-05 18:42:42',0.00,0.00),(173,1,'2026-08-06','2026-08-06','2026-08-06','pago',6,1,8,400.48,408.75,'73','Serviço de suporte mensal','2026-08-07 17:47:29','2026-08-07 18:32:58',24.03,0.00),(174,1,'2026-08-06','2026-08-06','2026-08-06','pago',6,1,7,175.00,178.62,'74','Serviço de suporte mensal','2026-08-07 17:47:41','2026-08-07 18:33:46',10.50,0.00),(175,1,'2026-08-07','2026-08-07','2026-08-06','pago',6,1,6,69.21,70.61,'75','Serviço suporte mensal','2026-08-07 17:47:55','2026-08-07 18:36:24',4.15,0.00),(176,1,'2026-08-05','2026-08-05','2026-08-05','pago',112,1,1,950.00,950.00,'Cartão Gian PicPay','Cartão PicPay Gian','2026-08-07 18:31:40','2026-08-07 18:31:40',0.00,0.00),(177,1,'2026-08-07','2026-08-07','2026-08-07','pago',29,1,1,596.00,596.00,'Magno','Comissão Magno ref. 2 notas','2026-08-07 18:41:52','2026-08-07 18:41:52',0.00,0.00),(178,1,'2026-08-07','2026-08-07','2026-08-07','pago',27,1,23,1442.69,1442.69,'Julho 26','Pro Labore Felipe ref. Julho 26','2026-08-07 18:44:45','2026-08-07 18:44:45',0.00,0.00),(179,1,'2026-08-07','2026-08-07','2026-08-07','pago',27,1,1,1442.69,1442.69,'Julho 26','Pro Labore Wagner ref. Julho26','2026-08-07 18:46:43','2026-08-07 18:46:43',0.00,0.00),(180,1,'2026-08-10','2026-08-10','2026-08-10','pago',112,1,27,2737.71,2737.71,'Agosto 26','Cartão Empresa ref. ago26','2026-08-10 17:32:55','2026-08-10 17:32:55',0.00,0.00),(181,1,'2026-08-12','2026-08-12','2026-08-12','pago',6,1,26,337.14,337.14,'76','Serviço suporte mensal','2026-08-12 18:14:01','2026-08-12 18:31:59',20.23,0.00),(182,1,'2026-08-12','2026-08-12','2026-08-12','pago',6,1,4,333.00,333.00,'77','Serviço de Suporte Remoto','2026-08-12 18:15:26','2026-08-12 18:38:46',19.98,0.00),(183,1,'2026-08-12','2026-08-12','2026-08-12','pago',112,1,1,485.00,485.00,'12 Agosto','Cartão Gian - inter','2026-08-12 18:36:36','2026-08-12 18:36:36',0.00,0.00),(184,1,'2026-08-17','2026-08-17','2026-08-17','pago',15,1,16,194.00,194.00,'Agosto 26','Repasse Hiper Sistemas ref. Jul26','2026-08-17 17:17:17','2026-08-17 17:17:17',0.00,0.00),(185,1,'2026-08-20','2026-08-20',NULL,'aberto',6,1,10,5585.11,0.00,'78','Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas - Prestação de serviçosde suporte em Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação de serviço de suporte técnico em informática ERP MXMExecução conforme previsto: - Contrato nº 030/2025 - Termo de Referência nº 024/2025 - Ordem de fornecimento nº001/2025 - Abrange atividades de manutenção corretiva e preventiva, apoio à operação, análise de log, ajustes e suporte relativos ao processo de apuração decontribuições federais (PIS/COFINS) e integração aos sistemas SGA/TCE','2026-08-20 14:11:57','2026-08-20 14:11:57',335.11,0.00),(186,1,'2026-08-20','2026-08-20','2026-08-20','pago',31,1,24,653.77,653.77,'Agosto 26','DAS Simples nacional ref. Julho 26','2026-08-20 17:42:20','2026-08-20 17:42:20',0.00,0.00),(187,1,'2026-08-20','2026-08-20','2026-08-20','pago',26,1,25,356.62,356.62,'Agosto 26','Pagto INSS ref. Julho 26','2026-08-20 17:44:14','2026-08-20 17:44:14',0.00,0.00),(188,1,'2026-08-24','2026-08-24','2026-08-24','pago',6,1,3,308.96,308.96,'79','Serviço de suporte mensal','2026-08-25 13:49:42','2026-08-25 17:24:47',18.54,0.00),(189,1,'2026-08-25','2026-08-25','2026-08-25','pago',112,1,1,1200.00,1200.00,'Cartao Wagner','Pagto cartões Wagner','2026-08-26 17:43:43','2026-08-26 17:43:43',0.00,0.00),(190,1,'2026-09-01','2026-10-01',NULL,'aberto',6,1,10,5585.11,0.00,'80','Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas - Prestação de serviçosde suporte em Ferramentas de ETL - Pentaho Data Integration SGA - Sistema de Gestão de arquivos Prestação de serviço de suporte técnico em informática ERP MXMExecução conforme previsto: - Contrato nº 030/2025 - Termo de Referência nº 024/2025 - Ordem de fornecimento nº001/2025 - Abrange atividades de manutenção corretiva e preventiva, apoio à operação, análise de log, ajustes e suporte relativos ao processo de apuração decontribuições federais (PIS/COFINS) e integração aos sistemas SGA/TCE','2026-09-01 16:56:53','2026-09-07 13:52:23',335.11,0.00),(191,1,'2026-09-01','2026-09-01',NULL,'aberto',6,1,11,5500.00,0.00,'81','Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas.-','2026-09-01 16:57:10','2026-09-01 16:57:10',330.00,0.00),(192,1,'2026-09-02','2026-09-02',NULL,'aberto',6,1,11,900.00,0.00,'82','Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais e suporte ao usuário em rotinas de sistemas','2026-09-02 14:07:38','2026-09-02 14:07:38',54.00,0.00),(193,1,'2026-09-01','2026-09-07','2026-09-07','pago',118,1,44,31.80,31.80,'4386076','Primeira cobrança Vale Saúde Empresa','2026-09-07 13:51:14','2026-09-07 13:51:14',0.00,0.00);
/*!40000 ALTER TABLE `lancamentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `parametros_sistema`
--

DROP TABLE IF EXISTS `parametros_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parametros_sistema` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `chave` varchar(100) NOT NULL,
  `valor` text NOT NULL,
  `tipo` varchar(20) DEFAULT 'string',
  `descricao` varchar(255) DEFAULT NULL,
  `criado_em` datetime DEFAULT current_timestamp(),
  `atualizado_em` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_parametro_chave` (`empresa_id`,`chave`),
  KEY `idx_parametro_chave` (`empresa_id`,`chave`),
  CONSTRAINT `parametros_sistema_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parametros_sistema`
--

LOCK TABLES `parametros_sistema` WRITE;
/*!40000 ALTER TABLE `parametros_sistema` DISABLE KEYS */;
INSERT INTO `parametros_sistema` VALUES (1,1,'aliquota_comissao_padrao','25.00','numeric','Alíquota padrão de comissão sobre vendas','2026-03-07 03:18:29','2026-03-07 03:18:29');
/*!40000 ALTER TABLE `parametros_sistema` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `username` varchar(80) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(120) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `is_admin` tinyint(1) DEFAULT 0,
  `dashboard_chart_days` int(11) DEFAULT 30,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_user_empresa_active` (`empresa_id`,`is_active`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,1,'admin','livesun@livesun.com.br','scrypt:32768:8:1$RuBgms8XYZq1Lyb8$29b71fcc9431cf114af99943a9eef932363888411047240f1b6e7529226d5992372d36369c1da576f749089b298f333afbafc87024aaeb9c7809736af5f49ce8','Admin',1,1,30,'2026-02-26 19:44:25','2026-02-26 19:44:25'),(2,1,'Nelci','nelci.vallotto@livesun.com.br','scrypt:32768:8:1$ZQgjncHW9vjUYttT$758289f8ee40a8e4df44fdf90326fe694ed129fb07790601a70fc65248ec6d0c13fc76fea978126756552f696e08ebc3ed142cb9e802cb3f704f8e68c0d33154','Nelci',1,0,30,'2026-02-26 19:45:22','2026-02-26 19:45:22'),(48,4,'teste','teste@livesun.com.br','scrypt:32768:8:1$nVmrbTRRcFOcIKNE$68a8c309c28264bc534f13cc6c9d8a61e9fb29bcc75e27305f00b0fcfa15c1c4dde5d1e7a102c97eaf7adb651fead25ae4e19574a5f77bb6be055b72c9686124','teste de teste',1,1,30,'2026-03-10 20:42:28','2026-03-10 20:42:28');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'u951548013_gfinanceiro'
--

--
-- Dumping routines for database 'u951548013_gfinanceiro'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-07 16:05:35
