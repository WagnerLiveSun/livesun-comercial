DROP TABLE IF EXISTS empresa_fiscal_itens;

CREATE TABLE empresa_fiscal_itens (
	id INT NOT NULL AUTO_INCREMENT,
	empresa_id INT NOT NULL,
	tipo VARCHAR(32) NOT NULL,
	valor VARCHAR(120) NOT NULL,
	principal TINYINT(1) NOT NULL DEFAULT 0,
	criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
	atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uq_empresa_fiscal_tipo_valor (empresa_id, tipo, valor),
	KEY idx_empresa_fiscal_empresa_tipo (empresa_id, tipo),
	KEY idx_empresa_fiscal_empresa_principal (empresa_id, tipo, principal),
	CONSTRAINT fk_empresa_fiscal_itens_empresa FOREIGN KEY (empresa_id) REFERENCES empresas (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
