#!/usr/bin/env python3
"""Script para criar todas as tabelas no banco de dados da Hostinger usando Flask-SQLAlchemy"""

import os
import sys

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configurar variáveis de ambiente para a Hostinger (usa .env/secrets quando presentes)
os.environ.setdefault('DB_TYPE', 'mysql')
os.environ.setdefault('DB_HOST', '195.35.61.111')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('DB_USER', 'u951548013_LS_Comercial')
os.environ['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', '')
os.environ.setdefault('DB_NAME', 'u951548013_LS_Comercial')
os.environ.setdefault('FLASK_ENV', 'production')
os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'temp-secret-key-for-migration')

from src.app import create_app
from src.models import db

def create_tables():
    """Cria todas as tabelas no banco de dados"""
    try:
        print("Criando aplicação Flask...")
        app = create_app()
        
        print("Conectando ao banco de dados...")
        with app.app_context():
            print("✅ Conexão estabelecida")
            print()
            
            print("Criando tabelas...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            print()
            
            # Verificar tabelas criadas
            print("Verificando tabelas criadas...")
            result = db.session.execute(db.text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Total de tabelas criadas: {len(tables)}")
            print()
            print("Tabelas:")
            for table in sorted(tables):
                print(f"  - {table}")
            
            print()
            print("✅ Criação de tabelas concluída com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CRIAÇÃO DE TABELAS - HOSTINGER")
    print("=" * 60)
    print()
    
    create_tables()
