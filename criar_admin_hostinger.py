#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar usuário admin no banco da Hostinger
Execute isto localmente, ele vai se conectar ao banco remoto
"""

import pymysql
from werkzeug.security import generate_password_hash

# Dados da conexão Hostinger
DB_HOST = 'localhost'  # Alterar para o host da Hostinger se necessário
DB_PORT = 3306
DB_USER = 'u951548013_LS_Comercial'
DB_PASSWORD = 'sua_senha_aqui'  # ALTERE ISTO com a senha real
DB_NAME = 'u951548013_LS_Comercial'

def criar_usuario_admin():
    """Cria usuário admin no banco remoto"""
    
    try:
        # Conectar ao banco
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        print("🔗 Conectado ao banco da Hostinger")
        
        # Gerar hash da senha
        password_hash = generate_password_hash('admin123', method='pbkdf2:sha256')
        print(f"🔐 Hash gerado para senha: {password_hash}")
        
        # Verificar se admin já existe
        cursor.execute("SELECT id FROM users WHERE username = 'admin' AND empresa_id IS NULL")
        if cursor.fetchone():
            print("⚠️  Usuário admin já existe, deletando...")
            cursor.execute("DELETE FROM users WHERE username = 'admin' AND empresa_id IS NULL")
            conn.commit()
        
        # Inserir novo admin
        sql = """
        INSERT INTO users (
            username, email, password_hash, full_name, 
            is_active, is_admin, role, empresa_id, dashboard_chart_days
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(sql, (
            'admin',
            'admin@livesun.local',
            password_hash,
            'Administrador',
            1,
            1,
            'admin',
            None,
            30
        ))
        conn.commit()
        
        print("✅ Usuário admin criado com sucesso!")
        print("\n📋 Credenciais:")
        print("   Usuário: admin")
        print("   Senha:   admin123")
        print("\n🌐 Acesse: https://app.livesun.com.br/auth/login")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        print("\nVerifique:")
        print("  1. DB_PASSWORD está correto?")
        print("  2. DB_HOST e DB_PORT estão corretos?")
        print("  3. Banco 'u951548013_LS_Comercial' existe?")

if __name__ == '__main__':
    print("="*70)
    print("  Criar Usuário Admin - Hostinger")
    print("="*70 + "\n")
    
    # IMPORTANTE: Altere DB_PASSWORD com a senha real!
    print("⚠️  IMPORTANTE: Altere DB_PASSWORD no script com a senha do banco!")
    print("   Após fazer isso, execute novamente.\n")
    
    criar_usuario_admin()
