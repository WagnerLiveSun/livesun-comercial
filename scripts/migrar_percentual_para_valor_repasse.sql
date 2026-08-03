-- Script de migração: Troca campo percentual_repasse por valor_repasse em entidades
-- Execute este script no banco de dados da aplicação

ALTER TABLE entidades ADD COLUMN valor_repasse DECIMAL(10,2) DEFAULT 0.00;

-- Copia valores existentes de percentual_repasse para valor_repasse (convertendo para valor fixo)
-- Supondo que o valor de referência seja o último valor_real de cada entidade (ajuste conforme necessário)
-- Exemplo genérico (ajuste para seu banco):
-- UPDATE entidades SET valor_repasse = (percentual_repasse/100) * (SELECT valor_real FROM lancamentos WHERE lancamentos.entidade_id = entidades.id ORDER BY data DESC LIMIT 1);

-- Após migração, remova o campo antigo se desejar:
-- ALTER TABLE entidades DROP COLUMN percentual_repasse;

-- Se não quiser migrar valores antigos, apenas deixe valor_repasse como 0.00 para todos.
