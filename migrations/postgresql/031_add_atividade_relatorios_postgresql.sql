-- Adicionar coluna atividade_relatorios na tabela empresa
-- Data: 2026-10-21
-- Motivo: Adicionar controle de acesso ao módulo de relatórios

ALTER TABLE app.empresa
ADD COLUMN IF NOT EXISTS atividade_relatorios BOOLEAN DEFAULT FALSE;

-- Adicionar comentário
COMMENT ON COLUMN app.empresa.atividade_relatorios IS 'Controla acesso ao módulo de relatórios gerenciais e fiscais';
