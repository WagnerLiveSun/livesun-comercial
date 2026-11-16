import hashlib
import hmac
import json
import time
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, abort, current_app, jsonify
from sqlalchemy import inspect, MetaData
from sqlalchemy.exc import IntegrityError
from src.extensions import csrf
from src.models import db, Empresa
from src.models.central_integracao import CentralConfiguracao, CentralVinculo, CentralEvento
from src.services.central_assinaturas import cipher, config, store, validate

central_bp = Blueprint('central_integracao', __name__)


def authenticate(raw):
    cfg = config()
    if not cfg or not cfg.ativo:
        abort(503)
    stamp = request.headers.get('X-LiveSun-Timestamp','')
    try:
        if abs(time.time()-int(stamp)) > 300:
            abort(401)
    except ValueError:
        abort(401)
    secret = cipher().decrypt(cfg.hmac_secret.encode())
    signature = 'sha256=' + hmac.new(secret, stamp.encode()+b'.'+raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, request.headers.get('X-LiveSun-Signature','')):
        abort(401)
    if request.headers.get('Cookie'):
        # Chamadas de serviço não herdam empresa da sessão de navegador.
        from flask import session
        session.clear()
        db.session.info.pop('livesun_rls_empresa_id',None)
    return cfg


def apply_service_tenant(company_id):
    if db.engine.dialect.name == 'postgresql':
        from sqlalchemy import text
        db.session.execute(text("SELECT set_config('app.empresa_id', :company, true)"), {'company':str(company_id)})


@central_bp.post('/webhooks/assinatura')
@csrf.exempt
def webhook():
    if request.content_length is None or request.content_length > 131072:
        abort(413)
    cfg = authenticate(request.get_data())
    data = request.get_json()
    if request.headers.get('X-LiveSun-Event') == 'INTEGRACAO_TESTE':
        if not isinstance(data,dict) or data.get('produto') != 'COMERCIAL' or not isinstance(data.get('nonce'),str) or len(data['nonce']) != 64:
            abort(422)
        proof=hmac.new(cipher().decrypt(cfg.hmac_secret.encode()),
            ('COMERCIAL:'+data['nonce']).encode(),hashlib.sha256).hexdigest()
        return {'produto':'COMERCIAL','nonce':data['nonce'],'prova':proof,'status':'receptor_pronto'},200
    try:
        event_id = data['evento_id']
        if not isinstance(event_id,str) or len(event_id)>100 or not event_id.startswith('evt_'):
            raise ValueError()
        if data['produto'] != 'COMERCIAL' or request.headers.get('X-LiveSun-Event') != data['evento']:
            raise ValueError()
        link = db.session.scalar(db.select(CentralVinculo).where(CentralVinculo.cliente_id == int(data['cliente_id'])).with_for_update())
        if not link:
            abort(422)
        apply_service_tenant(link.empresa_id)
        if db.session.get(CentralEvento,event_id):
            return {'status':'duplicado'},200
        state = data['entitlements']
        validate(state,link.cliente_id)
        if state['assinatura_id'] != data['assinatura_id'] or state['versao'] != data['versao'] or state['status'] != data['status_novo']:
            raise ValueError()
        applied=store(link,state,cfg.cache_ttl)
        db.session.add(CentralEvento(evento_id=event_id))
        db.session.commit()
        return {'status':'aplicado' if applied else 'obsoleto'},200
    except IntegrityError:
        db.session.rollback()
        if db.session.get(CentralEvento,event_id):
            return {'status':'duplicado'},200
        abort(409)
    except (KeyError,ValueError,TypeError):
        db.session.rollback()
        abort(422)


@central_bp.get('/central/estado/<int:customer>')
def state(customer):
    authenticate(request.path.encode())
    link=db.session.scalar(db.select(CentralVinculo).filter_by(cliente_id=customer))
    if not link:
        abort(404)
    return {'cliente_id':str(customer),'produto':'COMERCIAL','assinatura_id':link.assinatura_id,
            'versao':link.versao,'entitlements':link.payload}


def purge_company(company_id):
    """Apaga somente tabelas tenant-owned em ordem de FK, sem desligar integridade."""
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    tables = [table for table in reversed(metadata.sorted_tables) if 'empresa_id' in table.c]
    for table in tables:
        if table.name in ('central_vinculos_comercial',):
            continue
        db.session.execute(table.delete().where(table.c.empresa_id == company_id))
    db.session.execute(Empresa.__table__.delete().where(Empresa.id == company_id))
    # COMMIT apenas no receptor junto ao recibo idempotente.


@central_bp.post('/central/purgar')
@csrf.exempt
def purge():
    cfg=authenticate(request.get_data())
    if not cfg.purga_habilitada:
        abort(409, description='Purga deve ser habilitada após homologação em cópia descartável.')
    if request.headers.get('X-LiveSun-Event') != 'PURGA_SOLICITADA':
        abort(401)
    data=request.get_json()
    try:
        operation=data['operacao_id']
        if not isinstance(operation,str) or not operation.startswith('prg_') or len(operation)>100 or data['produto']!='COMERCIAL':
            raise ValueError()
        receipt='purga:'+operation
        if db.session.get(CentralEvento,receipt):
            return {'operacao_id':operation,'status':'concluida'},200
        link=db.session.scalar(db.select(CentralVinculo).where(CentralVinculo.cliente_id==int(data['cliente_id'])).with_for_update())
        if not link or link.assinatura_id != data['assinatura_id'] or link.payload.get('status')!='EXCLUIDA' or data.get('status')!='EXCLUIDA':
            abort(409)
        if data['versao'] < link.versao:
            abort(409)
        apply_service_tenant(link.empresa_id)
        excluded=datetime.fromisoformat(data['excluida_em'])
        if excluded.tzinfo is None:
            raise ValueError()
        if not data.get('antecipada') and datetime.now(timezone.utc) < excluded+timedelta(days=60):
            abort(409)
        purge_company(link.empresa_id)
        db.session.delete(link)
        db.session.add(CentralEvento(evento_id=receipt))
        db.session.commit()
        return {'operacao_id':operation,'status':'concluida'},200
    except (ValueError,KeyError,TypeError):
        db.session.rollback()
        abort(422)


def register(app, environment):
    from src.core.commercial_access import register_commercial_access_errors
    register_commercial_access_errors(app)
    app.config['CENTRAL_RUNTIME_ENV']=environment
    app.config.setdefault('CENTRAL_SUPPORTED',environment!='testing')
    from src.services.central_assinaturas import configure_environment
    configure_environment(app,environment)
    from src.routes import central_autocadastro  # registra rotas antes do blueprint
    app.register_blueprint(central_bp)