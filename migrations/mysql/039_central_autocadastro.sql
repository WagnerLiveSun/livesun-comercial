-- Outbox do autocadastro, sem alterar empresas ou assinaturas existentes.

CREATE TABLE IF NOT EXISTS central_cadastros_pendentes (
	id INTEGER NOT NULL AUTO_INCREMENT,
	empresa_id INTEGER NOT NULL,
	evento_id VARCHAR(50) NOT NULL,
	dados JSON NOT NULL,
	status VARCHAR(25) NOT NULL,
	solicitacao_id INTEGER,
	tentativas INTEGER NOT NULL,
	erro VARCHAR(100),
	proxima_tentativa DATETIME NOT NULL,
	criado_em DATETIME NOT NULL,
	vinculado_em DATETIME,
	PRIMARY KEY (id),
	UNIQUE (empresa_id),
	UNIQUE (evento_id)
)

;
