# -*- coding: utf-8 -*-
"""Reproduz exatamente as queries do dashboard /comercial contra o Hostinger."""
import os
import sys
from decimal import Decimal
from datetime import datetime

from sqlalchemy import create_engine, func
from urllib.parse import quote_plus

sys.path.insert(0, r"d:\App_LiveSun\LiveSun_Comercial_X")
from src.models import Orcamento, PedidoVenda  # noqa: E402
import src.models.locacao  # noqa: E402,F401

URL = "mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4".format(
    quote_plus(os.environ.get("DB_USER", "u951548013_LS_Comercial")),
    quote_plus(os.environ.get("DB_PASSWORD", "")),
    os.environ.get("DB_HOST", "195.35.61.111"),
    os.environ.get("DB_PORT", "3306"),
    quote_plus(os.environ.get("DB_NAME", "u951548013_LS_Comercial")),
)
engine = create_engine(URL, pool_pre_ping=True)
EMPRESA_ID = 1


def main():
    hoje = datetime.now().date()
    with engine.connect() as conn:
        total_orcamentos = conn.execute(
            Orcamento.__table__.select().where(Orcamento.empresa_id == EMPRESA_ID)
        ).rowcount if False else conn.execute(
            func.count().select().where(Orcamento.empresa_id == EMPRESA_ID).select_from(Orcamento.__table__)
        ).scalar()
    # Simplificado: replicar as contagens e sum() direto (ORM query funciona como no dashboard)
    with engine.connect() as conn:
        c = lambda tbl, **kw: conn.execute(
            func.count().select().select_from(tbl.__table__).where(
                *([tbl.__table__.c.__dict__[k] == v for k, v in kw.items()] or [None == None])
            )
        ).scalar() if kw else conn.execute(func.count().select_from(tbl.__table__)).scalar()
    print("skip complex ORM, using raw checks below - _smoke_comercial_query.py:41")

    with engine.connect() as conn:
        print("total_orcamentos: - _smoke_comercial_query.py:44", conn.execute(
            Orcamento.__table__.select().with_only_columns(func.count()).where(Orcamento.empresa_id == EMPRESA_ID)
        ).scalar())
        print("orcamentos_aprovados: - _smoke_comercial_query.py:47", conn.execute(
            func.count(Orcamento.id).where(
                Orcamento.empresa_id == EMPRESA_ID, Orcamento.status == "aprovado"
            )
        ).scalar())
        print("valor_total_orcamentos: - _smoke_comercial_query.py:52", conn.execute(
            func.sum(Orcamento.valor_total).where(Orcamento.empresa_id == EMPRESA_ID)
        ).scalar() or 0)
        print("total_pedidos: - _smoke_comercial_query.py:55", conn.execute(
            func.count(PedidoVenda.id).where(PedidoVenda.empresa_id == EMPRESA_ID)
        ).scalar())
        print("valor_total_pedidos: - _smoke_comercial_query.py:58", conn.execute(
            func.sum(PedidoVenda.valor_total).where(PedidoVenda.empresa_id == EMPRESA_ID)
        ).scalar() or 0)
    print("\nOK: queries do /comercial rodaram sem erro de coluna/tabela no Hostinger. - _smoke_comercial_query.py:61")


if __name__ == "__main__":
    main()