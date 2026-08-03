from sqlalchemy import create_engine, text
from config.config import Config
import sys

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

try:
    with engine.connect() as conn:
        result = conn.execute(text("DESCRIBE CTISS_BH"))
        columns = result.fetchall()
        print("Estrutura da tabela CTISS_BH:")
        for col in columns:
            print(f"  {col}")
except Exception as e:
    print(f"Erro ao verificar estrutura: {e}")
    sys.exit(1)
