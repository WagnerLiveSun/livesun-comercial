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
from src.services.planos import (
    ALL_MODULE_LABELS,
    PLAN_CHOICES,
    get_plan_label,
    modules_for_plan,
    normalize_plan,
    plan_rank,
    sync_empresa_modules,
)

# Dias de retenção dos dados após a exclusão da empresa antes da purga definitiva.
RETENCAO_EXCLUSAO_DIAS = 60


def _safe_all(query, padrao=None, rotulo='consulta'):
    try:
        return query.all()
    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        current_app.logger.warning(f'Falha em {rotulo}: {exc}')
        return [] if padrao is None else padrao


admin_comercial_bp = Blueprint('admin_comercial', __name__, url_prefix='/backoffice/comercial')


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().lower() for item in value.split(',') if item.strip()]


def _has_backoffice_identity_permission() -> bool:
    # Admins da LiveSun (sem empresa vinculada) têm acesso automático ao backoffice
    if getattr(current_user, 'empresa_id', None) is None and getattr(current_user, 'role', '') == 'admin':
        return True

    # Verifica se é admin antes de checar permissões de backoffice
    if getattr(current_user, 'role', '') != 'admin':
        return False

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


def _registrar_evento(empresa_id: int, categoria: str, tipo: str, descricao: str,
                      detalhes: dict | None = None, origem_tabela: str | None = None,
                      origem_id: int | None = None) -> None:
    """Função desativada - EventoSistema removido."""
    pass


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


def _dias_restantes_exclusao(data_exclusao) -> int:
    """Dias restantes até a purga definitiva dos dados (60 dias a partir da exclusão)."""
    if not data_exclusao:
        return 0
    limite = data_exclusao + timedelta(days=RETENCAO_EXCLUSAO_DIAS)
    restantes = (limite - datetime.utcnow()).days
    return max(restantes, 0)


def _hard_delete_empresa(empresa_id: int) -> None:
    """Remove definitivamente (hard delete) todos os registros vinculados à empresa.

    Apaga toda tabela que possua coluna ``empresa_id`` e, por fim, o registro da
    própria empresa (inclusive a assinatura, que também possui ``empresa_id``).
    Reaproveitado tanto pela purga automática (retenção de 60 dias) quanto pela
    purga manual disparada no console de gestão comercial.

    Roda dentro da transação da sessão atual (``db.session``) de propósito: o
    contexto RLS do Postgres (``app.empresa_id`` via ``SET LOCAL``) só vale na
    transação da sessão. Abrir conexão/transação separada aqui quebraria o RLS.
    """
    inspector = inspect(db.engine)
    tables = [
        t for t in inspector.get_table_names()
        if 'empresa_id' in {c['name'] for c in inspector.get_columns(t)}
    ]
    conn = db.session.connection()
    if db.engine.dialect.name == 'mysql':
        conn.execute(text('SET FOREIGN_KEY_CHECKS=0'))
    try:
        for table in tables:
            conn.execute(
                text(f'DELETE FROM {table} WHERE empresa_id = :empresa_id'),
                {'empresa_id': empresa_id},
            )
        conn.execute(text('DELETE FROM empresas WHERE id = :empresa_id'), {'empresa_id': empresa_id})
        if db.engine.dialect.name == 'mysql':
            conn.execute(text('SET FOREIGN_KEY_CHECKS=1'))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def _purge_expired_exclusions():
    """Remove definitivamente (hard delete) dados de empresas excluídas há mais de 60 dias."""
    limite = datetime.utcnow() - timedelta(days=RETENCAO_EXCLUSAO_DIAS)
    expiradas = (
        AssinaturaEmpresa.query
        .filter(AssinaturaEmpresa.status == 'excluida')
        .filter(AssinaturaEmpresa.data_exclusao != None)  # noqa: E711
        .filter(AssinaturaEmpresa.data_exclusao < limite)
        .all()
    )
    for assinatura in expiradas:
        empresa_id = assinatura.empresa_id
        try:
            _hard_delete_empresa(empresa_id)
        except Exception as exc:  # noqa: BLE001
            # O _hard_delete_empresa já faz rollback interno, mas o belt-and-
            # braces aqui garante a sessão limpa antes das queries do painel.
            db.session.rollback()
            current_app.logger.error(f'Erro na purga de empresa {empresa_id}: {exc}')


@admin_comercial_bp.route('/', methods=['GET'])
@login_required
@require_role('admin')
def index():
    gate = _require_backoffice_access()
    if gate:
        return gate

    # Purga definitiva de empresas excluídas há mais de 60 dias (retenção).
    _purge_expired_exclusions()

    assinaturas = AssinaturaEmpresa.query.all()
    assinaturas_map = {a.empresa_id: a for a in assinaturas}

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

    empresas = Empresa.query.all()
    rows = []
    for empresa in empresas:
        assinatura = assinaturas_map.get(empresa.id)

        data_volume = int(entidades_count.get(empresa.id, 0) or 0) + int(lancamentos_count.get(empresa.id, 0) or 0)
        atraso_info = pending_charge_map.get(empresa.id, {'qtd': 0, 'valor': Decimal('0.00')})

        if assinatura:
            rows.append({
                'empresa_id': empresa.id,
                'empresa_nome': empresa.nome,
                'empresa': empresa,
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
                'modulos': {
                    key: bool(getattr(empresa, f'atividade_{key}', False))
                    for key in ALL_MODULE_LABELS
                },
                'data_exclusao': assinatura.data_exclusao,
                'dias_restantes_exclusao': _dias_restantes_exclusao(assinatura.data_exclusao),
                'data_purga_exclusao': (
                    assinatura.data_exclusao + timedelta(days=RETENCAO_EXCLUSAO_DIAS)
                    if assinatura.data_exclusao else None
                ),
                'bonus_liberado': bool(assinatura.bonus_liberado),
                'bonus_motivo': assinatura.bonus_motivo,
                'bonus_concedido_em': assinatura.bonus_concedido_em,
                'bonus_dias': assinatura.bonus_dias,
                'bonus_fim': (
                    assinatura.bonus_concedido_em + timedelta(days=assinatura.bonus_dias)
                    if assinatura.bonus_dias and assinatura.bonus_concedido_em else None
                ),
            })
        else:
            rows.append({
                'empresa_id': empresa.id,
                'empresa_nome': empresa.nome,
                'empresa': empresa,
                'plano': 'Sem assinatura',
                'plano_codigo': None,
                'proximo_plano_codigo': None,
                'status': 'pendente',
                'vigencia': None,
                'mudanca_plano_efetivar_em': None,
                'gateway_customer_id': None,
                'gateway_subscription_id': None,
                'users_total': int(users_count.get(empresa.id, 0) or 0),
                'users_ativos': int(users_active_count.get(empresa.id, 0) or 0),
                'volume_dados': data_volume,
                'atraso_qtd': atraso_info['qtd'],
                'atraso_valor': atraso_info['valor'],
                'modulos': {
                    key: bool(getattr(empresa, f'atividade_{key}', False))
                    for key in ALL_MODULE_LABELS
                },
                'data_exclusao': None,
                'dias_restantes_exclusao': None,
                'data_purga_exclusao': None,
                'bonus_liberado': False,
                'bonus_motivo': None,
                'bonus_concedido_em': None,
                'bonus_dias': None,
                'bonus_fim': None,
            })

    rows.sort(key=lambda item: item['empresa_nome'].lower())

    new_since = datetime.utcnow() - timedelta(days=7)
    novas_assinaturas = (
        AssinaturaEmpresa.query
        .filter(AssinaturaEmpresa.criado_em >= new_since)
        .order_by(AssinaturaEmpresa.criado_em.desc())
        .all()
    )

    filtros = {'categoria': '', 'tipo': ''}
    eventos = []

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
        filtros=filtros,
        ofertas=ofertas,
        planos_disponiveis=PLAN_CHOICES,
        module_labels=ALL_MODULE_LABELS,
        retencao_dias=RETENCAO_EXCLUSAO_DIAS,
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
    nova_assinatura = False
    if not assinatura:
        # Criar assinatura padrão para empresa sem assinatura
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            flash('Empresa não encontrada.', 'danger')
            return redirect(url_for('admin_comercial.index'))

        assinatura = AssinaturaEmpresa(
            empresa_id=empresa_id,
            plano_codigo='basic',
            status='pendente',
            data_inicio=datetime.utcnow().date(),
            data_vencimento=datetime.utcnow() + timedelta(days=30),
            gateway_customer_id=None,
            gateway_subscription_id=None,
        )
        db.session.add(assinatura)
        db.session.flush()
        nova_assinatura = True

    acao = (request.form.get('acao') or '').strip().lower()

    # Se é uma nova assinatura criada agora, apenas salvar e não executar mudança de status
    if nova_assinatura:
        db.session.commit()
        flash(f'Assinatura criada para empresa "{empresa.nome}". Configure o plano posteriormente.', 'success')
        return redirect(url_for('admin_comercial.index'))

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

    categoria = 'sucesso'
    tipo = 'ATUALIZACAO_USUARIO'
    if acao == 'cancelar':
        tipo = 'EXCLUIR'
    elif acao == 'suspender':
        categoria = 'alerta'
    _registrar_evento(
        empresa_id,
        categoria,
        tipo,
        f'Ação "{acao}" registrada no backoffice comercial.',
    )

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
        # Criar assinatura padrão para empresa sem assinatura
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            flash('Empresa não encontrada.', 'danger')
            return redirect(url_for('admin_comercial.index'))

        novo_plano = normalize_plan(request.form.get('novo_plano'))
        assinatura = AssinaturaEmpresa(
            empresa_id=empresa_id,
            plano_codigo=novo_plano,
            status='ativa',
            data_inicio=datetime.utcnow().date(),
            data_vencimento=datetime.utcnow() + timedelta(days=30),
            gateway_customer_id=None,
            gateway_subscription_id=None,
        )
        db.session.add(assinatura)
        db.session.commit()

        # Sincroniza os módulos liberados conforme a assinatura/plano escolhido.
        empresa.plano = novo_plano
        sync_empresa_modules(empresa, novo_plano)

        flash(f'Assinatura criada para empresa "{empresa.nome}" com plano {novo_plano}.', 'success')
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

    # Sincroniza os módulos liberados conforme a assinatura/plano escolhido.
    empresa = Empresa.query.get(empresa_id)
    if empresa is not None:
        empresa.plano = novo_plano
        sync_empresa_modules(empresa, novo_plano)

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

    _registrar_evento(
        empresa_id,
        'sucesso',
        'MUDANCA_PLANO',
        f'Plano alterado de {plano_atual} para {novo_plano} (efetivado no backoffice).',
    )

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

    _registrar_evento(
        None,
        'sucesso',
        'ATUALIZACAO_USUARIO',
        'Preço do catálogo comercial atualizado no backoffice.',
    )

    flash('Preço da oferta atualizado com sucesso.', 'success')
    return redirect(url_for('admin_comercial.index'))


@admin_comercial_bp.route('/empresa/<int:empresa_id>/modulos', methods=['POST'])
@login_required
@require_role('admin')
def atualizar_modulos(empresa_id: int):
    gate = _require_backoffice_access()
    if gate:
        return gate

    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        flash('Empresa não encontrada.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    # Estes switches passam a ser controlados pelo backoffice comercial,
    # liberando o acesso da empresa conforme a assinatura escolhida.
    for module_key in ALL_MODULE_LABELS:
        checkbox_name = f'modulo_{module_key}'
        attr_name = f'atividade_{module_key}'
        if hasattr(empresa, attr_name):
            setattr(empresa, attr_name, checkbox_name in request.form)

    db.session.commit()

    _registrar_evento(
        empresa_id,
        'sucesso',
        'ATUALIZACAO_USUARIO',
        f'Módulos/atividades da empresa "{empresa.nome}" atualizados no backoffice.',
    )

    flash(f'Módulos da empresa "{empresa.nome}" atualizados com sucesso.', 'success')
    return redirect(url_for('admin_comercial.index'))


@admin_comercial_bp.route('/assinatura/<int:empresa_id>/bonus', methods=['POST'])
@login_required
@require_role('admin')
def atualizar_bonus_assinatura(empresa_id: int):
    gate = _require_backoffice_access()
    if gate:
        return gate

    assinatura = AssinaturaEmpresa.query.filter_by(empresa_id=empresa_id).first()
    nova_assinatura = False
    if not assinatura:
        # Criar assinatura padrão para empresa sem assinatura
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            flash('Empresa não encontrada.', 'danger')
            return redirect(url_for('admin_comercial.index'))

        assinatura = AssinaturaEmpresa(
            empresa_id=empresa_id,
            plano_codigo='basic',
            status='ativa',
            data_inicio=datetime.utcnow().date(),
            data_vencimento=datetime.utcnow() + timedelta(days=30),
            gateway_customer_id=None,
            gateway_subscription_id=None,
        )
        db.session.add(assinatura)
        db.session.flush()
        nova_assinatura = True

    acao = (request.form.get('acao') or '').strip().lower()

    # Se é uma nova assinatura criada agora, apenas salvar e não executar ações de bônus
    if nova_assinatura:
        db.session.commit()
        flash(f'Assinatura criada para empresa "{empresa.nome}". Configure o bônus posteriormente.', 'success')
        return redirect(url_for('admin_comercial.index'))

    if acao == 'conceder':
        bonus_tipo = (request.form.get('bonus_tipo') or '').strip()
        bonus_motivo = (request.form.get('bonus_motivo') or '').strip()

        if not bonus_tipo:
            flash('Tipo de bônus não informado.', 'warning')
            return redirect(url_for('admin_comercial.index'))

        assinatura.bonus_liberado = True
        assinatura.bonus_tipo = bonus_tipo
        assinatura.bonus_motivo = bonus_motivo or f'Bônus {bonus_tipo} concedido manualmente via backoffice'
        assinatura.bonus_concedido_em = datetime.utcnow()

        bonus_dias = request.form.get('bonus_dias')
        if bonus_dias:
            try:
                assinatura.bonus_dias = int(bonus_dias)
            except ValueError:
                pass

        db.session.commit()

        _registrar_evento(
            empresa_id,
            'sucesso',
            'ATUALIZACAO_USUARIO',
            'Bônus concedido no backoffice comercial.',
        )

        flash('Bônus concedido com sucesso.', 'success')

    elif acao == 'revogar':
        assinatura.bonus_liberado = False
        assinatura.bonus_tipo = None
        assinatura.bonus_motivo = None
        assinatura.bonus_concedido_em = None
        db.session.commit()

        _registrar_evento(
            empresa_id,
            'sucesso',
            'ATUALIZACAO_USUARIO',
            'Bônus revogado no backoffice comercial.',
        )

        flash('Bônus revogado com sucesso.', 'success')
        
    else:
        flash('Ação de bônus inválida.', 'warning')
        return redirect(url_for('admin_comercial.index'))

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

    assinatura = AssinaturaEmpresa.query.filter_by(empresa_id=empresa_id).first()
    if assinatura:
        # Exclusão lógica: remove o acesso imediatamente e mantém os dados por
        # `RETENCAO_EXCLUSAO_DIAS` (60 dias) a contar de hoje.
        data_exclusao = datetime.utcnow()
        assinatura.status = 'excluida'
        assinatura.bloqueio_nivel = 'total'
        assinatura.bloqueado_desde = data_exclusao
        assinatura.data_exclusao = data_exclusao
        assinatura.motivo_status = (
            f'Empresa excluída em {data_exclusao.strftime("%d/%m/%Y %H:%M")}. '
            f'Dados mantidos por {RETENCAO_EXCLUSAO_DIAS} dias para retenção.'
        )
    else:
        nova = AssinaturaEmpresa(
            empresa_id=empresa_id,
            plano_codigo=normalize_plan(empresa.plano),
            status='excluida',
            bloqueio_nivel='total',
            bloqueado_desde=datetime.utcnow(),
            data_exclusao=datetime.utcnow(),
            data_inicio=datetime.utcnow().date(),
            data_vencimento=datetime.utcnow().date(),
            motivo_status=f'Empresa excluída. Dados mantidos por {RETENCAO_EXCLUSAO_DIAS} dias.',
        )
        db.session.add(nova)

    # Remove imediatamente as contas de acesso (usuários), encerrando a sessão.
    User.query.filter_by(empresa_id=empresa_id).update({'is_active': False})

    db.session.commit()

    _registrar_evento(
        empresa_id,
        'alerta',
        'EXCLUSAO_DEFINITIVA',
        f'Empresa "{empresa.nome}" excluída (exclusão lógica com retenção de {RETENCAO_EXCLUSAO_DIAS} dias).',
    )

    flash(
        f'Empresa "{empresa.nome}" excluída. O acesso foi removido e os dados serão '
        f'mantidos por {RETENCAO_EXCLUSAO_DIAS} dias antes da remoção definitiva.',
        'success',
    )
    return redirect(url_for('admin_comercial.index'))


@admin_comercial_bp.route('/empresa/<int:empresa_id>/purge', methods=['POST'])
@login_required
@require_role('admin')
def purgar_empresa(empresa_id: int):
    """Purga manual (hard delete) dos dados de uma empresa já excluída logicamente.

    Exige que o operador digite ``PURGAR``. Liberada no console de gestão assim que
    a retenção de ``RETENCAO_EXCLUSAO_DIAS`` completa; se disparada antes do prazo,
    é permitida, mas registrada como purga antecipada.
    """
    gate = _require_backoffice_access()
    if gate:
        return gate

    confirm = (request.form.get('confirmacao') or '').strip().upper()
    if confirm != 'PURGAR':
        flash('Confirmação inválida para a purga. Digite PURGAR.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    if getattr(current_user, 'empresa_id', None) == empresa_id:
        flash('Não é permitido purgar os dados da própria empresa logada.', 'danger')
        return redirect(url_for('admin_comercial.index'))

    empresa = Empresa.query.filter_by(id=empresa_id).first()
    if not empresa:
        flash('Empresa não encontrada.', 'warning')
        return redirect(url_for('admin_comercial.index'))

    assinatura = AssinaturaEmpresa.query.filter_by(empresa_id=empresa_id).first()
    if not assinatura or assinatura.status != 'excluida':
        flash(
            'A purga definitiva só está disponível para empresas marcadas como '
            '"excluída" (exclusão lógica já aplicada).',
            'warning',
        )
        return redirect(url_for('admin_comercial.index'))

    nome = empresa.nome
    dias_restantes = _dias_restantes_exclusao(assinatura.data_exclusao)
    antecipada = dias_restantes > 0

    try:
        _hard_delete_empresa(empresa_id)
    except Exception as exc:  # noqa: BLE001
        current_app.logger.error(f'Erro na purga manual da empresa {empresa_id}: {exc}')
        flash('Não foi possível concluir a purga dos dados. Verifique os logs do servidor.', 'danger')
        return redirect(url_for('admin_comercial.index'))

    _registrar_evento(
        empresa_id,
        'sucesso' if not antecipada else 'alerta',
        'EXCLUIR',
        f'Dados da empresa "{nome}" excluídos definitivamente via purga manual '
        f'{"antes" if antecipada else "após"} do prazo de retenção.',
    )

    if antecipada:
        flash(
            f'Dados da empresa "{nome}" excluídos DEFINITIVAMENTE do banco — purga '
            f'ANTECIPADA: faltavam {dias_restantes} dia(s) para completar os '
            f'{RETENCAO_EXCLUSAO_DIAS} dias de retenção.',
            'warning',
        )
    else:
        flash(
            f'Dados da empresa "{nome}" excluídos DEFINITIVAMENTE do banco após o '
            f'período de retenção de {RETENCAO_EXCLUSAO_DIAS} dias.',
            'success',
        )
    return redirect(url_for('admin_comercial.index'))
