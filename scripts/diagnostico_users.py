#!/usr/bin/env python3
"""Diagnostico: compara users e empresas origem x destino."""
import pymysql

CONFIG_ORIGEM = {
    'host': '195.35.61.111', 'port': 3306,
    'user': 'u951548013_gfinanceiro', 'password': 'quemsabe123!A',
    'database': 'u951548013_gfinanceiro', 'charset': 'utf8mb4',
}
CONFIG_DESTINO = {
    'host': '195.35.61.111', 'port': 3306,
    'user': 'u951548013_LS_Comercial', 'password': 'quemsabe123!A',
    'database': 'u951548013_LS_Comercial', 'charset': 'utf8mb4',
}

def dump(conn, rotulo):
    cur = conn.cursor()
    print(f"\n===== USERS ({rotulo}) ===== - diagnostico_users.py:18")
    cur.execute("SELECT id, username, email, is_admin, LEFT(password_hash, 25), full_name FROM users ORDER BY id")
    for r in cur.fetchall():
        print(f"id={r[0]:>3}  user={r[1]!r:<20} email={r[2]!r:<32} admin={r[3]} hash={r[4]!r} nome={r[5]!r} - diagnostico_users.py:21")
    print(f"===== EMPRESAS ({rotulo}) ===== - diagnostico_users.py:22")
    cur.execute("SELECT id, nome, cnpj FROM empresas ORDER BY id")
    for r in cur.fetchall():
        print(f"id={r[0]}  nome={r[1]!r}  cnpj={r[2]!r} - diagnostico_users.py:25")
    cur.close()

o = pymysql.connect(**CONFIG_ORIGEM)
d = pymysql.connect(**CONFIG_DESTINO)
dump(o, 'ORIGEM')
dump(d, 'DESTINO')
o.close(); d.close()
