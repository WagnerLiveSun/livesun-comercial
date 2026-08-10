# -*- coding: utf-8 -*-
"""Validação pós-ajuste do banco Hostinger (apenas leitura)."""
import os
import pymysql

CONN = dict(
    host=os.environ.get("DB_HOST", "195.35.61.111"),
    port=int(os.environ.get("DB_PORT", 3306)),
    user=os.environ.get("DB_USER", "u951548013_LS_Comercial"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "u951548013_LS_Comercial"),
    charset="utf8mb4",
    connect_timeout=10,
)


def main():
    c = pymysql.connect(**CONN)
    cur = c.cursor()
    print("== Contagens (dados preservados) ==")
    for t in [
        "empresas", "users", "entidades", "orcamentos", "pedidos_venda",
        "nfse_nacional_emissoes", "documentos_venda", "produtos", "lancamentos",
    ]:
        cur.execute(f"SELECT COUNT(*) FROM `{t}`")
        print(f"  {t}: {cur.fetchone()[0]}")

    print("\n== Colunas recém-adicionadas ==")
    checks = [
        ("pedidos_venda", "documento_nfse_id"),
        ("pedidos_venda", "documento_nfe_id"),
        ("pedidos_venda_itens", "documento_item_id"),
        ("pedidos_venda_itens", "tipo_documento"),
        ("nfse_nacional_emissoes", "pedido_id"),
        ("documentos_venda", "pedido_id"),
        ("documentos_venda", "origem_tipo"),
    ]
    for t, col in checks:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema=%s AND table_name=%s AND column_name=%s",
            (CONN["database"], t, col),
        )
        print(f"  {t}.{col}: {'OK' if cur.fetchone()[0] else 'FALTA!'}")

    c.close()


if __name__ == "__main__":
    main()