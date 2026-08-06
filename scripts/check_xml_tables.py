#!/usr/bin/env python3
"""Script para verificar estrutura das tabelas XML no banco Hostinger"""

import pymysql

# Credenciais do banco HOSTINGER
HOSTINGER_DB_HOST = "195.35.61.111"
HOSTINGER_DB_PORT = 3306
HOSTINGER_DB_USER = "u951548013_LS_Comercial"
HOSTINGER_DB_PASSWORD = "quemsabe123!A"
HOSTINGER_DB_NAME = "u951548013_LS_Comercial"

try:
    connection = pymysql.connect(
        host=HOSTINGER_DB_HOST,
        port=HOSTINGER_DB_PORT,
        user=HOSTINGER_DB_USER,
        password=HOSTINGER_DB_PASSWORD,
        database=HOSTINGER_DB_NAME,
        connect_timeout=10
    )
    
    print("Estrutura da tabela compras_nf_xml_import:")
    print("=" * 60)
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE compras_nf_xml_import")
        for row in cursor.fetchall():
            print(f"  {row[0]:25} {row[1]:20} {row[2]:10} {row[3]:10} {row[4] or '':15} {row[5] or '':15}")
    
    print("\nEstrutura da tabela compras_nf_xml_itens:")
    print("=" * 60)
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE compras_nf_xml_itens")
        for row in cursor.fetchall():
            print(f"  {row[0]:25} {row[1]:20} {row[2]:10} {row[3]:10} {row[4] or '':15} {row[5] or '':15}")
    
    connection.close()
    
except Exception as e:
    print(f"Erro: {e}")
