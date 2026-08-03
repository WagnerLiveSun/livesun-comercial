-- Índices para performance do relatório de fluxo de caixa consolidado
-- Ajustado para os nomes reais das tabelas do projeto.

CREATE INDEX idx_lancamentos_empresa_vencimento
    ON lancamentos(empresa_id, data_vencimento);

CREATE INDEX idx_lancamentos_empresa_evento
    ON lancamentos(empresa_id, data_evento);

CREATE INDEX idx_lancamentos_empresa_status_vencimento
    ON lancamentos(empresa_id, status, data_vencimento);

CREATE INDEX idx_fluxo_contas_empresa_tipo_ativo
    ON fluxo_contas_modelo(empresa_id, tipo, ativo);
