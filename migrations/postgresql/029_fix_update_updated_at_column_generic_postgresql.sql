-- ============================================================================
-- LiveSun Comercial - 029 - Corrige trigger update_updated_at_column genérico
-- ============================================================================
-- PROBLEMA:
--   A função security.update_updated_at_column() gravava SEMPRE em
--   NEW.atualizado_em. Porém as tabelas users, role_permissions e
--   user_permission_overrides possuem a coluna updated_at (não atualizado_em).
--   Todo UPDATE nessas tabelas falhava com:
--     psycopg2.errors.UndefinedColumn: record "new" has no field "atualizado_em"
--   Ex.: excluir_empresa -> User.query...update({'is_active': False}).
--
-- CORREÇÃO:
--   A função passa a detectar, via to_jsonb(NEW), qual das colunas de timestamp
--   existe na tabela e atualiza somente a(s) presente(s). Assim cobre tanto
--   updated_at quanto atualizado_em, sem precisar recriar os triggers.
--
-- EXECUÇÃO:
--   Conectar ao database comercial no MontuDB como comercial_db_owner (ou postgres).
--   A role livesun_api NÃO pode executar este DDL (sem CREATE no schema security).
-- ============================================================================

CREATE OR REPLACE FUNCTION security.update_updated_at_column()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
DECLARE
    v_row jsonb;
BEGIN
    v_row := to_jsonb(NEW);

    IF v_row ? 'atualizado_em' THEN
        NEW.atualizado_em := CURRENT_TIMESTAMP;
    END IF;

    IF v_row ? 'updated_at' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$function$;

-- Mantém o owner técnico e garante execução pela role da aplicação.
ALTER FUNCTION security.update_updated_at_column() OWNER TO comercial_db_owner;
REVOKE ALL ON FUNCTION security.update_updated_at_column() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION security.update_updated_at_column() TO livesun_api;

-- FIM DO SCRIPT
