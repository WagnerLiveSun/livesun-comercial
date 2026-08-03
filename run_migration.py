import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import Empresa

app = create_app()

with app.app_context():
    # Verificar se a coluna já existe
    try:
        # Tentar fazer uma query que usa a coluna
        Empresa.query.first()
        print("Coluna atividade_contratos já existe no banco de dados.")
    except Exception as e:
        if "Unknown column 'empresas.atividade_contratos'" in str(e):
            print("Coluna atividade_contratos não existe. Adicionando...")
            
            # Executar a migration
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE empresas ADD COLUMN atividade_contratos BOOLEAN DEFAULT FALSE AFTER atividade_locacao"))
                conn.commit()
            
            print("Coluna atividade_contratos adicionada com sucesso!")
        else:
            print(f"Erro diferente: {e}")
            raise
