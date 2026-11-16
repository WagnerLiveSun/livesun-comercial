from datetime import datetime, timedelta
from flask import request, abort
from sqlalchemy.exc import IntegrityError
from src.extensions import csrf
from src.models import db, Empresa, AssinaturaEmpresa
from src.models.central_integracao import CentralCadastroPendente, CentralVinculo, CentralEvento, utcnow
from src.services.central_assinaturas import store, validate
from src.routes.central_integracao import central_bp, authenticate, apply_service_tenant


@central_bp.get('/central/cadastros-pendentes')
def pending_registrations():
    authenticate(request.path.encode())
    cursor = request.args.get('apos',default=0,type=int)
    if cursor < 0:
        abort(422)
    rows = db.session.scalars(db.select(CentralCadastroPendente).where(
        CentralCadastroPendente.id > cursor, CentralCadastroPendente.status != 'VINCULADO')
        .order_by(CentralCadastroPendente.id).limit(51)).all()
    page=rows[:50]
    return {'cadastros':[{'dados':row.dados} for row in page],
            'proximo':page[-1].id if len(rows)>50 else None}


@central_bp.post('/central/cadastros/vincular')
@csrf.exempt
def bind_approved_registration():
    if request.content_length is None or request.content_length > 131072:
        abort(413)
    cfg=authenticate(request.get_data())
    if request.headers.get('X-LiveSun-Event') != 'CADASTRO_HABILITADO':
        abort(401)
    data=request.get_json()
    receipt=None
    try:
        if data['produto']!='COMERCIAL' or data['status'] not in ('VINCULO_PENDENTE','VINCULADA'):
            abort(422)
        company_id=data['empresa_id']
        customer=data['cliente_id']
        if type(company_id) is not int or type(customer) is not int or customer<=0:
            abort(422)
        row=db.session.scalar(db.select(CentralCadastroPendente).where(
            CentralCadastroPendente.empresa_id==company_id,CentralCadastroPendente.evento_id==data['evento_id']).with_for_update())
        if not row:
            abort(404)
        apply_service_tenant(company_id)
        link=db.session.get(CentralVinculo,company_id)
        if link and link.cliente_id!=customer:
            abort(409)
        receipt='cadastro:'+row.evento_id
        if receipt and db.session.get(CentralEvento,receipt):
            if not link or link.assinatura_id != data['assinatura_id']:
                abort(409)
            return {'evento_id':row.evento_id,'status':'vinculado'},200
        company=db.session.get(Empresa,company_id)
        if not company:
            abort(404)
        state=data['entitlements']
        validate(state,customer)
        if state['assinatura_id']!=data['assinatura_id'] or state['status'] not in ('ATIVA','TRIAL') or state['acesso_produto'] is not True:
            abort(409)
        legacy=db.session.scalar(db.select(AssinaturaEmpresa).filter_by(empresa_id=company_id))
        if legacy and legacy.bonus_liberado:
            end=(legacy.bonus_concedido_em+timedelta(days=legacy.bonus_dias)).date() if legacy.bonus_dias and legacy.bonus_concedido_em else None
            if not state.get('bonificada') or state.get('bonificacao_ate')!=(end.isoformat() if end else None):
                abort(409)
        if not link:
            link=CentralVinculo(empresa_id=company_id,cliente_id=customer,assinatura_id=0,versao=0)
            db.session.add(link)
        store(link,state,cfg.cache_ttl)
        row.status,row.solicitacao_id,row.vinculado_em,row.erro='VINCULADO',data['solicitacao_id'],utcnow(),None
        db.session.add(CentralEvento(evento_id=receipt))
        db.session.commit()
        return {'evento_id':row.evento_id,'status':'vinculado'},200
    except IntegrityError:
        db.session.rollback()
        if db.session.get(CentralEvento,receipt):
            return {'evento_id':data['evento_id'],'status':'vinculado'},200
        abort(409)
    except (TypeError,KeyError,ValueError):
        db.session.rollback()
        abort(422)