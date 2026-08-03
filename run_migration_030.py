import sys
sys.path.insert(0, 'D:\\App_LiveSun\\LiveSun_Comercial_X')

from src.app import create_app
from src.models import db

app = create_app()

with app.app_context():
    # Ler e executar a migração
    with open('migrations/030_add_nfse_emissao_cancelamento_fields.sql', 'r') as f:
        sql = f.read()
    
    try:
        db.session.execute(db.text(sql))
        db.session.commit()
        print("Migração executada com sucesso!")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao executar migração: {e}")
        sys.exit(1)
