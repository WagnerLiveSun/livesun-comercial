#!/usr/bin/env python3
"""Script para testar conexão com banco de dados MySQL na Hostinger"""

import pymysql
from pymysql import MySQLError
import os

# Credenciais do banco de dados na Hostinger (via variáveis de ambiente)
DB_HOST = os.environ.get("DB_HOST", "195.35.61.111")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "u951548013_LS_Comercial")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "u951548013_LS_Comercial")

def test_connection():
    """Testa a conexão com o banco de dados"""
    try:
        print(f"Tentando conectar ao banco de dados...")
        print(f"Host: {DB_HOST}")
        print(f"Porta: {DB_PORT}")
        print(f"Usuário: {DB_USER}")
        print(f"Banco: {DB_NAME}")
        print()
        
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=10
        )
        
        print("✅ Conexão bem-sucedida!")
        
        # Testar uma query simples
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"Versão do MySQL: {version[0]}")
            
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"Número de tabelas: {len(tables)}")
            if tables:
                print("Tabelas existentes:")
                for table in tables:
                    print(f"  - {table[0]}")
        
        connection.close()
        print("\n✅ Teste concluído com sucesso!")
        return True
        
    except MySQLError as e:
        print(f"❌ Erro ao conectar ao banco de dados:")
        print(f"   Código: {e.args[0]}")
        print(f"   Mensagem: {e.args[1]}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado:")
        print(f"   {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
