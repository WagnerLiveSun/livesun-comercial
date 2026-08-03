#!/usr/bin/env python
"""
Script para inicialização do banco de dados.
Cria todas as tabelas e diretórios necessários.
"""
import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app
from src.models import db

def init_database():
    """Inicializa o banco de dados criando todas as tabelas."""
    app = create_app()
    
    with app.app_context():
        print("Criando tabelas do banco de dados...")
        db.create_all()
        print("✓ Tabelas criadas com sucesso!")
        
        print("\nVerificando diretórios necessários...")
        xsd_dir = os.getenv('NFS_XSD_DIR', os.path.join(os.path.dirname(__file__), '..', 'NFS_XSD_DIR'))
        xml_out_dir = os.getenv('NFS_XML_OUT_DIR', os.path.join(os.path.dirname(__file__), '..', 'dist', 'data', 'XML'))
        upload_folder = os.getenv('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), '..', 'uploads'))
        
        for directory in [xsd_dir, xml_out_dir, upload_folder]:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Diretório criado/verificado: {directory}")
        
        print("\n✓ Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_database()
