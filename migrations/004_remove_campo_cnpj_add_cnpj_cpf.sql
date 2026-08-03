-- MIGRAÇÃO: Remove campo cnpj da tabela entidades e adiciona cnpj_cpf obrigatório
ALTER TABLE entidades
DROP COLUMN cnpj,
ADD COLUMN cnpj_cpf VARCHAR(18) NOT NULL,
ADD INDEX idx_entidades_cnpj_cpf (cnpj_cpf);