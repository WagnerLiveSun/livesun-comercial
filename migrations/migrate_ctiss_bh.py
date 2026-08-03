from sqlalchemy import create_engine, inspect, text
from config.config import Config
import sys

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
inspector = inspect(engine)

# Verificar se tabela CTISS_BH existe
tables = inspector.get_table_names()
print('Tabelas no banco:', [t for t in tables if 'ctiss' in t.lower() or 'bh' in t.lower()])

if 'CTISS_BH' in tables:
    columns = inspector.get_columns('CTISS_BH')
    print('\nEstrutura da tabela CTISS_BH:')
    for col in columns:
        print(f"  {col['name']}: {col['type']} (nullable: {col['nullable']})")
    
    # Mostrar alguns dados
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM CTISS_BH LIMIT 5"))
        rows = result.fetchall()
        print('\nDados de exemplo (primeiras 5 linhas):')
        for row in rows:
            print(f"  {row}")
else:
    print('Tabela CTISS_BH não encontrada')
    sys.exit(1)
