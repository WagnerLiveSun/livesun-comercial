#!/usr/bin/env python3
"""
Script de verificação e atualização completa do banco de dados.
Checa se todas as tabelas e colunas necessárias existem e cria as novas se necessário.
"""

import os
import sys
from sqlalchemy import text, inspect
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db
from src.models.locacao import *  # Importa todos os modelos de locação

def atualizar_banco():
    load_dotenv()
    app = create_app()
    
    with app.app_context():
        print("🔍 Iniciando verificação e atualização do banco de dados... - verificar_banco.py:24")
        
        try:
            inspector = inspect(db.engine)
            tabelas_existentes = inspector.get_table_names()
            
            # 1. Verificar campos de atividades na tabela empresas
            print("🏢 Verificando tabela 'empresas'... - verificar_banco.py:31")
            if 'empresas' in tabelas_existentes:
                colunas_empresas = [c['name'] for c in inspector.get_columns('empresas')]
                atividades = [
                    ('atividade_comercial', 'BOOLEAN DEFAULT FALSE'),
                    ('atividade_servicos', 'BOOLEAN DEFAULT FALSE'),
                    ('atividade_financeiro', 'BOOLEAN DEFAULT FALSE'),
                    ('atividade_locacao', 'BOOLEAN DEFAULT FALSE')
                ]
                
                for campo, tipo in atividades:
                    if campo not in colunas_empresas:
                        print(f"➕ Adicionando coluna '{campo}' na tabela 'empresas'... - verificar_banco.py:43")
                        try:
                            # Tenta adicionar a coluna
                            db.session.execute(text(f"ALTER TABLE empresas ADD COLUMN {campo} {tipo}"))
                            db.session.commit()
                            print(f"✅ Coluna '{campo}' adicionada. - verificar_banco.py:48")
                        except Exception as e:
                            print(f"⚠️ Erro ao adicionar {campo}: {e}. Tentando sem DEFAULT... - verificar_banco.py:50")
                            try:
                                db.session.rollback()
                                db.session.execute(text(f"ALTER TABLE empresas ADD COLUMN {campo} BOOLEAN"))
                                db.session.commit()
                                print(f"✅ Coluna '{campo}' adicionada (sem default). - verificar_banco.py:55")
                            except Exception as e2:
                                print(f"❌ Falha crítica ao adicionar {campo}: {e2} - verificar_banco.py:57")
                                db.session.rollback()
            else:
                print("❌ Tabela 'empresas' não encontrada! Certifiquese de que o banco base está correto. - verificar_banco.py:60")

            # 2. Criar novas tabelas (Locação e outras faltantes)
            print("🏗️ Verificando e criando novas tabelas... - verificar_banco.py:63")
            try:
                # O create_all do SQLAlchemy só cria tabelas que NÃO existem
                db.create_all()
                print("✅ Tabelas verificadas/criadas com sucesso! - verificar_banco.py:67")
            except Exception as e:
                print(f"❌ Erro ao criar tabelas: {e} - verificar_banco.py:69")
                db.session.rollback()

            print("\n🚀 Banco de dados atualizado e pronto para uso! - verificar_banco.py:72")
            return 0
            
        except Exception as e:
            print(f"❌ Erro geral durante a atualização: {e} - verificar_banco.py:76")
            return 1

if __name__ == "__main__":
    sys.exit(atualizar_banco())
