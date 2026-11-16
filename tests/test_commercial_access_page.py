from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import requests
from flask import Flask
from src.core.commercial_access import CommercialAccessError, register_commercial_access_errors
from src.services import central_assinaturas as central

ROOT = Path(__file__).resolve().parents[1]


def application(authenticated=False, code=403):
    app = Flask(__name__, template_folder=str(ROOT/'src/templates'), static_folder=str(ROOT/'src/static'))
    app.config.update(TESTING=True, SECRET_KEY='test-only')
    app.jinja_env.globals.update(current_user=SimpleNamespace(is_authenticated=authenticated))
    app.add_url_rule('/login', endpoint='auth.login', view_func=lambda: 'login')
    app.add_url_rule('/logout', endpoint='auth.logout', view_func=lambda: 'logout')
    app.add_url_rule('/dashboard', endpoint='dashboard.index', view_func=lambda: 'dashboard')
    register_commercial_access_errors(app)

    @app.get('/restricted')
    def restricted():
        raise CommercialAccessError('Acesso indisponível para sua assinatura.', code)
    return app


@pytest.mark.parametrize('authenticated', [False, True])
@pytest.mark.parametrize('code', [403, 503])
def test_themed_support_page_preserves_error_status(authenticated, code):
    response = application(authenticated, code).test_client().get('/restricted')
    assert response.status_code == code
    html = response.get_data(as_text=True)
    assert 'LiveSun Comercial' in html
    assert 'commercial-access.css' in html
    assert 'mailto:suporte@livesun.com.br' in html
    assert 'tel:+5571999990204' in html
    assert '71 99999-0204' in html
    assert 'href="https://app.pipefy.com/public/form/ETeM9Gbz" target="_blank" rel="noopener noreferrer"' in html
    assert 'Verificar acesso novamente' in html
    assert ('Sair da conta' if authenticated else 'Voltar ao login') in html
    assert 'class="ls-sidebar' not in html
    assert 'ls-theme' in html
    assert response.headers['Cache-Control'] == 'no-store'
    if code == 503:
        assert response.headers['Retry-After'] == '60'


def test_json_and_unrelated_permissions_not_replaced():
    app = application()
    from flask import abort
    app.add_url_rule('/forbidden', view_func=lambda: abort(403))
    response = app.test_client().get('/restricted', headers={'Accept':'application/json'})
    assert response.status_code == 403
    assert response.json['error'] == 'acesso_comercial_indisponivel'
    assert b'commercial-access-support' not in app.test_client().get('/forbidden').data


def test_suspension_uses_commercial_exception_without_writes():
    with application().app_context(), patch.object(central.db.session, 'get', return_value=object()), \
            patch.object(central, 'entitlements', return_value={'status':'SUSPENSA','acesso_produto':False}):
        with pytest.raises(CommercialAccessError) as error:
            central.check(1)
        assert error.value.code == 403


def test_connection_failure_keeps_503_and_rollback():
    link = SimpleNamespace(payload={}, valido_ate=None, cliente_id=123)
    cfg = SimpleNamespace(base_url='https://central.example', token='encrypted', cache_ttl=900)
    app = application()
    app.config['CENTRAL_RUNTIME_ENV'] = 'production'
    with app.app_context(), patch.object(central, 'config', return_value=cfg), \
            patch.object(central.db.session, 'get', return_value=link), \
            patch.object(central.db.session, 'rollback') as rollback, \
            patch.object(central, 'cipher') as cipher, \
            patch('requests.Session.get', side_effect=requests.Timeout):
        cipher.return_value.decrypt.return_value = b'test-token'
        with pytest.raises(CommercialAccessError) as error:
            central.entitlements(1)
        assert error.value.code == 503
        rollback.assert_called_once()