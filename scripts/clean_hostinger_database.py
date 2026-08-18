#!/usr/bin/env python3
"""Script para limpar todas as tabelas do banco de dados na Hostinger"""

import pymysql
from pymysql import MySQLError

# Credenciais do banco de dados na Hostinger
DB_HOST = "195.35.61.111"
DB_PORT = 3306
DB_USER = "u951548013_LS_Comercial"
DB_PASSWORD = "quemsabe123!A"
DB_NAME = "u951548013_LS_Comercial"

# Lista de tabelas para dropar (ordem não importa com FKs desabilitadas)
TABLES = [
    'locacao_auditoria',
    'locacao_faturamento',
    'locacao_devolucao_caucao',
    'locacao_cobranca',
    'locacao_titulo',
    'locacao_inspecao',
    'locacao_devolucao',
    'locacao_retirada_item',
    'locacao_retirada',
    'locacao_reserva',
    'locacao_contrato',
    'locacao_orcamento_item',
    'locacao_orcamento',
    'locacao_evento',
    'locacao_manutencao',
    'locacao_parametro',
    'locacao_disponibilidade',
    'locacao_kit_item',
    'locacao_kit',
    'locacao_peca',
    'contrato_parametro_valor',
    'contrato_parametro',
    'contrato_anexo',
    'contrato_historico',
    'contrato_clausula',
    'contrato',
    'clausula_contrato_padrao',
    'nfse_nacional_evento',
    'nfse_nacional_fila',
    'nfse_nacional_integracao_origem',
    'nfse_nacional_emissao',
    'nfse_nacional_certificado',
    'nfse_nacional_configuracao',
    'nfse_nbs_referencia',
    'nfse_servico_nacional_referencia',
    'nfse_ctrib_mun_referencia',
    'nfse_municipio_referencia',
    'nfse_cnae_referencia',
    'nfse_indop_referencia',
    'lancamentos',
    'fluxo_conta',
    'contas_banco',
    'servicos',
    'fiscal_parametros',
    'empresas',
    'usuarios',
    'entidades',
    'assinatura_empresa',
    'catalogo_planos_comercial',
    'cobranca_recorrente',
    'comissoes',
    'compras_nf_itens',
    'compras_nf_lancamentos',
    'compras_nf_manual',
    'conciliacao_bancaria',
    'conciliacao_item',
    'documento_venda',
    'documento_venda_itens',
    'empresa_fiscal_itens',
    'estoque_movimentos',
    'evento_cobranca',
    'filiais',
    'fluxo_caixa_previsto',
    'fluxo_caixa_realizado',
    'fluxo_contas_modelo',
    'historico_mudanca_plano',
    'importacao_nfse',
    'notificacao_comercial',
    'orcamentos',
    'orcamentos_itens',
    'parametros_sistema',
    'pdv_itens',
    'pdv_sessoes',
    'pdv_vendas',
    'pedidos_venda',
    'pedidos_venda_itens',
    'produtos',
    'role_permissions',
    'tabelas_preco',
    'tabelas_preco_itens',
    'user_permission_overrides',
]

def clean_database():
    """Remove todas as tabelas do banco de dados"""
    try:
        print(f"Conectando ao banco de dados...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=10
        )
        
        print("✅ Conexão bem-sucedida!")
        print()
        
        # Desabilitar verificação de chaves estrangeiras
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            print("✅ Verificação de chaves estrangeiras desabilitada")
        
        # Dropar tabelas
        with connection.cursor() as cursor:
            for table in TABLES:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"✅ Tabela '{table}' removida")
                except MySQLError as e:
                    print(f"⚠️  Erro ao remover '{table}': {e.args[1]}")
        
        # Reabilitar verificação de chaves estrangeiras
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            print("✅ Verificação de chaves estrangeiras reabilitada")
        
        connection.commit()
        connection.close()
        
        print()
        print("✅ Limpeza concluída com sucesso!")
        print(f"Total de tabelas processadas: {len(TABLES)}")
        return True
        
    except MySQLError as e:
        print(f"❌ Erro ao conectar ao banco de dados:")
        print(f"   Código: {e.args[0]}")
        print(f"   Mensagem: {e.args[1]}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado:")
        print(f"   {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("LIMPEZA DO BANCO DE DADOS - HOSTINGER")
    print("=" * 60)
    print()
    
    confirm = input("⚠️  ATENÇÃO: Isso removerá TODAS as tabelas do banco!\nDeseja continuar? (s/N): ")
    
    if confirm.lower() == 's':
        clean_database()
    else:
        print("❌ Operação cancelada pelo usuário.")
