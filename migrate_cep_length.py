"""
Script para aumentar o tamanho da coluna endereco_cep na tabela entidades
de VARCHAR(8) para VARCHAR(9)
"""
import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import app, db
from models import Entidade

def migrate():
    with app.app_context():
        try:
            # Executar a alteração direta no banco
            db.session.execute(db.text("ALTER TABLE entidades MODIFY COLUMN endereco_cep VARCHAR(9)"))
            db.session.commit()
            print("✓ Coluna endereco_cep alterada para VARCHAR(9) com sucesso")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Erro ao alterar coluna: {e}")
            return False
    return True

if __name__ == '__main__':
    print("Iniciando migração do tamanho da coluna endereco_cep...")
    if migrate():
        print("Migração concluída com sucesso!")
    else:
        print("Migração falhou!")
        sys.exit(1)
