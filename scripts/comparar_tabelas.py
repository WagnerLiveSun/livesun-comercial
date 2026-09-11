#!/usr/bin/env python3
"""
Script para comparar estrutura de tabelas entre origem e destino
"""

import pymysql
from pymysql import Error

CONFIG_ORIGEM = {
    'host': '195.35.61.111',
    'port': 3306,
    'user': 'u951548013_gfinanceiro',
    'password': 'quemsabe123!A',
    'database': 'u951548013_gfinanceiro',
    'charset': 'utf8mb4'
}

CONFIG_DESTINO = {
    'host': '195.35.61.111',
    'port': 3306,
    'user': 'u951548013_LS_Comercial',
    'password': 'quemsabe123!A',
    'database': 'u951548013_LS_Comercial',
    'charset': 'utf8mb4'
}

def obter_colunas(conn, tabela):
    """Obtém lista de colunas de uma tabela"""
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {tabela}")
    colunas = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return colunas

def comparar_tabelas():
    """Compara estrutura de tabelas entre origem e destino"""
    
    print("=" * 60)
    print("COMPARANDO ESTRUTURA DE TABELAS")
    print("=" * 60)
    
    try:
        conn_origem = pymysql.connect(**CONFIG_ORIGEM)
        conn_destino = pymysql.connect(**CONFIG_DESTINO)
        
        tabelas = [
            'empresas', 'users', 'fluxo_contas_modelo', 'entidades',
            'contas_banco', 'lancamentos', 'fluxo_caixa_realizado',
            'fluxo_caixa_previsto', 'parametros_sistema', 'comissoes',
            'importacao_nfse'
        ]
        
        for tabela in tabelas:
            print(f"\n{tabela}:")
            print("-" * 40)
            
            try:
                colunas_origem = obter_colunas(conn_origem, tabela)
                colunas_destino = obter_colunas(conn_destino, tabela)
                
                print(f"  Origem: {len(colunas_origem)} colunas")
                print(f"  Destino: {len(colunas_destino)} colunas")
                
                # Colunas apenas no destino
                apenas_destino = set(colunas_destino) - set(colunas_origem)
                if apenas_destino:
                    print(f"  Apenas no destino: {', '.join(sorted(apenas_destino))}")
                
                # Colunas apenas na origem
                apenas_origem = set(colunas_origem) - set(colunas_destino)
                if apenas_origem:
                    print(f"  Apenas na origem: {', '.join(sorted(apenas_origem))}")
                
            except Error as e:
                print(f"  Erro: {e}")
        
        conn_origem.close()
        conn_destino.close()
        
    except Error as e:
        print(f"[ERRO] Erro ao conectar: {e}")

if __name__ == "__main__":
    comparar_tabelas()
