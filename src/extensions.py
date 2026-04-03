from collections import defaultdict, deque
from functools import wraps
from threading import Lock
from time import monotonic

from flask import current_app, flash, redirect, request
from flask_login import current_user
from flask_wtf.csrf import CSRFProtect


_RATE_LIMIT_STATE = defaultdict(deque)
_RATE_LIMIT_LOCK = Lock()


class SimpleRateLimiter:
    def reset(self):
        with _RATE_LIMIT_LOCK:
            _RATE_LIMIT_STATE.clear()

    def _parse_limit(self, limit_value: str):
        amount_text, period_text = limit_value.split('/', 1)
        amount = int(amount_text.strip())
        period_text = period_text.strip().lower()

        if period_text.startswith('second'):
            window_seconds = 1
        elif period_text.startswith('minute'):
            window_seconds = 60
        elif period_text.startswith('hour'):
            window_seconds = 3600
        elif period_text.startswith('day'):
            window_seconds = 86400
        else:
            raise ValueError(f'Periodo de rate limit nao suportado: {limit_value}')

        return amount, window_seconds

    def _client_key(self, endpoint_name: str):
        if current_user.is_authenticated:
            identity = f'user:{current_user.get_id()}'
        else:
            identity = f'ip:{request.remote_addr or "unknown"}'
        return f'{endpoint_name}:{identity}'

    def limit(self, limit_value: str):
        amount, window_seconds = self._parse_limit(limit_value)

        def decorator(view_func):
            @wraps(view_func)
            def wrapped(*args, **kwargs):
                if not current_app.config.get('RATELIMIT_ENABLED', True):
                    return view_func(*args, **kwargs)

                key = self._client_key(request.endpoint or view_func.__name__)
                now = monotonic()
                cutoff = now - window_seconds

                with _RATE_LIMIT_LOCK:
                    hits = _RATE_LIMIT_STATE[key]
                    while hits and hits[0] < cutoff:
                        hits.popleft()
                    if len(hits) >= amount:
                        flash('Muitas tentativas. Aguarde um pouco antes de tentar novamente.', 'warning')
                        return redirect(request.url)
                    hits.append(now)

                return view_func(*args, **kwargs)

            return wrapped

        return decorator


def require_role(*allowed_roles):
    """
    Decorator to check if user has one of the allowed roles.
    Usage: @require_role('admin') or @require_role('admin', 'operator')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Acesso restrito. Por favor faça login.', 'danger')
                return redirect(current_app.config.get('LOGIN_URL', '/auth/login'))
            
            user_role = getattr(current_user, 'role', 'viewer')
            if user_role not in allowed_roles:
                flash(f'Acesso negado. Privilégios insuficientes (você é {user_role}).', 'danger')
                return redirect(request.referrer or '/')
            
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


limiter = SimpleRateLimiter()
csrf = CSRFProtect()