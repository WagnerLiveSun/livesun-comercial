# -*- coding: utf-8 -*-
"""Smoke test read-only das queries dos painéis (comercial e fiscal) contra o Hostinger."""
import sys
from urllib.parse import quote_plus

sys.path.insert(0, r"d:\App_LiveSun\LiveSun_Comercial_X")

from sqlalchemy import create_engine, func, select  # noqa: E402

# Registra os models
from src.models import (  # noqa: E402
    Orcamento,
    PedidoVenda,
    PedidoVendaItem,
    NfseNacionalEmissao,
    DocumentoVenda,
)
import src.models.locacao  # noqa: E402,F401

URL = "mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4".format(
    quote_plus("u951548013_LS_Comercial"),
    quote_plus("quemsabe123!A"),
    "195.35.61.111",
    "3306",
    quote_plus("u951548013_LS_Comercial"),
)
engine = create_engine(URL, pool_pre_ping=True)


def main():
    from datetime import datetime, timedelta

    hoje = datetime.now().date()
    primeiro_dia_mes = datetime(hoje.year, hoje.month, 1)
    semana_atras = hoje - timedelta(days=7)

    with engine.connect() as conn:
        # --- Painel Comercial ---
        print("[Comercial] - _smoke_dashboards_hostinger.py:39")
        q = select(func.count()).select_from(Orcamento.__table__)
        q2 = select(func.count()).select_from(PedidoVenda.__table__)
        q3 = select(func.count()).select_from(DocumentoVenda.__table__)
        q4 = select(func.count()).select_from(PedidoVendaItem.__table__)
        for nome, st in [("orcamentos", q), ("pedidos_venda", q2),
                         ("documentos_venda", q3), ("pedidos_venda_itens", q4)]:
            print(f"SELECT {nome}: {conn.execute(st).scalar()} registros - _smoke_dashboards_hostinger.py:46")
        # Query do painel comercial (pedidos do mês, com todas as colunas)
        st = select(func.count()).where(
            PedidoVenda.empresa_id == 1,
            PedidoVenda.data_emissao >= primeiro_dia_mes,
        )
        print(f"pedidos do mês (com todas as colunas): {conn.execute(st).scalar()} - _smoke_dashboards_hostinger.py:52")

        # --- Painel Fiscal ---
        print("\n[Fiscal] - _smoke_dashboards_hostinger.py:55")
        st = select(func.count()).where(
            NfseNacionalEmissao.empresa_id == 1,
            NfseNacionalEmissao.criado_em >= primeiro_dia_mes,
            NfseNacionalEmissao.status_processamento == "AUTORIZADA",
        )
        print(f"nfse emitidas/aut. mês (todas as colunas): {conn.execute(st).scalar()} - _smoke_dashboards_hostinger.py:61")
        st = select(func.count()).where(
            NfseNacionalEmissao.situacao_fiscal.in_(["REJEITADA", "ERRO"])
        )
        print(f"nfse rejeitadas: {conn.execute(st).scalar()} - _smoke_dashboards_hostinger.py:65")

    print("\nOK: nenhum erro de coluna/tabela nas consultas dos painéis. - _smoke_dashboards_hostinger.py:67")


if __name__ == "__main__":
    main()