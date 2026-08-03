from sqlalchemy import create_engine
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.config import Config

sql = open('migrations/021_fix_nfse_emissao_tp_ret_issqn_default.sql', 'r', encoding='utf-8').read()
print('Using DB URI:', Config.SQLALCHEMY_DATABASE_URI)
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
try:
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)
    print('Migration 021 applied successfully')
except Exception as e:
    print('Migration failed:', e)
    sys.exit(1)