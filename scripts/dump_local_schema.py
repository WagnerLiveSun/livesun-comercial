#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o inventário do schema do banco LOCAL (MySQL) em JSON para comparação."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql

LOCAL_DB = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "controller_owner"),
    "password": os.environ.get("DB_PASSWORD", "Controller@2026!"),
    "database": os.environ.get("DB_NAME", "comercial"),
}


def main():
    conn = pymysql.connect(**LOCAL_DB, charset="utf8mb4", connect_timeout=10)
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = [r[0] for r in cur.fetchall()]
    schema = {}
    for t in sorted(tables):
        cur.execute(f"SHOW COLUMNS FROM `{t}`")
        cols = {}
        for (f, typ, null, key, default, extra) in cur.fetchall():
            cols[f] = {"type": typ, "nullable": null == "YES", "key": key, "default": default, "extra": extra}
        schema[t] = cols
    conn.close()

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_local_schema.json")
    with open(out, "w", encoding="utf-8") as fp:
        json.dump(schema, fp, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"LOCAL TABLES: {len(tables)} - dump_local_schema.py:35")
    print(f"OK arquivo: {out} - dump_local_schema.py:36")


if __name__ == "__main__":
    main()