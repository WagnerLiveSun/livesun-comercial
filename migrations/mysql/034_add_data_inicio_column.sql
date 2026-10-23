-- MIGRACAO 034: Adicionar coluna data_inicio na tabela assinatura_empresa (MySQL)
-- A coluna data_inicio foi adicionada ao modelo Python (src/models/__init__.py)
-- mas nao existe no banco MySQL. Esta migration verifica e adiciona a coluna.

-- Verificar se a coluna data_inicio ja existe
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'assinatura_empresa' 
  AND table_schema = DATABASE() 
  AND column_name = 'data_inicio';

-- Se o resultado estiver vazio, execute:
ALTER TABLE assinatura_empresa 
ADD COLUMN data_inicio DATE NOT NULL AFTER gateway_subscription_id;

-- Atualizar trigger para MySQL
-- MySQL nao suporta EXECUTE FUNCTION como PostgreSQL, entao a trigger eh simples:
CREATE TRIGGER IF NOT EXISTS update_assinatura_empresa_atualizado_em
    BEFORE UPDATE ON assinatura_empresa
    FOR EACH ROW
    SET atualizado_em = CURRENT_TIMESTAMP;

-- Verificar se a coluna existe agora
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'assinatura_empresa' 
  AND table_schema = DATABASE() 
  AND column_name IN ('data_inicio', 'atualizado_em')
ORDER BY column_name;
