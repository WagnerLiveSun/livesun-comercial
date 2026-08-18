"""Script para aplicar migration usando conexão Flask existente."""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from src.app import app, db
from config.config import Config

def execute_migration():
    """Executa o script SQL usando a conexão Flask."""
    
    print("="*60)
    print("APLICANDO MIGRATION: add_pedido_nfse_fields.sql")
    print(f"Banco: {Config.DB_NAME}")
    print(f"Host: {Config.DB_HOST}")
    print("="*60 + "\n")
    
    try:
        # Ler o script SQL
        migration_file = BASE_DIR / 'migrations' / 'add_pedido_nfse_fields.sql'
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Separar comandos SQL (ALTER TABLE pode ter múltiplas linhas)
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
        
        print(f"Encontrados {len(sql_commands)} comandos SQL\n")
        
        with app.app_context():
            for i, command in enumerate(sql_commands, 1):
                if command:
                    try:
                        print(f"Executando comando {i}/{len(sql_commands)}: {command[:60]}...")
                        db.session.execute(db.text(command))
                        db.session.commit()
                        print(f"✓ Comando {i} executado com sucesso")
                    except Exception as e:
                        # Se o erro for "Duplicate column name", ignorar (coluna já existe)
                        if "Duplicate column name" in str(e):
                            print(f"⚠ Coluna já existe (ignorando): {e}")
                        else:
                            print(f"✗ Erro no comando {i}: {e}")
                            raise
        
        print(f"\n{'='*60}")
        print("✓ Migration aplicada com sucesso!")
        print(f"{'='*60}\n")
        return True
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"✗ Erro ao aplicar migration: {e}")
        print(f"{'='*60}\n")
        return False

if __name__ == '__main__':
    success = execute_migration()
    sys.exit(0 if success else 1)
