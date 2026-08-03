#!/usr/bin/env python3
"""
Script de migração de dados do MySQL para PostgreSQL
Migra todos os dados do banco MySQL comercial para o PostgreSQL
"""

import os
import sys
from datetime import datetime
import pymysql
import psycopg2
from psycopg2.extras import execute_batch

# Configurações MySQL
MYSQL_HOST = os.environ.get('DB_HOST', 'localhost')
MYSQL_PORT = int(os.environ.get('DB_PORT', 3306))
MYSQL_USER = os.environ.get('DB_USER', 'root')
MYSQL_PASSWORD = os.environ.get('DB_PASSWORD', '')
MYSQL_DATABASE = os.environ.get('DB_NAME', 'comercial')

# Configurações PostgreSQL
PG_HOST = os.environ.get('PG_HOST', 'localhost')
PG_PORT = int(os.environ.get('PG_PORT', 5432))
PG_USER = os.environ.get('PG_USER', 'postgres')
PG_PASSWORD = os.environ.get('PG_PASSWORD', 'livesun')
PG_DATABASE = os.environ.get('PG_DATABASE', 'comercial')

# Mapeamento de tabelas para migrar
TABELAS_MIGRAR = [
    'empresas',
    'users',
    'role_permissions',
    'user_permission_overrides',
    'fluxo_contas_modelo',
    'contas_banco',
    'entidades',
    'lancamentos',
    'fluxo_caixa_realizado',
    'fluxo_caixa_previsto',
    'parametros_sistema',
    'comissoes',
    'importacao_nfse',
    'conciliacao_bancaria',
    'conciliacao_item',
    'filiais',
    'produtos',
    'servicos',
    'estoque_movimentos',
    'compras_nf_manual',
    'compras_nf_itens',
    'compras_nf_lancamentos',
    'documentos_venda',
    'documentos_venda_itens',
    'tabelas_preco',
    'tabelas_preco_itens',
    'orcamentos',
    'orcamentos_itens',
    'pedidos_venda',
    'pedidos_venda_itens',
    'pdv_sessoes',
    'pdv_vendas',
    'pdv_itens',
    'rbac_roles',
    'rbac_permissions',
    'rbac_user_roles',
    'rbac_role_permissions',
    'auditoria_eventos'
]

def conectar_mysql():
    """Conecta ao MySQL"""
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4'
        )
        print(f"✓ Conectado ao MySQL: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
        return conn
    except Exception as e:
        print(f"✗ Erro ao conectar ao MySQL: {e}")
        sys.exit(1)

def conectar_postgresql():
    """Conecta ao PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        print(f"✓ Conectado ao PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
        return conn
    except Exception as e:
        print(f"✗ Erro ao conectar ao PostgreSQL: {e}")
        sys.exit(1)

def obter_colunas_tabela(conn_mysql, tabela):
    """Obtém as colunas de uma tabela MySQL"""
    with conn_mysql.cursor() as cursor:
        cursor.execute(f"DESCRIBE {tabela}")
        colunas = [row[0] for row in cursor.fetchall()]
        return colunas

def migrar_tabela(mysql_conn, pg_conn, tabela):
    """Migra dados de uma tabela específica"""
    print(f"\n→ Migrando tabela: {tabela}")
    
    # Obter colunas
    colunas = obter_colunas_tabela(mysql_conn, tabela)
    colunas_str = ', '.join(colunas)
    placeholders = ', '.join(['%s'] * len(colunas))
    
    # Ler dados do MySQL
    with mysql_conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(f"SELECT {colunas_str} FROM {tabela}")
        dados = cursor.fetchall()
        
        if not dados:
            print(f"  - Tabela vazia, pulando")
            return 0
        
        print(f"  - {len(dados)} registros encontrados")
    
    # Inserir no PostgreSQL
    with pg_conn.cursor() as cursor:
        # Desabilitar triggers temporariamente para performance
        cursor.execute(f"ALTER TABLE {tabela} DISABLE TRIGGER ALL")
        
        try:
            # Inserir em batch
            valores = []
            for linha in dados:
                valores.append(tuple(linha[col] for col in colunas))
            
            insert_query = f"""
                INSERT INTO {tabela} ({colunas_str})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """
            
            execute_batch(cursor, insert_query, valores, page_size=1000)
            pg_conn.commit()
            
            print(f"  ✓ {len(dados)} registros migrados")
            
        except Exception as e:
            pg_conn.rollback()
            print(f"  ✗ Erro ao migrar: {e}")
            return 0
        finally:
            # Reabilitar triggers
            cursor.execute(f"ALTER TABLE {tabela} ENABLE TRIGGER ALL")
    
    return len(dados)

def main():
    print("=" * 60)
    print("MIGRAÇÃO DE DADOS: MySQL → PostgreSQL")
    print("=" * 60)
    print(f"\nConfiguração MySQL:")
    print(f"  Host: {MYSQL_HOST}:{MYSQL_PORT}")
    print(f"  Database: {MYSQL_DATABASE}")
    print(f"  User: {MYSQL_USER}")
    
    print(f"\nConfiguração PostgreSQL:")
    print(f"  Host: {PG_HOST}:{PG_PORT}")
    print(f"  Database: {PG_DATABASE}")
    print(f"  User: {PG_USER}")
    print()
    
    # Conectar aos bancos
    mysql_conn = conectar_mysql()
    pg_conn = conectar_postgresql()
    
    total_registros = 0
    tabelas_migradas = 0
    
    # Migrar cada tabela
    for tabela in TABELAS_MIGRAR:
        try:
            qtd = migrar_tabela(mysql_conn, pg_conn, tabela)
            if qtd > 0:
                total_registros += qtd
                tabelas_migradas += 1
        except Exception as e:
            print(f"✗ Erro fatal ao migrar {tabela}: {e}")
            continue
    
    # Fechar conexões
    mysql_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 60)
    print("RESUMO DA MIGRAÇÃO")
    print("=" * 60)
    print(f"Tabelas migradas: {tabelas_migradas}/{len(TABELAS_MIGRAR)}")
    print(f"Total de registros: {total_registros}")
    print("=" * 60)

if __name__ == '__main__':
    main()
