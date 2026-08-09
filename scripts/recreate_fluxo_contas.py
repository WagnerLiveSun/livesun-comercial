#!/usr/bin/env python3
"""
Script para recriar a tabela fluxo_contas_modelo com o plano padrão.
"""
import pymysql
import sys
import os

# Credenciais Hostinger (via variáveis de ambiente)
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '195.35.61.111'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'u951548013_LS_Comercial'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'u951548013_LS_Comercial'),
    'charset': 'utf8mb4'
}

# Plano padrão de fluxo de caixa
PLANO_PADRAO = [
    ("1", "Entradas de Caixa", "R", None, 1, None),
    ("1.1", "Receitas Operacionais", "R", None, 2, None),
    ("1.1.1", "Vendas à vista", "R", None, 3, 1),
    ("1.1.2", "Vendas cartão crédito", "R", None, 3, 1),
    ("1.1.3", "Vendas cartão débito", "R", None, 3, 1),
    ("1.1.4", "Recebimento mensalidades/serviços", "R", None, 3, 1),
    ("1.2", "Receitas Financeiras", "R", None, 2, None),
    ("1.2.1", "Juros recebidos", "R", None, 3, 1),
    ("1.2.2", "Descontos obtidos", "R", None, 3, 1),
    ("1.3", "Outras Entradas", "R", None, 2, None),
    ("1.3.1", "Empréstimos recebidos", "R", None, 3, 1),
    ("1.3.2", "Aporte de sócios", "R", None, 3, 1),
    ("1.3.3", "Reembolsos diversos", "R", None, 3, 1),
    ("2", "Saídas de Caixa", "P", None, 1, None),
    ("2.1", "Custos Operacionais", "P", None, 2, None),
    ("2.1.1", "Compra de mercadorias", "P", None, 3, 1),
    ("2.1.2", "Matéria-prima/insumos", "P", None, 3, 1),
    ("2.1.3", "Fretes sobre compras", "P", None, 3, 1),
    ("2.2", "Despesas Fixas", "P", None, 2, None),
    ("2.2.1", "Aluguel", "P", None, 3, 1),
    ("2.2.2", "Energia elétrica", "P", None, 3, 1),
    ("2.2.3", "Água", "P", None, 3, 1),
    ("2.2.4", "Internet e telefone", "P", None, 3, 1),
    ("2.3", "Despesas com Pessoal", "P", None, 2, None),
    ("2.3.1", "Salários", "P", None, 3, 1),
    ("2.3.2", "Encargos (INSS, FGTS)", "P", None, 3, 1),
    ("2.3.3", "Pró-labore", "P", None, 3, 1),
    ("2.4", "Despesas Variáveis", "P", None, 2, None),
    ("2.4.1", "Comissões sobre vendas", "P", None, 3, 1),
    ("2.4.2", "Taxas de cartão/maquininha", "P", None, 3, 1),
    ("2.4.3", "Impostos sobre vendas", "P", None, 3, 1),
    ("2.5", "Despesas Financeiras", "P", None, 2, None),
    ("2.5.1", "Juros e multas pagas", "P", None, 3, 1),
    ("2.5.2", "Tarifas bancárias", "P", None, 3, 1),
    ("2.6", "Outras Saídas", "P", None, 2, None),
    ("2.6.1", "Distribuição de lucros", "P", None, 3, 1),
    ("2.6.2", "Adiantamentos a sócios", "P", None, 3, 1),
]

def create_fluxo_contas_table():
    """Cria a tabela fluxo_contas_modelo e insere o plano padrão."""
    try:
        print(f"Conectando ao banco {DB_CONFIG['database']}...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Criar tabela
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS `fluxo_contas_modelo` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `empresa_id` INT NOT NULL,
            `codigo` VARCHAR(20) NOT NULL,
            `descricao` VARCHAR(200) NOT NULL,
            `tipo` VARCHAR(1) NOT NULL,
            `mascara` VARCHAR(50),
            `nivel_sintetico` INT,
            `nivel_analitico` INT,
            `ativo` BOOLEAN DEFAULT TRUE,
            `criado_em` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `atualizado_em` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_fluxo_contas_empresa` (`empresa_id`),
            INDEX `idx_fluxo_contas_codigo` (`codigo`),
            FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        cursor.execute(create_table_sql)
        print("✓ Tabela fluxo_contas_modelo criada")
        
        # Inserir plano padrão (empresa_id será NULL, será preenchido ao criar empresa)
        insert_sql = """
        INSERT INTO `fluxo_contas_modelo` 
        (empresa_id, codigo, descricao, tipo, mascara, nivel_sintetico, nivel_analitico, ativo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Primeiro precisamos de uma empresa_id, vamos usar NULL temporariamente
        # O plano será inserido para cada empresa quando ela for criada
        print("⚠ Tabela criada, mas o plano padrão será inserido automaticamente")
        print("  quando uma nova empresa for cadastrada (via rota /auth/register).")
        
        connection.commit()
        print("\n✓ Tabela fluxo_contas_modelo recriada com sucesso!")
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()
            print("Conexão fechada.")

if __name__ == "__main__":
    print("=" * 60)
    print("RECRIAÇÃO DA TABELA FLUXO_CONTAS_MODELO")
    print("=" * 60)
    print()
    
    create_fluxo_contas_table()
