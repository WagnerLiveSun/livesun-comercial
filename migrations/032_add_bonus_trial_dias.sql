-- MIGRACAO 032: Bonificação tipo trial com prazo determinado
ALTER TABLE assinatura_empresa
ADD COLUMN bonus_tipo VARCHAR(20) NULL; -- 'ilimitado' ou 'trial'

ALTER TABLE assinatura_empresa
ADD COLUMN bonus_dias INT NULL; -- dias de trial quando bonus_tipo = 'trial'
