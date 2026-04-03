# Initialize routes
from . import auth
from . import dashboard
from . import entidades
from . import fluxo
from . import contas_banco

from . import lancamentos
from . import importacoes
from . import conciliacao

__all__ = [
    'auth',
    'dashboard',
    'entidades',
    'fluxo',
    'contas_banco',
    'lancamentos',
    'importacoes',
    'conciliacao',
]
