#!/usr/bin/env python3
"""
Script para verificar dados existentes no banco de destino
"""

import pymysql
from pymysql import Error

CONFIG_DESTINO = {
    'host': '195.35.61.111',
    'port': 3306,
    'user': 'u951548013_LS_Comercial',
    'password': 'quemsabe123!A',
    'database': 'u951548013_LS_Comercial',
    'charset': 'utf8mb4'
}

def verificar_destino():
    """Verifica dados existentes no banco de destino"""
    
    print("=" * 60)
    print("VERIFICANDO DADOS NO BANCO DE DESTINO")
    print("=" * 60)
    
    try:
        conn = pymysql.connect(**CONFIG_DESTINO)
        cursor = conn.cursor()
        
        tabelas = [
            'empresas', 'users', 'fluxo_contas_modelo', 'entidades',
            'contas_banco', 'lancamentos', 'fluxo_caixa_realizado',
            'fluxo_caixa_previsto', 'parametros_sistema', 'comissoes',
            'importacao_nfse'
        ]
        
        print("\nRegistros existentes:\n")
        
        for tabela in tabelas:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                count = cursor.fetchone()[0]
                print(f"  {tabela}: {count} registros")
                
                if count > 0:
                    cursor.execute(f"SELECT id FROM {tabela} LIMIT 3")
                    ids = [row[0] for row in cursor.fetchall()]
                    print(f"    IDs: {ids}")
            except Error as e:
                print(f"  {tabela}: Erro - {e}")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"[ERRO] Erro ao conectar: {e}")

if __name__ == "__main__":
    verificar_destino()
