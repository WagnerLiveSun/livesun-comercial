-- MIGRACAO 009: Estruturas da etapa comercial
-- Premissas aprovadas:
-- - Gateway fase 1: Asaas
-- - Carencia inicial: 7 dias
-- - Efetivacao upgrade/downgrade: apos 30 dias
-- - Catalogo comercial inicial v1

-- ============================================
-- 1) Catalogo de planos comercial (versionado)
-- ============================================
CREATE TABLE IF NOT EXISTS catalogo_planos_comercial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_plano VARCHAR(30) NOT NULL,
    nome_exibicao VARCHAR(80) NOT NULL,
    versao_oferta INT NOT NULL DEFAULT 1,
    periodicidade VARCHAR(20) NOT NULL DEFAULT 'mensal',
    preco DECIMAL(10,2) NOT NULL,
    moeda VARCHAR(10) NOT NULL DEFAULT 'BRL',
    limite_usuarios INT NULL,
    recursos_json TEXT NULL,
    ativo BOOLEAN NOT NULL DEFAULT 1,
    vigencia_inicio DATE NULL,
    vigencia_fim DATE NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_catalogo_plano_periodo_versao (codigo_plano, periodicidade, versao_oferta),
    INDEX idx_catalogo_plano (codigo_plano),
    INDEX idx_catalogo_periodicidade (periodicidade),
    INDEX idx_catalogo_ativo (ativo),
    INDEX idx_catalogo_versao (versao_oferta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2) Assinatura atual por empresa
-- ============================================
CREATE TABLE IF NOT EXISTS assinatura_empresa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    catalogo_plano_id INT NULL,
    plano_codigo VARCHAR(30) NOT NULL DEFAULT 'premium',
    ciclo_cobranca VARCHAR(20) NOT NULL DEFAULT 'mensal',
    status VARCHAR(20) NOT NULL DEFAULT 'trial',
    gateway VARCHAR(30) NOT NULL DEFAULT 'asaas',
    gateway_customer_id VARCHAR(120) NULL,
    gateway_subscription_id VARCHAR(120) NULL,
    data_inicio DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_renovacao DATE NULL,
    data_fim_trial DATE NULL,
    carencia_dias INT NOT NULL DEFAULT 7,
    data_limite_carencia DATE NULL,
    bloqueio_nivel VARCHAR(20) NOT NULL DEFAULT 'nenhum',
    bloqueado_desde DATETIME NULL,
    motivo_status VARCHAR(255) NULL,
    politica_efetivacao_dias INT NOT NULL DEFAULT 30,
    proximo_plano_codigo VARCHAR(30) NULL,
    mudanca_plano_solicitada_em DATETIME NULL,
    mudanca_plano_efetivar_em DATETIME NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_assinatura_empresa_atual (empresa_id),
    INDEX idx_assinatura_status (status),
    INDEX idx_assinatura_plano (plano_codigo),
    INDEX idx_assinatura_vencimento (data_vencimento),
    INDEX idx_assinatura_gateway (gateway),
    INDEX idx_assinatura_mudanca_efetivar (mudanca_plano_efetivar_em),
    CONSTRAINT fk_assinatura_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_assinatura_catalogo_plano FOREIGN KEY (catalogo_plano_id) REFERENCES catalogo_planos_comercial(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3) Cobrancas recorrentes
-- ============================================
CREATE TABLE IF NOT EXISTS cobranca_recorrente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    assinatura_id INT NOT NULL,
    gateway VARCHAR(30) NOT NULL DEFAULT 'asaas',
    gateway_cobranca_id VARCHAR(120) NULL,
    referencia_interna VARCHAR(120) NOT NULL,
    competencia_ano INT NOT NULL,
    competencia_mes INT NOT NULL,
    periodicidade VARCHAR(20) NOT NULL DEFAULT 'mensal',
    valor_previsto DECIMAL(10,2) NOT NULL,
    valor_pago DECIMAL(10,2) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    data_emissao DATE NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATETIME NULL,
    tentativas_pagamento INT NOT NULL DEFAULT 0,
    ultimo_erro VARCHAR(255) NULL,
    payload_gateway TEXT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_cobranca_referencia_interna (referencia_interna),
    UNIQUE KEY uq_cobranca_gateway_id (gateway_cobranca_id),
    INDEX idx_cobranca_empresa (empresa_id),
    INDEX idx_cobranca_assinatura (assinatura_id),
    INDEX idx_cobranca_status (status),
    INDEX idx_cobranca_vencimento (data_vencimento),
    INDEX idx_cobranca_competencia (competencia_ano, competencia_mes),
    INDEX idx_cobranca_empresa_status_venc (empresa_id, status, data_vencimento),
    CONSTRAINT fk_cobranca_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_cobranca_assinatura FOREIGN KEY (assinatura_id) REFERENCES assinatura_empresa(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4) Eventos de cobranca (webhook/auditoria)
-- ============================================
CREATE TABLE IF NOT EXISTS evento_cobranca (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NULL,
    assinatura_id INT NULL,
    cobranca_id INT NULL,
    gateway VARCHAR(30) NOT NULL DEFAULT 'asaas',
    event_id_externo VARCHAR(150) NOT NULL,
    tipo_evento VARCHAR(80) NOT NULL,
    status_processamento VARCHAR(20) NOT NULL DEFAULT 'recebido',
    recebido_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    processado_em DATETIME NULL,
    payload TEXT NULL,
    mensagem_erro VARCHAR(255) NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_evento_cobranca_gateway_evento (gateway, event_id_externo),
    INDEX idx_evento_empresa (empresa_id),
    INDEX idx_evento_assinatura (assinatura_id),
    INDEX idx_evento_cobranca (cobranca_id),
    INDEX idx_evento_tipo (tipo_evento),
    INDEX idx_evento_status (status_processamento),
    INDEX idx_evento_recebido (recebido_em),
    CONSTRAINT fk_evento_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_evento_assinatura FOREIGN KEY (assinatura_id) REFERENCES assinatura_empresa(id),
    CONSTRAINT fk_evento_cobranca FOREIGN KEY (cobranca_id) REFERENCES cobranca_recorrente(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5) Historico de mudanca de plano
-- ============================================
CREATE TABLE IF NOT EXISTS historico_mudanca_plano (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    assinatura_id INT NOT NULL,
    plano_origem VARCHAR(30) NOT NULL,
    plano_destino VARCHAR(30) NOT NULL,
    tipo_mudanca VARCHAR(20) NOT NULL,
    regra_efetivacao VARCHAR(30) NOT NULL DEFAULT 'apos_30_dias',
    solicitado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    efetivado_em DATETIME NULL,
    solicitado_por_user_id INT NULL,
    executado_por_user_id INT NULL,
    observacoes TEXT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_hist_empresa (empresa_id),
    INDEX idx_hist_assinatura (assinatura_id),
    INDEX idx_hist_tipo (tipo_mudanca),
    INDEX idx_hist_solicitado (solicitado_em),
    INDEX idx_hist_efetivado (efetivado_em),
    CONSTRAINT fk_hist_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_hist_assinatura FOREIGN KEY (assinatura_id) REFERENCES assinatura_empresa(id),
    CONSTRAINT fk_hist_solicitado_por FOREIGN KEY (solicitado_por_user_id) REFERENCES users(id),
    CONSTRAINT fk_hist_executado_por FOREIGN KEY (executado_por_user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 6) Notificacoes comerciais
-- ============================================
CREATE TABLE IF NOT EXISTS notificacao_comercial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    assinatura_id INT NULL,
    tipo VARCHAR(50) NOT NULL,
    canal VARCHAR(20) NOT NULL DEFAULT 'email',
    destinatario VARCHAR(150) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    agendada_para DATETIME NULL,
    enviada_em DATETIME NULL,
    tentativas INT NOT NULL DEFAULT 0,
    erro VARCHAR(255) NULL,
    payload TEXT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_notif_empresa (empresa_id),
    INDEX idx_notif_assinatura (assinatura_id),
    INDEX idx_notif_tipo (tipo),
    INDEX idx_notif_status (status),
    INDEX idx_notif_agendada (agendada_para),
    CONSTRAINT fk_notif_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_notif_assinatura FOREIGN KEY (assinatura_id) REFERENCES assinatura_empresa(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
SELECT * FROM (
    SELECT
        'basic' AS codigo_plano,
        'Basico' AS nome_exibicao,
        1 AS versao_oferta,
        'mensal' AS periodicidade,
        49.00 AS preco,
        'BRL' AS moeda,
        2 AS limite_usuarios,
           '{"allow_advanced_cashflow_reports":false,"allow_imports":false,"allow_conciliation":false,"allow_commissions":false,"allow_governance":false}',
        1 AS ativo,
        CURDATE() AS vigencia_inicio
    UNION ALL
    SELECT 'intermediate', 'Intermediario', 1, 'mensal', 129.00, 'BRL', 5,
           '{"allow_advanced_cashflow_reports":true,"allow_imports":true,"allow_conciliation":true,"allow_commissions":true,"allow_governance":false}',
           1, CURDATE()
    UNION ALL
    SELECT 'premium', 'Premium', 1, 'mensal', 249.00, 'BRL', NULL,
           '{"allow_advanced_cashflow_reports":true,"allow_imports":true,"allow_conciliation":true,"allow_commissions":true,"allow_governance":true}',
           1, CURDATE()
    UNION ALL
    SELECT 'basic', 'Basico', 1, 'anual', 490.00, 'BRL', 2,
           '{"allow_advanced_cashflow_reports":false,"allow_imports":false,"allow_conciliation":false,"allow_commissions":false,"allow_governance":false}',
           1, CURDATE()
    UNION ALL
    SELECT 'intermediate', 'Intermediario', 1, 'anual', 1290.00, 'BRL', 5,
           '{"allow_advanced_cashflow_reports":true,"allow_imports":true,"allow_conciliation":true,"allow_commissions":true,"allow_governance":false}',
           1, CURDATE()
    UNION ALL
    SELECT 'premium', 'Premium', 1, 'anual', 2490.00, 'BRL', NULL,
           '{"allow_advanced_cashflow_reports":true,"allow_imports":true,"allow_conciliation":true,"allow_commissions":true,"allow_governance":true}',
           1, CURDATE()
) AS seed
WHERE NOT EXISTS (
    SELECT 1
    FROM catalogo_planos_comercial c
    WHERE c.codigo_plano = seed.codigo_plano
      AND c.periodicidade = seed.periodicidade
      AND c.versao_oferta = seed.versao_oferta
);
