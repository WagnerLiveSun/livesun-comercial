-- Identificacao do provedor de cobranca e integracao opcional Banco Inter.
ALTER TABLE app.contas_banco
    ADD COLUMN IF NOT EXISTS codigo_banco VARCHAR(3);
CREATE INDEX IF NOT EXISTS idx_contas_banco_codigo ON app.contas_banco (codigo_banco);

CREATE TABLE IF NOT EXISTS app.inter_conta_config (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES app.empresas(id),
    conta_banco_id INTEGER NOT NULL UNIQUE REFERENCES app.contas_banco(id),
    cobranca_habilitada BOOLEAN NULL DEFAULT NULL,
    ambiente VARCHAR(20) NULL,
    client_id_criptografado TEXT NULL,
    client_secret_criptografado TEXT NULL,
    certificado_criptografado TEXT NULL,
    chave_privada_criptografada TEXT NULL,
    webhook_token_criptografado TEXT NULL,
    juros_mensal_percentual NUMERIC(5,2) NULL,
    multa_percentual NUMERIC(5,2) NULL,
    ativo BOOLEAN NULL DEFAULT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.inter_cobrancas (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES app.empresas(id),
    conta_banco_id INTEGER NOT NULL REFERENCES app.contas_banco(id),
    lancamento_id INTEGER NOT NULL REFERENCES app.lancamentos(id),
    entidade_id INTEGER NOT NULL REFERENCES app.entidades(id),
    codigo_solicitacao VARCHAR(100),
    seu_numero VARCHAR(50) NOT NULL,
    nosso_numero VARCHAR(50),
    valor NUMERIC(15,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    status_inter VARCHAR(40),
    status_interno VARCHAR(40) NOT NULL DEFAULT 'pendente',
    linha_digitavel VARCHAR(150),
    codigo_barras VARCHAR(100),
    qr_code TEXT,
    pdf_url TEXT,
    origem VARCHAR(20) NOT NULL DEFAULT 'lancamento',
    nfse_emissao_id INTEGER REFERENCES app.nfse_nacional_emissoes(id),
    juros_mensal_percentual NUMERIC(5,2),
    multa_percentual NUMERIC(5,2),
    payload TEXT,
    mensagem_erro TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (empresa_id, seu_numero),
    UNIQUE (empresa_id, codigo_solicitacao)
);
CREATE INDEX IF NOT EXISTS idx_inter_cobranca_lancamento ON app.inter_cobrancas (empresa_id, lancamento_id);

CREATE TABLE IF NOT EXISTS app.inter_webhook_eventos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES app.empresas(id),
    evento_id VARCHAR(120) NOT NULL,
    codigo_solicitacao VARCHAR(100),
    payload TEXT,
    status_processamento VARCHAR(30) NOT NULL DEFAULT 'recebido',
    mensagem_erro TEXT,
    recebido_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processado_em TIMESTAMP NULL,
    UNIQUE (empresa_id, evento_id)
);
CREATE INDEX IF NOT EXISTS idx_inter_webhook_codigo ON app.inter_webhook_eventos (codigo_solicitacao);
