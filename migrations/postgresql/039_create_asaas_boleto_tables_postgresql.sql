CREATE TABLE IF NOT EXISTS app.asaas_conta_config (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES app.empresas(id),
    conta_banco_id INTEGER NOT NULL UNIQUE REFERENCES app.contas_banco(id),
    cobranca_habilitada BOOLEAN NULL DEFAULT NULL,
    ambiente VARCHAR(20) NULL,
    api_key_criptografada TEXT NULL,
    webhook_token_criptografado TEXT NULL,
    ativo BOOLEAN NULL DEFAULT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.asaas_clientes (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES app.empresas(id),
    entidade_id INTEGER NOT NULL REFERENCES app.entidades(id),
    asaas_customer_id VARCHAR(80) NOT NULL,
    cpf_cnpj VARCHAR(20),
    nome_razao_social VARCHAR(200),
    email VARCHAR(200),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (empresa_id, entidade_id),
    UNIQUE (empresa_id, asaas_customer_id)
);

CREATE TABLE IF NOT EXISTS app.asaas_cobrancas (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES app.empresas(id),
    conta_banco_id INTEGER NOT NULL REFERENCES app.contas_banco(id),
    lancamento_id INTEGER NOT NULL REFERENCES app.lancamentos(id),
    entidade_id INTEGER NOT NULL REFERENCES app.entidades(id),
    asaas_payment_id VARCHAR(80),
    asaas_customer_id VARCHAR(80),
    external_reference VARCHAR(150) NOT NULL,
    billing_type VARCHAR(20) NOT NULL DEFAULT 'BOLETO',
    valor NUMERIC(15,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    status_asaas VARCHAR(40),
    status_interno VARCHAR(40) NOT NULL DEFAULT 'pendente',
    invoice_url TEXT,
    bank_slip_url TEXT,
    identification_field VARCHAR(120),
    payload TEXT,
    mensagem_erro TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (empresa_id, external_reference),
    UNIQUE (empresa_id, asaas_payment_id)
);

CREATE TABLE IF NOT EXISTS app.asaas_webhook_eventos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES app.empresas(id),
    evento_id VARCHAR(120) NOT NULL,
    evento VARCHAR(80),
    asaas_payment_id VARCHAR(80),
    external_reference VARCHAR(150),
    payload TEXT,
    status_processamento VARCHAR(30) NOT NULL DEFAULT 'recebido',
    mensagem_erro TEXT,
    recebido_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processado_em TIMESTAMP NULL,
    UNIQUE (empresa_id, evento_id)
);
