#!/usr/bin/env python3
"""
Migracao em lotes: fluxo_caixa_realizado e fluxo_caixa_previsto
Origem: u951548013_gfinanceiro -> Destino: u951548013_LS_Comercial (MySQL Hostinger)

- Leitura em lotes por id (ORDER BY id LIMIT n) para evitar timeout
- INSERT IGNORE (idempotente) + commit a cada lote (retomada)
- Reconexao automatica de origem/destino se a conexao cair
- Retoma do MAX(id) ja existente no destino
- Validacao final origem x destino
"""

import sys
from datetime import datetime, date
from decimal import Decimal

import pymysql
from pymysql.err import Error, OperationalError

# ---------------------------------------------------------------------------
# Configuracao
# ---------------------------------------------------------------------------
CONFIG_ORIGEM = {
    'host': '195.35.61.111',
    'port': 3306,
    'user': 'u951548013_gfinanceiro',
    'password': 'quemsabe123!A',
    'database': 'u951548013_gfinanceiro',
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'read_timeout': 300,
    'write_timeout': 300,
}

CONFIG_DESTINO = {
    'host': '195.35.61.111',
    'port': 3306,
    'user': 'u951548013_LS_Comercial',
    'password': 'quemsabe123!A',
    'database': 'u951548013_LS_Comercial',
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'read_timeout': 300,
    'write_timeout': 300,
}

TAMANHO_LOTE = 1000  # registros por lote (ajustavel)

# Erros tipicos de conexao perdida / timeout
ERROS_CONEXAO = (2006, 2013, 2020, 4031)


def conectar(config, rotulo):
    conn = pymysql.connect(**config)
    print(f"[OK] Conectado ao banco {config['database']} ({rotulo}) - migrar_fluxo_em_lotes.py:55")
    return conn


def reconectar(conn, config, rotulo):
    """Fecha (se aberta) e reabre a conexao. Retorna nova conexao."""
    try:
        if conn:
            conn.close()
    except Exception:
        pass
    return conectar(config, rotulo)


def manter_conexao(conn, config, rotulo):
    """Garante conexao viva; reconecta se necessario."""
    try:
        conn.ping(reconnect=False)
        return conn
    except Exception:
        print(f"[INFO] Conexao {rotulo} perdida. Reconectando... - migrar_fluxo_em_lotes.py:75")
        return reconectar(conn, config, rotulo)


def preparar_destino(conn_destino):
    """FK checks off (preserva historico mesmo com referencias ausentes)."""
    cursor = conn_destino.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.close()


def ultimo_id_destino(conn_destino, tabela):
    cursor = conn_destino.cursor()
    cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {tabela}")
    valor = cursor.fetchone()[0] or 0
    cursor.close()
    return int(valor)


def total_origem(conn_origem, tabela):
    cursor = conn_origem.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
    total = cursor.fetchone()[0]
    cursor.close()
    return int(total)


def formatar_valor(valor):
    if valor is None:
        return None
    if isinstance(valor, (datetime, date)):
        return valor.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(valor, Decimal):
        return str(valor)
    return valor
