#!/usr/bin/env python3
"""
Script de migração para adicionar colunas valor_venda_padrao e valor_custo na tabela produtos.
Execute: python migrar_produtos_valores.py
"""

import os
import sys

# Configurar ambiente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import pymysql

def run_migration():
    """Adiciona as colunas de valor na tabela produtos."""
    
    # Conectar ao banco
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 3306))
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'livesun_comercial')
    
    print(f"Conectando ao banco {db_name} em {db_host}:{db_port}...")
    
    try:
        conn = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            # Verificar se colunas já existem
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'produtos' 
                AND COLUMN_NAME IN ('valor_venda_padrao', 'valor_custo')
            """, (db_name,))
            
            colunas_existentes = [row[0] for row in cursor.fetchall()]
            
            # Adicionar valor_venda_padrao se não existir
            if 'valor_venda_padrao' not in colunas_existentes:
                print("Adicionando coluna 'valor_venda_padrao'...")
                cursor.execute("""
                    ALTER TABLE produtos 
                    ADD COLUMN valor_venda_padrao DECIMAL(15,2) NOT NULL DEFAULT 0.00 
                    AFTER estoque_minimo
                """)
                print("  ✓ Coluna valor_venda_padrao adicionada")
            else:
                print("  ✓ Coluna valor_venda_padrao já existe")
            
            # Adicionar valor_custo se não existir
            if 'valor_custo' not in colunas_existentes:
                print("Adicionando coluna 'valor_custo'...")
                cursor.execute("""
                    ALTER TABLE produtos 
                    ADD COLUMN valor_custo DECIMAL(15,2) NOT NULL DEFAULT 0.00 
                    AFTER valor_venda_padrao
                """)
                print("  ✓ Coluna valor_custo adicionada")
            else:
                print("  ✓ Coluna valor_custo já existe")
            
            conn.commit()
            print("\n✅ Migração concluída com sucesso!")
            
    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()
    
    return 0

if __name__ == '__main__':
    sys.exit(run_migration())
