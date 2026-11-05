-- Identificacao do provedor de cobranca e integracao opcional Banco Inter.
ALTER TABLE contas_banco
    ADD COLUMN codigo_banco VARCHAR(3) NULL,
    ADD INDEX idx_contas_banco_codigo (codigo_banco);

CREATE TABLE IF NOT EXISTS inter_conta_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    cobranca_habilitada BOOLEAN NULL DEFAULT NULL,
    ambiente VARCHAR(20) NULL,
    client_id_criptografado TEXT NULL,
    client_secret_criptografado TEXT NULL,
    certificado_criptografado TEXT NULL,
    chave_privada_criptografada TEXT NULL,
    webhook_token_criptografado TEXT NULL,
    juros_mensal_percentual DECIMAL(5,2) NULL,
    multa_percentual DECIMAL(5,2) NULL,
    ativo BOOLEAN NULL DEFAULT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_inter_conta_config_conta (conta_banco_id),
    INDEX idx_inter_config_empresa (empresa_id),
    CONSTRAINT fk_inter_config_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_inter_config_conta FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inter_cobrancas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    lancamento_id INT NOT NULL,
    entidade_id INT NOT NULL,
    codigo_solicitacao VARCHAR(100) NULL,
    seu_numero VARCHAR(50) NOT NULL,
    nosso_numero VARCHAR(50) NULL,
    valor DECIMAL(15,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    status_inter VARCHAR(40) NULL,
    status_interno VARCHAR(40) NOT NULL DEFAULT 'pendente',
    linha_digitavel VARCHAR(150) NULL,
    codigo_barras VARCHAR(100) NULL,
    qr_code TEXT NULL,
    pdf_url TEXT NULL,
    origem VARCHAR(20) NOT NULL DEFAULT 'lancamento',
    nfse_emissao_id INT NULL,
    juros_mensal_percentual DECIMAL(5,2) NULL,
    multa_percentual DECIMAL(5,2) NULL,
    payload TEXT NULL,
    mensagem_erro TEXT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_inter_cobranca_seu_numero (empresa_id, seu_numero),
    UNIQUE KEY uq_inter_cobranca_codigo (empresa_id, codigo_solicitacao),
    INDEX idx_inter_cobranca_lancamento (empresa_id, lancamento_id),
    CONSTRAINT fk_inter_cobranca_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_inter_cobranca_conta FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),
    CONSTRAINT fk_inter_cobranca_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_inter_cobranca_entidade FOREIGN KEY (entidade_id) REFERENCES entidades(id),
    CONSTRAINT fk_inter_cobranca_nfse FOREIGN KEY (nfse_emissao_id) REFERENCES nfse_nacional_emissoes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inter_webhook_eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    evento_id VARCHAR(120) NOT NULL,
    codigo_solicitacao VARCHAR(100) NULL,
    payload TEXT NULL,
    status_processamento VARCHAR(30) NOT NULL DEFAULT 'recebido',
    mensagem_erro TEXT NULL,
    recebido_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    processado_em DATETIME NULL,
    UNIQUE KEY uq_inter_webhook_empresa_evento (empresa_id, evento_id),
    INDEX idx_inter_webhook_codigo (codigo_solicitacao),
    CONSTRAINT fk_inter_webhook_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
