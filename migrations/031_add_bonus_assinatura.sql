-- MIGRACAO 031: Bonificação de assinatura (acesso liberado sem limite de dias)
-- Colunas na tabela assinatura_empresa para liberar o uso da empresa
-- independentemente do processo de assinatura/cobrança.

ALTER TABLE assinatura_empresa
ADD COLUMN bonus_liberado TINYINT(1) NOT NULL DEFAULT 0;

ALTER TABLE assinatura_empresa
ADD COLUMN bonus_motivo VARCHAR(255) NULL;

ALTER TABLE assinatura_empresa
ADD COLUMN bonus_concedido_em DATETIME NULL;

CREATE INDEX idx_assinatura_bonus_liberado ON assinatura_empresa (bonus_liberado);
