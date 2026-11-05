ALTER TABLE app.asaas_conta_config
    ADD COLUMN IF NOT EXISTS juros_mensal_percentual NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS multa_percentual NUMERIC(5,2);

ALTER TABLE app.asaas_cobrancas
    ADD COLUMN IF NOT EXISTS origem VARCHAR(20) NOT NULL DEFAULT 'lancamento',
    ADD COLUMN IF NOT EXISTS nfse_emissao_id INTEGER,
    ADD COLUMN IF NOT EXISTS juros_mensal_percentual NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS multa_percentual NUMERIC(5,2);

CREATE INDEX IF NOT EXISTS idx_asaas_cobranca_nfse
    ON app.asaas_cobrancas (empresa_id, nfse_emissao_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_asaas_cobranca_nfse'
    ) THEN
        ALTER TABLE app.asaas_cobrancas
            ADD CONSTRAINT fk_asaas_cobranca_nfse
            FOREIGN KEY (nfse_emissao_id)
            REFERENCES app.nfse_nacional_emissoes(id);
    END IF;
END $$;
