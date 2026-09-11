#!/usr/bin/env python3
"""
Script para executar a migração do banco Financeiro para o Comercial
Lê dados do banco de origem e insere no banco de destino usando Python
"""

import pymysql
from pymysql import Error
from datetime import datetime, date
import sys

# Configurações dos bancos de dados
CONFIG_ORIGEM = {
    'host': '195.35.61.111',
    'port': 3306,
    'user': 'u951548013_gfinanceiro',
    'password': 'quemsabe123!A',
    'database': 'u951548013_gfinanceiro',
    'charset': 'utf8mb4'
}

CONFIG_DESTINO = {
    'host': '195.35.61.111',
    'port': 3306,
    'user': 'u951548013_LS_Comercial',
    'password': 'quemsabe123!A',
    'database': 'u951548013_LS_Comercial',
    'charset': 'utf8mb4'
}

def migrar_tabela(conn_origem, conn_destino, tabela, campos_extras=None):
    """
    Migra dados de uma tabela do banco origem para o destino
    
    Args:
        conn_origem: Conexão com banco de origem
        conn_destino: Conexão com banco de destino
        tabela: Nome da tabela
        campos_extras: Dicionário com campos extras a adicionar no destino
    
    Returns:
        (sucesso, qtd_registros)
    """
    cursor_origem = conn_origem.cursor()
    cursor_destino = conn_destino.cursor()
    
    try:
        # Obter colunas de ambos os bancos
        cursor_origem.execute(f"DESCRIBE {tabela}")
        colunas_origem = [row[0] for row in cursor_origem.fetchall()]
        
        cursor_destino.execute(f"DESCRIBE {tabela}")
        colunas_destino_all = [row[0] for row in cursor_destino.fetchall()]
        
        # Usar apenas colunas que existem em AMBOS os bancos
        colunas_comuns = [col for col in colunas_origem if col in colunas_destino_all]
        
        # Preparar colunas destino (colunas comuns + extras se fornecidos)
        colunas_destino = list(colunas_comuns)
        if campos_extras:
            for col in campos_extras.keys():
                if col in colunas_destino_all and col not in colunas_destino:
                    colunas_destino.append(col)
        
        # Ler dados da origem (apenas colunas comuns) - com LIMIT para evitar timeout
        colunas_sql_origem = ', '.join(colunas_comuns)
        cursor_origem.execute(f"SELECT {colunas_sql_origem} FROM {tabela}")
        dados_origem = cursor_origem.fetchall()
        
        print(f"[INFO] {tabela}: {len(dados_origem)} registros para migrar")
        
        if not dados_origem:
            print(f"[INFO] {tabela}: 0 registros (tabela vazia)")
            return True, 0
        
        # Preparar INSERT com IGNORE para evitar conflitos
        colunas_sql = ', '.join([f"`{col}`" for col in colunas_destino])
        
        # Preparar dados para inserção
        dados_inserir = []
        for linha in dados_origem:
            dados_dict = dict(zip(colunas_comuns, linha))
            
            nova_linha = []
            # Garantir ordem correta das colunas
            for col in colunas_destino:
                if col in colunas_comuns:
                    nova_linha.append(dados_dict[col])
                elif campos_extras and col in campos_extras:
                    nova_linha.append(campos_extras[col])
                else:
                    nova_linha.append(None)  # Coluna não existe na origem
            
            dados_inserir.append(tuple(nova_linha))
        
        # Executar INSERT um a um usando formatação manual
        for dados in dados_inserir:
            try:
                # Formatar valores manualmente
                valores_formatados = []
                for valor in dados:
                    if valor is None:
                        valores_formatados.append('NULL')
                    elif isinstance(valor, str):
                        valores_formatados.append(f"'{valor.replace(chr(39), chr(39)+chr(39))}'")  # Escape aspas simples
                    elif isinstance(valor, bool):
                        valores_formatados.append('1' if valor else '0')
                    elif isinstance(valor, (datetime, date)):
                        valores_formatados.append(f"'{valor.strftime('%Y-%m-%d %H:%M:%S')}'")
                    elif isinstance(valor, (int, float)):
                        valores_formatados.append(str(valor))
                    else:
                        # Para Decimal e outros tipos numéricos
                        valores_formatados.append(str(valor))
                
                valores_sql = ', '.join(valores_formatados)
                insert_sql = f"INSERT IGNORE INTO `{tabela}` ({colunas_sql}) VALUES ({valores_sql})"
                cursor_destino.execute(insert_sql)
            except Error as e:
                print(f"[ERRO] {tabela}: {e}")
                print(f"[DEBUG] SQL: {insert_sql}")
                print(f"[DEBUG] Colunas destino: {colunas_destino}")
                print(f"[DEBUG] Colunas comuns: {colunas_comuns}")
                raise e
        
        return True, len(dados_inserir)
        
    except Error as e:
        print(f"[ERRO] {tabela}: {e}")
        return False, 0
    finally:
        cursor_origem.close()
        cursor_destino.close()

def executar_migracao():
    """Executa a migração completa"""
    
    print("=" * 60)
    print("INICIANDO MIGRACAO: Financeiro -> Comercial")
    print("=" * 60)
    
    # Conectar aos bancos
    print("\nConectando aos bancos...")
    conn_origem = None
    conn_destino = None
    
    try:
        conn_origem = pymysql.connect(**CONFIG_ORIGEM)
        print(f"[OK] Conectado ao banco {CONFIG_ORIGEM['database']}")
    except Error as e:
        print(f"[ERRO] Erro ao conectar ao banco de origem: {e}")
        return False
    
    try:
        conn_destino = pymysql.connect(**CONFIG_DESTINO)
        print(f"[OK] Conectado ao banco {CONFIG_DESTINO['database']}")
    except Error as e:
        print(f"[ERRO] Erro ao conectar ao banco de destino: {e}")
        if conn_origem:
            conn_origem.close()
        return False
    
    # Iniciar transação no destino
    conn_destino.autocommit(False)
    
    try:
        # Desabilitar verificação de FK
        cursor_destino = conn_destino.cursor()
        cursor_destino.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor_destino.close()
        
        print("\nExecutando migração...")
        print("-" * 60)
        
        erros = []
        total_migrado = 0
        
        # Função para reconectar se necessário
        def reconectar_destino():
            nonlocal conn_destino
            try:
                if conn_destino:
                    conn_destino.close()
                conn_destino = pymysql.connect(**CONFIG_DESTINO)
                conn_destino.autocommit(False)
                cursor = conn_destino.cursor()
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                cursor.close()
                print("[INFO] Reconectado ao banco de destino")
                return True
            except Error as e:
                print(f"[ERRO] Falha ao reconectar: {e}")
                return False
        
        # 1. empresas
        sucesso, qtd = migrar_tabela(
            conn_origem, conn_destino, 'empresas',
            campos_extras={
                'nome_fantasia': None,
                'plano': 'premium',
                'atividade_comercial': 1,
                'atividade_servicos': 1,
                'atividade_financeiro': 1,
                'atividade_locacao': 0,
                'atividade_contratos': 0,
                'atividade_propostas': 0,
                'atividade_dashboard': 1,
                'endereco_rua': None,
                'endereco_numero': None,
                'endereco_bairro': None,
                'codigo_municipio_ibge': None,
                'endereco_cidade': None,
                'endereco_uf': None,
                'endereco_cep': None,
                'inscricao_municipal': None,
                'inscricao_estadual': None,
                'telefone': None,
                'email': None,
                'op_simp_nac': 3,
                'reg_ap_trib_sn': 1
            }
        )
        if sucesso:
            print(f"[OK] empresas: {qtd} registros migrados")
            total_migrado += qtd
        else:
            erros.append("empresas")
        
        # 2. users
        # Precisa ler dados primeiro para calcular o role
        cursor_origem = conn_origem.cursor()
        cursor_origem.execute("SELECT * FROM users")
        colunas_users = [desc[0] for desc in cursor_origem.description]
        dados_users = cursor_origem.fetchall()
        cursor_origem.close()
        
        if dados_users:
            cursor_destino = conn_destino.cursor()
            for linha in dados_users:
                dados_dict = dict(zip(colunas_users, linha))
                role = 'admin' if dados_dict['is_admin'] == 1 else 'viewer'
                
                insert_sql = """INSERT IGNORE INTO users (id, empresa_id, username, email, password_hash, 
                                full_name, is_active, is_admin, role, dashboard_chart_days, 
                                created_at, updated_at) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                
                cursor_destino.execute(insert_sql, (
                    dados_dict['id'],
                    dados_dict['empresa_id'],
                    dados_dict['username'],
                    dados_dict['email'],
                    dados_dict['password_hash'],
                    dados_dict['full_name'],
                    dados_dict['is_active'],
                    dados_dict['is_admin'],
                    role,
                    dados_dict['dashboard_chart_days'],
                    dados_dict['created_at'],
                    dados_dict['updated_at']
                ))
            
            print(f"[OK] users: {len(dados_users)} registros migrados")
            total_migrado += len(dados_users)
            cursor_destino.close()
        else:
            print(f"[INFO] users: 0 registros (tabela vazia)")
        
        # 3. fluxo_contas_modelo - NAO MIGRAR (tabela de sistema/plano de contas padrao)
        print("[INFO] fluxo_contas_modelo: NAO migrado (tabela de sistema - usar plano de contas padrao do Comercial)")
        
        # 4. entidades
        sucesso, qtd = migrar_tabela(
            conn_origem, conn_destino, 'entidades',
            campos_extras={
                'nome_fantasia': None,
                'inscricao_estadual': None,
                'inscricao_municipal': None,
                'endereco_rua': None,
                'endereco_numero': None,
                'endereco_bairro': None,
                'codigo_municipio_ibge': None,
                'endereco_cidade': None,
                'endereco_uf': None,
                'endereco_cep': None,
                'telefone': None,
                'email': None,
                'contrato_produto': None
            }
        )
        if sucesso:
            print(f"[OK] entidades: {qtd} registros migrados")
            total_migrado += qtd
        else:
            erros.append("entidades")
        
        # 5. contas_banco
        sucesso, qtd = migrar_tabela(
            conn_origem, conn_destino, 'contas_banco',
            campos_extras={'is_principal': 0}
        )
        if sucesso:
            print(f"[OK] contas_banco: {qtd} registros migrados")
            total_migrado += qtd
        else:
            erros.append("contas_banco")
        
        # 6. lancamentos
        sucesso, qtd = migrar_tabela(
            conn_origem, conn_destino, 'lancamentos',
            campos_extras={'referencia_banco': None, 'fonte': 'migracao'}
        )
        if sucesso:
            print(f"[OK] lancamentos: {qtd} registros migrados")
            total_migrado += qtd
        else:
            erros.append("lancamentos")
        
        # 7. fluxo_caixa_realizado - NAO MIGRAR (tabela calculada, pode ser regenerada)
        print("[INFO] fluxo_caixa_realizado: NAO migrado (tabela calculada - sera regenerada pelo sistema)")
        
        # 8. fluxo_caixa_previsto - NAO MIGRAR (tabela calculada, pode ser regenerada)
        print("[INFO] fluxo_caixa_previsto: NAO migrado (tabela calculada - sera regenerada pelo sistema)")
        
        # Reconectar antes das tabelas restantes
        print("[INFO] Reconectando antes de continuar...")
        if not reconectar_destino():
            print("[ERRO] Falha ao reconectar, abortando migração")
            erros.append("falha ao reconectar")
        else:
            # 9. parametros_sistema
            sucesso, qtd = migrar_tabela(conn_origem, conn_destino, 'parametros_sistema')
            if sucesso:
                print(f"[OK] parametros_sistema: {qtd} registros migrados")
                total_migrado += qtd
            else:
                erros.append("parametros_sistema")
            
            # 10. comissoes
            sucesso, qtd = migrar_tabela(conn_origem, conn_destino, 'comissoes')
            if sucesso:
                print(f"[OK] comissoes: {qtd} registros migrados")
                total_migrado += qtd
            else:
                erros.append("comissoes")
            
            # 11. importacao_nfse
            sucesso, qtd = migrar_tabela(conn_origem, conn_destino, 'importacao_nfse')
            if sucesso:
                print(f"[OK] importacao_nfse: {qtd} registros migrados")
                total_migrado += qtd
            else:
                erros.append("importacao_nfse")
        
        # Verificação final
        print("\n" + "-" * 60)
        print("VERIFICACAO DE INTEGRIDADE")
        print("-" * 60)
        
        tabelas = [
            'empresas', 'users', 'entidades',
            'contas_banco', 'lancamentos', 'parametros_sistema', 'comissoes',
            'importacao_nfse'
        ]
        
        cursor_destino = conn_destino.cursor()
        for tabela in tabelas:
            try:
                cursor_destino.execute(f"SELECT COUNT(*) FROM {tabela}")
                count = cursor_destino.fetchone()[0]
                print(f"  {tabela}: {count} registros")
            except Error as e:
                print(f"  {tabela}: Erro ao contar - {e}")
        cursor_destino.close()
        
        # Commit ou Rollback
        if len(erros) == 0:
            conn_destino.commit()
            print("\n" + "=" * 60)
            print("[OK] MIGRACAO CONCLUIDA COM SUCESSO")
            print("=" * 60)
            print(f"Total de registros migrados: {total_migrado}")
            print("Lembre-se de ajustar manualmente o campo is_principal em contas_banco se necessário.")
            return True
        else:
            conn_destino.rollback()
            print("\n" + "=" * 60)
            print("[ERRO] MIGRACAO FALHOU - ROLLBACK EXECUTADO")
            print("=" * 60)
            print(f"Tabelas com erro: {', '.join(erros)}")
            return False

    except Error as e:
        conn_destino.rollback()
        print(f"\n[ERRO] Erro durante migracao: {e}")
        print("ROLLBACK executado.")
        return False
        
    finally:
        # Reabilitar verificação de FK
        try:
            cursor_destino = conn_destino.cursor()
            cursor_destino.execute("SET FOREIGN_KEY_CHECKS = 1")
            cursor_destino.close()
        except:
            pass
        
        if conn_origem:
            conn_origem.close()
        if conn_destino:
            conn_destino.close()
        
        print("\nConexoes encerradas.")

if __name__ == "__main__":
    try:
        resultado = executar_migracao()
        sys.exit(0 if resultado else 1)
    except KeyboardInterrupt:
        print("\n\nMigracao interrompida pelo usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
