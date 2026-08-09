#!/usr/bin/env python3
"""Script para listar tabelas do banco Hostinger"""

import pymysql
import os

# Credenciais do banco HOSTINGER (via variáveis de ambiente)
HOSTINGER_DB_HOST = os.environ.get("DB_HOST", "195.35.61.111")
HOSTINGER_DB_PORT = int(os.environ.get("DB_PORT", 3306))
HOSTINGER_DB_USER = os.environ.get("DB_USER", "u951548013_LS_Comercial")
HOSTINGER_DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
HOSTINGER_DB_NAME = os.environ.get("DB_NAME", "u951548013_LS_Comercial")

try:
    connection = pymysql.connect(
        host=HOSTINGER_DB_HOST,
        port=HOSTINGER_DB_PORT,
        user=HOSTINGER_DB_USER,
        password=HOSTINGER_DB_PASSWORD,
        database=HOSTINGER_DB_NAME,
        connect_timeout=10
    )
    
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
    print("Tabelas no banco Hostinger:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    connection.close()
    
except Exception as e:
    print(f"Erro: {e}")
