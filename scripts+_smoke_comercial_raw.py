# -*- coding: utf-8 -*-
"""Valida RAW (pymysql) as colunas/tabelas que comercial() lê no Hostinger."""
import os
import pymysql
from urllib.parse import quote_plus

conn = pymysql.connect(
    host=os.environ.get("DB_HOST", "195.35.61.111"),
    port=int(os.environ.get("DB_PORT", "3306")),
    user=os.environ.get("DB_USER", "u951548013_LS_Comercial"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "u951548013_LS_Comercial"),
    charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
EID = 1
try:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) c FROM orcamentos WHERE empresa_id=%s - scripts+_smoke_comercial_raw.py:17", (EID,)); r=cur.fetchone(); print("orcamentos total:", r["c"])
        cur.execute("SELECT COUNT(*) c FROM orcamentos WHERE empresa_id=%s AND status='aprovado' - scripts+_smoke_comercial_raw.py:18", (EID,)); print("orcamentos aprovados:", cur.fetchone()["c"])
        cur.execute("SELECT COUNT(*) c FROM orcamentos WHERE empresa_id=%s AND status='emitido' - scripts+_smoke_comercial_raw.py:19", (EID,)); print("orcamentos emitidos:", cur.fetchone()["c"])
        cur.execute("SELECT COALESCE(SUM(valor_total),0) FROM orcamentos WHERE empresa_id=%s - scripts+_smoke_comercial_raw.py:20", (EID,)); print("valor_total_orcamentos:", cur.fetchone()["c"])
        cur.execute("SELECT COUNT(*) c FROM pedidos_venda WHERE empresa_id=%s - scripts+_smoke_comercial_raw.py:21", (EID,)); print("pedidos total:", cur.fetchone()["c"])
        cur.execute("SELECT COUNT(*) c FROM pedidos_venda WHERE empresa_id=%s AND status='pendente' - scripts+_smoke_comercial_raw.py:22", (EID,)); print("pedidos pendentes:", cur.fetchone()["c"])
        cur.execute("SELECT COALESCE(SUM(valor_total),0) FROM pedidos_venda WHERE empresa_id=%s - scripts+_smoke_comercial_raw.py:23", (EID,)); print("valor_total_pedidos:", cur.fetchone()["c"])
    print("\nOK: colunas/tabelas do /comercial existem e respondem no Hostinger. - scripts+_smoke_comercial_raw.py:24")
finally:
    conn.close()
