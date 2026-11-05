-- Parametros opcionais da conta Asaas e origem da cobranca.
ALTER TABLE asaas_conta_config
    ADD COLUMN juros_mensal_percentual DECIMAL(5,2) NULL,
    ADD COLUMN multa_percentual DECIMAL(5,2) NULL;

ALTER TABLE asaas_cobrancas
    ADD COLUMN origem VARCHAR(20) NOT NULL DEFAULT 'lancamento',
    ADD COLUMN nfse_emissao_id INT NULL,
    ADD COLUMN juros_mensal_percentual DECIMAL(5,2) NULL,
    ADD COLUMN multa_percentual DECIMAL(5,2) NULL,
    ADD INDEX idx_asaas_cobranca_nfse (empresa_id, nfse_emissao_id),
    ADD CONSTRAINT fk_asaas_cobranca_nfse
        FOREIGN KEY (nfse_emissao_id) REFERENCES nfse_nacional_emissoes(id);
