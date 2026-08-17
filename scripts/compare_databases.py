#!/usr/bin/env python3
"""Script para comparar tabelas entre banco local e banco da Hostinger"""

import pymysql
from pymysql import MySQLError
import os

# Credenciais do banco LOCAL (via variáveis de ambiente)
LOCAL_DB_HOST = os.environ.get("LOCAL_DB_HOST", "localhost")
LOCAL_DB_PORT = int(os.environ.get("LOCAL_DB_PORT", 3306))
LOCAL_DB_USER = os.environ.get("LOCAL_DB_USER", "root")
LOCAL_DB_PASSWORD = os.environ.get("LOCAL_DB_PASSWORD", "")
LOCAL_DB_NAME = os.environ.get("LOCAL_DB_NAME", "comercial")

# Credenciais do banco HOSTINGER (via variáveis de ambiente)
HOSTINGER_DB_HOST = os.environ.get("DB_HOST", "195.35.61.111")
HOSTINGER_DB_PORT = int(os.environ.get("DB_PORT", 3306))
HOSTINGER_DB_USER = os.environ.get("DB_USER", "u951548013_LS_Comercial")
HOSTINGER_DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
HOSTINGER_DB_NAME = os.environ.get("DB_NAME", "u951548013_LS_Comercial")

def get_tables(host, port, user, password, database):
    """Retorna lista de tabelas do banco de dados"""
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
        
        connection.close()
        return sorted(tables)
        
    except MySQLError as e:
        print(f"❌ Erro ao conectar ao banco {database}: - compare_databases.py:42")
        print(f"Código: {e.args[0]} - compare_databases.py:43")
        print(f"Mensagem: {e.args[1]} - compare_databases.py:44")
        return []

def compare_databases():
    """Compara tabelas entre banco local e Hostinger"""
    print("= - compare_databases.py:49" * 60)
    print("COMPARAÇÃO DE BANCOS DE DADOS - compare_databases.py:50")
    print("= - compare_databases.py:51" * 60)
    print()
    
    print("Conectando ao banco LOCAL... - compare_databases.py:54")
    local_tables = get_tables(LOCAL_DB_HOST, LOCAL_DB_PORT, LOCAL_DB_USER, LOCAL_DB_PASSWORD, LOCAL_DB_NAME)
    print(f"✅ Banco LOCAL: {len(local_tables)} tabelas - compare_databases.py:56")
    print()
    
    print("Conectando ao banco HOSTINGER... - compare_databases.py:59")
    hostinger_tables = get_tables(HOSTINGER_DB_HOST, HOSTINGER_DB_PORT, HOSTINGER_DB_USER, HOSTINGER_DB_PASSWORD, HOSTINGER_DB_NAME)
    print(f"✅ Banco HOSTINGER: {len(hostinger_tables)} tabelas - compare_databases.py:61")
    print()
    
    # Converter para sets para comparação
    local_set = set(local_tables)
    hostinger_set = set(hostinger_tables)
    
    # Tabelas apenas no local
    only_local = local_set - hostinger_set
    if only_local:
        print(f"⚠️  Tabelas apenas no LOCAL ({len(only_local)}): - compare_databases.py:71")
        for table in sorted(only_local):
            print(f"{table} - compare_databases.py:73")
        print()
    else:
        print("✅ Nenhuma tabela apenas no LOCAL - compare_databases.py:76")
        print()
    
    # Tabelas apenas na Hostinger
    only_hostinger = hostinger_set - local_set
    if only_hostinger:
        print(f"⚠️  Tabelas apenas na HOSTINGER ({len(only_hostinger)}): - compare_databases.py:82")
        for table in sorted(only_hostinger):
            print(f"{table} - compare_databases.py:84")
        print()
    else:
        print("✅ Nenhuma tabela apenas na HOSTINGER - compare_databases.py:87")
        print()
    
    # Tabelas comuns
    common = local_set & hostinger_set
    print(f"✅ Tabelas comuns: {len(common)} - compare_databases.py:92")
    print()
    
    # Resumo
    print("= - compare_databases.py:96" * 60)
    print("RESUMO - compare_databases.py:97")
    print("= - compare_databases.py:98" * 60)
    print(f"Local:     {len(local_tables)} tabelas - compare_databases.py:99")
    print(f"Hostinger: {len(hostinger_tables)} tabelas - compare_databases.py:100")
    print(f"Comuns:    {len(common)} tabelas - compare_databases.py:101")
    print(f"Apenas local:      {len(only_local)} tabelas - compare_databases.py:102")
    print(f"Apenas hostinger:  {len(only_hostinger)} tabelas - compare_databases.py:103")
    print()
    
    if not only_local and not only_hostinger:
        print("✅ BANCOS SINCRONIZADOS  Todas as tabelas são iguais! - compare_databases.py:107")
        return True
    else:
        print("⚠️  BANCOS DIFERENTES  Verifique as tabelas listadas acima - compare_databases.py:110")
        return False

if __name__ == "__main__":
    compare_databases()
