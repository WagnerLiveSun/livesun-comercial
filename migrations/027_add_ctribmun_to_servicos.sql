-- Adicionar coluna ctribmun na tabela servicos para NFS-e Nacional
ALTER TABLE servicos 
ADD COLUMN ctribmun VARCHAR(12) NULL;
