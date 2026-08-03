"""
Script de migração para adicionar atividade_contratos
Este script adiciona a coluna atividade_contratos na tabela empresas
"""

import os
import sys

# Adicionar o caminho do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app
from src.models import db

def run_migrations():
    """Executa as migrações necessárias"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("[MIGRAÇÃO] Adicionando atividade_contratos")
        print("=" * 60)
        print()
        
        try:
            print("[1/1] Verificando/Adicionando coluna atividade_contratos...")
            
            conn = db.engine.raw_connection()
            cursor = conn.cursor()
            
            # Verificar se a coluna já existe
            try:
                cursor.execute("SELECT atividade_contratos FROM empresas LIMIT 1")
                print("✓ Coluna 'atividade_contratos' já existe")
            except Exception as e:
                print("⚠ Coluna 'atividade_contratos' não existe, adicionando...")
                cursor.execute("ALTER TABLE empresas ADD COLUMN atividade_contratos BOOLEAN DEFAULT FALSE AFTER atividade_locacao")
                conn.commit()
                print("✓ Coluna 'atividade_contratos' adicionada com sucesso")
            
            cursor.close()
            conn.close()
            
            print()
            print("=" * 60)
            print("[SUCESSO] Migração concluída com sucesso!")
            print("=" * 60)
            print()
            
        except Exception as e:
            print()
            print("=" * 60)
            print("[ERRO] Erro durante a migração!")
            print("=" * 60)
            print(f"Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)
