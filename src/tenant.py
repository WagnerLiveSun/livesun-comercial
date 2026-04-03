from flask_login import current_user


def tenant_id() -> int:
    """Return the current authenticated user's company id."""
    return current_user.empresa_id


def scoped_query(model):
    """Return a query scoped to the current tenant (empresa)."""
    return model.query.filter_by(empresa_id=tenant_id())


def scoped_get_or_404(model, entity_id: int, id_field: str = 'id'):
    """Return a tenant-scoped record by id or raise 404."""
    column = getattr(model, id_field)
    return scoped_query(model).filter(column == entity_id).first_or_404()
