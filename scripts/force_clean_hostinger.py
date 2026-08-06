#!/usr/bin/env python3
"""
Script para limpar completamente o banco de dados da Hostinger.
Dropa todas as tabelas de forma agressiva.
"""
import pymysql
import sys

# Credenciais Hostinger
DB_CONFIG = {
    'host': '195.35.61.111',
    'port': 3306,
    'user': 'u951548013_LS_Comercial',
    'password': 'quemsabe123!A',
    'database': 'u951548013_LS_Comercial',
    'charset': 'utf8mb4'
}

def force_clean_database():
    """Dropa todas as tabelas do banco de dados, exceto plano de fluxo de caixa."""
    try:
        print(f"Conectando ao banco {DB_CONFIG['database']}...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Desabilitar verificação de chaves estrangeiras
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        print("✓ Foreign key checks desabilitados")
        
        # Listar todas as tabelas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # Tabelas a preservar
        PRESERVE_TABLES = ['fluxo_conta_model']
        
        if not tables:
            print("Nenhuma tabela encontrada no banco.")
        else:
            print(f"Encontradas {len(tables)} tabelas:")
            for table in tables:
                table_name = table[0]
                status = "PRESERVAR" if table_name in PRESERVE_TABLES else "DROPAR"
                print(f"  - {table_name} [{status}]")
            
            # Dropar todas as tabelas exceto as preservadas
            for table in tables:
                table_name = table[0]
                if table_name in PRESERVE_TABLES:
                    print(f"⊘ Tabela {table_name} preservada")
                    continue
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                    print(f"✓ Tabela {table_name} dropada")
                except Exception as e:
                    print(f"✗ Erro ao dropar tabela {table_name}: {e}")
        
        # Reabilitar verificação de chaves estrangeiras
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        print("✓ Foreign key checks reabilitados")
        
        # Commit
        connection.commit()
        print("\n✓ Banco de dados limpo com sucesso (plano de fluxo de caixa preservado)!")
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()
            print("Conexão fechada.")

if __name__ == "__main__":
    print("=" * 60)
    print("LIMPEZA AGRESSIVA DO BANCO DE DADOS HOSTINGER")
    print("=" * 60)
    print()
    
    confirm = input("Tem certeza que deseja dropar TODAS as tabelas? (s/N): ")
    if confirm.lower() != 's':
        print("Operação cancelada.")
        sys.exit(0)
    
    force_clean_database()
