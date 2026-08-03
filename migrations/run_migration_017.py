from sqlalchemy import create_engine
from config.config import Config
import sys

sql = open('migrations/017_add_nfse_cert_removed_fields.sql', 'r', encoding='utf-8').read()
print('Using DB URI:', Config.SQLALCHEMY_DATABASE_URI)
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
try:
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)
    print('Migration 017 applied successfully')
except Exception as e:
    print('Migration failed:', e)
    sys.exit(1)
