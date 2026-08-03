-- Adicionar campo is_principal à tabela contas_banco
ALTER TABLE contas_banco ADD COLUMN is_principal BOOLEAN NOT NULL DEFAULT 0;
CREATE INDEX idx_contas_banco_is_principal ON contas_banco(is_principal);

-- Adicionar campo fluxo_conta_id à tabela entidades
ALTER TABLE entidades ADD COLUMN fluxo_conta_id INTEGER NULL;
ALTER TABLE entidades ADD CONSTRAINT fk_entidades_fluxo_conta FOREIGN KEY (fluxo_conta_id) REFERENCES fluxo_contas_modelo(id);
