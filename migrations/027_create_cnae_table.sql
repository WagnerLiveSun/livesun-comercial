-- Migração 027: Criar tabela nfse_cnae_referencia para CNAE
-- Data: 2026-07-29

CREATE TABLE IF NOT EXISTS nfse_cnae_referencia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    denominacao VARCHAR(500) NOT NULL,
    secao VARCHAR(2),
    divisao VARCHAR(5),
    grupo VARCHAR(10),
    classe VARCHAR(10),
    subclasse VARCHAR(20),
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_nfse_cnae_codigo (codigo),
    INDEX idx_nfse_cnae_codigo (codigo),
    INDEX idx_nfse_cnae_denominacao (denominacao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
