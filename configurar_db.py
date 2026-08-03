#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de configuração interativa do banco de dados

Ajuda a configurar as credenciais corretas do MySQL
"""

import os
import subprocess
import sys

def clear_screen():
    """Limpa a tela"""
    os.system('cls' if os.name == 'nt' else 'clear')

def test_mysql_connection(host, port, user, password):
    """Testa conexão com MySQL"""
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password if password else None
        )
        conn.close()
        return True
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {str(e)}")
        return False

def main():
    clear_screen()
    print("=" * 70)
    print("  LiveSun Comercial - Configurador de Banco de Dados")
    print("=" * 70)
    
    # Verificar se MySQL está instalado
    print("\n🔍 Verificando se MySQL está disponível...")
    
    try:
        subprocess.run(['mysql', '--version'], capture_output=True, check=True)
        print("✅ MySQL encontrado!")
    except FileNotFoundError:
        print("⚠️  MySQL não encontrado no PATH")
        print("   Você pode instalá-lo de: https://dev.mysql.com/downloads/mysql/")
        print("   Ou use MariaDB: https://mariadb.org/download/")
        
    # Ler arquivo .env atual
    env_file = '.env'
    env_vars = {}
    
    if os.path.exists(env_file):
        print(f"\n📄 Arquivo {env_file} encontrado")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    # Configuração atual
    print("\n" + "=" * 70)
    print("  CONFIGURAÇÃO ATUAL")
    print("=" * 70)
    print(f"\nDB_HOST:     {env_vars.get('DB_HOST', 'localhost')}")
    print(f"DB_PORT:     {env_vars.get('DB_PORT', '3306')}")
    print(f"DB_USER:     {env_vars.get('DB_USER', 'root')}")
    print(f"DB_PASSWORD: {'[VAZIO]' if not env_vars.get('DB_PASSWORD') else '***'}")
    print(f"DB_NAME:     {env_vars.get('DB_NAME', 'comercial')}")
    
    # Menu
    print("\n" + "=" * 70)
    print("  OPÇÕES")
    print("=" * 70)
    print("1. Testar conexão atual")
    print("2. Reconfigar credenciais MySQL")
    print("3. Usar configuração SQLite (para testes)")
    print("4. Sair")
    
    choice = input("\nEscolha uma opção (1-4): ").strip()
    
    if choice == '1':
        # Testar conexão
        host = env_vars.get('DB_HOST', 'localhost')
        port = env_vars.get('DB_PORT', '3306')
        user = env_vars.get('DB_USER', 'root')
        password = env_vars.get('DB_PASSWORD', '')
        
        print(f"\n🔗 Testando conexão com {user}@{host}:{port}...")
        if test_mysql_connection(host, port, user, password):
            print("✅ Conexão bem-sucedida!")
        else:
            print("❌ Falha na conexão. Verifique as credenciais.")
            
    elif choice == '2':
        # Reconfigurarar
        print("\n" + "=" * 70)
        print("  NOVA CONFIGURAÇÃO")
        print("=" * 70)
        
        host = input("\nDB_HOST (padrão: localhost): ").strip() or "localhost"
        port = input("DB_PORT (padrão: 3306): ").strip() or "3306"
        user = input("DB_USER (padrão: root): ").strip() or "root"
        password = input("DB_PASSWORD (deixe vazio para sem senha): ").strip()
        db_name = input("DB_NAME (padrão: comercial): ").strip() or "comercial"
        
        print(f"\n🔗 Testando conexão com {user}@{host}:{port}...")
        if test_mysql_connection(host, port, user, password):
            print("✅ Conexão bem-sucedida!")
            
            # Salvar configuração
            env_vars['DB_HOST'] = host
            env_vars['DB_PORT'] = port
            env_vars['DB_USER'] = user
            env_vars['DB_PASSWORD'] = password
            env_vars['DB_NAME'] = db_name
            env_vars['DB_TYPE'] = 'mysql'
            
            # Determinar ordem das chaves
            order = [
                'FLASK_ENV', 'FLASK_APP', 'FLASK_DEBUG', 'SECRET_KEY',
                'DB_TYPE', 'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
                'SERVER_HOST', 'SERVER_PORT', 'SESSION_TIMEOUT'
            ]
            
            # Escrever .env
            with open(env_file, 'w') as f:
                f.write("# Flask Configuration\n")
                f.write(f"FLASK_ENV={env_vars.get('FLASK_ENV', 'development')}\n")
                f.write(f"FLASK_APP={env_vars.get('FLASK_APP', 'src/app.py')}\n")
                f.write(f"FLASK_DEBUG={env_vars.get('FLASK_DEBUG', 'True')}\n")
                f.write(f"SECRET_KEY={env_vars.get('SECRET_KEY', 'livesun-dev-2026-change-in-production')}\n")
                f.write("\n# Database Configuration - MySQL\n")
                f.write(f"DB_TYPE={env_vars.get('DB_TYPE', 'mysql')}\n")
                f.write(f"DB_HOST={host}\n")
                f.write(f"DB_PORT={port}\n")
                f.write(f"DB_USER={user}\n")
                f.write(f"DB_PASSWORD={password}\n")
                f.write(f"DB_NAME={db_name}\n")
                f.write("\n# Server Configuration\n")
                f.write(f"SERVER_HOST={env_vars.get('SERVER_HOST', '0.0.0.0')}\n")
                f.write(f"SERVER_PORT={env_vars.get('SERVER_PORT', '5000')}\n")
                f.write("\n# Security\n")
                f.write(f"SESSION_TIMEOUT={env_vars.get('SESSION_TIMEOUT', '3600')}\n")
            
            print(f"\n✅ Configuração salva em {env_file}")
            
        else:
            print("❌ Conexão falhace. Verifique as credenciais e tente novamente.")
    
    elif choice == '3':
        # SQLite
        print("\n⚠️  SQLite é útil apenas para testes")
        print("   MySQL é recomendado para produção")
        
        if input("\nDeseja continuar com SQLite? (s/n): ").lower() == 's':
            env_vars['DB_TYPE'] = 'sqlite'
            env_vars['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///livesun_comercial.db'
            
            with open(env_file, 'w') as f:
                f.write("# Flask Configuration\n")
                f.write(f"FLASK_ENV={env_vars.get('FLASK_ENV', 'development')}\n")
                f.write(f"FLASK_APP={env_vars.get('FLASK_APP', 'src/app.py')}\n")
                f.write(f"FLASK_DEBUG={env_vars.get('FLASK_DEBUG', 'True')}\n")
                f.write(f"SECRET_KEY={env_vars.get('SECRET_KEY', 'livesun-dev-2026-change-in-production')}\n")
                f.write("\n# Database Configuration - SQLite\n")
                f.write("DB_TYPE=sqlite\n")
                f.write("DB_HOST=\n")
                f.write("DB_PORT=\n")
                f.write("DB_USER=\n")
                f.write("DB_PASSWORD=\n")
                f.write("DB_NAME=comercial\n")
                f.write("\n# Server Configuration\n")
                f.write(f"SERVER_HOST={env_vars.get('SERVER_HOST', '0.0.0.0')}\n")
                f.write(f"SERVER_PORT={env_vars.get('SERVER_PORT', '5000')}\n")
                f.write("\n# Security\n")
                f.write(f"SESSION_TIMEOUT={env_vars.get('SESSION_TIMEOUT', '3600')}\n")
            
            print(f"✅ Configurado para SQLite em {env_file}")
    
    elif choice == '4':
        print("\nSaindo...")
        sys.exit(0)
    
    # Oferecer inicializar banco
    if choice in ['1', '2', '3']:
        if input("\n\nDeseja inicializar o banco de dados agora? (s/n): ").lower() == 's':
            print("\n" + "=" * 70)
            print("  INICIALIZANDO BANCO DE DADOS")
            print("=" * 70)
            try:
                result = subprocess.run(
                    [sys.executable, 'inicializar_db.py'],
                    capture_output=False
                )
                if result.returncode == 0:
                    print("\n✅ Banco de dados inicializado com sucesso!")
            except Exception as e:
                print(f"\n❌ Erro ao inicializar: {str(e)}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        sys.exit(1)
