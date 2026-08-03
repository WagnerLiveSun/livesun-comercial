"""
Hardening multi-tenant isolation at database level.

What this migration does:
1. Adds empresa_id indexes (if missing) on financial/domain tables.
2. Corrects lancamentos.empresa_id based on entidade ownership when mismatched.
3. Prints cross-company inconsistencies for manual follow-up.
"""

from __future__ import annotations

from sqlalchemy import inspect, text

from src.app import create_app
from src.models import db


TABLES_WITH_EMPRESA = [
    'entidades',
    'fluxo_contas_modelo',
    'contas_banco',
    'lancamentos',
    'fluxo_caixa_previsto',
    'fluxo_caixa_realizado',
    'comissoes',
    'parametros_sistema',
]


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    cols = {c['name'] for c in inspector.get_columns(table_name)}
    return column_name in cols


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    indexes = {idx['name'] for idx in inspector.get_indexes(table_name)}
    return index_name in indexes


def run() -> bool:
    app = create_app()

    with app.app_context():
        inspector = inspect(db.engine)

        print('=' * 70)
        print('[TENANT MIGRATION] Iniciando hardening de isolamento por empresa')
        print('=' * 70)

        try:
            with db.engine.begin() as conn:
                # 1) Ensure indexes by empresa_id where possible.
                for table in TABLES_WITH_EMPRESA:
                    if not _table_exists(inspector, table):
                        print(f'- Tabela ausente, ignorando: {table}')
                        continue
                    if not _column_exists(inspector, table, 'empresa_id'):
                        print(f'- Coluna empresa_id ausente em {table}, ignorando índice')
                        continue

                    idx_name = f'idx_{table}_empresa_id'
                    if _index_exists(inspector, table, idx_name):
                        print(f'  ✓ Índice já existe: {idx_name}')
                        continue

                    conn.execute(text(f'CREATE INDEX {idx_name} ON {table} (empresa_id)'))
                    print(f'  + Índice criado: {idx_name}')

                # 2) Fix lancamentos ownership based on linked entidade.
                if _table_exists(inspector, 'lancamentos') and _table_exists(inspector, 'entidades'):
                    updated = conn.execute(
                        text(
                            """
                            UPDATE lancamentos l
                            JOIN entidades e ON e.id = l.entidade_id
                            SET l.empresa_id = e.empresa_id
                            WHERE l.empresa_id IS NULL OR l.empresa_id <> e.empresa_id
                            """
                        )
                    )
                    print(f'  + Lançamentos ajustados por entidade: {updated.rowcount}')

                # 2.1) Fix fluxo_conta cross-company references by matching codigo
                # within the lancamento company (choosing the smallest id when duplicated).
                if _table_exists(inspector, 'lancamentos') and _table_exists(inspector, 'fluxo_contas_modelo'):
                    updated_fluxo = conn.execute(
                        text(
                            """
                            UPDATE lancamentos l
                            JOIN fluxo_contas_modelo f_wrong ON f_wrong.id = l.fluxo_conta_id
                            JOIN (
                                SELECT f2.empresa_id, f2.codigo, MIN(f2.id) AS id_correto
                                FROM fluxo_contas_modelo f2
                                GROUP BY f2.empresa_id, f2.codigo
                            ) f_map ON f_map.empresa_id = l.empresa_id AND f_map.codigo = f_wrong.codigo
                            SET l.fluxo_conta_id = f_map.id_correto
                            WHERE l.empresa_id <> f_wrong.empresa_id
                            """
                        )
                    )
                    print(f'  + Lançamentos ajustados por fluxo/código: {updated_fluxo.rowcount}')

            # 3) Consistency report for cross-tenant references.
            inconsistencies = {
                'lancamentos_vs_contas_banco': db.session.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM lancamentos l
                        JOIN contas_banco cb ON cb.id = l.conta_banco_id
                        WHERE l.empresa_id <> cb.empresa_id
                        """
                    )
                ).scalar_one(),
                'lancamentos_vs_fluxo': db.session.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM lancamentos l
                        JOIN fluxo_contas_modelo f ON f.id = l.fluxo_conta_id
                        WHERE l.empresa_id <> f.empresa_id
                        """
                    )
                ).scalar_one(),
                'lancamentos_vs_entidades': db.session.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM lancamentos l
                        JOIN entidades e ON e.id = l.entidade_id
                        WHERE l.empresa_id <> e.empresa_id
                        """
                    )
                ).scalar_one(),
            }

            print('\n[RELATÓRIO] Inconsistências restantes:')
            for key, value in inconsistencies.items():
                print(f'  - {key}: {value}')

            print('\n[TENANT MIGRATION] Concluída com sucesso')
            return True

        except Exception as exc:
            print(f'\n[ERRO] Falha na migração: {exc}')
            return False


if __name__ == '__main__':
    ok = run()
    raise SystemExit(0 if ok else 1)
