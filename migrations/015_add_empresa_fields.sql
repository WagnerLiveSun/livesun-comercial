-- Migration: Adiciona campos de endereço, inscrições e contato à tabela `empresas`.
-- Aplique este script manualmente em uma cópia/backup do banco.

ALTER TABLE empresas
  ADD COLUMN endereco_rua VARCHAR(150),
  ADD COLUMN endereco_numero VARCHAR(10),
  ADD COLUMN endereco_bairro VARCHAR(100),
  ADD COLUMN endereco_cidade VARCHAR(100),
  ADD COLUMN endereco_uf VARCHAR(2),
  ADD COLUMN endereco_cep VARCHAR(8),
  ADD COLUMN inscricao_municipal VARCHAR(50),
  ADD COLUMN inscricao_estadual VARCHAR(50),
  ADD COLUMN telefone VARCHAR(20),
  ADD COLUMN email VARCHAR(120);

-- Observação: Este arquivo não tenta ser idempotente (evita IF NOT EXISTS por compatibilidade
-- com diferentes versões do MySQL). Caso a coluna já exista, o comando retornará erro.