from __future__ import annotations

import hmac
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, inspect, text

from src.extensions import require_role
from src.models import (
    AssinaturaEmpresa,
    CatalogoPlanoComercial,
    CobrancaRecorrente,
    Empresa,
    Entidade,
    EventoCobranca,
    HistoricoMudancaPlano,
    Lancamento,
    NotificacaoComercial,
    User,
    db,
)
from src.services.planos import PLAN_CHOICES, get_plan_label, normalize_plan, plan_rank


admin_comercial_bp = Blueprint('admin_comercial', __name__, url_prefix='/backoffice/comercial')


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().lower() for item in value.split(',') if item.strip()]


def _has_backoffice_identity_permission() -> bool:
    allowed_emails = _split_csv(current_app.config.get('BACKOFFICE_ALLOWED_EMAILS'))
    allowed_usernames = _split_csv(current_app.config.get('BACKOFFICE_ALLOWED_USERNAMES'))

    current_email = (getattr(current_user, 'email', '') or '').strip().lower()
    current_username = (getattr(current_user, 'username', '') or '').strip().lower()

    if not allowed_emails and not allowed_usernames:
        return False
    if allowed_emails and current_email in allowed_emails:
        return True
    if allowed_usernames and current_username in allowed_usernames:
        return True
    return False


def _requires_access_key() -> bool:
    return bool((current_app.config.get('BACKOFFICE_ACCESS_KEY') or '').strip())


def _require_backoffice_access():
    if not _has_backoffice_identity_permission():
        abort(403)

    if _requires_access_key() and not session.get('backoffice_authorized'):
        return redirect(url_for('admin_comercial.acesso'))
    return None


@admin_comercial_bp.route('/acesso', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def acesso():
    if not _has_backoffice_identity_permission():
        abort(403)

    if request.method == 'POST':
        provided = (request.form.get('access_key') or '').strip()
        expected = (current_app.config.get('BACKOFFICE_ACCESS_KEY') or '').strip()

        if not expected:
            session['backoffice_authorized'] = True
            flash('Backoffice liberado para seu usuário.', 'success')
            return redirect(url_for('admin_comercial.index'))

        if hmac.compare_digest(provided, expected):
            session['backoffice_authorized'] = True
            flash('Acesso ao backoffice concedido.', 'success')
            return redirect(url_for('admin_comercial.index'))

        flash('Chave de acesso inválida.', 'danger')

    return render_template('admin/backoffice_access.html')


def _to_brl(value: Decimal | float | int | None) -> str:
    num = Decimal(str(value or 0)).quantize(Decimal('0.01'))
    txt = f'{num:,.2f}'
    return txt.replace(',', 'X').replace('.', ',').replace('X', '.')


@admin_comercial_bp.route('/', methods=['GET'])
@login_required
@require_role('admin')
def index():
    gate = _require_backoffice_access()
    if gate:
        return gate

    assinaturas = AssinaturaEmpresa.query.all()
    empresa_ids = [a.empresa_id for a in assinaturas]

    users_count = dict(
        db.session.query(User.empresa_id, func.count(User.id))
        .group_by(User.empresa_id)
        .all()
    )
    users_active_count = dict(
        db.session.query(User.empresa_id, func.count(User.id))
        .filter(User.is_active.is_(True))
        .group_by(User.empresa_id)
        .all()
    )
    entidades_count = dict(
        db.session.query(Entidade.empresa_id, func.count(Entidade.id))
        .group_by(Entidade.empresa_id)
        .all()
    )
    lancamentos_count = dict(
        db.session.query(Lancamento.empresa_id, func.count(Lancamento.id))
        .group_by(Lancamento.empresa_id)
        .all()
    )
    pending_charge_rows = (
        db.session.query(CobrancaRecorrente.empresa_id, func.count(CobrancaRecorrente.id), func.coalesce(func.sum(CobrancaRecorrente.valor_previsto), 0))
        .filter(CobrancaRecorrente.status.in_(['vencido', 'falhou']))
        .group_by(CobrancaRecorrente.empresa_id)
        .all()
    )
    pending_charge_map = {row[0]: {'qtd': int(row[1] or 0), 'valor': Decimal(str(row[2] or 0))} for row in pending_charge_rows}

    empresas_map = {e.id: e for e in Empresa.query.all()}
    rows = []
    for assinatura in assinaturas:
        empresa = empresas_map.get(assinatura.empresa_id)
        if not empresa:
            continue

        data_volume = int(entidades_count.get(empresa.id, 0) or 0) + int(lancamentos_count.get(empresa.id, 0) or 0)
        atraso_info = pending_charge_map.get(empresa.id, {'qtd': 0, 'valor': Decimal('0.00')})
        rows.append({
            'empresa_id': empresa.id,
            'empresa_nome': empresa.nome,
            'plano': get_plan_label(assinatura.plano_codigo),
            'plano_codigo': normalize_plan(assinatura.plano_codigo),
            'proximo_plano_codigo': normalize_plan(assinatura.proximo_plano_codigo) if assinatura.proximo_plano_codigo else None,
            'status': assinatura.status,
            'vigencia': assinatura.data_vencimento,
            'mudanca_plano_efetivar_em': assinatura.mudanca_plano_efetivar_em,
            'gateway_customer_id': assinatura.gateway_customer_id,
            'gateway_subscription_id': assinatura.gateway_subscription_id,
            'users_total': int(users_count.get(empresa.id, 0) or 0),
            'users_ativos': int(users_active_count.get(empresa.id, 0) or 0),
            'volume_dados': data_volume,
            'atraso_qtd': atraso_info['qtd'],
            'atraso_valor': atraso_info['valor'],
        })

    rows.sort(key=lambda item: item['empresa_nome'].lower())

    new_since = datetime.utcnow() - timedelta(days=7)
    novas_assinaturas = (
        AssinaturaEmpresa.query
        .filter(AssinaturaEmpresa.criado_em >= new_since)
        .order_by(AssinaturaEmpresa.criado_em.desc())
        .all()
    )

    erro_eventos = (
        EventoCobranca.query
        .filter_by(status_processamento='erro')
        .order_by(EventoCobranca.recebido_em.desc())
        .limit(30)
        .all()
    )

    resumo = {
        'clientes_ativos': sum(1 for r in rows if r['status'] in {'ativa', 'trial'}),
        'clientes_suspensos': sum(1 for r in rows if r['status'] == 'suspensa'),
        'clientes_cancelados': sum(1 for r in rows if r['status'] == 'cancelada'),
        'inadimplentes': sum(1 for r in rows if r['atraso_qtd'] > 0),
        'valor_em_atraso': sum((r['atraso_valor'] for r in rows), Decimal('0.00')),
    }

    ofertas = (
        CatalogoPlanoComercial.query
        .filter_by(ativo=True)
        .order_by(CatalogoPlanoComercial.codigo_plano.asc(), CatalogoPlanoComercial.periodicidade.asc(), CatalogoPlanoComercial.versao_oferta.desc())
        .all()
    )

    return render_template(
        'admin/comercial_panel.html',
        rows=rows,
        resumo=resumo,
        novas_assinaturas=novas_assinaturas,
        erro_eventos=erro_eventos,
        ofertas=ofertas,
        planos_disponiveis=PLAN_CHOICES,
        to_brl=_to_brl,
    )


@admin_comercial_bp.route('/assinatura/<int:empresa_id>/status', methods=['POST'])
@login_required
@require_role('admin')
def atualizar_status_assinatura(empresa_id: int):
    gate = _require_backoffice_access()
    if gate:
        return gate

    assinatura = AssinaturaEmpresa.query.filter_by(empresa_id=empresa_id).first()
    if not assinatura:
        flash('Assinatura da empresa não encontrada.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    acao = (request.form.get('acao') or '').strip().lower()
    if acao == 'ativar':
        assinatura.status = 'ativa'
        assinatura.bloqueio_nivel = 'nenhum'
        assinatura.bloqueado_desde = None
        assinatura.motivo_status = 'Status alterado manualmente para ativa.'
    elif acao == 'suspender':
        assinatura.status = 'suspensa'
        assinatura.bloqueio_nivel = 'total'
        assinatura.bloqueado_desde = assinatura.bloqueado_desde or datetime.utcnow()
        assinatura.motivo_status = 'Status alterado manualmente para suspensa.'
    elif acao == 'cancelar':
        assinatura.status = 'cancelada'
        assinatura.bloqueio_nivel = 'total'
        assinatura.bloqueado_desde = assinatura.bloqueado_desde or datetime.utcnow()
        assinatura.motivo_status = 'Status alterado manualmente para cancelada.'
    elif acao == 'reativar':
        assinatura.status = 'ativa'
        assinatura.bloqueio_nivel = 'nenhum'
        assinatura.bloqueado_desde = None
        assinatura.motivo_status = 'Reativada manualmente após regularização.'
    else:
        flash('Ação de status inválida.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    db.session.commit()
    flash('Status da assinatura atualizado com sucesso.', 'success')
    return redirect(url_for('admin_comercial.index'))


@admin_comercial_bp.route('/assinatura/<int:empresa_id>/plano', methods=['POST'])
@login_required
@require_role('admin')
def atualizar_plano_assinatura(empresa_id: int):
    gate = _require_backoffice_access()
    if gate:
        return gate

    assinatura = AssinaturaEmpresa.query.filter_by(empresa_id=empresa_id).first()
    if not assinatura:
        flash('Assinatura da empresa não encontrada.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    novo_plano = normalize_plan(request.form.get('novo_plano'))
    planos_validos = {codigo for codigo, _ in PLAN_CHOICES}
    if novo_plano not in planos_validos:
        flash('Plano informado inválido.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    plano_atual = normalize_plan(assinatura.plano_codigo)
    if novo_plano == plano_atual:
        flash('O plano selecionado já é o plano vigente.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    rank_atual = plan_rank(plano_atual)
    rank_novo = plan_rank(novo_plano)
    tipo_mudanca = 'lateral'
    if rank_novo > rank_atual:
        tipo_mudanca = 'upgrade'
    elif rank_novo < rank_atual:
        tipo_mudanca = 'downgrade'

    efetivado_em = datetime.utcnow()

    assinatura.plano_codigo = novo_plano
    assinatura.proximo_plano_codigo = None
    assinatura.mudanca_plano_solicitada_em = efetivado_em
    assinatura.mudanca_plano_efetivar_em = efetivado_em
    assinatura.motivo_status = f'Mudança de plano efetivada imediatamente no backoffice em {efetivado_em.strftime("%d/%m/%Y %H:%M")}.'

    historico = HistoricoMudancaPlano(
        empresa_id=assinatura.empresa_id,
        assinatura_id=assinatura.id,
        plano_origem=plano_atual,
        plano_destino=novo_plano,
        tipo_mudanca=tipo_mudanca,
        regra_efetivacao='imediata_backoffice',
        solicitado_por_user_id=current_user.id,
        executado_por_user_id=current_user.id,
        efetivado_em=efetivado_em,
        observacoes=f'Mudança registrada e efetivada imediatamente pelo backoffice em {efetivado_em.strftime("%d/%m/%Y %H:%M")}.' ,
    )
    db.session.add(historico)
    db.session.commit()

    flash(f'{tipo_mudanca.capitalize()} de plano efetivado com sucesso.', 'success')
    return redirect(url_for('admin_comercial.index'))


@admin_comercial_bp.route('/catalogo/preco', methods=['POST'])
@login_required
@require_role('admin')
def atualizar_preco_catalogo():
    gate = _require_backoffice_access()
    if gate:
        return gate

    oferta_id = request.form.get('oferta_id', type=int)
    novo_preco_raw = (request.form.get('novo_preco') or '').strip().replace('.', '').replace(',', '.')
    try:
        novo_preco = Decimal(novo_preco_raw)
    except Exception:
        flash('Preço inválido.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    if novo_preco <= 0:
        flash('Preço deve ser maior que zero.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    oferta = CatalogoPlanoComercial.query.filter_by(id=oferta_id, ativo=True).first()
    if not oferta:
        flash('Oferta não encontrada.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    oferta.preco = novo_preco
    db.session.commit()
    flash('Preço da oferta atualizado com sucesso.', 'success')
    return redirect(url_for('admin_comercial.index'))


@admin_comercial_bp.route('/empresa/<int:empresa_id>/delete', methods=['POST'])
@login_required
@require_role('admin')
def excluir_empresa(empresa_id: int):
    gate = _require_backoffice_access()
    if gate:
        return gate

    confirm = (request.form.get('confirmacao') or '').strip().upper()
    if confirm != 'EXCLUIR':
        flash('Confirmação inválida para exclusão. Digite EXCLUIR.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    if getattr(current_user, 'empresa_id', None) == empresa_id:
        flash('Não é permitido excluir a própria empresa logada.', 'danger')
        return redirect(url_for('admin_comercial.index'))

    empresa = Empresa.query.filter_by(id=empresa_id).first()
    if not empresa:
        flash('Empresa não encontrada.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    try:
        inspector = inspect(db.engine)
        tables = []
        for table in inspector.get_table_names():
            columns = {col['name'] for col in inspector.get_columns(table)}
            if 'empresa_id' in columns:
                tables.append(table)

        conn = db.session.connection()
        if db.engine.dialect.name == 'mysql':
            conn.execute(text('SET FOREIGN_KEY_CHECKS=0'))

        for table in tables:
            conn.execute(text(f'DELETE FROM {table} WHERE empresa_id = :empresa_id'), {'empresa_id': empresa_id})

        conn.execute(text('DELETE FROM empresas WHERE id = :empresa_id'), {'empresa_id': empresa_id})

        if db.engine.dialect.name == 'mysql':
            conn.execute(text('SET FOREIGN_KEY_CHECKS=1'))

        db.session.commit()
        flash('Empresa e dados relacionados removidos com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao excluir empresa: {exc}', 'danger')

    return redirect(url_for('admin_comercial.index'))
