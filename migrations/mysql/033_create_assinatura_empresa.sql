-- MIGRACAO 033: Criacao da tabela assinatura_empresa para MySQL
-- Esta migracao adiciona a tabela assinatura_empresa que
-- nao estava presente no banco MySQL (apenas no PostgreSQL).

CREATE TABLE IF NOT EXISTS assinatura_empresa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    catalogo_plano_id INT,
    plano_codigo VARCHAR(30) NOT NULL DEFAULT 'premium',
    ciclo_cobranca VARCHAR(20) NOT NULL DEFAULT 'mensal',
    status VARCHAR(20) NOT NULL DEFAULT 'trial',
    gateway VARCHAR(30) NOT NULL DEFAULT 'asaas',
    gateway_customer_id VARCHAR(120),
    gateway_subscription_id VARCHAR(120),
    data_inicio DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_renovacao DATE,
    data_fim_trial DATE,
    carencia_dias INT NOT NULL DEFAULT 7,
    data_limite_carencia DATE,
    bloqueio_nivel VARCHAR(20) NOT NULL DEFAULT 'nenhum',
    bloqueado_desde TIMESTAMP,
    motivo_status VARCHAR(255),
    politica_efetivacao_dias INT NOT NULL DEFAULT 30,
    proximo_plano_codigo VARCHAR(30),
    mudanca_plano_solicitada_em TIMESTAMP,
    mudanca_plano_efetivar_em TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_assinatura_empresa_atual UNIQUE (empresa_id),
    CONSTRAINT fk_assinatura_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_assinatura_catalogo_plano FOREIGN KEY (catalogo_plano_id) REFERENCES catalogo_planos_comercial(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_assinatura_status ON assinatura_empresa(status);
CREATE INDEX idx_assinatura_plano ON assinatura_empresa(plano_codigo);
CREATE INDEX idx_assinatura_vencimento ON assinatura_empresa(data_vencimento);
CREATE INDEX idx_assinatura_gateway ON assinatura_empresa(gateway);
CREATE INDEX idx_assinatura_mudanca_efetivar ON assinatura_empresa(mudanca_plano_efetivar_em);

CREATE TRIGGER update_assinatura_empresa_atualizado_em
    BEFORE UPDATE ON assinatura_empresa
    FOR EACH ROW
    SET atualizado_em = CURRENT_TIMESTAMP;
