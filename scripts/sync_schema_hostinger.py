#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compara e ajusta o schema do banco MySQL da HOSTINGER com o código/banco local.

Uso:
  python scripts/sync_schema_hostinger.py --compare   # apenas comparação (relatório)
  python scripts/sync_schema_hostinger.py --apply     # compara e APLICA ajustes no Hostinger

Credenciais Hostinger via variáveis de ambiente:
  DB_HOST (default 195.35.61.111), DB_PORT (3306),
  DB_USER (default u951548013_LS_Comercial),
  DB_PASSWORD (OBRIGATÓRIA), DB_NAME (default u951548013_LS_Comercial)

Banco local (referência) via .env do projeto (localhost/comercial @controller_owner).
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import create_engine, inspect as sa_inspect, text  # noqa: E402

# Registra os modelos (metadata) do código atual
from src.models import db  # noqa: E402
import src.models.locacao  # noqa: E402,F401  # garante tabelas do módulo locação


HOST = os.environ.get("DB_HOST", "195.35.61.111")
PORT = int(os.environ.get("DB_PORT", 3306))
USER = os.environ.get("DB_USER", "u951548013_LS_Comercial")
PASSWORD = os.environ.get("DB_PASSWORD", "")
DBNAME = os.environ.get("DB_NAME", "u951548013_LS_Comercial")


def build_engine():
    if not PASSWORD:
        raise SystemExit("ERRO: variável de ambiente DB_PASSWORD não definida (senha do MySQL Hostinger).")
    url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def inventario_modelo():
    """Tabelas/colunas esperadas, conforme o código-fonte (SQLAlchemy models)."""
    expected = {}
    for m in db.Model.registry.mappers:
        tbl = m.local_table
        if tbl is None:
            continue
        cols = {}
        for c in tbl.columns:
            cols[c.name] = {
                "type": str(c.type),
                "nullable": bool(c.nullable),
                "default": None if c.server_default is None else str(c.server_default.arg).strip(),
                "primary_key": bool(c.primary_key),
                "autoincrement": bool(c.autoincrement),
                "index": bool(c.index),
                "unique": bool(c.unique),
            }
        expected[tbl.name] = cols
    return expected


def get_mysql_schema(engine):
    insp = sa_inspect(engine)
    schema = {}
    for t in insp.get_table_names():
        cols = {}
        for c in insp.get_columns(t):
            cols[c["name"]] = {
                "type": str(c["type"]),
                "nullable": bool(c.get("nullable")),
            }
        schema[t] = cols
    return schema


def interpreta_para_mysql(col_name, meta):
    """Gera definição de coluna compatível com MySQL a partir da metadata do modelo."""
    from sqlalchemy.dialects import mysql

    tipo = meta["type"]
    t = tipo.upper().strip()
    extra = ""
    if t.startswith("BIGINT"):
        extra = " BIGINT"
    elif t.startswith("INTEGER") or t.startswith("INT"):
        extra = " INTEGER"
    elif t.startswith("SMALLINT"):
        extra = " SMALLINT"
    elif t.startswith("DECIMAL") or t.startswith("NUMERIC"):
        extra = " DECIMAL" + (t[t.index("("):] if "(" in t else "(10,2)")
    elif t.startswith("FLOAT"):
        extra = " FLOAT"
    elif t.startswith("DOUBLE"):
        extra = " DOUBLE"
    elif t.startswith("BOOLEAN") or t.startswith("BOOL"):
        extra = " BOOLEAN"
    elif t.startswith("TINYINT"):
        extra = " TINYINT(1)" + (t[t.index("("):] if "(" in t else "")
    elif t.startswith("VARCHAR"):
        extra = " VARCHAR" + (t[t.index("("):] if "(" in t else "(255)")
    elif t.startswith("CHAR"):
        extra = " CHAR" + (t[t.index("("):] if "(" in t else "(255)")
    elif t.startswith("TEXT"):
        extra = " TEXT"
    elif t.startswith("DATETIME"):
        extra = " DATETIME"
    elif t.startswith("TIMESTAMP"):
        extra = " DATETIME"
    elif t.startswith("DATE"):
        extra = " DATE"
    elif t.startswith("JSON"):
        extra = " JSON"
    else:
        extra = f" {t}"

    ddl = f"`{col_name}`{extra}"
    default = meta["default"]
    nullable = "NULL" if meta["nullable"] else "NOT NULL"
    if default is not None:
        base_type = t.split("(")[0]
        if base_type in ("BOOLEAN", "BOOL", "TINYINT"):
            default = "1" if str(default) in ("True", "'true'", "true", "1", "t") else "0"
            ddl += f" DEFAULT {default}"
        elif base_type in ("VARCHAR", "CHAR", "TEXT"):
            ddl += f" DEFAULT '{str(default).replace(chr(39), chr(39) * 2)}'"
        elif base_type in ("DATETIME", "TIMESTAMP", "DATE"):
            ddl += f" DEFAULT {default}"
        else:
            ddl += f" DEFAULT {default}"
        nullable = "NULL"  # com dados existentes, coluna nova entra como NULL
    else:
        # Sem default explícito: adiciona como NULL para não quebrar registros existentes
        nullable = "NULL"
    ddl += f" {nullable}"
    return ddl


def comparar(engine, expected):
    actual = get_mysql_schema(engine)
    relatorio = {
        "tabelas_faltando": sorted(set(expected) - set(actual)),
        "tabelas_extras": sorted(set(actual) - set(expected)),
        "colunas_faltando": {},
        "tabelas_comuns": sorted(set(expected) & set(actual)),
    }
    for t in relatorio["tabelas_comuns"]:
        falt = sorted(set(expected[t]) - set(actual[t]))
        if falt:
            relatorio["colunas_faltando"][t] = falt
    return relatorio
def exibir_relatorio(rel):
    print("= - sync_schema_hostinger.py:158" * 70)
    print("RELATÓRIO DE COMPARAÇÃO  LOCAL/MODELO vs HOSTINGER - sync_schema_hostinger.py:159")
    print("= - sync_schema_hostinger.py:160" * 70)
    print(f"Tabelas faltando no Hostinger  : {len(rel['tabelas_faltando'])} - sync_schema_hostinger.py:161")
    for t in rel["tabelas_faltando"]:
        print(f"+ {t} - sync_schema_hostinger.py:163")
    print(f"Tabelas extras no Hostinger    : {len(rel['tabelas_extras'])} - sync_schema_hostinger.py:164")
    for t in rel["tabelas_extras"]:
        print(f"{t} - sync_schema_hostinger.py:166")
    print(f"Tabelas comuns                 : {len(rel['tabelas_comuns'])} - sync_schema_hostinger.py:167")
    total_cols = sum(len(v) for v in rel["colunas_faltando"].values())
    print(f"Colunas faltando em tabelas existentes: {total_cols} - sync_schema_hostinger.py:169")
    for t, cols in rel["colunas_faltando"].items():
        print(f"{t}: {', '.join(cols)} - sync_schema_hostinger.py:171")
    print("= - sync_schema_hostinger.py:172" * 70)


def aplicar(engine, expected, rel):
    print("\n[1/3] Criando tabelas ausentes via db.metadata.create_all() ... - sync_schema_hostinger.py:176")
    db.metadata.create_all(engine)
    print("OK  create_all concluído (cria apenas tabelas que não existem).\n - sync_schema_hostinger.py:178")

    print("[2/3] Adicionando colunas faltantes em tabelas existentes ... - sync_schema_hostinger.py:180")
    mudancas = 0
    for t, cols in sorted(rel["colunas_faltando"].items()):
        if t not in expected:
            continue
        for col_name in cols:
            meta = expected[t][col_name]
            if meta.get("primary_key") or meta.get("autoincrement"):
                print(f"{t}.{col_name} é PK/autoincrement  requer recriação, ignorado. - sync_schema_hostinger.py:188")
                continue
            ddl = "ALTER TABLE `%s` ADD COLUMN %s" % (t, interpreta_para_mysql(col_name, meta))
            try:
                with engine.begin() as conn:
                    conn.execute(text(ddl))
                print(f"OK  ALTER {t}.{col_name} - sync_schema_hostinger.py:194")
                mudancas += 1
            except Exception as e:
                er = str(e)
                if "Duplicate column" in er or "already exists" in er:
                    print(f"{t}.{col_name} já existia (ignorado) - sync_schema_hostinger.py:199")
                else:
                    print(f"!! Erro {t}.{col_name}: {er[:120]} - sync_schema_hostinger.py:201")
    print(f"{mudancas} alterações de coluna aplicadas.\n - sync_schema_hostinger.py:202")

    print("[3/3] Verificando integridade final ... - sync_schema_hostinger.py:204")
    atualizado = comparar(engine, expected)
    print(f"Tabelas ainda faltando   : {len(atualizado['tabelas_faltando'])} - sync_schema_hostinger.py:206")
    print(f"Colunas ainda faltando   : {sum(len(v) for v in atualizado['colunas_faltando'].values())} - sync_schema_hostinger.py:207")
    if not atualizado["tabelas_faltando"] and not atualizado["colunas_faltando"]:
        print("OK  Schema do Hostinger alinhado com o códigofonte!\n - sync_schema_hostinger.py:209")
    else:
        for t in atualizado["tabelas_faltando"]:
            print(f"/* tabela ausente */ {t} - sync_schema_hostinger.py:212")
        for t, cols in atualizado["colunas_faltando"].items():
            print(f"/* colunas pendentes */ {t}: {', '.join(cols)} - sync_schema_hostinger.py:214")


def main():
    if "--apply" not in sys.argv and "--compare" not in sys.argv:
        raise SystemExit("Use --compare (relatório) ou --apply (aplica ajustes).")

    engine = build_engine()
    expected = inventario_modelo()
    print(f"Conectando em {HOST}:{PORT}/{DBNAME} como {USER} ... - sync_schema_hostinger.py:223")
    with engine.connect():
        print("Conexão OK! - sync_schema_hostinger.py:225")

    rel = comparar(engine, expected)
    exibir_relatorio(rel)

    out = BASE_DIR / "_relatorio_hostinger.json"
    with open(out, "w", encoding="utf-8") as fp:
        json.dump(rel, fp, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"Relatório salvo em {out} - sync_schema_hostinger.py:233")

    if "--apply" in sys.argv:
        aplicar(engine, expected, rel)
    else:
        print("\n(Nenhuma alteração foi aplicada. Use apply para aplicar.) - sync_schema_hostinger.py:238")


if __name__ == "__main__":
    main()