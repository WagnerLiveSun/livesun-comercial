"""Somente assinatura LiveSun; não importa serviços bancários Asaas/Inter."""
import base64
import hashlib
import os
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit
import requests
from cryptography.fernet import Fernet
from flask import current_app, abort
from src.models import db, Empresa
from src.models.central_integracao import CentralConfiguracao, CentralVinculo
from src.core.commercial_access import CommercialAccessError


def cipher():
    configured = current_app.config.get('CENTRAL_ENCRYPTION_KEY')
    key = configured.encode() if configured else base64.urlsafe_b64encode(hashlib.sha256(current_app.secret_key.encode()).digest())
    return Fernet(key)


def config():
    if current_app.config.get('CENTRAL_USE_ENV'):
        from types import SimpleNamespace
        return SimpleNamespace(base_url=current_app.config['CENTRAL_BASE_URL'],
            token=cipher().encrypt(current_app.config['CENTRAL_API_TOKEN'].encode()).decode(),
            hmac_secret=cipher().encrypt(current_app.config['CENTRAL_WEBHOOK_SECRET'].encode()).decode(),
            ativo=current_app.config['CENTRAL_ENABLED'],cache_ttl=current_app.config['CENTRAL_CACHE_TTL_SECONDS'],
            purga_habilitada=False)
    return db.session.get(CentralConfiguracao, 1)


def configure_environment(app, environment):
    if environment == 'testing' or 'CENTRAL_ENABLED' not in os.environ:
        return
    app.config.update(CENTRAL_USE_ENV=True,
        CENTRAL_ENABLED=os.getenv('CENTRAL_ENABLED','false').lower()=='true',
        CENTRAL_BASE_URL=os.getenv('CENTRAL_BASE_URL','').rstrip('/'),
        CENTRAL_API_TOKEN=os.getenv('CENTRAL_API_TOKEN',''),
        CENTRAL_WEBHOOK_SECRET=os.getenv('CENTRAL_WEBHOOK_SECRET',''),
        CENTRAL_CACHE_TTL_SECONDS=int(os.getenv('CENTRAL_CACHE_TTL_SECONDS','900')),
        CENTRAL_ALLOW_LOCAL_HTTP=os.getenv('CENTRAL_ALLOW_LOCAL_HTTP','false').lower()=='true')
    if app.config['CENTRAL_ENABLED']:
        if not app.config['CENTRAL_API_TOKEN'] or len(app.config['CENTRAL_WEBHOOK_SECRET'])<32:
            raise RuntimeError('Configure token e segredo HMAC do Central no ambiente.')
        if not 1 <= app.config['CENTRAL_CACHE_TTL_SECONDS'] <= 900:
            raise RuntimeError('Cache do Central deve estar entre 1 e 900 segundos.')
        with app.app_context():
            validate_url(app.config['CENTRAL_BASE_URL'])


def enabled():
    if not current_app.config.get('CENTRAL_RUNTIME_ENV'):
        return False
    if not current_app.config.get('CENTRAL_SUPPORTED', True):
        return False
    from sqlalchemy import inspect
    # Reutiliza a transacao atual; outra conexao pode interferir no cadastro
    # ainda nao confirmado, especialmente em SQLite com conexao compartilhada.
    if not inspect(db.session.connection()).has_table('central_config_comercial'):
        return False
    item = config()
    return bool(item and item.ativo)


def validate_url(url):
    parsed = urlsplit(url)
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
        raise ValueError('Informe somente a origem do Central.')
    local = (current_app.config.get('CENTRAL_RUNTIME_ENV') in ('development','testing')
        and (not current_app.config.get('CENTRAL_USE_ENV') or current_app.config.get('CENTRAL_ALLOW_LOCAL_HTTP'))
        and parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1','localhost','::1'))
    if parsed.scheme != 'https' and not local:
        raise ValueError('Produção exige HTTPS; testes locais aceitam somente loopback.')
    return url.rstrip('/')


def validate(data, customer):
    if (not isinstance(data, dict) or data.get('produto') != 'COMERCIAL' or data.get('cliente_id') != str(customer)
        or type(data.get('assinatura_id')) is not int or data['assinatura_id'] < 1
        or type(data.get('versao')) is not int or data['versao'] < 1
        or type(data.get('acesso_produto')) is not bool or not isinstance(data.get('limites'), dict)
        or data.get('status') not in ('ATIVA','TRIAL','SUSPENSA','BLOQUEADA','CANCELADA','EXCLUIDA','EXPIRADA')):
        raise ValueError('Estado comercial inválido.')
    until = datetime.fromisoformat(data['valido_ate'])
    if until.tzinfo is None:
        raise ValueError('Validade inválida.')
    return until.astimezone(timezone.utc).replace(tzinfo=None)


def store(link, data, ttl=900):
    until = validate(data, link.cliente_id)
    if (data['assinatura_id'], data['versao']) < (link.assinatura_id, link.versao):
        return False
    link.payload = data
    link.assinatura_id, link.versao = data['assinatura_id'], data['versao']
    link.valido_ate = min(until, datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=ttl))
    # Plano oficial é espelhado; não sincroniza módulos nem permissões internas.
    company = db.session.get(Empresa, link.empresa_id)
    plan = str(data.get('plano', '')).lower().removesuffix('_anual')
    if company and plan in ('basic','intermediate','premium'):
        company.plano = plan
    if company and 'usuarios' in data['limites']:
        limit = data['limites']['usuarios']
        if type(limit) is not int or limit < 0:
            raise ValueError('Limite inválido.')
        company.usuarios_maximos = limit
    return True


def entitlements(company_id):
    cfg = config()
    link = db.session.get(CentralVinculo, company_id)
    if not cfg or not link:
        raise CommercialAccessError('O vínculo comercial da sua empresa ainda não foi concluído. Entre em contato com o suporte.')
    if link.payload and link.valido_ate and link.valido_ate > datetime.now(timezone.utc).replace(tzinfo=None):
        return link.payload
    try:
        base = validate_url(cfg.base_url)
        with requests.Session() as http:
            http.trust_env = False
            response = http.get(f'{base}/api/v1/entitlements/{link.cliente_id}/COMERCIAL',
                headers={'Authorization': 'Bearer ' + cipher().decrypt(cfg.token.encode()).decode()},
                timeout=(3,5), allow_redirects=False)
        if response.status_code in (401,403,404):
            raise CommercialAccessError('Não foi possível autorizar o acesso da sua empresa. Entre em contato com o suporte.')
        response.raise_for_status()
        data = response.json()
        link = db.session.scalar(db.select(CentralVinculo).where(CentralVinculo.empresa_id == company_id)
            .with_for_update().execution_options(populate_existing=True))
        store(link, data, cfg.cache_ttl)
        db.session.commit()
        if link.valido_ate <= datetime.now(timezone.utc).replace(tzinfo=None):
            raise CommercialAccessError('Não foi possível atualizar a autorização de acesso. Tente novamente em instantes.', 503)
        return link.payload
    except (requests.RequestException, ValueError, KeyError, TypeError):
        db.session.rollback()
        current_app.logger.warning('Central indisponível; acesso sensível não liberado por contingência.')
        raise CommercialAccessError('Não foi possível consultar sua assinatura neste momento. Tente novamente em instantes ou fale com o suporte.', 503)


def check(company_id):
    link = db.session.get(CentralVinculo, company_id)
    if link is None:
        # Bonificações já concedidas permanecem intactas até vínculo explícito.
        from src.models import AssinaturaEmpresa
        legacy = db.session.scalar(db.select(AssinaturaEmpresa).filter_by(empresa_id=company_id))
        if legacy and legacy.bonus_liberado and legacy.status != 'excluida':
            end = (legacy.bonus_concedido_em + timedelta(days=legacy.bonus_dias)).date() if legacy.bonus_dias and legacy.bonus_concedido_em else None
            if end is None or end >= datetime.now(timezone.utc).date():
                return {'status':'ATIVA','acesso_produto':True,'bonificada':True,
                        'bonificacao_ate':end.isoformat() if end else None,'limites':{}}
        from src.services.central_autocadastro import awaits_approval
        if awaits_approval(company_id):
            raise CommercialAccessError('Seu cadastro foi recebido e aguarda habilitação pela LiveSun. Fale com nossa equipe para acompanhar o atendimento.')
    data = entitlements(company_id)
    if data['status'] not in ('ATIVA','TRIAL') or not data['acesso_produto']:
        raise CommercialAccessError('O acesso ao LiveSun Comercial está indisponível para sua assinatura. Fale com nossa equipe para verificar a situação e regularizar o acesso.')
    return data