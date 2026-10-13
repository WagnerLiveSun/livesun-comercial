"""Contexto de tenant e aplicacao de RLS PostgreSQL (SET LOCAL via set_config)."""

from __future__ import annotations

import logging

from flask import abort, current_app, has_app_context, has_request_context, request, session
from flask_login import current_user
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from src.core.database_config import is_postgresql_uri, postgres_rls_enabled
from src.models import db

logger = logging.getLogger(__name__)

_RLS_INFO_KEY = 'livesun_rls_empresa_id'

PUBLIC_ENDPOINT_PREFIXES = (
    'static',
    'auth.login',
    'auth.register',
    'auth.forgot_password',
    'auth.reset_password',
    'comercial_webhook.',
)

PUBLIC_PATH_PREFIXES = (
    '/static/',
    '/auth/login',
    '/auth/register',
    '/auth/forgot-password',
    '/auth/reset-password',
    '/webhooks/',
)


def is_postgresql() -> bool:
    if has_app_context():
        uri = str(current_app.config.get('SQLALCHEMY_DATABASE_URI') or '')
        if uri.startswith('sqlite'):
            return False
        if is_postgresql_uri(uri):
            return True
        try:
            return db.engine.dialect.name == 'postgresql'
        except Exception:
            return False
    from src.core.database_config import is_postgresql_configured
    return is_postgresql_configured()


def _parse_empresa_id(raw) -> int | None:
    if raw is None or raw == '':
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def persist_auth_tenant_session(user) -> None:
    """Grava identificadores de tenant apos login. Nao usa dados do request."""
    if user is None:
        return
    session['user_id'] = user.id
    empresa_id = _parse_empresa_id(getattr(user, 'empresa_id', None))
    if empresa_id is None:
        session.pop('empresa_id', None)
    else:
        session['empresa_id'] = empresa_id
    is_platform = bool(getattr(user, 'is_livesun_admin', lambda: False)())
    session['is_platform_admin'] = is_platform


def clear_auth_tenant_session() -> None:
    session.pop('empresa_id', None)
    session.pop('user_id', None)
    session.pop('is_platform_admin', None)


def _authenticated_empresa_id() -> int | None:
    if has_request_context() and getattr(current_user, 'is_authenticated', False):
        return _parse_empresa_id(getattr(current_user, 'empresa_id', None))
    return None


def get_current_empresa_id() -> int:
    """empresa_id da sessao autenticada. Nao le query string, form, header ou JSON."""
    empresa_id = _authenticated_empresa_id()
    if empresa_id is not None:
        session_eid = None
        if has_request_context():
            session_eid = _parse_empresa_id(session.get('empresa_id'))
            if session_eid is not None and session_eid != empresa_id:
                abort(403)
        return empresa_id

    abort(401)


def _is_public_request() -> bool:
    if not has_request_context():
        return True
    endpoint = request.endpoint or ''
    if endpoint == 'static' or endpoint.startswith('static'):
        return True
    for prefix in PUBLIC_ENDPOINT_PREFIXES:
        if endpoint == prefix or endpoint.startswith(prefix):
            return True
    path = request.path or ''
    for prefix in PUBLIC_PATH_PREFIXES:
        if path == prefix.rstrip('/') or path.startswith(prefix):
            return True
    if path == '/suporte':
        return True
    return False


def _should_apply_rls() -> bool:
    if not is_postgresql():
        return False
    if not postgres_rls_enabled():
        return False
    if not has_request_context():
        return False
    if _is_public_request():
        return False
    return True


def apply_postgres_tenant_context(sql_session=None) -> None:
    """Aplica set_config(..., true) na transacao atual. No-op em MySQL/SQLite."""
    if not _should_apply_rls():
        return

    sess = sql_session if sql_session is not None else db.session
    empresa_id = _authenticated_empresa_id()
    if empresa_id is None:
        empresa_id = _parse_empresa_id(session.get('empresa_id'))
        if empresa_id is None:
            return
        if not session.get('_user_id') and not session.get('user_id'):
            return

    last = sess.info.get(_RLS_INFO_KEY)
    if last == empresa_id:
        return

    sess.execute(
        text("SELECT set_config('app.empresa_id', :empresa_id, true)"),
        {'empresa_id': str(empresa_id)},
    )
    sess.info[_RLS_INFO_KEY] = empresa_id


def tenant_sql_session():
    """Garante o contexto RLS na sessao SQLAlchemy atual e a devolve."""
    apply_postgres_tenant_context()
    return db.session


def _clear_rls_mark(session_obj, _flush_context=None):
    session_obj.info.pop(_RLS_INFO_KEY, None)


def _on_after_begin(session_obj, transaction, connection):
    """Reaplica o contexto RLS apos commit/rollback (nova transacao).

    Executa direto na ``connection`` do evento: chamar ``session.execute``
    ou acessar ``current_user`` (que pode disparar ``load_user`` e outra
    ``session.execute``) dentro de ``after_begin`` reentra na sessao em
    provisionamento de conexao e gera InvalidRequestError.

    So usa o ``empresa_id`` da sessao Flask (cookie ja validado no login);
    a reconciliacao com ``current_user.empresa_id`` continua acontecendo em
    ``apply_postgres_tenant_context`` (before_request), que aborta 403 na
    divergencia.
    """
    if not _should_apply_rls():
        return
    empresa_id = _parse_empresa_id(session.get('empresa_id'))
    if empresa_id is None:
        return
    if not session.get('_user_id') and not session.get('user_id'):
        return
    if session_obj.info.get(_RLS_INFO_KEY) == empresa_id:
        return
    connection.execute(
        text("SELECT set_config('app.empresa_id', :empresa_id, true)"),
        {'empresa_id': str(empresa_id)},
    )
    session_obj.info[_RLS_INFO_KEY] = empresa_id


def register_tenant_session_events() -> None:
    if getattr(register_tenant_session_events, '_registered', False):
        return
    event.listen(Session, 'after_begin', _on_after_begin)
    event.listen(Session, 'after_commit', _clear_rls_mark)
    event.listen(Session, 'after_rollback', _clear_rls_mark)
    register_tenant_session_events._registered = True
