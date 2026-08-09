#!/usr/bin/env python3
"""Script para executar SQL no banco Hostinger"""

import pymysql
from pymysql import MySQLError
import os

# Credenciais do banco HOSTINGER (via variáveis de ambiente)
HOSTINGER_DB_HOST = os.environ.get("DB_HOST", "195.35.61.111")
HOSTINGER_DB_PORT = int(os.environ.get("DB_PORT", 3306))
HOSTINGER_DB_USER = os.environ.get("DB_USER", "u951548013_LS_Comercial")
HOSTINGER_DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
HOSTINGER_DB_NAME = os.environ.get("DB_NAME", "u951548013_LS_Comercial")

def execute_sql_file(sql_file_path):
    """Executa um arquivo SQL no banco Hostinger"""
    try:
        # Ler o arquivo SQL
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Conectar ao banco
        print(f"Conectando ao banco Hostinger: {HOSTINGER_DB_NAME}...")
        connection = pymysql.connect(
            host=HOSTINGER_DB_HOST,
            port=HOSTINGER_DB_PORT,
            user=HOSTINGER_DB_USER,
            password=HOSTINGER_DB_PASSWORD,
            database=HOSTINGER_DB_NAME,
            connect_timeout=10
        )
        
        print("✅ Conexão estabelecida!")
        
        # Executar o script SQL
        with connection.cursor() as cursor:
            # Dividir o script em comandos individuais
            statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    try:
                        cursor.execute(statement)
                        print(f"✅ Comando {i}/{len(statements)} executado")
                    except MySQLError as e:
                        # Ignorar erros de "IF NOT EXISTS" ou índices duplicados
                        if "already exists" in str(e) or "Duplicate" in str(e):
                            print(f"⚠️  Comando {i}/{len(statements)} ignorado (já existe)")
                        else:
                            raise
        
        # Commit das mudanças
        connection.commit()
        print("\n✅ Script SQL executado com sucesso!")
        
        # Verificar se as tabelas foram criadas
        cursor.execute("SHOW TABLES LIKE 'compra_nf_xml%'")
        tables = cursor.fetchall()
        print(f"\n📋 Tabelas criadas: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        connection.close()
        return True
        
    except MySQLError as e:
        print(f"❌ Erro ao executar SQL:")
        print(f"   Código: {e.args[0]}")
        print(f"   Mensagem: {e.args[1]}")
        return False
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {sql_file_path}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        sql_file = sys.argv[1]
    else:
        sql_file = "create_xml_import_tables_mysql.sql"
    
    print("=" * 60)
    print("EXECUTAR SQL NO BANCO HOSTINGER")
    print("=" * 60)
    print(f"Arquivo: {sql_file}")
    print()
    
    success = execute_sql_file(sql_file)
    
    if success:
        print("\n✅ Operação concluída com sucesso!")
    else:
        print("\n❌ Operação falhou!")
