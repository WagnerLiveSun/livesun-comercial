# -*- coding: utf-8 -*-
"""Valida RAW (pymysql) as colunas/tabelas que comercial() lê no Hostinger."""
import os
import pymysql

conn = pymysql.connect(
    host=os.environ.get("DB_HOST", "195.35.61.111"),
    port=int(os.environ.get("DB_PORT", "3306")),
    user=os.environ.get("DB_USER", "u951548013_LS_Comercial"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "u951548013_LS_Comercial"),
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
)
EID = 1
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) c FROM orcamentos WHERE empresa_id=%s", (EID,))
    print("orcamentos total: - _smoke_comercial_raw.py:18", cur.fetchone()["c"])
    cur.execute("SELECT COUNT(*) c FROM orcamentos WHERE empresa_id=%s AND status='aprovado'", (EID,))
    print("orcamentos aprovados: - _smoke_comercial_raw.py:20", cur.fetchone()["c"])
    cur.execute("SELECT COALESCE(SUM(valor_total),0) c FROM orcamentos WHERE empresa_id=%s", (EID,))
    print("valor_total_orcamentos: - _smoke_comercial_raw.py:22", cur.fetchone()["c"])
    cur.execute("SELECT COUNT(*) c FROM pedidos_venda WHERE empresa_id=%s", (EID,))
    print("pedidos total: - _smoke_comercial_raw.py:24", cur.fetchone()["c"])
    cur.execute("SELECT COUNT(*) c FROM pedidos_venda WHERE empresa_id=%s AND status='pendente'", (EID,))
    print("pedidos pendentes: - _smoke_comercial_raw.py:26", cur.fetchone()["c"])
    cur.execute("SELECT COALESCE(SUM(valor_total),0) c FROM pedidos_venda WHERE empresa_id=%s", (EID,))
    print("valor_total_pedidos: - _smoke_comercial_raw.py:28", cur.fetchone()["c"])
conn.close()
print("\nOK: /comercial queries OK no Hostinger (colunas/tabelas existem e respondem). - _smoke_comercial_raw.py:30")
