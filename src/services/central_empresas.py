"""Descoberta de empresas legadas, sem acesso direto do Central ao MySQL."""
import hashlib
import json
from datetime import timedelta
from src.models import db, Empresa, User, AssinaturaEmpresa, CatalogoPlanoComercial
from src.models.central_integracao import CentralVinculo
from sqlalchemy import or_, exists
from sqlalchemy.orm import joinedload


def legacy_event(company_id):
    return 'cad_' + hashlib.sha256(f'comercial:empresa:{company_id}'.encode()).hexdigest()[:32]


def fingerprint(item):
    return hashlib.sha256(json.dumps(item, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def catalog(cursor=0):
    """Ofertas ativas ou contratadas; sem alterar catálogo nem inventar preços."""
    referenced = exists().where(AssinaturaEmpresa.catalogo_plano_id == CatalogoPlanoComercial.id)
    offers = list(db.session.scalars(db.select(CatalogoPlanoComercial).where(
        CatalogoPlanoComercial.id > cursor, or_(CatalogoPlanoComercial.ativo.is_(True), referenced))
        .order_by(CatalogoPlanoComercial.id).limit(51)))
    ids = [offer.id for offer in offers[:50]]
    used = set(db.session.scalars(db.select(AssinaturaEmpresa.catalogo_plano_id).where(
        AssinaturaEmpresa.catalogo_plano_id.in_(ids)))) if ids else set()
    return [{
        'id': offer.id, 'categoria': offer.codigo_plano, 'nome': offer.nome_exibicao,
        'periodicidade': offer.periodicidade, 'versao': offer.versao_oferta,
        'preco': str(offer.preco), 'moeda': offer.moeda, 'usuarios': offer.limite_usuarios,
        'ativo': bool(offer.ativo), 'contratado': offer.id in used,
        'vigencia_inicio': offer.vigencia_inicio.isoformat() if offer.vigencia_inicio else None,
        'vigencia_fim': offer.vigencia_fim.isoformat() if offer.vigencia_fim else None,
    } for offer in offers[:50]], offers[49].id if len(offers) > 50 else None


def legacy_terms(company, subscription):
    if not subscription:
        return None
    bonus_end = None
    if subscription.bonus_liberado and subscription.bonus_dias and subscription.bonus_concedido_em:
        bonus_end = (subscription.bonus_concedido_em + timedelta(days=subscription.bonus_dias)).date()
    offer = subscription.catalogo_plano
    return {
        'id': subscription.id, 'status': subscription.status,
        'plano': subscription.plano_codigo, 'periodicidade': subscription.ciclo_cobranca,
        'preco': str(offer.preco) if offer else None,
        'data_inicio': subscription.data_inicio.isoformat(),
        'data_vencimento': subscription.data_vencimento.isoformat(),
        'trial_ate': subscription.data_fim_trial.isoformat() if subscription.data_fim_trial else None,
        'bonificada': bool(subscription.bonus_liberado),
        'bonificacao_ate': bonus_end.isoformat() if bonus_end else None,
        'usuarios': company.usuarios_maximos,
        'recorrencia_externa': bool(subscription.gateway_subscription_id),
        'mudanca_plano_pendente': bool(subscription.proximo_plano_codigo),
        'carencia_dias': subscription.carencia_dias,
        'bloqueio_nivel': subscription.bloqueio_nivel,
    }


def company_data(company, subscription=None, link=None, owner=None):
    return {
        'dados': {'evento_id': legacy_event(company.id), 'empresa_id': company.id,
                  'razao_social': company.nome, 'nome_fantasia': company.nome_fantasia,
                  'cnpj_cpf': ''.join(c for c in (company.cnpj or '') if c.isdigit()),
                  'email': company.email or (owner.email if owner else None),
                  'telefone': company.telefone,
                  'responsavel': (owner.full_name or owner.username) if owner else company.nome},
        'ativo': not subscription or subscription.status != 'excluida',
        'cliente_id': link.cliente_id if link else None,
        'assinatura': legacy_terms(company, subscription),
    }


def companies(cursor=0, identifier=None):
    query = db.select(Empresa).order_by(Empresa.id)
    query = query.where(Empresa.id == identifier) if identifier else query.where(Empresa.id > cursor).limit(51)
    rows = list(db.session.scalars(query))
    ids = [row.id for row in rows]
    if not ids:
        return [], None
    subscriptions = {row.empresa_id: row for row in db.session.scalars(
        db.select(AssinaturaEmpresa).options(joinedload(AssinaturaEmpresa.catalogo_plano))
        .where(AssinaturaEmpresa.empresa_id.in_(ids)))}
    links = {row.empresa_id: row for row in db.session.scalars(
        db.select(CentralVinculo).where(CentralVinculo.empresa_id.in_(ids)))}
    owners = {}
    for user in db.session.scalars(db.select(User).where(User.empresa_id.in_(ids), User.is_active.is_(True))
                                  .order_by(User.is_admin.desc(), User.id)):
        owners.setdefault(user.empresa_id, user)
    return [company_data(row, subscriptions.get(row.id), links.get(row.id), owners.get(row.id))
            for row in rows[:50]], rows[49].id if len(rows) > 50 else None


def matches_legacy_state(terms, state):
    """O callback não pode converter suspensão em acesso nem trocar plano/bonificação."""
    from datetime import date
    expected = {'ativa':'ATIVA', 'trial':'TRIAL', 'suspensa':'SUSPENSA', 'cancelada':'CANCELADA',
                'expirada':'EXPIRADA', 'bloqueada':'BLOQUEADA'}.get(terms['status'])
    if terms['bonificada']:
        if terms['bonificacao_ate'] and date.fromisoformat(terms['bonificacao_ate']) < date.today():
            return False
        expected = 'ATIVA'
    elif expected == 'TRIAL':
        if not terms['trial_ate']:
            return False
        if date.fromisoformat(terms['trial_ate']) <= date.today():
            expected = 'EXPIRADA'
    if (not expected or state['status'] != expected
            or str(state.get('plano', '')).lower().removesuffix('_anual') != terms['plano']
            or state.get('bonificada') is not terms['bonificada']
            or state.get('bonificacao_ate') != terms['bonificacao_ate']
            or terms['recorrencia_externa'] or terms['mudanca_plano_pendente']
            or (not terms['bonificada'] and terms['bloqueio_nivel'] not in ('nenhum', 'total'))):
        return False
    if expected not in ('ATIVA','TRIAL') and state['acesso_produto']:
        return False
    if state['acesso_produto'] and state['limites'].get('usuarios') != terms['usuarios']:
        return False
    return True