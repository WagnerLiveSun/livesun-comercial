from sqlalchemy import create_engine
from config.config import Config
import sys
import os

# Detectar tipo de banco de dados
db_type = os.environ.get('DB_TYPE', 'mysql').lower()

if db_type == 'postgresql' or db_type == 'postgres':
    sql_file = 'migrations/postgresql/024_migrate_ctiss_bh_to_nfse_ctrib_mun_postgresql.sql'
else:
    sql_file = 'migrations/024_migrate_ctiss_bh_to_nfse_ctrib_mun.sql'

sql = open(sql_file, 'r', encoding='utf-8').read()
print(f'Using DB URI: {Config.SQLALCHEMY_DATABASE_URI}')
print(f'Using SQL file: {sql_file}')
print('Migrando dados de CTISS_BH para nfse_ctrib_mun_referencia...')
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
try:
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)
    print('Migration 024 applied successfully')
except Exception as e:
    print('Migration failed:', e)
    sys.exit(1)
