-- Migration: adiciona campos cadastrais na tabela entidades

ALTER TABLE entidades
  ADD COLUMN nome_fantasia VARCHAR(150) NULL,
  ADD COLUMN inscricao_estadual VARCHAR(50) NULL,
  ADD COLUMN inscricao_municipal VARCHAR(50) NULL,
  ADD COLUMN endereco_rua VARCHAR(150) NULL,
  ADD COLUMN endereco_numero VARCHAR(10) NULL,
  ADD COLUMN endereco_bairro VARCHAR(100) NULL,
  ADD COLUMN endereco_cidade VARCHAR(100) NULL,
  ADD COLUMN endereco_uf VARCHAR(2) NULL,
  ADD COLUMN endereco_cep VARCHAR(8) NULL,
  ADD COLUMN telefone VARCHAR(20) NULL,
  ADD COLUMN email VARCHAR(120) NULL,
  ADD COLUMN contrato_produto TEXT NULL;