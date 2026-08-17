#!/usr/bin/env python3
"""Script para comparar e sincronizar tabelas de referência entre base local e Hostinger"""

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

# Tabelas de referência para sincronizar
REFERENCE_TABLES = [
    'nfse_municipios_referencia',
    'nfse_servicos_nacionais_referencia',
    'nfse_nbs_referencia',
    'nfse_ctrib_mun_referencia',
    'nfse_cnae_referencia',
    'nfse_indop_referencia',
]

def get_row_count(host, port, user, password, database, table):
    """Retorna o número de registros em uma tabela"""
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
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
        
        connection.close()
        return count
        
    except MySQLError as e:
        print(f"❌ Erro ao contar registros da tabela {table}: - sync_reference_tables.py:52")
        print(f"Código: {e.args[0]} - sync_reference_tables.py:53")
        print(f"Mensagem: {e.args[1]} - sync_reference_tables.py:54")
        return -1

def get_table_columns(host, port, user, password, database, table):
    """Retorna lista de colunas de uma tabela"""
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
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            columns = [row[0] for row in cursor.fetchall()]
        
        connection.close()
        return columns
        
    except MySQLError as e:
        print(f"❌ Erro ao obter colunas da tabela {table}: - sync_reference_tables.py:77")
        print(f"Código: {e.args[0]} - sync_reference_tables.py:78")
        print(f"Mensagem: {e.args[1]} - sync_reference_tables.py:79")
        return []

def copy_table_data(source_host, source_port, source_user, source_password, source_database,
                   target_host, target_port, target_user, target_password, target_database, table):
    """Copia dados de uma tabela do banco origem para o banco destino"""
    try:
        # Conectar ao banco origem
        source_conn = pymysql.connect(
            host=source_host,
            port=source_port,
            user=source_user,
            password=source_password,
            database=source_database,
            connect_timeout=10
        )
        
        # Conectar ao banco destino
        target_conn = pymysql.connect(
            host=target_host,
            port=target_port,
            user=target_user,
            password=target_password,
            database=target_database,
            connect_timeout=10
        )
        
        # Obter colunas de ambas as tabelas
        source_columns = get_table_columns(source_host, source_port, source_user, source_password, source_database, table)
        target_columns = get_table_columns(target_host, target_port, target_user, target_password, target_database, table)
        
        # Usar apenas colunas que existem em ambas as tabelas
        common_columns = [col for col in source_columns if col in target_columns]
        
        if not common_columns:
            print(f"❌ Nenhuma coluna em comum entre as tabelas - sync_reference_tables.py:114")
            return -1
        
        # Ler dados da origem (apenas colunas comuns)
        columns_str = ', '.join(common_columns)
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT {columns_str} FROM {table}")
            rows = cursor.fetchall()
        
        # Limpar tabela destino
        with target_conn.cursor() as cursor:
            cursor.execute(f"SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"SET FOREIGN_KEY_CHECKS = 1")
        
        # Inserir dados no destino
        if rows:
            placeholders = ', '.join(['%s'] * len(common_columns))
            insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
            
            with target_conn.cursor() as cursor:
                cursor.executemany(insert_sql, rows)
        
        target_conn.commit()
        source_conn.close()
        target_conn.close()
        
        return len(rows)
        
    except MySQLError as e:
        print(f"❌ Erro ao copiar dados da tabela {table}: - sync_reference_tables.py:144")
        print(f"Código: {e.args[0]} - sync_reference_tables.py:145")
        print(f"Mensagem: {e.args[1]} - sync_reference_tables.py:146")
        return -1

def compare_and_sync():
    """Compara e sincroniza tabelas de referência"""
    print("= - sync_reference_tables.py:151" * 60)
    print("COMPARAÇÃO E SINCRONIZAÇÃO DE TABELAS DE REFERÊNCIA - sync_reference_tables.py:152")
    print("= - sync_reference_tables.py:153" * 60)
    print()
    
    tables_to_sync = []
    
    for table in REFERENCE_TABLES:
        print(f"📊 Tabela: {table} - sync_reference_tables.py:159")
        
        # Contar registros no local
        local_count = get_row_count(LOCAL_DB_HOST, LOCAL_DB_PORT, LOCAL_DB_USER, 
                                   LOCAL_DB_PASSWORD, LOCAL_DB_NAME, table)
        print(f"Local:     {local_count:,} registros - sync_reference_tables.py:164" if local_count >= 0 else "   Local:     ERRO")
        
        # Contar registros na Hostinger
        hostinger_count = get_row_count(HOSTINGER_DB_HOST, HOSTINGER_DB_PORT, HOSTINGER_DB_USER,
                                       HOSTINGER_DB_PASSWORD, HOSTINGER_DB_NAME, table)
        print(f"Hostinger: {hostinger_count:,} registros - sync_reference_tables.py:169" if hostinger_count >= 0 else "   Hostinger: ERRO")
        
        # Verificar se precisa sincronizar
        if local_count > hostinger_count:
            diff = local_count - hostinger_count
            print(f"⚠️  Diferença: {diff:,} registros faltando na Hostinger - sync_reference_tables.py:174")
            tables_to_sync.append((table, local_count, hostinger_count))
        elif local_count == hostinger_count:
            print(f"✅ Sincronizada - sync_reference_tables.py:177")
        else:
            print(f"⚠️  Hostinger tem mais registros que o local - sync_reference_tables.py:179")
        
        print()
    
    if not tables_to_sync:
        print("✅ Todas as tabelas estão sincronizadas! - sync_reference_tables.py:184")
        return
    
    # Perguntar se deseja sincronizar
    print("= - sync_reference_tables.py:188" * 60)
    print(f"Tabelas para sincronizar: {len(tables_to_sync)} - sync_reference_tables.py:189")
    print("= - sync_reference_tables.py:190" * 60)
    for table, local, hostinger in tables_to_sync:
        print(f"{table}: Local ({local:,}) → Hostinger ({hostinger:,}) - sync_reference_tables.py:192")
    print()
    
    confirm = input("Deseja sincronizar estas tabelas? (s/N): ")
    
    if confirm.lower() != 's':
        print("❌ Operação cancelada pelo usuário. - sync_reference_tables.py:198")
        return
    
    print()
    print("🔄 Iniciando sincronização... - sync_reference_tables.py:202")
    print()
    
    for table, local_count, hostinger_count in tables_to_sync:
        print(f"📥 Copiando {table}... - sync_reference_tables.py:206")
        copied = copy_table_data(
            LOCAL_DB_HOST, LOCAL_DB_PORT, LOCAL_DB_USER, LOCAL_DB_PASSWORD, LOCAL_DB_NAME,
            HOSTINGER_DB_HOST, HOSTINGER_DB_PORT, HOSTINGER_DB_USER, HOSTINGER_DB_PASSWORD, HOSTINGER_DB_NAME,
            table
        )
        
        if copied >= 0:
            print(f"✅ {copied:,} registros copiados - sync_reference_tables.py:214")
        else:
            print(f"❌ Erro ao copiar tabela - sync_reference_tables.py:216")
        print()
    
    print("= - sync_reference_tables.py:219" * 60)
    print("✅ Sincronização concluída! - sync_reference_tables.py:220")
    print("= - sync_reference_tables.py:221" * 60)

if __name__ == "__main__":
    compare_and_sync()
