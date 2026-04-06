from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


PLAN_ORDER = {
    'basic': 1,
    'intermediate': 2,
    'premium': 3,
}

PLAN_LABELS = {
    'basic': 'Básico',
    'intermediate': 'Intermediário',
    'premium': 'Premium',
}

PLAN_CHOICES = [
    ('basic', 'Básico'),
    ('intermediate', 'Intermediário'),
    ('premium', 'Premium'),
]

# Ajuste inicial de limites. Se precisar mudar a estratégia comercial depois,
# altere apenas este ponto central.
PLAN_CONFIG: Dict[str, Dict[str, object]] = {
    'basic': {
        'label': 'Básico',
        'max_users': 2,
        'show_advanced_cashflow_fields': False,
        'allow_advanced_cashflow_reports': False,
        'allow_imports': False,
        'allow_conciliation': False,
        'allow_commissions': False,
        'allow_governance': False,
    },
    'intermediate': {
        'label': 'Intermediário',
        'max_users': 5,
        'show_advanced_cashflow_fields': True,
        'allow_advanced_cashflow_reports': True,
        'allow_imports': True,
        'allow_conciliation': True,
        'allow_commissions': True,
        'allow_governance': False,
    },
    'premium': {
        'label': 'Premium',
        'max_users': None,
        'show_advanced_cashflow_fields': True,
        'allow_advanced_cashflow_reports': True,
        'allow_imports': True,
        'allow_conciliation': True,
        'allow_commissions': True,
        'allow_governance': True,
    },
}

# Matriz oficial de disponibilidade por plano (1=basic, 2=intermediate, 3=premium).
PLAN_ENDPOINT_MIN_LEVEL = {
    # Dashboard
    'dashboard.index': 1,

    # Entidades
    'entidades.index': 1,
    'entidades.criar': 1,
    'entidades.editar': 1,
    'entidades.ver': 1,
    'entidades.deletar': 1,
    'entidades.api_search': 1,

    # Plano de fluxo
    'fluxo.index': 2,
    'fluxo.criar': 2,
    'fluxo.editar': 2,
    'fluxo.deletar': 2,
    'fluxo.api_search': 2,

    # Contas bancarias
    'contas_banco.index': 1,
    'contas_banco.criar': 1,
    'contas_banco.editar': 1,
    'contas_banco.ver': 1,
    'contas_banco.deletar': 1,
    'contas_banco.api_search': 1,

    # Lancamentos
    'lancamentos.index': 1,
    'lancamentos.criar': 1,
    'lancamentos.editar': 1,
    'lancamentos.pagar': 1,
    'lancamentos.deletar': 1,

    # Relatorios basicos (basic)
    'relatorios.listagem_lancamentos': 1,
    'relatorios.export_listagem_lancamentos': 1,
    'relatorios.listagem_notas_nfse': 1,
    'relatorios.export_listagem_notas_nfse': 1,

    # Relatorios avancados (intermediate+)
    'relatorios.fluxo_caixa': 2,
    'relatorios.fluxo_caixa_csv': 2,
    'relatorios.export_fluxo_caixa_csv': 2,
    'relatorios.export_fluxo_caixa': 2,
    'relatorios.fluxo_caixa_previsto': 2,
    'relatorios.fluxo_caixa_realizado': 2,
    'relatorio_fluxo.index': 2,
    'relatorio_fluxo.exportar': 2,

    # Importacoes (intermediate+)
    'importacoes.importar_nfse': 2,
    'importacoes.importar_ofx': 2,

    # Conciliacao (intermediate+)
    'conciliacao.index': 2,
    'conciliacao.nova': 2,
    'conciliacao.detalhe': 2,
    'conciliacao.reconciliar': 2,
    'conciliacao.vincular_item': 2,
    'conciliacao.desvincular_item': 2,

    # Comissoes (intermediate+)
    'comissoes.listar': 2,
    'comissoes.apurar': 2,
    'comissoes.relatorio': 2,
    'comissoes.parametros': 2,
    'comissoes.exportar_csv': 2,

    # Governanca (premium)
    'auth.add_user': 1,
    'auth.perfil': 1,
    'auth.controle_acesso': 3,
    'auth.controle_processos': 3,
    'auth.controle_usuario_permissoes': 3,
}


def normalize_plan(plan: Optional[str]) -> str:
    value = (plan or 'premium').strip().lower()
    return value if value in PLAN_CONFIG else 'premium'


def plan_rank(plan: Optional[str]) -> int:
    return PLAN_ORDER.get(normalize_plan(plan), PLAN_ORDER['premium'])


def get_plan_config(plan: Optional[str]) -> Dict[str, object]:
    return PLAN_CONFIG[normalize_plan(plan)]


def get_plan_label(plan: Optional[str]) -> str:
    return PLAN_LABELS[normalize_plan(plan)]


def plan_allows_endpoint(plan: Optional[str], endpoint_name: Optional[str]) -> bool:
    if not endpoint_name:
        return True
    required_level = PLAN_ENDPOINT_MIN_LEVEL.get(endpoint_name, 1)
    return plan_rank(plan) >= required_level


def plan_allows_feature(plan: Optional[str], feature_key: str) -> bool:
    config = get_plan_config(plan)
    return bool(config.get(feature_key, False))


def max_users_for_plan(plan: Optional[str]) -> Optional[int]:
    value = get_plan_config(plan).get('max_users')
    return int(value) if value is not None else None


def is_basic_plan(plan: Optional[str]) -> bool:
    return normalize_plan(plan) == 'basic'


def is_intermediate_plan(plan: Optional[str]) -> bool:
    return normalize_plan(plan) == 'intermediate'


def is_premium_plan(plan: Optional[str]) -> bool:
    return normalize_plan(plan) == 'premium'
