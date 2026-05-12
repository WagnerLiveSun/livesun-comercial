-- MIGRACAO 012: Parcelas de compras (vinculo compra x lancamentos)

CREATE TABLE IF NOT EXISTS compras_nf_lancamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    compra_id INT NOT NULL,
    lancamento_id INT NOT NULL,
    parcela_numero INT NOT NULL,
    parcela_total INT NOT NULL,
    valor_parcela DECIMAL(15,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_compra_parcela (compra_id, parcela_numero),
    INDEX idx_compra_lanc_empresa (empresa_id),
    INDEX idx_compra_lanc_compra (compra_id),
    INDEX idx_compra_lanc_venc (data_vencimento),
    CONSTRAINT fk_compra_lanc_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_compra_lanc_compra FOREIGN KEY (compra_id) REFERENCES compras_nf_manual(id) ON DELETE CASCADE,
    CONSTRAINT fk_compra_lanc_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
