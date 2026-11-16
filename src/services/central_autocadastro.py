"""Outbox transacional do autocadastro. Não transmite senhas nem permissões."""
from datetime import timedelta
from uuid import uuid4
import requests
from flask import current_app
from src.models import db
from src.models.central_integracao import CentralCadastroPendente, utcnow
from src.services.central_assinaturas import config, cipher, validate_url, enabled


def enqueue(company, user):
    # Publicar o receptor não ativa o onboarding do Central: mantém o legado
    # até a integração ser explicitamente habilitada pelo operador.
    if not enabled():
        return None
    row = db.session.scalar(db.select(CentralCadastroPendente).filter_by(empresa_id=company.id))
    if row:
        return row
    event = 'cad_' + uuid4().hex
    row = CentralCadastroPendente(empresa_id=company.id, evento_id=event, dados={
        'evento_id':event, 'empresa_id':company.id, 'razao_social':company.nome,
        'nome_fantasia':company.nome_fantasia or None,
        'cnpj_cpf': ''.join(c for c in (company.cnpj or '') if c.isdigit()),
        'email':user.email, 'telefone':company.telefone or None,
        'responsavel':user.full_name})
    db.session.add(row)
    return row


def awaits_approval(company_id):
    if not enabled():
        return False
    from sqlalchemy import inspect
    if not inspect(db.engine).has_table('central_cadastros_pendentes'):
        return False
    row=db.session.scalar(db.select(CentralCadastroPendente).filter_by(empresa_id=company_id))
    return bool(row and row.status!='VINCULADO')


def send_one(company_id=None):
    if not enabled():
        return False
    cfg = config()
    if not cfg or not cfg.token or not cfg.base_url:
        return False
    query = db.select(CentralCadastroPendente).where(
        CentralCadastroPendente.status.in_(['PENDENTE_ENVIO','ENVIANDO']),
        CentralCadastroPendente.proxima_tentativa <= utcnow())
    if company_id is not None:
        query = query.where(CentralCadastroPendente.empresa_id == company_id)
    row = db.session.scalar(query.order_by(CentralCadastroPendente.id).with_for_update(skip_locked=True))
    if not row:
        db.session.rollback()
        return False
    identifier = row.id
    row.tentativas += 1
    row.status, row.proxima_tentativa = 'ENVIANDO', utcnow() + timedelta(minutes=2)
    payload = dict(row.dados)
    base = cfg.base_url
    token = cipher().decrypt(cfg.token.encode()).decode()
    db.session.commit()
    try:
        with requests.Session() as http:
            http.trust_env = False
            response = http.post(validate_url(base)+'/api/v1/cadastros',json=payload,
                headers={'Authorization':'Bearer '+token},timeout=(2,4),allow_redirects=False)
        if response.status_code not in (200,202):
            raise ValueError('Central não confirmou cadastro.')
        data = response.json()
        if (data.get('evento_id') != payload['evento_id'] or data.get('produto') != 'COMERCIAL'
                or data.get('empresa_id') != payload['empresa_id']
                or type(data.get('solicitacao_id')) is not int):
            raise ValueError('Confirmação de cadastro inválida.')
        row = db.session.scalar(db.select(CentralCadastroPendente).where(CentralCadastroPendente.id == identifier)
            .with_for_update().execution_options(populate_existing=True))
        # Callback pode ter concluído vínculo enquanto a resposta de envio estava em trânsito.
        if row.status != 'VINCULADO':
            row.status, row.solicitacao_id, row.erro = 'AGUARDANDO_HABILITACAO', data['solicitacao_id'], None
        db.session.commit()
    except Exception:
        db.session.rollback()
        row = db.session.scalar(db.select(CentralCadastroPendente).where(CentralCadastroPendente.id == identifier)
            .with_for_update().execution_options(populate_existing=True))
        if row and row.status != 'VINCULADO':
            row.status, row.erro = 'PENDENTE_ENVIO', 'CENTRAL_NAO_CONFIRMOU_CADASTRO'
            row.proxima_tentativa = utcnow() + timedelta(seconds=min(3600,10*2**min(row.tentativas,8)))
            db.session.commit()
        current_app.logger.warning('Autocadastro aguardando envio ao Central.')
    return True


def notify_after_commit(company_id):
    try:
        return send_one(company_id)
    except Exception:
        db.session.rollback()
        current_app.logger.warning('Autocadastro preservado na fila local para reenvio.')
        return False