#!/usr/bin/env python3
"""
Script de verificação completa do banco de dados.
Checa se todas as tabelas e colunas necessárias existem.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import pymysql

# Definição de todas as tabelas e colunas esperadas
TABELAS_ESPERADAS = {
    'produtos': [
        'id', 'empresa_id', 'filial_id', 'codigo_interno', 'descricao_resumida',
        'descricao_completa', 'unidade_medida', 'codigo_barras', 'gtin', 'ncm',
        'ex_tipi', 'cest', 'ipi_classe', 'origem_mercadoria', 'tipo_item',
        'controla_estoque', 'estoque_atual', 'estoque_minimo', 'valor_venda_padrao', 'valor_custo',
        'ativo', 'criado_em', 'atualizado_em'
    ],
    'servicos': [
        'id', 'empresa_id', 'filial_id', 'codigo_interno', 'descricao',
        'codigo_servico', 'nbs', 'natureza_servico', 'indicador_incidencia',
        'ativo', 'criado_em', 'atualizado_em'
    ],
    'tabelas_preco': [
        'id', 'empresa_id', 'codigo', 'nome', 'descricao', 'ativo',
        'criado_em', 'atualizado_em'
    ],
    'tabelas_preco_itens': [
        'id', 'empresa_id', 'tabela_preco_id', 'produto_id', 'servico_id',
        'preco_custo', 'preco_venda', 'markup', 'desconto_maximo', 'ativo',
        'criado_em', 'atualizado_em'
    ],
    'orcamentos': [
        'id', 'empresa_id', 'filial_id', 'numero', 'cliente_id', 'vendedor_id',
        'data_emissao', 'data_validade', 'tabela_preco_id', 'observacoes',
        'observacoes_internas', 'status', 'valor_produtos', 'valor_servicos',
        'valor_desconto', 'valor_total', 'pedido_id', 'criado_por_user_id',
        'data_aprovacao', 'aprovado_por_user_id', 'ativo',
        'criado_em', 'atualizado_em'
    ],
    'orcamentos_itens': [
        'id', 'empresa_id', 'orcamento_id', 'sequencia', 'tipo_item',
        'produto_id', 'servico_id', 'descricao', 'quantidade', 'valor_unitario',
        'valor_desconto', 'valor_total', 'observacoes',
        'criado_em', 'atualizado_em'
    ],
    'pedidos_venda': [
        'id', 'empresa_id', 'filial_id', 'numero', 'orcamento_id', 'cliente_id',
        'vendedor_id', 'data_emissao', 'data_entrega', 'data_faturamento',
        'tabela_preco_id', 'observacoes', 'observacoes_internas', 'status',
        'valor_produtos', 'valor_servicos', 'valor_desconto', 'valor_frete',
        'valor_total', 'documento_venda_id', 'criado_por_user_id',
        'ativo', 'criado_em', 'atualizado_em'
    ],
    'pedidos_venda_itens': [
        'id', 'empresa_id', 'pedido_id', 'sequencia', 'tipo_item',
        'produto_id', 'servico_id', 'descricao', 'quantidade', 'valor_unitario',
        'valor_desconto', 'valor_total', 'observacoes',
        'criado_em', 'atualizado_em'
    ],
    'pdv_sessoes': [
        'id', 'empresa_id', 'filial_id', 'user_id', 'numero', 'pdv_nome',
        'data_abertura', 'data_fechamento', 'valor_abertura', 'valor_fechamento',
        'valor_vendas', 'valor_sangrias', 'valor_suprimentos', 'status',
        'observacoes', 'criado_em', 'atualizado_em'
    ],
    'pdv_vendas': [
        'id', 'empresa_id', 'filial_id', 'sessao_id', 'numero', 'cliente_id',
        'data_venda', 'subtotal', 'valor_desconto', 'valor_total',
        'valor_dinheiro', 'valor_cartao_credito', 'valor_cartao_debito',
        'valor_pix', 'valor_recebido', 'valor_troco', 'status',
        'observacoes', 'criado_em', 'atualizado_em'
    ],
    'pdv_itens': [
        'id', 'empresa_id', 'venda_id', 'sequencia', 'tipo_item',
        'produto_id', 'servico_id', 'codigo', 'descricao', 'quantidade',
        'valor_unitario', 'valor_total', 'codigo_barras',
        'criado_em', 'atualizado_em'
    ],
}

def verificar_banco():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 3306))
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'livesun_comercial')
    
    print(f"Verificando banco {db_name}...\n")
    
    try:
        conn = pymysql.connect(
            host=db_host, port=db_port, user=db_user,
            password=db_password, database=db_name, charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            problemas = []
            
            for tabela, colunas_esperadas in TABELAS_ESPERADAS.items():
                # Verificar se tabela existe
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                """, (db_name, tabela))
                
                if cursor.fetchone()[0] == 0:
                    problemas.append(f"❌ TABELA AUSENTE: {tabela}")
                    continue
                
                # Verificar colunas
                cursor.execute("""
                    SELECT COLUMN_NAME FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                """, (db_name, tabela))
                
                colunas_existentes = [row[0] for row in cursor.fetchall()]
                colunas_faltando = [c for c in colunas_esperadas if c not in colunas_existentes]
                
                if colunas_faltando:
                    problemas.append(f"❌ TABELA {tabela} - COLUNAS AUSENTES: {', '.join(colunas_faltando)}")
                else:
                    print(f"✅ Tabela {tabela}: OK")
            
            if problemas:
                print("\n" + "="*60)
                print("PROBLEMAS ENCONTRADOS:")
                print("="*60)
                for p in problemas:
                    print(p)
                return 1
            else:
                print("\n" + "="*60)
                print("✅ BANCO DE DADOS COMPLETO!")
                print("="*60)
                return 0
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    sys.exit(verificar_banco())
