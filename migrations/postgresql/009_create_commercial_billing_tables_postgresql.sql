-- MIGRACAO 009: Estruturas da etapa comercial - PostgreSQL
-- Premissas aprovadas:
-- - Gateway fase 1: Asaas
-- - Carencia inicial: 7 dias
-- - Efetivacao upgrade/downgrade: apos 30 dias
-- - Catalogo comercial inicial v1

-- ============================================
-- 1) Catalogo de planos comercial (versionado)
-- ============================================
CREATE TABLE IF NOT EXISTS catalogo_planos_comercial (
    id SERIAL PRIMARY KEY,
    codigo_plano VARCHAR(30) NOT NULL,
    nome_exibicao VARCHAR(80) NOT NULL,
    versao_oferta INTEGER NOT NULL DEFAULT 1,
    periodicidade VARCHAR(20) NOT NULL DEFAULT 'mensal',
    preco NUMERIC(10,2) NOT NULL,
    moeda VARCHAR(10) NOT NULL DEFAULT 'BRL',
    limite_usuarios INTEGER,
    recursos_json TEXT,
    ativo BOOLEAN NOT NULL DEFAULT true,
    vigencia_inicio DATE,
    vigencia_fim DATE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_catalogo_plano_periodo_versao UNIQUE (codigo_plano, periodicidade, versao_oferta)
);

CREATE INDEX idx_catalogo_plano ON catalogo_planos_comercial(codigo_plano);
CREATE INDEX idx_catalogo_periodicidade ON catalogo_planos_comercial(periodicidade);
CREATE INDEX idx_catalogo_ativo ON catalogo_planos_comercial(ativo);
CREATE INDEX idx_catalogo_versao ON catalogo_planos_comercial(versao_oferta);

CREATE TRIGGER update_catalogo_planos_comercial_atualizado_em
    BEFORE UPDATE ON catalogo_planos_comercial
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 2) Assinatura atual por empresa
-- ============================================
CREATE TABLE IF NOT EXISTS assinatura_empresa (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    catalogo_plano_id INTEGER,
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
    carencia_dias INTEGER NOT NULL DEFAULT 7,
    data_limite_carencia DATE,
    bloqueio_nivel VARCHAR(20) NOT NULL DEFAULT 'nenhum',
    bloqueado_desde TIMESTAMP,
    motivo_status VARCHAR(255),
    politica_efetivacao_dias INTEGER NOT NULL DEFAULT 30,
    proximo_plano_codigo VARCHAR(30),
    mudanca_plano_solicitada_em TIMESTAMP,
    mudanca_plano_efetivar_em TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_assinatura_empresa_atual UNIQUE (empresa_id),
    CONSTRAINT fk_assinatura_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_assinatura_catalogo_plano FOREIGN KEY (catalogo_plano_id) REFERENCES catalogo_planos_comercial(id)
);

CREATE INDEX idx_assinatura_status ON assinatura_empresa(status);
CREATE INDEX idx_assinatura_plano ON assinatura_empresa(plano_codigo);
CREATE INDEX idx_assinatura_vencimento ON assinatura_empresa(data_vencimento);
CREATE INDEX idx_assinatura_gateway ON assinatura_empresa(gateway);
CREATE INDEX idx_assinatura_mudanca_efetivar ON assinatura_empresa(mudanca_plano_efetivar_em);

CREATE TRIGGER update_assinatura_empresa_atualizado_em
    BEFORE UPDATE ON assinatura_empresa
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 3) Cobrancas recorrentes
-- ============================================
CREATE TABLE IF NOT EXISTS cobranca_recorrente (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    assinatura_id INTEGER NOT NULL,
    gateway VARCHAR(30) NOT NULL DEFAULT 'asaas',
    gateway_cobranca_id VARCHAR(120),
    referencia_interna VARCHAR(120) NOT NULL,
    competencia_ano INTEGER NOT NULL,
    competencia_mes INTEGER NOT NULL,
    periodicidade VARCHAR(20) NOT NULL DEFAULT 'mensal',
    valor_previsto NUMERIC(10,2) NOT NULL,
    valor_pago NUMERIC(10,2),
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    data_emissao DATE,
    data_vencimento DATE NOT NULL,
    data_pagamento TIMESTAMP,
    tentativas_pagamento INTEGER NOT NULL DEFAULT 0,
    ultimo_erro VARCHAR(255),
    payload_gateway TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_cobranca_referencia_interna UNIQUE (referencia_interna),
    CONSTRAINT uq_cobranca_gateway_id UNIQUE (gateway_cobranca_id),
    CONSTRAINT fk_cobranca_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_cobranca_assinatura FOREIGN KEY (assinatura_id) REFERENCES assinatura_empresa(id)
);

CREATE INDEX idx_cobranca_empresa ON cobranca_recorrente(empresa_id);
CREATE INDEX idx_cobranca_assinatura ON cobranca_recorrente(assinatura_id);
CREATE INDEX idx_cobranca_status ON cobranca_recorrente(status);
CREATE INDEX idx_cobranca_vencimento ON cobranca_recorrente(data_vencimento);
CREATE INDEX idx_cobranca_competencia ON cobranca_recorrente(competencia_ano, competencia_mes);
CREATE INDEX idx_cobranca_empresa_status_venc ON cobranca_recorrente(empresa_id, status, data_vencimento);

CREATE TRIGGER update_cobranca_recorrente_atualizado_em
    BEFORE UPDATE ON cobranca_recorrente
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4) Eventos de cobranca (webhook/auditoria)
-- ============================================
CREATE TABLE IF NOT EXISTS evento_cobranca (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER,
    assinatura_id INTEGER,
    cobranca_id INTEGER,
    gateway VARCHAR(30) NOT NULL DEFAULT 'asaas',
    event_id_externo VARCHAR(150) NOT NULL,
    tipo_evento VARCHAR(80) NOT NULL,
    status_processamento VARCHAR(20) NOT NULL DEFAULT 'recebido',
    recebido_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processado_em TIMESTAMP,
    payload TEXT,
    mensagem_erro VARCHAR(255),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_evento_cobranca_gateway_evento UNIQUE (gateway, event_id_externo),
    CONSTRAINT fk_evento_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_evento_assinatura FOREIGN KEY (assinatura_id) REFERENCES assinatura_empresa(id),
    CONSTRAINT fk_evento_cobranca FOREIGN KEY (cobranca_id) REFERENCES cobranca_recorrente(id)
);

CREATE INDEX idx_evento_empresa ON evento_cobranca(empresa_id);
CREATE INDEX idx_evento_assinatura ON evento_cobranca(assinatura_id);
CREATE INDEX idx_evento_cobranca ON evento_cobranca(cobranca_id);
CREATE INDEX idx_evento_tipo ON evento_cobranca(tipo_evento);
CREATE INDEX idx_evento_status ON evento_cobranca(status_processamento);
CREATE INDEX idx_evento_recebido ON evento_cobranca(recebido_em);

CREATE TRIGGER update_evento_cobranca_atualizado_em
    BEFORE UPDATE ON evento_cobranca
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 5) Historico de mudanca de plano
-- ============================================
CREATE TABLE IF NOT EXISTS historico_mudanca_plano (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    assinatura_id INTEGER NOT NULL,
    plano_origem VARCHAR(30) NOT NULL,
    plano_destino VARCHAR(30) NOT NULL,
    tipo_mudanca VARCHAR(20) NOT NULL,
    regra_efetivacao VARCHAR(30) NOT NULL DEFAULT 'apos_30_dias',
    solicitado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    efetivado_em TIMESTAMP,
    solicitado_por_user_id INTEGER,
    executado_por_user_id INTEGER,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hist_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_hist_assinatura FOREIGN KEY (assinatura_id) REFERENCES assinatura_empresa(id),
    CONSTRAINT fk_hist_solicitado_por FOREIGN KEY (solicitado_por_user_id) REFERENCES users(id),
    CONSTRAINT fk_hist_executado_por FOREIGN KEY (executado_por_user_id) REFERENCES users(id)
);

CREATE INDEX idx_hist_empresa ON historico_mudanca_plano(empresa_id);
CREATE INDEX idx_hist_assinatura ON historico_mudanca_plano(assinatura_id);
CREATE INDEX idx_hist_tipo ON historico_mudanca_plano(tipo_mudanca);
CREATE INDEX idx_hist_solicitado ON historico_mudanca_plano(solicitado_em);
CREATE INDEX idx_hist_efetivado ON historico_mudanca_plano(efetivado_em);

CREATE TRIGGER update_historico_mudanca_plano_atualizado_em
    BEFORE UPDATE ON historico_mudanca_plano
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6) Notificacoes comerciais
-- ============================================
CREATE TABLE IF NOT EXISTS notificacao_comercial (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    assinatura_id INTEGER,
    tipo VARCHAR(50) NOT NULL,
    canal VARCHAR(20) NOT NULL DEFAULT 'email',
    destinatario VARCHAR(150),
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    agendada_para TIMESTAMP,
    enviada_em TIMESTAMP,
    tentativas INTEGER NOT NULL DEFAULT 0,
    erro VARCHAR(255),
    payload TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notif_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_notif_assinatura FOREIGN KEY (assinatura_id) REFERENCES assinatura_empresa(id)
);

CREATE INDEX idx_notif_empresa ON notificacao_comercial(empresa_id);
CREATE INDEX idx_notif_assinatura ON notificacao_comercial(assinatura_id);
CREATE INDEX idx_notif_tipo ON notificacao_comercial(tipo);
CREATE INDEX idx_notif_status ON notificacao_comercial(status);
CREATE INDEX idx_notif_agendada ON notificacao_comercial(agendada_para);

CREATE TRIGGER update_notificacao_comercial_atualizado_em
    BEFORE UPDATE ON notificacao_comercial
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 7) Seed do catalogo comercial v1 aprovado
-- ============================================
INSERT INTO catalogo_planos_comercial (
    codigo_plano,
    nome_exibicao,
    versao_oferta,
    periodicidade,
    preco,
    moeda,
    limite_usuarios,
    recursos_json,
    ativo,
    vigencia_inicio
)
VALUES
    ('basic', 'Basico', 1, 'mensal', 49.00, 'BRL', 2,
     '{"allow_advanced_cashflow_reports":false,"allow_imports":false,"allow_conciliation":false,"allow_commissions":false,"allow_governance":false}',
     true, CURRENT_DATE),
    ('intermediate', 'Intermediario', 1, 'mensal', 129.00, 'BRL', 5,
     '{"allow_advanced_cashflow_reports":true,"allow_imports":true,"allow_conciliation":true,"allow_commissions":true,"allow_governance":false}',
     true, CURRENT_DATE),
    ('premium', 'Premium', 1, 'mensal', 249.00, 'BRL', NULL,
     '{"allow_advanced_cashflow_reports":true,"allow_imports":true,"allow_conciliation":true,"allow_commissions":true,"allow_governance":true}',
     true, CURRENT_DATE),
    ('basic', 'Basico', 1, 'anual', 490.00, 'BRL', 2,
     '{"allow_advanced_cashflow_reports":false,"allow_imports":false,"allow_conciliation":false,"allow_commissions":false,"allow_governance":false}',
     true, CURRENT_DATE),
    ('intermediate', 'Intermediario', 1, 'anual', 1290.00, 'BRL', 5,
     '{"allow_advanced_cashflow_reports":true,"allow_imports":true,"allow_conciliation":true,"allow_commissions":true,"allow_governance":false}',
     true, CURRENT_DATE),
    ('premium', 'Premium', 1, 'anual', 2490.00, 'BRL', NULL,
     '{"allow_advanced_cashflow_reports":true,"allow_imports":true,"allow_conciliation":true,"allow_commissions":true,"allow_governance":true}',
     true, CURRENT_DATE)
ON CONFLICT (codigo_plano, periodicidade, versao_oferta) DO NOTHING;
