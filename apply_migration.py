"""Script para aplicar migration SQL nas bases de dados local e Hostinger."""

import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from config.config import Config
import pymysql

def execute_migration(db_config, db_name):
    """Executa o script SQL na base de dados especificada."""
    
    print(f"\n{'='*60}")
    print(f"Aplicando migration na base: {db_name}")
    print(f"Host: {db_config['host']}")
    print(f"{'='*60}\n")
    
    try:
        # Conectar ao banco
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"✓ Conectado ao banco {db_name}")
        
        # Ler o script SQL
        migration_file = BASE_DIR / 'migrations' / 'add_pedido_nfse_fields.sql'
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Separar comandos SQL
        sql_commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        cursor = connection.cursor()
        
        for i, command in enumerate(sql_commands, 1):
            if command:
                try:
                    print(f"  Executando comando {i}/{len(sql_commands)}: {command[:50]}...")
                    cursor.execute(command)
                    print(f"  ✓ Comando {i} executado com sucesso")
                except pymysql.MySQLError as e:
                    # Se o erro for "Duplicate column name", ignorar (coluna já existe)
                    if "Duplicate column name" in str(e):
                        print(f"  ⚠ Coluna já existe (ignorando): {e}")
                    else:
                        raise
        
        connection.commit()
        print(f"\n✓ Migration aplicada com sucesso na base {db_name}")
        
    except Exception as e:
        print(f"\n✗ Erro ao aplicar migration na base {db_name}: {e}")
        if 'connection' in locals():
            connection.rollback()
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    
    return True

def main():
    """Função principal."""
    
    print("="*60)
    print("APLICANDO MIGRATION: add_pedido_nfse_fields.sql")
    print("="*60)
    
    # Configuração da base local (usar configurações do config.py)
    local_config = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
    }
    
    # Configuração da base Hostinger (credenciais fixas do script de teste)
    hostinger_config = {
        'host': "195.35.61.111",
        'port': 3306,
        'user': "u951548013_LS_Comercial",
        'password': "quemsabe123!A",
        'database': "u951548013_LS_Comercial",
    }
    
    # Aplicar na base local
    local_success = execute_migration(local_config, "LOCAL")
    
    # Aplicar na base Hostinger
    hostinger_success = execute_migration(hostinger_config, "HOSTINGER")
    
    print(f"\n{'='*60}")
    print("RESUMO")
    print(f"{'='*60}")
    print(f"Local:    {'✓ SUCESSO' if local_success else '✗ FALHA'}")
    print(f"Hostinger: {'✓ SUCESSO' if hostinger_success else '✗ FALHA'}")
    print(f"{'='*60}\n")
    
    if local_success and hostinger_success:
        print("✓ Migration aplicada em ambas as bases com sucesso!")
        return 0
    else:
        print("✗ Migration falhou em uma ou ambas as bases")
        return 1

if __name__ == '__main__':
    sys.exit(main())
