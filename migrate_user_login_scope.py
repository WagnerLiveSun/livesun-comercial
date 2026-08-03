"""
Migration for company-scoped usernames.

Changes:
1. Drop global unique index on users.username if present.
2. Ensure unique composite index on (empresa_id, username).
3. Keep email globally unique.
"""

from sqlalchemy import inspect, text

from src.app import create_app
from src.models import db


UNIQUE_INDEX_NAME = 'uq_users_empresa_username'


def _unique_constraints(inspector):
    try:
        return inspector.get_unique_constraints('users')
    except Exception:
        return []


def _indexes(inspector):
    try:
        return inspector.get_indexes('users')
    except Exception:
        return []


def run() -> bool:
    app = create_app()

    with app.app_context():
        inspector = inspect(db.engine)
        unique_constraints = _unique_constraints(inspector)
        indexes = _indexes(inspector)
        unique_names = {item.get('name') for item in unique_constraints}
        index_names = {item.get('name') for item in indexes}

        print('=' * 70)
        print('[USER MIGRATION] Ajustando login para empresa + usuário')
        print('=' * 70)

        try:
            with db.engine.begin() as conn:
                if 'username' in unique_names or 'username' in index_names:
                    conn.execute(text('ALTER TABLE users DROP INDEX username'))
                    print('  - Índice único global removido: username')
                else:
                    print('  = Índice único global username não encontrado')

                inspector = inspect(db.engine)
                unique_constraints = _unique_constraints(inspector)
                indexes = _indexes(inspector)
                unique_names = {item.get('name') for item in unique_constraints}
                index_names = {item.get('name') for item in indexes}

                if UNIQUE_INDEX_NAME not in unique_names and UNIQUE_INDEX_NAME not in index_names:
                    conn.execute(
                        text(
                            'ALTER TABLE users '
                            'ADD CONSTRAINT uq_users_empresa_username UNIQUE (empresa_id, username)'
                        )
                    )
                    print('  + Constraint criada: uq_users_empresa_username')
                else:
                    print('  = Constraint já existe: uq_users_empresa_username')

            print('[USER MIGRATION] Concluída com sucesso')
            return True
        except Exception as exc:
            print(f'[ERRO] Falha na migração: {exc}')
            return False


if __name__ == '__main__':
    ok = run()
    raise SystemExit(0 if ok else 1)
