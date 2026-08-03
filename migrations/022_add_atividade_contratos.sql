-- Adicionar atividade_contratos à tabela empresas
ALTER TABLE empresas ADD COLUMN atividade_contratos BOOLEAN DEFAULT FALSE AFTER atividade_locacao;
