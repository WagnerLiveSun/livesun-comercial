from flask import Flask
import pytest
from src.services.central_assinaturas import configure_environment,config,cipher


def test_environment_configuration_without_database(monkeypatch):
    for key,value in {'CENTRAL_ENABLED':'true','CENTRAL_BASE_URL':'http://127.0.0.1:5001',
        'CENTRAL_API_TOKEN':'test-token','CENTRAL_WEBHOOK_SECRET':'h'*40,'CENTRAL_ALLOW_LOCAL_HTTP':'true'}.items():
        monkeypatch.setenv(key,value)
    app=Flask(__name__)
    app.config.update(SECRET_KEY='test-only',CENTRAL_RUNTIME_ENV='development')
    configure_environment(app,'development')
    with app.app_context():
        cfg=config()
        assert cfg.ativo and cfg.base_url=='http://127.0.0.1:5001'
        assert cipher().decrypt(cfg.token.encode()).decode()=='test-token'
        assert not cfg.purga_habilitada


def test_http_environment_refused_in_production(monkeypatch):
    for key,value in {'CENTRAL_ENABLED':'true','CENTRAL_BASE_URL':'http://127.0.0.1:5001',
        'CENTRAL_API_TOKEN':'test-token','CENTRAL_WEBHOOK_SECRET':'h'*40,'CENTRAL_ALLOW_LOCAL_HTTP':'true'}.items():
        monkeypatch.setenv(key,value)
    app=Flask(__name__)
    app.config.update(SECRET_KEY='test-only',CENTRAL_RUNTIME_ENV='production')
    with pytest.raises(ValueError):configure_environment(app,'production')