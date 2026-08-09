"""Script para aplicar migration específica da tabela contratos na Hostinger."""

import pymysql
import os

# Credenciais do banco de dados na Hostinger (via variáveis de ambiente)
DB_HOST = os.environ.get("DB_HOST", "195.35.61.111")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "u951548013_LS_Comercial")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "u951548013_LS_Comercial")

def execute_migration():
    """Executa o script SQL na base Hostinger."""
    
    print("="*60)
    print("APLICANDO MIGRATION: fix_contrato_status.sql")
    print(f"Banco: {DB_NAME}")
    print(f"Host: {DB_HOST}")
    print("="*60 + "\n")
    
    try:
        # Conectar ao banco
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"✓ Conectado ao banco {DB_NAME}")
        
        # Ler o script SQL
        migration_file = "migrations/fix_contrato_status.sql"
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Separar comandos SQL
        sql_commands = []
        current_command = []
        for line in sql_script.split('\n'):
            line = line.strip()
            if line.startswith('--'):
                continue
            if line:
                current_command.append(line)
                if line.endswith(';'):
                    sql_commands.append(' '.join(current_command))
                    current_command = []
        
        # Adicionar comando restante se houver
        if current_command:
            sql_commands.append(' '.join(current_command))
        
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
        print(f"\n✓ Migration aplicada com sucesso na base {DB_NAME}")
        
    except Exception as e:
        print(f"\n✗ Erro ao aplicar migration na base {DB_NAME}: {e}")
        if 'connection' in locals():
            connection.rollback()
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    
    return True

if __name__ == '__main__':
    success = execute_migration()
    print(f"\n{'='*60}")
    print(f"{'✓ SUCESSO' if success else '✗ FALHA'}")
    print(f"{'='*60}\n")
    exit(0 if success else 1)
