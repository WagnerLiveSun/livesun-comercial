from functools import wraps

from flask import abort
from flask_login import current_user


def tenant_id() -> int | None:
    """Return the current authenticated user's company id."""
    if not current_user.is_authenticated:
        return None
    return getattr(current_user, 'empresa_id', None)


def scoped_query(model):
    """Return a query scoped to the current tenant (empresa)."""
    tid = tenant_id()
    if tid is None:
        # Retorna query vazia se não houver tenant (usuário não autenticado)
        return model.query.filter_by(empresa_id=-1)
    return model.query.filter_by(empresa_id=tid)


def scoped_get_or_404(model, entity_id: int, id_field: str = 'id'):
    """Return a tenant-scoped record by id or raise 404."""
    column = getattr(model, id_field)
    return scoped_query(model).filter(column == entity_id).first_or_404()


def validate_ownership(model_class, id_param: str = 'id', empresa_id_field: str = 'empresa_id'):
    """
    Decorator factory para validar que o objeto acessado pertence ao tenant atual.

    Usage:
        @validate_ownership(Lancamento)
        def editar_lancamento(id):
            # O lancamento com 'id' garantidamente pertence à empresa do usuário
            lancamento = Lancamento.query.get_or_404(id)
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            obj_id = kwargs.get(id_param)
            if obj_id is not None:
                obj = model_class.query.get(obj_id)
                if not obj:
                    abort(404)
                obj_empresa_id = getattr(obj, empresa_id_field, None)
                current_tid = tenant_id()
                if obj_empresa_id != current_tid:
                    abort(403)  # Forbidden - objeto não pertence ao tenant
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
