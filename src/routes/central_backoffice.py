from datetime import datetime, timedelta
import requests
from cryptography.fernet import InvalidToken
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required
from src.extensions import csrf, require_role
from src.models import db, Empresa, User, AssinaturaEmpresa, CobrancaRecorrente
from src.models.central_integracao import CentralConfiguracao, CentralVinculo, CentralCadastroPendente
from src.services.central_assinaturas import config, cipher, validate_url, validate, store

central_admin = Blueprint('central_admin',__name__,url_prefix='/backoffice/comercial/central')


def gate():
    from src.routes.admin_comercial import _require_backoffice_access
    return _require_backoffice_access()


def fetch_link_state(customer):
    cfg=config()
    if not cfg:
        raise ValueError('Configure a conexão com o Central antes de vincular.')
    try:
        with requests.Session() as http:
            http.trust_env=False
            response=http.get(validate_url(cfg.base_url)+f'/api/v1/entitlements/{customer}/COMERCIAL',
                headers={'Authorization':'Bearer '+cipher().decrypt(cfg.token.encode()).decode()},
                timeout=(3,5),allow_redirects=False)
        if response.status_code==404:
            raise ValueError(f'O Central não encontrou assinatura COMERCIAL para o cliente ID {customer}. '
                'No Central, cadastre um plano do Comercial e crie a assinatura desse cliente antes de testar ou vincular.')
        if response.status_code in (401,403):
            raise ValueError('Credencial não autorizada para o Comercial. Confira o token e o produto no Central.')
        if response.status_code!=200:
            raise ValueError('O Central não confirmou a consulta. Confira o serviço e tente novamente.')
        data=response.json()
        until=validate(data,customer)
        from src.models.central_integracao import utcnow
        if until<=utcnow():
            raise ValueError('Autorização retornada pelo Central está expirada. Confira data e hora dos servidores.')
        return data
    except requests.RequestException:
        raise ValueError('Não foi possível conectar ao Central. Confira o endereço e se o serviço está iniciado.') from None
    except InvalidToken:
        raise ValueError('Credencial local não pôde ser lida. Confira a chave de proteção da configuração.') from None


@central_admin.route('/',methods=['GET','POST'])
@login_required
@require_role('admin')
def setup():
    denied=gate()
    if denied:
        return denied
    cfg=config()
    if request.method=='POST':
        from flask import current_app
        if current_app.config.get('CENTRAL_USE_ENV'):
            flash('Configuração definida pelo .env. Altere as variáveis de ambiente e reinicie o serviço.','warning')
            return redirect(url_for('central_admin.setup'))
        if not cfg:
            cfg=CentralConfiguracao(id=1)
            db.session.add(cfg)
        cfg.base_url=validate_url(request.form.get('base_url',''))
        token=request.form.get('token','').strip()
        secret=request.form.get('secret','').strip()
        if token:
            if len(token)>2000:
                abort(422)
            cfg.token=cipher().encrypt(token.encode()).decode()
        if secret:
            if not 32 <= len(secret) <= 200:
                abort(422)
            cfg.hmac_secret=cipher().encrypt(secret.encode()).decode()
        if not cfg.token or not cfg.hmac_secret:
            abort(422)
        cfg.cache_ttl=int(request.form.get('ttl','900'))
        if not 1<=cfg.cache_ttl<=900:
            abort(422)
        activate='ativo' in request.form
        if activate:
            missing = db.session.scalar(db.select(AssinaturaEmpresa.empresa_id).where(
                AssinaturaEmpresa.bonus_liberado.is_(False),
                ~db.exists(db.select(CentralVinculo.empresa_id).where(CentralVinculo.empresa_id == AssinaturaEmpresa.empresa_id))))
            if missing:
                db.session.rollback()
                flash('Há empresas com assinatura legada sem vínculo. Complete todos os vínculos antes da virada.','warning')
                return redirect(url_for('central_admin.setup'))
        if activate and request.form.get('confirmacao')!='CENTRAL':
            flash('Confirme a ativação após conferir os vínculos. Bonificações existentes serão preservadas.','warning')
            db.session.rollback()
            return redirect(url_for('central_admin.setup'))
        cfg.ativo=activate
        cfg.purga_habilitada = 'purga_habilitada' in request.form and request.form.get('confirmacao_purga') == 'PURGA HOMOLOGADA'
        db.session.commit()
        flash('Configuração salva. Bonificações existentes preservadas.','success')
        return redirect(url_for('central_admin.setup'))
    return render_template('admin/central_setup.html',cfg=cfg,
        companies=Empresa.query.order_by(Empresa.nome).all(),links=CentralVinculo.query.all(),
        pending=CentralCadastroPendente.query.order_by(CentralCadastroPendente.id.desc()).limit(100).all())


@central_admin.post('/cadastros/<int:company_id>/reenviar')
@login_required
@require_role('admin')
def resend_registration(company_id):
    denied=gate()
    if denied:
        return denied
    from src.models.central_integracao import CentralCadastroPendente, utcnow
    from src.services.central_autocadastro import notify_after_commit
    row=db.session.scalar(db.select(CentralCadastroPendente).filter_by(empresa_id=company_id))
    if not row or row.status=='VINCULADO':
        abort(422)
    row.status,row.proxima_tentativa='PENDENTE_ENVIO',utcnow()
    db.session.commit()
    notify_after_commit(company_id)
    flash('Reenvio solicitado. O cadastro continua aguardando habilitação no Central.','success')
    return redirect(url_for('central_admin.setup'))


@central_admin.post('/vincular')
@login_required
@require_role('admin')
def bind():
    denied=gate()
    if denied:
        return denied
    company_id=request.form.get('empresa_id',type=int)
    customer=request.form.get('cliente_id',type=int)
    if not company_id or not customer or customer<1:
        flash('Selecione a empresa e informe o ID numérico do cliente no Central. O código CLI_ não é esse ID.','warning')
        return redirect(url_for('central_admin.setup'))
    company=db.session.get(Empresa,company_id)
    if not company:
        flash('Empresa não encontrada no Comercial. Atualize a página.','warning')
        return redirect(url_for('central_admin.setup'))
    existing=db.session.get(CentralVinculo,company.id)
    if existing:
        flash((f'Esta empresa já está vinculada ao cliente ID {existing.cliente_id} no Central. '
               'Use Testar conexão para conferir a assinatura; não é necessário vincular novamente.')
              if existing.cliente_id==customer else
              f'Esta empresa já está vinculada ao cliente ID {existing.cliente_id}. O vínculo existente não foi substituído.',
              'info' if existing.cliente_id==customer else 'warning')
        return redirect(url_for('central_admin.setup'))
    other=db.session.scalar(db.select(CentralVinculo).filter_by(cliente_id=customer))
    if other:
        flash('Este cliente do Central já está vinculado a outra empresa do Comercial. Confira os IDs.','warning')
        return redirect(url_for('central_admin.setup'))
    try:
        data=fetch_link_state(customer)
    except (ValueError,KeyError,TypeError) as error:
        message=str(error) if type(error) is ValueError else 'Resposta do Central inválida. Confira a configuração.'
        flash(message,'warning')
        return redirect(url_for('central_admin.setup'))
    legacy = db.session.scalar(db.select(AssinaturaEmpresa).filter_by(empresa_id=company.id))
    if legacy and legacy.bonus_liberado:
        end=(legacy.bonus_concedido_em+timedelta(days=legacy.bonus_dias)).date() if legacy.bonus_dias and legacy.bonus_concedido_em else None
        if not data.get('bonificada') or data.get('bonificacao_ate') != (end.isoformat() if end else None):
            flash('Esta empresa está bonificada. Cadastre a mesma bonificação no Central antes de vinculá-la.','warning')
            return redirect(url_for('central_admin.setup'))
    link=CentralVinculo(empresa_id=company.id,cliente_id=customer,assinatura_id=0,versao=0)
    db.session.add(link)
    try:
        store(link,data,config().cache_ttl)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('O vínculo já foi registrado por outra operação. Atualize a página para conferir.','warning')
        return redirect(url_for('central_admin.setup'))
    flash('Empresa vinculada com sucesso. Estado da assinatura: '+data['status']+'.','success')
    return redirect(url_for('central_admin.setup'))


@central_admin.post('/testar/<int:company_id>')
@login_required
@require_role('admin')
def test(company_id):
    denied=gate()
    if denied:
        return denied
    link=db.session.get(CentralVinculo,company_id)
    if not link:
        flash('Empresa ainda não vinculada. Informe o cliente do Central e clique em Vincular.','warning')
        return redirect(url_for('central_admin.setup'))
    try:
        # Testar força consulta real, sem aceitar um cache antigo como teste de conexão.
        data=fetch_link_state(link.cliente_id)
        flash('Conexão confirmada. Assinatura COMERCIAL: '+data['status']+
              (' · acesso liberado.' if data['acesso_produto'] else ' · acesso bloqueado pelo estado da assinatura.'),'success')
    except (ValueError,KeyError,TypeError) as error:
        flash(str(error) if type(error) is ValueError else 'Resposta do Central inválida. Confira a configuração.','warning')
    return redirect(url_for('central_admin.setup'))
