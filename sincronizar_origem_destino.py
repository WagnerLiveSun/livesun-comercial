#!/usr/bin/env python3
"""
Sincronizacao Origem -> Destino (MySQL local -> MySQL Hostinger).

O que o script faz:
1. Compatibilidade de schema: compara as colunas de cada tabela entre a origem
   e o destino e cria no destino as colunas que faltam (ALTER TABLE idempotente).
2. Recria os usuarios do destino: apaga users no destino e reinsere a partir da
   origem (preservando password_hash, role e permissoes).
3. Deleta e reinsere (a partir da origem) as tabelas de dados operacionais:
   lancamentos, estoque_movimentos, importacao_nfse, importacao de XML de
   compras (compras_nf_xml_import / compras_nf_xml_itens), compras_nf_manual,
   compras_nf_itens e compras_nf_lancamentos (tabelas de movimento).
4. NAO toca nas tabelas de sistema: fluxo de caixa, municipio, codigos de
   servico, empresas, entidades, contas_banco, permissoes, referencias fiscais.

Uso:
    python sincronizar_origem_destino.py           # dry-run (nao altera dados)
    python sincronizar_origem_destino.py --exec    # executa de verdade
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv

load_dotenv()

import pymysql

# ---------------------------------------------------------------------------
# Configuracao ORIGEM (local, via .env)
# ---------------------------------------------------------------------------
ORIGEM = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'comercial'),
}

# ---------------------------------------------------------------------------
# Configuracao DESTINO (Hostinger) - pode sobrescrever via variaveis DEST_DB_*
# ---------------------------------------------------------------------------
DESTINO = {
    'host': os.getenv('DEST_DB_HOST', '195.35.61.111'),
    'port': int(os.getenv('DEST_DB_PORT', 3306)),
    'user': os.getenv('DEST_DB_USER', 'u951548013_LS_Comercial'),
    'password': os.getenv('DEST_DB_PASSWORD', 'quemsabe123!A'),
    'database': os.getenv('DEST_DB_NAME', 'u951548013_LS_Comercial'),
}

# Tabelas de DADOS: apagadas no destino e reinseridas a partir da origem.
# Ordem importa: filhas primeiro (para deletar) e pais primeiro (para inserir).
TABELAS_DADOS = [
    # importacao de XML de compras (movimento)
    'compras_nf_xml_itens',
    'compras_nf_xml_import',
    # compras manuais / movimento de NF
    'compras_nf_lancamentos',
    'compras_nf_itens',
    'compras_nf_manual',
    # importacao de NFS-e
    'importacao_nfse',
    # movimento de estoque
    'estoque_movimentos',
    # lancamentos financeiros
    'lancamentos',
]

# Tabelas de SISTEMA que NUNCA sao apagadas no destino (preservadas).
TABELAS_PRESERVADAS = [
    # fluxo de caixa e plano de contas
    'fluxo_contas_modelo', 'fluxo_caixa_realizado', 'fluxo_caixa_previsto',
    'contas_banco',
    # cadastros base
    'empresas', 'entidades', 'parametros_sistema',
    # municipio / codigos de servico / referencias fiscais
    'nfse_municipios_referencia', 'nfse_ctrib_mun_referencia', 'ctiss_bh',
    'nfse_cnae_referencia', 'nfse_nbs_referencia', 'nbs_nbs',
    'nfse_servicos_nacionais_referencia', 'nfse_indop_referencia',
    'nfse_nacional_integracoes_origem',
    # fiscal / contratos / planos
    'empresa_fiscal_itens', 'contratos', 'contrato_parametros',
    'contrato_parametros_valores', 'contrato_clausulas',
    'clausulas_contrato_padrao', 'catalogo_planos_comercial',
    # permissoes / rbac
    'role_permissions', 'user_permission_overrides',
    'rbac_roles', 'rbac_permissions', 'rbac_user_roles', 'rbac_role_permissions',
]

# Usuarios do destino: recriados a partir da origem.
TABELA_USERS = 'users'


def conectar(conf, label):
    try:
        conn = pymysql.connect(
            host=conf['host'], port=conf['port'], user=conf['user'],
            password=conf['password'], database=conf['database'],
            charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
        )
        print(f"OK Conectado a {label}: {conf['host']}:{conf['port']}/{conf['database']} - sincronizar_origem_destino.py:107")
        return conn
    except Exception as e:
        print(f"ERRO ao conectar em {label}: {e} - sincronizar_origem_destino.py:110")
        sys.exit(1)


def tabelas_existentes(conn):
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES")
        return {list(row.values())[0] for row in cur.fetchall()}


def colunas_tabela(conn, tabela):
    """Retorna dict {coluna: tipo_bruto} via SHOW COLUMNS."""
    with conn.cursor() as cur:
        cur.execute(f"SHOW COLUMNS FROM `{tabela}`")
        return {row['Field']: f"{row['Type']} {'NULL' if row['Null'] == 'YES' else 'NOT NULL'}"
                for row in cur.fetchall()}
