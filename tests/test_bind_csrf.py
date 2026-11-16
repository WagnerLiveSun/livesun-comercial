from pathlib import Path
from unittest.mock import patch,Mock
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import generate_csrf
from config.config import Config
from src.extensions import csrf
from src.models import db, Empresa
from src.models.central_integracao import CentralVinculo
from src.routes.central_backoffice import central_admin
from src.core.form_security import register_form_errors


def make_app():
    app=Flask(__name__,template_folder=str(Path(__file__).resolve().parents[1]/'src/templates'))
    app.config.update(TESTING=True,SECRET_KEY='test-only',SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SESSION_COOKIE_NAME=Config.SESSION_COOKIE_NAME,LOGIN_DISABLED=True,WTF_CSRF_ENABLED=True)
    db.init_app(app);csrf.init_app(app)
    manager=LoginManager(app)
    manager.user_loader(lambda identifier: None)
    app.register_blueprint(central_admin)
    register_form_errors(app)
    app.add_url_rule('/auth/login','auth.login',lambda:'login')
    app.add_url_rule('/token','token',lambda:generate_csrf())
    return app


def test_binding_keeps_session_when_other_product_cookie_changes():
    app=make_app()
    with app.app_context():
        Empresa.__table__.create(db.engine)
        CentralVinculo.__table__.create(db.engine)
        db.session.add(Empresa(id=1,nome='Teste',cnpj='123',plano='basic'))
        db.session.commit()
        client=app.test_client()
        page=client.get('/token')
        assert 'livesun_comercial_session=' in page.headers['Set-Cookie']
        token=page.get_data(as_text=True)
        client.set_cookie('session','cookie-outro-produto')
        client.set_cookie('livesun_central_session','cookie-central')
        # Mantém a view real; somente autorização e consulta legada são isoladas.
        view=app.view_functions['central_admin.bind']
        with patch('src.routes.central_backoffice.gate',return_value=None), \
             patch('src.routes.central_backoffice.db.session.scalar',return_value=None), \
             patch('src.routes.central_backoffice.fetch_link_state',return_value={'status':'ATIVA'}), \
             patch('src.routes.central_backoffice.store'), \
             patch('src.routes.central_backoffice.config',return_value=Mock(cache_ttl=900)):
            # require_role é testado nas suítes de autorização; acesso só para este ensaio.
            inner=view.__wrapped__.__wrapped__
            app.view_functions['central_admin.bind']=inner
            response=client.post('/backoffice/comercial/central/vincular',data={
                'csrf_token':token,'empresa_id':1,'cliente_id':7})
        assert response.status_code==302
        assert db.session.get(CentralVinculo,1).cliente_id==7
        db.session.remove();db.engine.dispose()


def test_missing_session_csrf_does_not_run_binding():
    app=make_app()
    with patch('src.routes.central_backoffice.gate') as gate:
        response=app.test_client().post('/backoffice/comercial/central/vincular',data={
            'csrf_token':'old-token','empresa_id':1,'cliente_id':7})
        gate.assert_not_called()
    assert response.status_code==400
    assert 'Atualize o formulário' in response.get_data(as_text=True)
    assert response.headers['Cache-Control']=='no-store'