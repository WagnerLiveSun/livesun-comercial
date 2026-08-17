# -*- coding: utf-8 -*-
"""Validação pós-ajuste do banco Hostinger (apenas leitura)."""
import pymysql

CONN = dict(
    host="195.35.61.111",
    port=3306,
    user="u951548013_LS_Comercial",
    password="quemsabe123!A",
    database="u951548013_LS_Comercial",
    charset="utf8mb4",
    connect_timeout=10,
)


def main():
    c = pymysql.connect(**CONN)
    cur = c.cursor()
    print("== Contagens (dados preservados) == - _validar_hostinger.py:19")
    for t in [
        "empresas", "users", "entidades", "orcamentos", "pedidos_venda",
        "nfse_nacional_emissoes", "documentos_venda", "produtos", "lancamentos",
    ]:
        cur.execute(f"SELECT COUNT(*) FROM `{t}`")
        print(f"{t}: {cur.fetchone()[0]} - _validar_hostinger.py:25")

    print("\n== Colunas recémadicionadas == - _validar_hostinger.py:27")
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
        print(f"{t}.{col}: {'OK' if cur.fetchone()[0] else 'FALTA!'} - _validar_hostinger.py:43")

    c.close()


if __name__ == "__main__":
    main()