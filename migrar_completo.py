#!/usr/bin/env python3
"""
Script de migração completo - adiciona todas as colunas faltantes.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import pymysql

MIGRATIONS = [
    # orcamentos
    ("ALTER TABLE orcamentos ADD COLUMN aprovado_por_user_id INT NULL AFTER data_aprovacao", "orcamentos.aprovado_por_user_id"),
    ("ALTER TABLE orcamentos ADD COLUMN ativo TINYINT(1) NOT NULL DEFAULT 1 AFTER aprovado_por_user_id", "orcamentos.ativo"),
    
    # orcamentos_itens
    ("ALTER TABLE orcamentos_itens ADD COLUMN sequencia INT NOT NULL DEFAULT 1 AFTER orcamento_id", "orcamentos_itens.sequencia"),
    ("ALTER TABLE orcamentos_itens ADD COLUMN observacoes TEXT NULL AFTER valor_total", "orcamentos_itens.observacoes"),
    
    # pedidos_venda
    ("ALTER TABLE pedidos_venda ADD COLUMN tabela_preco_id INT NULL AFTER data_faturamento", "pedidos_venda.tabela_preco_id"),
    ("ALTER TABLE pedidos_venda ADD COLUMN observacoes_internas TEXT NULL AFTER observacoes", "pedidos_venda.observacoes_internas"),
    ("ALTER TABLE pedidos_venda ADD COLUMN ativo TINYINT(1) NOT NULL DEFAULT 1 AFTER criado_por_user_id", "pedidos_venda.ativo"),
    
    # pedidos_venda_itens
    ("ALTER TABLE pedidos_venda_itens ADD COLUMN sequencia INT NOT NULL DEFAULT 1 AFTER pedido_id", "pedidos_venda_itens.sequencia"),
    ("ALTER TABLE pedidos_venda_itens ADD COLUMN observacoes TEXT NULL AFTER valor_total", "pedidos_venda_itens.observacoes"),
    
    # pdv_sessoes
    ("ALTER TABLE pdv_sessoes ADD COLUMN valor_sangrias DECIMAL(15,2) NOT NULL DEFAULT 0.00 AFTER valor_vendas", "pdv_sessoes.valor_sangrias"),
    ("ALTER TABLE pdv_sessoes ADD COLUMN valor_suprimentos DECIMAL(15,2) NOT NULL DEFAULT 0.00 AFTER valor_sangrias", "pdv_sessoes.valor_suprimentos"),
]

def run_migration():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 3306))
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'livesun_comercial')
    
    print(f"Executando migrações em {db_name}...\n")
    
    try:
        conn = pymysql.connect(
            host=db_host, port=db_port, user=db_user,
            password=db_password, database=db_name, charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            for sql, desc in MIGRATIONS:
                try:
                    cursor.execute(sql)
                    print(f"✅ {desc}")
                except pymysql.err.OperationalError as e:
                    if "Duplicate column" in str(e) or "already exists" in str(e):
                        print(f"✓ {desc} (já existe)")
                    else:
                        print(f"❌ {desc}: {e}")
            
            conn.commit()
            print("\n✅ Migração concluída!")
            return 0
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    sys.exit(run_migration())
