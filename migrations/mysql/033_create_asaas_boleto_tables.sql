-- Configuracao e rastreabilidade opcional de boletos Asaas.
-- Nenhuma conta bancaria existente precisa destes dados para continuar valida.

CREATE TABLE IF NOT EXISTS asaas_conta_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    cobranca_habilitada BOOLEAN NULL DEFAULT NULL,
    ambiente VARCHAR(20) NULL,
    api_key_criptografada TEXT NULL,
    webhook_token_criptografado TEXT NULL,
    ativo BOOLEAN NULL DEFAULT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_asaas_conta_config_conta (conta_banco_id),
    INDEX idx_asaas_config_empresa (empresa_id),
    CONSTRAINT fk_asaas_config_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_asaas_config_conta FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS asaas_clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    entidade_id INT NOT NULL,
    asaas_customer_id VARCHAR(80) NOT NULL,
    cpf_cnpj VARCHAR(20) NULL,
    nome_razao_social VARCHAR(200) NULL,
    email VARCHAR(200) NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_asaas_cliente_entidade (empresa_id, entidade_id),
    UNIQUE KEY uq_asaas_cliente_externo (empresa_id, asaas_customer_id),
    CONSTRAINT fk_asaas_cliente_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_asaas_cliente_entidade FOREIGN KEY (entidade_id) REFERENCES entidades(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS asaas_cobrancas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    conta_banco_id INT NOT NULL,
    lancamento_id INT NOT NULL,
    entidade_id INT NOT NULL,
    asaas_payment_id VARCHAR(80) NULL,
    asaas_customer_id VARCHAR(80) NULL,
    external_reference VARCHAR(150) NOT NULL,
    billing_type VARCHAR(20) NOT NULL DEFAULT 'BOLETO',
    valor DECIMAL(15,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    status_asaas VARCHAR(40) NULL,
    status_interno VARCHAR(40) NOT NULL DEFAULT 'pendente',
    invoice_url TEXT NULL,
    bank_slip_url TEXT NULL,
    identification_field VARCHAR(120) NULL,
    payload TEXT NULL,
    mensagem_erro TEXT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_asaas_cobranca_referencia (empresa_id, external_reference),
    UNIQUE KEY uq_asaas_cobranca_payment (empresa_id, asaas_payment_id),
    INDEX idx_asaas_cobranca_lancamento (empresa_id, lancamento_id),
    CONSTRAINT fk_asaas_cobranca_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_asaas_cobranca_conta FOREIGN KEY (conta_banco_id) REFERENCES contas_banco(id),
    CONSTRAINT fk_asaas_cobranca_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_asaas_cobranca_entidade FOREIGN KEY (entidade_id) REFERENCES entidades(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS asaas_webhook_eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    evento_id VARCHAR(120) NOT NULL,
    evento VARCHAR(80) NULL,
    asaas_payment_id VARCHAR(80) NULL,
    external_reference VARCHAR(150) NULL,
    payload TEXT NULL,
    status_processamento VARCHAR(30) NOT NULL DEFAULT 'recebido',
    mensagem_erro TEXT NULL,
    recebido_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    processado_em DATETIME NULL,
    UNIQUE KEY uq_asaas_webhook_empresa_evento (empresa_id, evento_id),
    INDEX idx_asaas_webhook_payment (asaas_payment_id),
    CONSTRAINT fk_asaas_webhook_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
