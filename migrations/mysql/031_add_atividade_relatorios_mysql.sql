-- Adicionar coluna atividade_relatorios na tabela empresa
-- Data: 2026-10-22
-- Motivo: Adicionar controle de acesso ao módulo de relatórios

ALTER TABLE empresas
ADD COLUMN atividade_relatorios BOOLEAN DEFAULT FALSE;
