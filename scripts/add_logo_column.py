#!/usr/bin/env python
"""
Script para adicionar a coluna logo_caminho à tabela empresas.
"""
import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app
from src.models import db

def add_logo_column():
    """Adiciona a coluna logo_caminho à tabela empresas."""
    app = create_app()
    
    with app.app_context():
        print("Adicionando coluna logo_caminho à tabela empresas...")
        
        # Verificar se a coluna já existe
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('empresas')]
        
        if 'logo_caminho' in columns:
            print("✓ Coluna logo_caminho já existe.")
            return
        
        # Adicionar a coluna usando SQL direto
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE empresas ADD COLUMN logo_caminho VARCHAR(255)"))
            conn.commit()
        
        print("✓ Coluna logo_caminho adicionada com sucesso!")

if __name__ == '__main__':
    add_logo_column()
