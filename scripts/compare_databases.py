#!/usr/bin/env python3
"""Script para comparar tabelas entre banco local e banco da Hostinger"""

import pymysql
from pymysql import MySQLError

# Credenciais do banco LOCAL
LOCAL_DB_HOST = "localhost"
LOCAL_DB_PORT = 3306
LOCAL_DB_USER = "root"
LOCAL_DB_PASSWORD = "livesun"
LOCAL_DB_NAME = "comercial"

# Credenciais do banco HOSTINGER
HOSTINGER_DB_HOST = "195.35.61.111"
HOSTINGER_DB_PORT = 3306
HOSTINGER_DB_USER = "u951548013_LS_Comercial"
HOSTINGER_DB_PASSWORD = "quemsabe123!A"
HOSTINGER_DB_NAME = "u951548013_LS_Comercial"

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
        print(f"❌ Erro ao conectar ao banco {database}:")
        print(f"   Código: {e.args[0]}")
        print(f"   Mensagem: {e.args[1]}")
        return []

def compare_databases():
    """Compara tabelas entre banco local e Hostinger"""
    print("=" * 60)
    print("COMPARAÇÃO DE BANCOS DE DADOS")
    print("=" * 60)
    print()
    
    print("Conectando ao banco LOCAL...")
    local_tables = get_tables(LOCAL_DB_HOST, LOCAL_DB_PORT, LOCAL_DB_USER, LOCAL_DB_PASSWORD, LOCAL_DB_NAME)
    print(f"✅ Banco LOCAL: {len(local_tables)} tabelas")
    print()
    
    print("Conectando ao banco HOSTINGER...")
    hostinger_tables = get_tables(HOSTINGER_DB_HOST, HOSTINGER_DB_PORT, HOSTINGER_DB_USER, HOSTINGER_DB_PASSWORD, HOSTINGER_DB_NAME)
    print(f"✅ Banco HOSTINGER: {len(hostinger_tables)} tabelas")
    print()
    
    # Converter para sets para comparação
    local_set = set(local_tables)
    hostinger_set = set(hostinger_tables)
    
    # Tabelas apenas no local
    only_local = local_set - hostinger_set
    if only_local:
        print(f"⚠️  Tabelas apenas no LOCAL ({len(only_local)}):")
        for table in sorted(only_local):
            print(f"   - {table}")
        print()
    else:
        print("✅ Nenhuma tabela apenas no LOCAL")
        print()
    
    # Tabelas apenas na Hostinger
    only_hostinger = hostinger_set - local_set
    if only_hostinger:
        print(f"⚠️  Tabelas apenas na HOSTINGER ({len(only_hostinger)}):")
        for table in sorted(only_hostinger):
            print(f"   - {table}")
        print()
    else:
        print("✅ Nenhuma tabela apenas na HOSTINGER")
        print()
    
    # Tabelas comuns
    common = local_set & hostinger_set
    print(f"✅ Tabelas comuns: {len(common)}")
    print()
    
    # Resumo
    print("=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Local:     {len(local_tables)} tabelas")
    print(f"Hostinger: {len(hostinger_tables)} tabelas")
    print(f"Comuns:    {len(common)} tabelas")
    print(f"Apenas local:      {len(only_local)} tabelas")
    print(f"Apenas hostinger:  {len(only_hostinger)} tabelas")
    print()
    
    if not only_local and not only_hostinger:
        print("✅ BANCOS SINCRONIZADOS - Todas as tabelas são iguais!")
        return True
    else:
        print("⚠️  BANCOS DIFERENTES - Verifique as tabelas listadas acima")
        return False

if __name__ == "__main__":
    compare_databases()
