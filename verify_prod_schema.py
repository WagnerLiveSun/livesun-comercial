"""Verifica (somente leitura) se todas as tabelas de locação existem no banco de produção."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

PROD_ENV = {
    'DB_TYPE': 'mysql',
    'DB_HOST': '195.35.61.111',
    'DB_PORT': '3306',
    'DB_USER': 'u951548013_LS_Comercial',
    'DB_PASSWORD': 'quemsabe123!A',
    'DB_NAME': 'u951548013_LS_Comercial',
}
for k, v in PROD_ENV.items():
    os.environ[k] = v

from src.app import create_app
from src.models import db
from sqlalchemy import inspect

EXPECTED = [
    'locacao_pecas', 'locacao_kits', 'locacao_kit_itens',
    'locacao_disponibilidade', 'locacao_parametros', 'locacao_eventos',
    'locacao_orcamentos', 'locacao_orcamento_itens', 'locacao_reservas',
    'locacao_contratos', 'locacao_retiradas', 'locacao_retirada_itens',
    'locacao_devolucoes', 'locacao_inspecoes', 'locacao_manutencoes',
    'locacao_titulos', 'locacao_cobrancas', 'locacao_devolucao_caucao',
    'locacao_faturamentos', 'locacao_auditoria',
]

ATIVIDADES = [
    'atividade_comercial', 'atividade_servicos', 'atividade_financeiro',
    'atividade_locacao', 'atividade_contratos', 'atividade_propostas',
    'atividade_dashboard',
]

app = create_app('production')
with app.app_context():
    insp = inspect(db.engine)
    existing = set(insp.get_table_names())
    missing = [t for t in EXPECTED if t not in existing]
    print('=== VERIFICACAO FINAL BANCO DE PRODUCAO === - verify_prod_schema.py:45')
    print(f'Tabelas de locação verificadas: {len(EXPECTED)} - verify_prod_schema.py:46')
    print(f'Faltando: {len(missing)} - verify_prod_schema.py:47')
    for t in missing:
        print(f'{t} - verify_prod_schema.py:49')

    if insp.has_table('empresas'):
        cols = {c['name'] for c in insp.get_columns('empresas')}
        missing_atv = [a for a in ATIVIDADES if a not in cols]
        print(f'\nColunas atividade_* faltando em empresas: {len(missing_atv)} - verify_prod_schema.py:54')
        for a in missing_atv:
            print(f'{a} - verify_prod_schema.py:56')

    print('\nRESULTADO: - verify_prod_schema.py:58', 'OK - todas presentes' if not missing and not missing_atv else 'PENDENTE')
