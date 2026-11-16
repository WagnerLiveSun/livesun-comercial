-- Integração de assinatura LiveSun. Aditiva; sem credenciais, sem alterar cobranças bancárias.


CREATE TABLE IF NOT EXISTS central_config_comercial (
	id INTEGER NOT NULL AUTO_INCREMENT,
	base_url VARCHAR(500) NOT NULL,
	token TEXT NOT NULL,
	hmac_secret TEXT NOT NULL,
	ativo BOOL NOT NULL,
	cache_ttl INTEGER NOT NULL,
	purga_habilitada BOOL NOT NULL DEFAULT false,
	PRIMARY KEY (id)
)

;


CREATE TABLE IF NOT EXISTS central_vinculos_comercial (
	empresa_id INTEGER NOT NULL AUTO_INCREMENT,
	cliente_id INTEGER NOT NULL,
	payload JSON NOT NULL,
	assinatura_id INTEGER NOT NULL,
	versao INTEGER NOT NULL,
	valido_ate DATETIME,
	PRIMARY KEY (empresa_id),
	UNIQUE (cliente_id)
)

;


CREATE TABLE IF NOT EXISTS central_eventos_comercial (
	evento_id VARCHAR(100) NOT NULL,
	recebido_em DATETIME NOT NULL,
	PRIMARY KEY (evento_id)
)

;
