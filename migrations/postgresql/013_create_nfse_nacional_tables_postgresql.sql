-- MIGRAÇÃO: tabelas do módulo NFS-e Nacional - PostgreSQL

CREATE TABLE IF NOT EXISTS nfse_nacional_configuracoes (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    ambiente VARCHAR(20) NOT NULL DEFAULT 'homologacao',
    inscricao_municipal VARCHAR(30),
    codigo_municipio VARCHAR(10),
    regime_tributario VARCHAR(50),
    serie VARCHAR(20) DEFAULT '1',
    versao_layout VARCHAR(30) DEFAULT '1.0',
    endpoint_base VARCHAR(255),
    emissor_ativo BOOLEAN DEFAULT TRUE,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_nfse_config_empresa_ambiente UNIQUE (empresa_id, ambiente),
    CONSTRAINT fk_nfse_config_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

CREATE INDEX idx_nfse_config_empresa ON nfse_nacional_configuracoes(empresa_id);

CREATE TRIGGER update_nfse_nacional_configuracoes_atualizado_em
    BEFORE UPDATE ON nfse_nacional_configuracoes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS nfse_nacional_certificados (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    ambiente VARCHAR(20) NOT NULL DEFAULT 'homologacao',
    arquivo_nome VARCHAR(255) NOT NULL,
    caminho_arquivo VARCHAR(255),
    validade_em DATE,
    ativo BOOLEAN DEFAULT TRUE,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_nfse_cert_empresa_ambiente_arquivo UNIQUE (empresa_id, ambiente, arquivo_nome),
    CONSTRAINT fk_nfse_cert_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

CREATE INDEX idx_nfse_cert_empresa ON nfse_nacional_certificados(empresa_id);
CREATE INDEX idx_nfse_cert_validade ON nfse_nacional_certificados(validade_em);

CREATE TRIGGER update_nfse_nacional_certificados_atualizado_em
    BEFORE UPDATE ON nfse_nacional_certificados
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS nfse_nacional_integracoes_origem (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    origem_tipo VARCHAR(40) NOT NULL,
    origem_id VARCHAR(80),
    origem_referencia VARCHAR(120),
    canal_origem VARCHAR(40) NOT NULL DEFAULT 'manual',
    payload_origem TEXT,
    hash_idempotencia VARCHAR(80) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_nfse_origem_empresa_tipo_id_canal UNIQUE (empresa_id, origem_tipo, origem_id, canal_origem),
    CONSTRAINT fk_nfse_origem_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

CREATE INDEX idx_nfse_origem_empresa ON nfse_nacional_integracoes_origem(empresa_id);
CREATE INDEX idx_nfse_origem_hash ON nfse_nacional_integracoes_origem(hash_idempotencia);

CREATE TRIGGER update_nfse_nacional_integracoes_origem_atualizado_em
    BEFORE UPDATE ON nfse_nacional_integracoes_origem
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS nfse_nacional_emissoes (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    configuracao_id INTEGER,
    certificado_id INTEGER,
    tomador_id INTEGER NOT NULL,
    servico_id INTEGER NOT NULL,
    integracao_origem_id INTEGER,
    lancamento_id INTEGER,
    ambiente VARCHAR(20) NOT NULL DEFAULT 'homologacao',
    numero_interno VARCHAR(50) NOT NULL,
    numero_nfse VARCHAR(30),
    chave_nfse VARCHAR(120),
    codigo_verificacao VARCHAR(40),
    protocolo VARCHAR(80),
    status_processamento VARCHAR(30) NOT NULL DEFAULT 'RASCUNHO',
    situacao_fiscal VARCHAR(30) NOT NULL DEFAULT 'PENDENTE',
    valor_servico NUMERIC(15,2) NOT NULL,
    valor_deducoes NUMERIC(15,2) DEFAULT 0.00,
    valor_iss NUMERIC(15,2) DEFAULT 0.00,
    servico_local_prestacao VARCHAR(20) NOT NULL DEFAULT 'emitente',
    tp_ret_issqn VARCHAR(2) NOT NULL DEFAULT '1',
    observacoes TEXT,
    xml_dps TEXT,
    xml_nfse TEXT,
    payload_envio TEXT,
    payload_retorno TEXT,
    log_tecnico TEXT,
    erro_retorno TEXT,
    hash_idempotencia VARCHAR(80) NOT NULL,
    versao_layout VARCHAR(30) DEFAULT '1.0',
    versao_xsd VARCHAR(30) DEFAULT '1.0',
    origem_tipo VARCHAR(40) NOT NULL DEFAULT 'MANUAL',
    origem_referencia VARCHAR(120),
    canal_origem VARCHAR(40) NOT NULL DEFAULT 'manual',
    criado_por_user_id INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_nfse_emissao_empresa_hash UNIQUE (empresa_id, hash_idempotencia),
    CONSTRAINT uq_nfse_emissao_empresa_numero_interno UNIQUE (empresa_id, numero_interno),
    CONSTRAINT fk_nfse_emissao_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_nfse_emissao_config FOREIGN KEY (configuracao_id) REFERENCES nfse_nacional_configuracoes(id),
    CONSTRAINT fk_nfse_emissao_cert FOREIGN KEY (certificado_id) REFERENCES nfse_nacional_certificados(id),
    CONSTRAINT fk_nfse_emissao_tomador FOREIGN KEY (tomador_id) REFERENCES entidades(id),
    CONSTRAINT fk_nfse_emissao_servico FOREIGN KEY (servico_id) REFERENCES servicos(id),
    CONSTRAINT fk_nfse_emissao_origem FOREIGN KEY (integracao_origem_id) REFERENCES nfse_nacional_integracoes_origem(id),
    CONSTRAINT fk_nfse_emissao_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id),
    CONSTRAINT fk_nfse_emissao_user FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_nfse_emissao_empresa_status ON nfse_nacional_emissoes(empresa_id, status_processamento);
CREATE INDEX idx_nfse_emissao_empresa_nfse ON nfse_nacional_emissoes(empresa_id, numero_nfse);
CREATE INDEX idx_nfse_emissao_tomador ON nfse_nacional_emissoes(tomador_id);
CREATE INDEX idx_nfse_emissao_servico ON nfse_nacional_emissoes(servico_id);

CREATE TRIGGER update_nfse_nacional_emissoes_atualizado_em
    BEFORE UPDATE ON nfse_nacional_emissoes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS nfse_nacional_fila (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    emissao_id INTEGER NOT NULL,
    status_fila VARCHAR(30) NOT NULL DEFAULT 'PENDENTE',
    tentativas INTEGER NOT NULL DEFAULT 0,
    proxima_tentativa_em TIMESTAMP,
    ultimo_erro TEXT,
    payload TEXT,
    processado_em TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_nfse_fila_empresa_emissao UNIQUE (empresa_id, emissao_id),
    CONSTRAINT fk_nfse_fila_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_nfse_fila_emissao FOREIGN KEY (emissao_id) REFERENCES nfse_nacional_emissoes(id) ON DELETE CASCADE
);

CREATE INDEX idx_nfse_fila_empresa_status ON nfse_nacional_fila(empresa_id, status_fila);

CREATE TRIGGER update_nfse_nacional_fila_atualizado_em
    BEFORE UPDATE ON nfse_nacional_fila
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS nfse_nacional_eventos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    emissao_id INTEGER NOT NULL,
    tipo_evento VARCHAR(40) NOT NULL,
    status_evento VARCHAR(30) NOT NULL DEFAULT 'registrado',
    protocolo VARCHAR(80),
    mensagem TEXT,
    payload_envio TEXT,
    payload_retorno TEXT,
    criado_por_user_id INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_nfse_evento_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_nfse_evento_emissao FOREIGN KEY (emissao_id) REFERENCES nfse_nacional_emissoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_nfse_evento_user FOREIGN KEY (criado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_nfse_evento_empresa_tipo ON nfse_nacional_eventos(empresa_id, tipo_evento);
CREATE INDEX idx_nfse_evento_emissao ON nfse_nacional_eventos(emissao_id);

CREATE TRIGGER update_nfse_nacional_eventos_atualizado_em
    BEFORE UPDATE ON nfse_nacional_eventos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
