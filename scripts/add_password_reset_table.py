#!/usr/bin/env python3
"""
Script para criar a tabela password_reset_codes no banco de dados.
"""
import sys
import os

# Adicionar diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.app import create_app
from src.models import db

def create_password_reset_table():
    """Cria a tabela password_reset_codes."""
    app = create_app('production')
    
    with app.app_context():
        # Criar todas as tabelas (incluindo a nova)
        db.create_all()
        print("✓ Tabela password_reset_codes criada com sucesso!")

if __name__ == "__main__":
    print("=" * 60)
    print("CRIAÇÃO DA TABELA PASSWORD_RESET_CODES")
    print("=" * 60)
    print()
    
    create_password_reset_table()
