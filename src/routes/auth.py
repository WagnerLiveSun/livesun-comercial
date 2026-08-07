from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal

from src.models import (
    db,
    User,
    Empresa,
    EmpresaFiscalItem,
    Servico,
    NfseServicoNacionalReferencia,
    NfseNbsReferencia,
    NfseCnaeReferencia,
    AssinaturaEmpresa,
    CobrancaRecorrente,
    CatalogoPlanoComercial,
    HistoricoMudancaPlano,
    NotificacaoComercial,
    PasswordResetCode,
)
from src.extensions import limiter, require_role
from src.access_control import (
    PERMISSION_CATALOG,
    build_operator_permissions,
    build_user_overrides_matrix,
    save_operator_permissions,
    save_user_overrides,
)
from src.services.planos import (
    get_plan_label,
    is_basic_plan,
    max_users_for_plan,
    normalize_plan,
    plan_allows_endpoint,
    plan_rank,
    PLAN_CHOICES,
)
from src.services.assinatura import ServicoAssinatura
from src.services.brevo import brevo_service
import random
import string

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _normalize_document(value):
    if not value:
        return ''
    return ''.join(ch for ch in value if ch.isdigit())


def _normalize_cnae(value):
    if not value:
        return ''
    return ''.join(ch for ch in value if ch.isdigit())


FISCAL_TIPO_LABELS = {
    'cnae': 'CNAE',
    'codigo_servico': 'Código nacional',
    'nbs': 'NBS',
}


def _append_unique_option(options, seen, valor, rotulo, extra=None):
    valor = (valor or '').strip()
    if not valor or valor in seen:
        return
    seen.add(valor)
    item = {'valor': valor, 'rotulo': rotulo or valor}
    if extra:
        item.update(extra)
    options.append(item)


def _empresa_fiscal_catalogos(empresa):
    codigo_servico_opcoes = []
    nbs_opcoes = []
    cnae_opcoes = []
    codigo_servico_nbs_map = {}

    seen_codigo_servico = set()
    seen_nbs = set()
    seen_cnae = set()

    servicos = []
    if empresa:
        servicos = (
            Servico.query
            .filter_by(empresa_id=empresa.id, ativo=True)
            .order_by(Servico.descricao.asc())
            .all()
        )

    for servico in servicos:
        codigo_servico = (servico.codigo_servico or '').strip()
        nbs = (servico.nbs or '').strip()
        rotulo = f'{codigo_servico} - {servico.descricao}'
        if nbs:
            rotulo = f'{rotulo} | NBS {nbs}'
            codigo_servico_nbs_map.setdefault(codigo_servico, nbs)
        _append_unique_option(
            codigo_servico_opcoes,
            seen_codigo_servico,
            codigo_servico,
            rotulo,
            {'nbs': nbs},
        )
        _append_unique_option(
            nbs_opcoes,
            seen_nbs,
            nbs,
            f'{nbs} - {servico.descricao}',
        )

    for ref in NfseServicoNacionalReferencia.query.filter_by(ativo=True).filter(
        NfseServicoNacionalReferencia.codigo_tributacao_nacional.isnot(None)
    ).order_by(NfseServicoNacionalReferencia.codigo_tributacao_nacional.asc()).all():
        codigo_servico = (ref.codigo_tributacao_nacional or '').strip()
        _append_unique_option(
            codigo_servico_opcoes,
            seen_codigo_servico,
            codigo_servico,
            f'{codigo_servico} - {ref.descricao}',
            {'nbs': codigo_servico_nbs_map.get(codigo_servico, '')},
        )

    for ref in NfseNbsReferencia.query.filter_by(ativo=True).order_by(NfseNbsReferencia.codigo_nbs.asc()).all():
        _append_unique_option(
            nbs_opcoes,
            seen_nbs,
            ref.codigo_nbs,
            f'{ref.codigo_nbs} - {ref.descricao}',
        )

    for ref in NfseCnaeReferencia.query.filter_by(ativo=True).filter(
        NfseCnaeReferencia.codigo.isnot(None)
    ).order_by(NfseCnaeReferencia.codigo.asc()).all():
        cnae = (ref.codigo or '').strip()
        _append_unique_option(
            cnae_opcoes,
            seen_cnae,
            cnae,
            f'{cnae} - {ref.denominacao}',
        )

    return {
        'codigo_servico_opcoes': codigo_servico_opcoes,
        'nbs_opcoes': nbs_opcoes,
        'cnae_opcoes': cnae_opcoes,
        'codigo_servico_nbs_map': codigo_servico_nbs_map,
    }


def _split_vals(value: str):
    return [item.strip() for item in (value or '').split(',') if item.strip()]


def _empresa_fiscal_csv(empresa: Empresa, tipo: str) -> str:
    return ', '.join(item.valor for item in empresa.fiscal_itens_por_tipo(tipo) if item.valor)


def _sync_empresa_fiscal_items(empresa: Empresa, request_form) -> None:
    for item in list(empresa.fiscal_itens):
        db.session.delete(item)

    fiscal_cnaes = (request_form.get('fiscal_cnaes') or '').strip()
    fiscal_codigos = (request_form.get('fiscal_codigos') or '').strip()
    fiscal_nbs = (request_form.get('fiscal_nbs') or '').strip()

    for idx, valor in enumerate(_split_vals(fiscal_cnaes)):
        db.session.add(EmpresaFiscalItem(empresa_id=empresa.id, tipo='cnae', valor=valor, principal=(idx == 0)))
    for idx, valor in enumerate(_split_vals(fiscal_codigos)):
        db.session.add(EmpresaFiscalItem(empresa_id=empresa.id, tipo='codigo_servico', valor=valor, principal=(idx == 0)))
    for idx, valor in enumerate(_split_vals(fiscal_nbs)):
        db.session.add(EmpresaFiscalItem(empresa_id=empresa.id, tipo='nbs', valor=valor, principal=(idx == 0)))


def _create_empresa_fiscal_item(empresa: Empresa, tipo: str, valor: str, principal: bool = False) -> None:
    valor = (valor or '').strip()
    if not valor:
        return
    item = EmpresaFiscalItem.query.filter_by(empresa_id=empresa.id, tipo=tipo, valor=valor).first()
    if not item:
        item = EmpresaFiscalItem(empresa_id=empresa.id, tipo=tipo, valor=valor, principal=principal)
        db.session.add(item)
    else:
        item.principal = principal or item.principal
    if principal:
        EmpresaFiscalItem.query.filter(
            EmpresaFiscalItem.empresa_id == empresa.id,
            EmpresaFiscalItem.tipo == tipo,
            EmpresaFiscalItem.valor != valor,
        ).update({'principal': False})
        item.principal = True


def _find_empresa_by_document(document_value: str):
    """Resolve empresa por CPF/CNPJ aceitando valor com ou sem máscara."""
    normalized = _normalize_document(document_value)
    if not normalized:
        return None

    # Caminho rápido: igual ao documento normalizado.
    empresa = Empresa.query.filter_by(cnpj=normalized).first()
    if empresa:
        return empresa

    # Compatibilidade com bases legadas que podem ter CNPJ/CPF mascarado.
    for candidate in Empresa.query.all():
        if _normalize_document(candidate.cnpj) == normalized:
            return candidate

    return None


def _precos_plano(plano_codigo: str) -> dict[str, str]:
    plano = normalize_plan(plano_codigo)
    defaults = {
        'basic': {'mensal': '49,00', 'anual': '490,00'},
        'intermediate': {'mensal': '129,00', 'anual': '1.290,00'},
        'premium': {'mensal': '249,00', 'anual': '2.490,00'},
    }

    precos = defaults.get(plano, defaults['premium']).copy()
    ofertas = (
        CatalogoPlanoComercial.query
        .filter_by(codigo_plano=plano, ativo=True)
        .order_by(CatalogoPlanoComercial.versao_oferta.desc(), CatalogoPlanoComercial.id.desc())
        .all()
    )
    for oferta in ofertas:
        periodicidade = (oferta.periodicidade or '').strip().lower()
        if periodicidade not in {'mensal', 'anual'}:
            continue
        valor = f'{oferta.preco:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        precos[periodicidade] = valor
    return precos

@auth_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
@require_role('admin')
@limiter.limit('10/minute')
def add_user():
    empresa_plano = normalize_plan(getattr(current_user.empresa, 'plano', 'premium'))
    limite_usuarios = max_users_for_plan(empresa_plano)
    if limite_usuarios is not None:
        usuarios_ativos = User.query.filter_by(empresa_id=current_user.empresa_id, is_active=True).count()
        if usuarios_ativos >= limite_usuarios:
            flash(
                f'O plano {get_plan_label(empresa_plano)} permite até {limite_usuarios} usuários ativos.',
                'warning'
            )
            return redirect(url_for('auth.controle_acesso'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')

        if not username or not email or not password or not full_name:
            flash('Preencha todos os campos', 'danger')
            return redirect(url_for('auth.add_user'))

        if User.query.filter_by(empresa_id=current_user.empresa_id, username=username).first():
            flash('Usuário já existe', 'danger')
            return redirect(url_for('auth.add_user'))
        if User.query.filter_by(email=email).first():
            flash('Email já registrado', 'danger')
            return redirect(url_for('auth.add_user'))

        # Salvar dados temporariamente na session
        from flask import session
        session['new_user_data'] = {
            'username': username,
            'email': email,
            'password': password,
            'full_name': full_name,
        }

        return redirect(url_for('auth.add_user_config'))

    # GET -> render form
    return render_template('auth/add_user.html')


@auth_bp.route('/add_user_config', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def add_user_config():
    """Configurar perfil e processos do novo usuário antes de criar."""
    from flask import session

    # Verificar se há dados temporários na session
    user_data = session.get('new_user_data')
    if not user_data:
        flash('Sessão expirada. Por favor, inicie o cadastro novamente.', 'warning')
        return redirect(url_for('auth.add_user'))

    if request.method == 'POST':
        role = (request.form.get('role') or '').strip().lower()
        is_active = request.form.get('is_active') == 'on'

        if role not in {'admin', 'operator', 'viewer'}:
            flash('Papel inválido.', 'danger')
            return redirect(url_for('auth.add_user_config'))

        # Criar o usuário com as permissões definidas
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data['full_name'],
            is_active=is_active,
            is_admin=role == 'admin',
            role=role,
            empresa_id=current_user.empresa_id
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        db.session.commit()

        # Salvar permissões de processos se não for admin
        if not user.is_admin:
            save_user_overrides(current_user.empresa_id, user.id, request.form)
            db.session.commit()

        # Limpar dados da session
        session.pop('new_user_data', None)

        flash(f'Usuário {user.username} criado com sucesso com perfil {role}.', 'success')
        return redirect(url_for('auth.controle_acesso'))

    # GET -> render form de configuração
    operator_permissions = build_operator_permissions(current_user.empresa_id)
    viewer_defaults = {
        item['key']: item['key'] in {
            'dashboard',
            'entidades',
            'fluxo',
            'contas_banco',
            'lancamentos',
            'comissoes',
            'nfse_nacional',
            'relatorios',
            'importar_nfse',
            'importar_ofx',
            'conciliacao',
        }
        for item in PERMISSION_CATALOG
    }

    return render_template(
        'auth/add_user_config.html',
        user_data=user_data,
        permission_catalog=PERMISSION_CATALOG,
        operator_permissions=operator_permissions,
        viewer_defaults=viewer_defaults,
    )


@auth_bp.route('/controle-acesso', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def controle_acesso():
    """Gerenciar papéis e status de usuários da empresa atual."""
    if request.method == 'POST':
        user_id = request.form.get('user_id', type=int)
        role = (request.form.get('role') or '').strip().lower()
        is_active = request.form.get('is_active') == 'on'

        if role not in {'admin', 'operator', 'viewer'}:
            flash('Papel inválido.', 'danger')
            return redirect(url_for('auth.controle_acesso'))

        user = User.query.filter_by(id=user_id, empresa_id=current_user.empresa_id).first()
        if not user:
            flash('Usuário não encontrado para esta empresa.', 'warning')
            return redirect(url_for('auth.controle_acesso'))

        # Evita que o último administrador ativo seja removido.
        if user.is_admin and role != 'admin':
            total_admins_ativos = User.query.filter_by(
                empresa_id=current_user.empresa_id,
                is_admin=True,
                is_active=True,
            ).count()
            if total_admins_ativos <= 1:
                flash('Não é permitido remover o último administrador ativo da empresa.', 'warning')
                return redirect(url_for('auth.controle_acesso'))

        if user.id == current_user.id and not is_active:
            flash('Você não pode desativar seu próprio usuário.', 'warning')
            return redirect(url_for('auth.controle_acesso'))

        user.role = role
        user.is_admin = role == 'admin'
        user.is_active = is_active
        db.session.commit()

        flash('Permissões atualizadas com sucesso.', 'success')
        return redirect(url_for('auth.controle_acesso'))

    usuarios = User.query.filter_by(empresa_id=current_user.empresa_id).order_by(User.username.asc()).all()
    return render_template(
        'auth/controle_acesso.html',
        usuarios=usuarios,
    )


@auth_bp.route('/controle-processos', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def controle_processos():
    """Gerenciar processos liberados para operator/viewer."""
    if request.method == 'POST':
        save_operator_permissions(current_user.empresa_id, request.form)
        db.session.commit()
        flash('Permissões de processos do operator atualizadas com sucesso.', 'success')
        return redirect(url_for('auth.controle_processos'))

    operator_permissions = build_operator_permissions(current_user.empresa_id)
    viewer_defaults = {
        item['key']: item['key'] in {
            'dashboard',
            'entidades',
            'fluxo',
            'contas_banco',
            'lancamentos',
            'comissoes',
            'nfse_nacional',
            'relatorios',
            'importar_nfse',
            'importar_ofx',
            'conciliacao',
        }
        for item in PERMISSION_CATALOG
    }

    return render_template(
        'auth/controle_processos.html',
        permission_catalog=PERMISSION_CATALOG,
        operator_permissions=operator_permissions,
        viewer_defaults=viewer_defaults,
    )


@auth_bp.route('/controle-acesso/<int:user_id>/permissoes', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def controle_usuario_permissoes(user_id):
    user = User.query.filter_by(id=user_id, empresa_id=current_user.empresa_id).first_or_404()

    if user.is_admin:
        flash('Administrador possui acesso completo e nao requer override por usuario.', 'info')
        return redirect(url_for('auth.controle_acesso'))

    if request.method == 'POST':
        save_user_overrides(current_user.empresa_id, user.id, request.form)
        db.session.commit()
        flash('Excecoes de permissao do usuario atualizadas com sucesso.', 'success')
        return redirect(url_for('auth.controle_usuario_permissoes', user_id=user.id))

    overrides_matrix = build_user_overrides_matrix(current_user.empresa_id, user.id, user.role)
    return render_template(
        'auth/controle_usuario_permissoes.html',
        usuario=user,
        permission_catalog=PERMISSION_CATALOG,
        overrides_matrix=overrides_matrix,
    )


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('5/minute')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
            try:
                empresa_cnpj = _normalize_document(request.form.get('empresa_cnpj'))
                username = (request.form.get('username') or '').strip()
                password = request.form.get('password')
                if not username or not password:
                    flash('Preencha usuário e senha', 'danger')
                    return redirect(url_for('auth.login'))

                user = None
                empresa = None

                # Tenta login normal (com empresa)
                if empresa_cnpj:
                    empresa = _find_empresa_by_document(empresa_cnpj)
                    if empresa:
                        user = User.query.filter(
                            User.empresa_id == empresa.id,
                            func.lower(User.username) == username.lower(),
                        ).first()

                # Se não encontrou, tenta usuário LiveSun (sem empresa)
                if user is None:
                    user = User.query.filter(
                        User.empresa_id.is_(None),
                        func.lower(User.username) == username.lower(),
                    ).first()
                    import logging
                    if user:
                        logging.info(f'Login: usuário sem empresa encontrado: {user.username} (empresa_id={user.empresa_id})')

                if user is None:
                    import logging
                    logging.warning(f'Login falhou: usuário não encontrado - username={username}, cnpj={empresa_cnpj}')
                    flash('Empresa, usuário ou senha inválidos', 'danger')
                    return redirect(url_for('auth.login'))
                    
                if not user.check_password(password):
                    import logging
                    logging.warning(f'Login falhou: senha incorreta - username={username}')
                    flash('Empresa, usuário ou senha inválidos', 'danger')
                    return redirect(url_for('auth.login'))
                    
                if not user.is_active:
                    import logging
                    logging.warning(f'Login falhou: usuário inativo - username={username}')
                    flash('Empresa, usuário ou senha inválidos', 'danger')
                    return redirect(url_for('auth.login'))

                # Bloqueio por assinatura: usuários de empresas suspensas/canceladas/excluídas
                # não podem entrar (controle tem autoridade sobre o acesso da empresa).
                if user.empresa_id is not None:
                    from src.models import AssinaturaEmpresa
                    _assinatura = AssinaturaEmpresa.query.filter_by(empresa_id=user.empresa_id).first()
                    if _assinatura and _assinatura.status in {'suspensa', 'cancelada', 'excluida'}:
                        import logging
                        logging.info(
                            f'Login bloqueado por assinatura {_assinatura.status}: '
                            f'username={username}, empresa_id={user.empresa_id}'
                        )
                        _bloqueio = {
                            'suspensa': 'suspensa',
                            'cancelada': 'cancelada',
                            'excluida': 'excluída',
                        }.get(_assinatura.status, _assinatura.status)
                        flash(
                            f'A assinatura da sua empresa está {_bloqueio}. '
                            f'Entre em contato com o suporte para regularizar o acesso.',
                            'danger',
                        )
                        return redirect(url_for('auth.login'))

                import logging
                logging.info(f'Login sucesso: username={username}, empresa_id={user.empresa_id}, role={user.role}')

                # Usuário LiveSun (sem empresa) vai direto para backoffice
                if user.empresa_id is None and user.role == 'admin':
                    login_user(user, remember=request.form.get('remember'))
                    logging.info(f'Redirecionando para backoffice: {user.username}')
                    flash(f'Bem-vindo, {user.full_name or user.username}!', 'success')
                    return redirect(url_for('admin_comercial.index'))

                # Garante existencia da assinatura comercial e provisionamento no gateway quando habilitado.
                assinatura = ServicoAssinatura.obter_ou_criar_assinatura(empresa.id)

                if user.is_admin and not assinatura.gateway_subscription_id:
                    login_user(user, remember=request.form.get('remember'))
                    flash('Finalize os dados comerciais da assinatura para visualizar preço, trial e meios de pagamento.', 'warning')
                    return redirect(url_for('auth.assinatura'))

                login_user(user, remember=request.form.get('remember'))
                flash(f'Bem-vindo, {user.full_name or user.username}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
            except Exception as e:
                import logging, traceback
                logging.error('Erro ao processar login: %s\n%s', e, traceback.format_exc())
                flash('Erro interno ao processar login. Tente novamente ou contate o suporte.', 'danger')
                return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('3/hour')
def register():
    """Registro de novos usuários - apenas para ambiente de desenvolvimento"""
    if request.method == 'POST':
        try:
            empresa_nome = request.form.get('empresa_nome')
            empresa_cnpj = _normalize_document(request.form.get('empresa_cnpj'))
            empresa_plano = normalize_plan(request.form.get('plano'))
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            full_name = request.form.get('full_name')

            if not empresa_nome or not empresa_cnpj or not username or not email or not password or not full_name:
                flash('Preencha todos os campos', 'danger')
                return redirect(url_for('auth.register'))

            # Verifica se já existe empresa com mesmo CNPJ
            try:
                empresa_existente = Empresa.query.filter_by(cnpj=empresa_cnpj).first()
                if empresa_existente:
                    usuario_existente = User.query.filter_by(empresa_id=empresa_existente.id, is_admin=True).first()
                    import logging
                    logging.warning(f"empresa_existente: {empresa_existente}, usuario_existente: {usuario_existente}")
                    if usuario_existente:
                        flash(f'Já existe uma empresa cadastrada com este CPF/CNPJ. Usuário administrador responsável: {usuario_existente.username} (e-mail: {usuario_existente.email}). Caso não lembre o acesso, contate o suporte.', 'danger')
                    else:
                        flash('Já existe uma empresa cadastrada com este CPF/CNPJ. Caso não lembre o acesso, contate o suporte.', 'danger')
                    return redirect(url_for('auth.register'))
            except Exception as e:
                import logging, traceback
                logging.error(f"Erro ao verificar empresa existente: {e}\n{traceback.format_exc()}")
                flash('Erro interno ao verificar empresa existente. Tente novamente ou contate o suporte.', 'danger')
                return redirect(url_for('auth.register'))

            # Cria empresa
            empresa = Empresa(
                nome=empresa_nome,
                nome_fantasia=request.form.get('nome_fantasia'),
                cnpj=empresa_cnpj,
                plano=empresa_plano,
                endereco_rua=request.form.get('endereco_rua'),
                endereco_numero=request.form.get('endereco_numero'),
                endereco_bairro=request.form.get('endereco_bairro'),
                endereco_cidade=request.form.get('endereco_cidade'),
                endereco_uf=request.form.get('endereco_uf'),
                endereco_cep=request.form.get('endereco_cep'),
                inscricao_municipal=request.form.get('inscricao_municipal'),
                inscricao_estadual=request.form.get('inscricao_estadual'),
                telefone=request.form.get('telefone'),
                email=request.form.get('empresa_email'),
            )
            db.session.add(empresa)
            db.session.flush()  # Para obter o id

            # Inserir plano de fluxo de caixa padrão para a nova empresa
            from src.models import FluxoContaModel
            PLANO_PADRAO = [
            ("1", "Entradas de Caixa", "R", None, 1, None),
            ("1.1", "Receitas Operacionais", "R", None, 2, None),
            ("1.1.1", "Vendas à vista", "R", None, 3, 1),
            ("1.1.2", "Vendas cartão crédito", "R", None, 3, 1),
            ("1.1.3", "Vendas cartão débito", "R", None, 3, 1),
            ("1.1.4", "Recebimento mensalidades/serviços", "R", None, 3, 1),
            ("1.2", "Receitas Financeiras", "R", None, 2, None),
            ("1.2.1", "Juros recebidos", "R", None, 3, 1),
            ("1.2.2", "Descontos obtidos", "R", None, 3, 1),
            ("1.3", "Outras Entradas", "R", None, 2, None),
            ("1.3.1", "Empréstimos recebidos", "R", None, 3, 1),
            ("1.3.2", "Aporte de sócios", "R", None, 3, 1),
            ("1.3.3", "Reembolsos diversos", "R", None, 3, 1),
            ("2", "Saídas de Caixa", "P", None, 1, None),
            ("2.1", "Custos Operacionais", "P", None, 2, None),
            ("2.1.1", "Compra de mercadorias", "P", None, 3, 1),
            ("2.1.2", "Matéria-prima/insumos", "P", None, 3, 1),
            ("2.1.3", "Fretes sobre compras", "P", None, 3, 1),
            ("2.2", "Despesas Fixas", "P", None, 2, None),
            ("2.2.1", "Aluguel", "P", None, 3, 1),
            ("2.2.2", "Energia elétrica", "P", None, 3, 1),
            ("2.2.3", "Água", "P", None, 3, 1),
            ("2.2.4", "Internet e telefone", "P", None, 3, 1),
            ("2.3", "Despesas com Pessoal", "P", None, 2, None),
            ("2.3.1", "Salários", "P", None, 3, 1),
            ("2.3.2", "Encargos (INSS, FGTS)", "P", None, 3, 1),
            ("2.3.3", "Pró-labore", "P", None, 3, 1),
            ("2.4", "Despesas Variáveis", "P", None, 2, None),
            ("2.4.1", "Comissões sobre vendas", "P", None, 3, 1),
            ("2.4.2", "Taxas de cartão/maquininha", "P", None, 3, 1),
            ("2.4.3", "Impostos sobre vendas", "P", None, 3, 1),
            ("2.5", "Despesas Financeiras", "P", None, 2, None),
            ("2.5.1", "Juros e multas pagas", "P", None, 3, 1),
            ("2.5.2", "Tarifas bancárias", "P", None, 3, 1),
            ("2.6", "Outras Saídas", "P", None, 2, None),
            ("2.6.1", "Distribuição de lucros", "P", None, 3, 1),
            ("2.6.2", "Adiantamentos a sócios", "P", None, 3, 1),
        ]

            for codigo, descricao, tipo, mascara, nivel_sintetico, nivel_analitico in PLANO_PADRAO:
                conta = FluxoContaModel(
                    empresa_id=empresa.id,
                    codigo=codigo,
                    descricao=descricao,
                    tipo=tipo,
                    mascara=mascara,
                    nivel_sintetico=nivel_sintetico,
                    nivel_analitico=nivel_analitico,
                    ativo=True
                )
                db.session.add(conta)

            # Verifica se já existe usuário com mesmo username/email
            if User.query.filter_by(empresa_id=empresa.id, username=username).first():
                flash('Usuário já existe', 'danger')
                db.session.rollback()
                return redirect(url_for('auth.register'))
            if User.query.filter_by(email=email).first():
                flash('Email já registrado', 'danger')
                db.session.rollback()
                return redirect(url_for('auth.register'))

            # Sempre criar usuário admin neste cadastro
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                is_active=True,
                is_admin=True,
                role='admin',
                empresa_id=empresa.id
            )
            user.set_password(password)
            db.session.add(user)

            # Persistir apenas os itens fiscais principais informados no cadastro
            fiscal_tipo = (request.form.get('fiscal_tipo') or '').strip().lower()
            fiscal_valor = (request.form.get('fiscal_valor') or '').strip()
            if fiscal_tipo and fiscal_valor:
                try:
                    if fiscal_tipo not in FISCAL_TIPO_LABELS:
                        raise ValueError('Tipo fiscal inválido.')
                    _create_empresa_fiscal_item(empresa, fiscal_tipo, fiscal_valor, principal=True)
                except Exception:
                    db.session.rollback()
                    flash('Erro ao salvar o item fiscal inicial. Cadastro criado, edite na empresa depois.', 'warning')

            db.session.commit()

            # Cria assinatura inicial para garantir visibilidade imediata de trial/cobranca no onboarding.
            ServicoAssinatura.obter_ou_criar_assinatura(empresa.id)

            flash('Empresa e usuário administrador criados com sucesso. Faça login para continuar.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro no cadastro de empresa/usuário: %s\n%s', e, traceback.format_exc())
            flash('Erro interno ao cadastrar empresa/usuário. Tente novamente ou contate o suporte.', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html', plan_choices=PLAN_CHOICES)


@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if not current_user.is_admin:
        flash('Acesso permitido apenas para administradores.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        try:
            dias_grafico = int(request.form.get('dashboard_chart_days', '30'))
        except ValueError:
            dias_grafico = 30

        fiscal_action = (request.form.get('fiscal_action') or '').strip().lower()
        plano = normalize_plan(request.form.get('plano', current_user.empresa.plano if current_user.empresa else 'premium'))
        empresa = current_user.empresa

        # Upload de logo da empresa
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                import os
                from werkzeug.utils import secure_filename
                
                # Validar tamanho do arquivo (máximo 5MB)
                logo_file.seek(0, os.SEEK_END)
                file_size = logo_file.tell()
                logo_file.seek(0)
                
                max_size = 5 * 1024 * 1024  # 5MB
                if file_size > max_size:
                    flash('O arquivo é muito grande. Tamanho máximo: 5MB.', 'danger')
                    return redirect(url_for('auth.perfil'))
                
                # Validar tipo de arquivo
                allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
                file_ext = os.path.splitext(logo_file.filename)[1].lower()
                if file_ext not in allowed_extensions:
                    flash('Formato de arquivo não suportado. Use PNG, JPG, JPEG, GIF, BMP ou WEBP.', 'danger')
                    return redirect(url_for('auth.perfil'))
                
                # Criar diretório de logos se não existir
                logo_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'logos')
                os.makedirs(logo_dir, exist_ok=True)
                
                # Gerar nome seguro do arquivo
                filename = secure_filename(f"empresa_{empresa.id}_{logo_file.filename}")
                logo_path = os.path.join(logo_dir, filename)
                
                # Salvar arquivo
                logo_file.save(logo_path)
                
                # Atualizar caminho no banco
                empresa.logo_caminho = f"/uploads/logos/{filename}"
                db.session.commit()
                
                # Recarregar empresa para garantir dados atualizados na sessão
                db.session.refresh(empresa)
                
                flash('Logo da empresa atualizado com sucesso.', 'success')
                return redirect(url_for('auth.perfil'))

        if fiscal_action:
            if not empresa:
                flash('Empresa não encontrada para salvar itens fiscais.', 'danger')
            else:
                try:
                    if fiscal_action == 'add_item':
                        tipo = (request.form.get('fiscal_tipo') or '').strip().lower()
                        valor = (request.form.get('fiscal_valor') or '').strip()
                        principal = request.form.get('fiscal_principal') == 'on'
                        if tipo not in FISCAL_TIPO_LABELS:
                            raise ValueError('Tipo fiscal inválido.')
                        if not valor:
                            raise ValueError('Informe o valor do item fiscal.')

                        item = EmpresaFiscalItem.query.filter_by(empresa_id=empresa.id, tipo=tipo, valor=valor).first()
                        if not item:
                            item = EmpresaFiscalItem(empresa_id=empresa.id, tipo=tipo, valor=valor, principal=principal)
                            db.session.add(item)
                        else:
                            item.principal = principal or item.principal

                        if principal:
                            EmpresaFiscalItem.query.filter(
                                EmpresaFiscalItem.empresa_id == empresa.id,
                                EmpresaFiscalItem.tipo == tipo,
                                EmpresaFiscalItem.valor != valor,
                            ).update({'principal': False})
                            item.principal = True

                        db.session.commit()
                        flash('Item fiscal adicionado com sucesso.', 'success')
                        return redirect(url_for('auth.perfil', _anchor='perfil-fiscal-pane'))

                    if fiscal_action == 'set_primary':
                        item_id = request.form.get('fiscal_item_id', type=int)
                        item = EmpresaFiscalItem.query.filter_by(id=item_id, empresa_id=empresa.id).first()
                        if not item:
                            raise ValueError('Item fiscal não encontrado.')
                        EmpresaFiscalItem.query.filter(
                            EmpresaFiscalItem.empresa_id == empresa.id,
                            EmpresaFiscalItem.tipo == item.tipo,
                        ).update({'principal': False})
                        item.principal = True
                        db.session.commit()
                        flash('Item fiscal marcado como principal.', 'success')
                        return redirect(url_for('auth.perfil', _anchor='perfil-fiscal-pane'))

                    if fiscal_action == 'delete_item':
                        item_id = request.form.get('fiscal_item_id', type=int)
                        item = EmpresaFiscalItem.query.filter_by(id=item_id, empresa_id=empresa.id).first()
                        if not item:
                            raise ValueError('Item fiscal não encontrado.')
                        tipo = item.tipo
                        era_principal = bool(item.principal)
                        db.session.delete(item)
                        db.session.flush()
                        if era_principal:
                            proximo = (
                                EmpresaFiscalItem.query
                                .filter_by(empresa_id=empresa.id, tipo=tipo)
                                .order_by(EmpresaFiscalItem.principal.desc(), EmpresaFiscalItem.id.asc())
                                .first()
                            )
                            if proximo:
                                proximo.principal = True
                        db.session.commit()
                        flash('Item fiscal removido com sucesso.', 'success')
                        return redirect(url_for('auth.perfil', _anchor='perfil-fiscal-pane'))

                    flash('Ação fiscal inválida.', 'warning')
                except Exception as exc:
                    db.session.rollback()
                    flash(f'Erro ao salvar item fiscal: {exc}', 'danger')
        else:
            if dias_grafico < 7 or dias_grafico > 365:
                flash('Informe um periodo entre 7 e 365 dias.', 'warning')
            else:
                current_user.dashboard_chart_days = dias_grafico
                if current_user.empresa:
                    current_user.empresa.plano = plano
                db.session.commit()
                flash('Preferencias atualizadas com sucesso.', 'success')

    # Buscar dados da assinatura para exibir no perfil
    empresa_id = current_user.empresa_id
    assinatura = AssinaturaEmpresa.query.filter_by(empresa_id=empresa_id).first()
    proxima_cobranca = None
    if assinatura:
        proxima_cobranca = (
            CobrancaRecorrente.query
            .filter(
                CobrancaRecorrente.empresa_id == empresa_id,
                CobrancaRecorrente.status.in_(['pendente', 'vencido', 'falhou']),
            )
            .order_by(CobrancaRecorrente.data_vencimento.asc(), CobrancaRecorrente.id.asc())
            .first()
        )

    assinatura_resumo = {
        'disponivel': bool(assinatura),
        'plano_label': get_plan_label(assinatura.plano_codigo) if assinatura else '-',
        'status': (assinatura.status or '-').capitalize() if assinatura else '-',
        'ciclo': (assinatura.ciclo_cobranca or '-').capitalize() if assinatura else '-',
        'fim_trial': assinatura.data_fim_trial if assinatura else None,
        'vencimento': assinatura.data_vencimento if assinatura else None,
        'gateway': (assinatura.gateway or '-').upper() if assinatura else '-',
        'assinatura_gateway_id': assinatura.gateway_subscription_id if assinatura else None,
        'proxima_cobranca_status': (proxima_cobranca.status or '-').capitalize() if proxima_cobranca else '-',
        'proxima_cobranca_vencimento': proxima_cobranca.data_vencimento if proxima_cobranca else None,
        'proxima_cobranca_valor': Decimal(str(proxima_cobranca.valor_previsto or 0)) if proxima_cobranca else Decimal('0.00'),
    }

    empresa_fiscal_itens = []
    if current_user.empresa:
        empresa_fiscal_itens = (
            EmpresaFiscalItem.query
            .filter_by(empresa_id=current_user.empresa.id)
            .order_by(EmpresaFiscalItem.tipo.asc(), EmpresaFiscalItem.principal.desc(), EmpresaFiscalItem.valor.asc())
            .all()
        )

    return render_template(
        'auth/perfil.html',
        plan_choices=PLAN_CHOICES,
        assinatura_resumo=assinatura_resumo,
        empresa_fiscal_itens=empresa_fiscal_itens,
        fiscal_tipo_labels=FISCAL_TIPO_LABELS,
        fiscal_catalogos=_empresa_fiscal_catalogos(current_user.empresa) if current_user.empresa else {
            'codigo_servico_opcoes': [],
            'nbs_opcoes': [],
            'codigo_servico_nbs_map': {},
        },
        usuario=current_user,
    )


@auth_bp.route('/assinatura', methods=['GET', 'POST'])
@login_required
def assinatura():
    if not current_user.is_admin:
        flash('Acesso permitido apenas para administradores.', 'danger')
        return redirect(url_for('dashboard.index'))

    assinatura_atual = ServicoAssinatura.obter_ou_criar_assinatura(current_user.empresa_id)
    billing_choices = [
        ('BOLETO', 'Boleto'),
        ('PIX', 'Pix'),
        ('CREDIT_CARD', 'Cartão de crédito'),
    ]
    addon_catalog = [
        {
            'codigo': 'usuarios_adicionais',
            'nome': 'Usuários adicionais',
            'descricao': 'Amplia limite de usuários ativos no tenant.',
            'preco_referencia': 'Sob consulta',
            'nivel_minimo': 1,
        },
        {
            'codigo': 'conciliacao_avancada',
            'nome': 'Conciliação avançada',
            'descricao': 'Recursos avançados de conciliação e automação.',
            'preco_referencia': 'Sob consulta',
            'nivel_minimo': 2,
        },
        {
            'codigo': 'governanca_plus',
            'nome': 'Governança Plus',
            'descricao': 'Módulo estendido de governança e auditoria operacional.',
            'preco_referencia': 'Sob consulta',
            'nivel_minimo': 3,
        },
    ]

    if request.method == 'POST':
        acao = (request.form.get('acao') or 'configurar_cobranca').strip().lower()

        if acao == 'configurar_cobranca':
            ciclo = (request.form.get('ciclo_cobranca') or 'mensal').strip().lower()
            billing_type = (request.form.get('billing_type') or 'BOLETO').strip().upper()

            if ciclo not in {'mensal', 'anual'}:
                flash('Ciclo de cobrança inválido.', 'warning')
                return redirect(url_for('auth.assinatura'))
            if billing_type not in {'BOLETO', 'PIX', 'CREDIT_CARD'}:
                flash('Forma de pagamento inválida.', 'warning')
                return redirect(url_for('auth.assinatura'))

            assinatura_atual.ciclo_cobranca = ciclo
            assinatura_atual.motivo_status = f'Preferência comercial: {billing_type} / {ciclo}.'
            db.session.commit()

            ServicoAssinatura.provisionar_gateway_asaas(assinatura_atual, billing_type_override=billing_type)
            try:
                ServicoAssinatura.sincronizar_cobranca_pendente_asaas(assinatura_atual)
            except Exception:
                pass
            db.session.commit()

            if assinatura_atual.gateway_subscription_id:
                flash('Assinatura comercial configurada com sucesso. A cobrança será processada pelo Asaas.', 'success')
            else:
                flash('Preferências salvas. O vínculo de cobrança será concluído assim que o gateway confirmar os dados.', 'info')

            return redirect(url_for('auth.assinatura'))

        if acao == 'sincronizar_pagamento':
            try:
                synced = ServicoAssinatura.sincronizar_cobranca_pendente_asaas(assinatura_atual)
                db.session.commit()
                if synced and (synced.get('invoice_url') or synced.get('bank_slip_url')):
                    flash('Cobrança sincronizada com sucesso. Link de pagamento atualizado.', 'success')
                elif synced:
                    flash('Cobrança sincronizada, mas sem URL de pagamento disponível no retorno.', 'warning')
                else:
                    flash('Nenhuma cobrança pendente encontrada para esta assinatura.', 'info')
            except Exception as exc:
                db.session.rollback()
                flash(f'Falha ao sincronizar cobrança no Asaas: {str(exc)[:180]}', 'danger')
            return redirect(url_for('auth.assinatura'))

        if acao == 'solicitar_mudanca_plano':
            novo_plano = normalize_plan(request.form.get('novo_plano'))
            plano_atual = normalize_plan(assinatura_atual.plano_codigo)

            if novo_plano == plano_atual:
                flash('O plano selecionado já é o plano vigente.', 'warning')
                return redirect(url_for('auth.assinatura'))

            if assinatura_atual.proximo_plano_codigo:
                flash('Já existe uma mudança de plano pendente para esta assinatura.', 'warning')
                return redirect(url_for('auth.assinatura'))

            rank_atual = plan_rank(plano_atual)
            rank_novo = plan_rank(novo_plano)
            tipo_mudanca = 'lateral'
            if rank_novo > rank_atual:
                tipo_mudanca = 'upgrade'
            elif rank_novo < rank_atual:
                tipo_mudanca = 'downgrade'

            dias_regra = int(assinatura_atual.politica_efetivacao_dias or 30)
            efetivar_em = datetime.utcnow() + timedelta(days=dias_regra)

            assinatura_atual.proximo_plano_codigo = novo_plano
            assinatura_atual.mudanca_plano_solicitada_em = datetime.utcnow()
            assinatura_atual.mudanca_plano_efetivar_em = efetivar_em

            historico = HistoricoMudancaPlano(
                empresa_id=assinatura_atual.empresa_id,
                assinatura_id=assinatura_atual.id,
                plano_origem=plano_atual,
                plano_destino=novo_plano,
                tipo_mudanca=tipo_mudanca,
                regra_efetivacao='apos_30_dias',
                solicitado_por_user_id=current_user.id,
                observacoes=f'Solicitação via painel comercial. Efetivação prevista para {efetivar_em.strftime("%d/%m/%Y")}.',
            )
            db.session.add(historico)
            db.session.commit()

            flash('Solicitação de mudança de plano registrada com sucesso.', 'success')
            return redirect(url_for('auth.assinatura'))

        if acao == 'solicitar_addon':
            addon_codigo = (request.form.get('addon_codigo') or '').strip().lower()
            addon_map = {item['codigo']: item for item in addon_catalog}
            addon = addon_map.get(addon_codigo)
            if not addon:
                flash('Add-on inválido.', 'warning')
                return redirect(url_for('auth.assinatura'))

            notificacao = NotificacaoComercial(
                empresa_id=assinatura_atual.empresa_id,
                assinatura_id=assinatura_atual.id,
                tipo='solicitacao_addon',
                canal='sistema',
                destinatario=getattr(current_user, 'email', None),
                status='pendente',
                payload=f"{{'addon':'{addon_codigo}','solicitado_por':{current_user.id},'plano_atual':'{assinatura_atual.plano_codigo}'}}",
            )
            db.session.add(notificacao)
            db.session.commit()

            flash('Solicitação de add-on registrada. Nossa equipe comercial entrará em contato.', 'success')
            return redirect(url_for('auth.assinatura'))

        flash('Ação comercial inválida.', 'warning')
        return redirect(url_for('auth.assinatura'))




    precos = _precos_plano(assinatura_atual.plano_codigo)
    historico = (
        HistoricoMudancaPlano.query
        .filter_by(empresa_id=current_user.empresa_id)
        .order_by(HistoricoMudancaPlano.solicitado_em.desc(), HistoricoMudancaPlano.id.desc())
        .limit(10)
        .all()
    )
    planos_disponiveis = [
        {'codigo': code, 'label': label, 'selecionado': normalize_plan(code) == normalize_plan(assinatura_atual.plano_codigo)}
        for code, label in PLAN_CHOICES
    ]
    nivel_atual = plan_rank(assinatura_atual.plano_codigo)
    for item in addon_catalog:
        item['incluido_no_plano'] = nivel_atual >= int(item['nivel_minimo'])

    cobranca_pendente = (
        CobrancaRecorrente.query
        .filter(
            CobrancaRecorrente.empresa_id == current_user.empresa_id,
            CobrancaRecorrente.status.in_(['pendente', 'vencido']),
        )
        .order_by(CobrancaRecorrente.data_vencimento.asc(), CobrancaRecorrente.id.desc())
        .first()
    )

    pagamento = {
        'status': None,
        'valor': None,
        'vencimento': None,
        'invoice_url': None,
        'bank_slip_url': None,
    }
    try:
        synced = ServicoAssinatura.sincronizar_cobranca_pendente_asaas(assinatura_atual)
        if synced:
            pagamento.update(synced)
            db.session.commit()
    except Exception:
        db.session.rollback()

    if cobranca_pendente:
        pagamento['status'] = pagamento['status'] or cobranca_pendente.status
        pagamento['valor'] = pagamento['valor'] or cobranca_pendente.valor_previsto
        pagamento['vencimento'] = pagamento['vencimento'] or cobranca_pendente.data_vencimento

    return render_template(
        'auth/assinatura.html',
        assinatura=assinatura_atual,
        plano_label=get_plan_label(assinatura_atual.plano_codigo),
        precos=precos,
        billing_choices=billing_choices,
        planos_disponiveis=planos_disponiveis,
        historico_mudancas=historico,
        addon_catalog=addon_catalog,
        pagamento=pagamento,
    )


@auth_bp.route('/empresa/editar', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def editar_empresa():
    """Tela simples de manutenção/edição dos dados da empresa (admin)."""
    empresa = current_user.empresa
    if not empresa:
        flash('Empresa não encontrada para edição.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        try:
            print(f'[DEBUG] Form data received: {dict(request.form)}')
            
            # Fiscal actions (add/set primary/delete) from the Fiscal tab
            # These are handled separately and don't affect address fields
            fiscal_action = (request.form.get('fiscal_action') or '').strip().lower()
            if fiscal_action:
                if fiscal_action == 'add_item':
                    tipo = (request.form.get('fiscal_tipo') or '').strip().lower()
                    valor = (request.form.get('fiscal_valor') or '').strip()
                    principal = request.form.get('fiscal_principal') == 'on'
                    if tipo not in FISCAL_TIPO_LABELS:
                        raise ValueError('Tipo fiscal inválido.')
                    if not valor:
                        raise ValueError('Informe o valor do item fiscal.')

                    item = EmpresaFiscalItem.query.filter_by(empresa_id=empresa.id, tipo=tipo, valor=valor).first()
                    if not item:
                        item = EmpresaFiscalItem(empresa_id=empresa.id, tipo=tipo, valor=valor, principal=principal)
                        db.session.add(item)
                    else:
                        item.principal = principal or item.principal

                    if principal:
                        EmpresaFiscalItem.query.filter(
                            EmpresaFiscalItem.empresa_id == empresa.id,
                            EmpresaFiscalItem.tipo == tipo,
                            EmpresaFiscalItem.valor != valor,
                        ).update({'principal': False})
                        item.principal = True

                    db.session.commit()
                    flash('Item fiscal adicionado com sucesso.', 'success')
                    return redirect(url_for('auth.editar_empresa', _anchor='fiscal-tab'))

                if fiscal_action == 'set_primary':
                    item_id = request.form.get('fiscal_item_id', type=int)
                    item = EmpresaFiscalItem.query.filter_by(id=item_id, empresa_id=empresa.id).first()
                    if not item:
                        raise ValueError('Item fiscal não encontrado.')
                    EmpresaFiscalItem.query.filter(
                        EmpresaFiscalItem.empresa_id == empresa.id,
                        EmpresaFiscalItem.tipo == item.tipo,
                    ).update({'principal': False})
                    item.principal = True
                    db.session.commit()
                    flash('Item fiscal marcado como principal.', 'success')
                    return redirect(url_for('auth.editar_empresa', _anchor='fiscal-tab'))

                if fiscal_action == 'delete_item':
                    item_id = request.form.get('fiscal_item_id', type=int)
                    item = EmpresaFiscalItem.query.filter_by(id=item_id, empresa_id=empresa.id).first()
                    if not item:
                        raise ValueError('Item fiscal não encontrado.')
                    tipo = item.tipo
                    era_principal = bool(item.principal)
                    db.session.delete(item)
                    db.session.flush()
                    if era_principal:
                        proximo = (
                            EmpresaFiscalItem.query
                            .filter_by(empresa_id=empresa.id, tipo=tipo)
                            .order_by(EmpresaFiscalItem.principal.desc(), EmpresaFiscalItem.id.asc())
                            .first()
                        )
                        if proximo:
                            proximo.principal = True
                    db.session.commit()
                    flash('Item fiscal removido com sucesso.', 'success')
                    return redirect(url_for('auth.editar_empresa', _anchor='fiscal-tab'))

            # If no fiscal action, process general company data (address, etc.)
            # Only validate and save address fields if they were submitted
            
            empresa.endereco_rua = (request.form.get('endereco_rua') or '').strip()
            empresa.endereco_numero = (request.form.get('endereco_numero') or '').strip()
            empresa.endereco_bairro = (request.form.get('endereco_bairro') or '').strip()
            municipio_ref = (request.form.get('municipio_ref') or '').strip()
            
            print(f'[DEBUG] municipio_ref: {municipio_ref}')
            print(f'[DEBUG] endereco_rua: {empresa.endereco_rua}')
            print(f'[DEBUG] endereco_numero: {empresa.endereco_numero}')
            print(f'[DEBUG] endereco_bairro: {empresa.endereco_bairro}')
            
            from src.models import NfseMunicipioReferencia
            municipio = NfseMunicipioReferencia.query.filter_by(codigo_ibge=municipio_ref, ativo=True).first() if municipio_ref else None
            if municipio:
                empresa.codigo_municipio_ibge = municipio.codigo_ibge
                empresa.endereco_cidade = municipio.nome_municipio
                # Tenta usar uf_sigla, se vazio extrai do nome_uf
                if municipio.uf_sigla:
                    empresa.endereco_uf = municipio.uf_sigla
                elif municipio.nome_uf:
                    # Mapeamento de nomes de estados para siglas
                    uf_map = {
                        'Rio de Janeiro': 'RJ',
                        'São Paulo': 'SP',
                        'Minas Gerais': 'MG',
                        'Bahia': 'BA',
                        'Paraná': 'PR',
                        'Rio Grande do Sul': 'RS',
                        'Pernambuco': 'PE',
                        'Ceará': 'CE',
                        'Pará': 'PA',
                        'Santa Catarina': 'SC',
                        'Goiás': 'GO',
                        'Maranhão': 'MA',
                        'Amazonas': 'AM',
                        'Espírito Santo': 'ES',
                        'Mato Grosso': 'MT',
                        'Mato Grosso do Sul': 'MS',
                        'Rio Grande do Norte': 'RN',
                        'Alagoas': 'AL',
                        'Piauí': 'PI',
                        'Distrito Federal': 'DF',
                        'Goias': 'GO',
                        'Paraíba': 'PB',
                        'Sergipe': 'SE',
                        'Amapá': 'AP',
                        'Rondônia': 'RO',
                        'Tocantins': 'TO',
                        'Acre': 'AC',
                        'Roraima': 'RR',
                    }
                    empresa.endereco_uf = uf_map.get(municipio.nome_uf, municipio.nome_uf[:2].upper())
                else:
                    empresa.endereco_uf = ''
            else:
                # Se não selecionou município, usa valores do form
                empresa.endereco_cidade = (request.form.get('endereco_cidade') or '').strip()
                # Remove caracteres não alfabéticos e converte para maiúsculas
                uf_raw = (request.form.get('endereco_uf') or '').strip()
                empresa.endereco_uf = ''.join(filter(str.isalpha, uf_raw)).upper()
            empresa.endereco_cep = ''.join(ch for ch in (request.form.get('endereco_cep') or '') if ch.isdigit())
            empresa.inscricao_municipal = (request.form.get('inscricao_municipal') or '').strip()
            empresa.inscricao_estadual = (request.form.get('inscricao_estadual') or '').strip()
            empresa.nome_fantasia = (request.form.get('nome_fantasia') or '').strip()
            empresa.telefone = (request.form.get('telefone') or '').strip()
            empresa.email = (request.form.get('empresa_email') or '').strip()
            empresa.op_simp_nac = int(request.form.get('op_simp_nac', 3) or 3)
            empresa.reg_ap_trib_sn = int(request.form.get('reg_ap_trib_sn', 1) or 1)

            # Basic validations
            missing = []
            if not empresa.inscricao_municipal:
                missing.append('Inscrição municipal')
            if not empresa.endereco_rua:
                missing.append('Endereço (rua)')
            if not empresa.endereco_numero:
                missing.append('Número')
            if not empresa.endereco_bairro:
                missing.append('Bairro')
            if not empresa.endereco_cep:
                missing.append('CEP')
            if not empresa.endereco_uf:
                missing.append('UF')
            if not empresa.telefone:
                missing.append('Telefone')
            if not empresa.email:
                missing.append('Email')

            if missing:
                flash('Campos obrigatórios ausentes: ' + ', '.join(missing), 'danger')
                return redirect(url_for('auth.editar_empresa'))

            db.session.commit()
            flash('Dados da empresa atualizados com sucesso.', 'success')
            return redirect(url_for('auth.editar_empresa'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao salvar dados da empresa: {exc}', 'danger')

    from src.models import NfseMunicipioReferencia
    municipios = NfseMunicipioReferencia.query.filter_by(ativo=True).order_by(NfseMunicipioReferencia.nome_municipio).all()
    
    return render_template(
        'auth/empresa_edit.html',
        empresa=empresa,
        municipios=municipios,
        fiscal_cnaes=_empresa_fiscal_csv(empresa, 'cnae'),
        empresa_fiscal_itens=(
            EmpresaFiscalItem.query.filter_by(empresa_id=empresa.id).order_by(EmpresaFiscalItem.tipo.asc(), EmpresaFiscalItem.principal.desc(), EmpresaFiscalItem.valor.asc()).all()
            if empresa else []
        ),
        fiscal_tipo_labels=FISCAL_TIPO_LABELS,
        fiscal_catalogos=_empresa_fiscal_catalogos(empresa),
    )


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Página de recuperação de senha - solicitação de envio de código."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Por favor, informe seu email.', 'warning')
            return render_template('auth/forgot_password.html')
        
        # Verificar se usuário existe
        user = User.query.filter_by(email=email).first()
        if not user:
            # Não informamos se email existe ou não por segurança
            flash('Se o email estiver cadastrado, você receberá um código de recuperação.', 'info')
            return render_template('auth/forgot_password.html')
        
        # Gerar código de 6 dígitos
        code = ''.join(random.choices(string.digits, k=6))
        
        # Expiração em 15 minutos
        expires_at = datetime.now() + timedelta(minutes=15)
        
        # Invalidar códigos anteriores do mesmo email
        PasswordResetCode.query.filter_by(email=email).update({'used': True})
        
        # Criar novo código
        reset_code = PasswordResetCode(
            email=email,
            code=code,
            expires_at=expires_at,
            used=False
        )
        db.session.add(reset_code)
        
        try:
            db.session.commit()
            
            # Enviar email via Brevo
            username = user.full_name or user.username
            if brevo_service.send_reset_password_email(email, username, code):
                flash('Código de recuperação enviado para seu email. Verifique sua caixa de entrada.', 'success')
                return redirect(url_for('auth.reset_password', email=email))
            else:
                flash('Erro ao enviar email. Tente novamente mais tarde.', 'danger')
                
        except Exception as e:
            db.session.rollback()
            flash('Erro ao processar solicitação. Tente novamente.', 'danger')
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Página de redefinição de senha usando código."""
    email = request.args.get('email', '')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        code = request.form.get('code', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validações básicas
        if not email or not code or not new_password:
            flash('Todos os campos são obrigatórios.', 'warning')
            return render_template('auth/reset_password.html', email=email)
        
        if len(new_password) < 8:
            flash('A senha deve ter no mínimo 8 caracteres.', 'warning')
            return render_template('auth/reset_password.html', email=email)
        
        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'warning')
            return render_template('auth/reset_password.html', email=email)
        
        # Buscar código válido
        reset_code = PasswordResetCode.query.filter_by(
            email=email,
            code=code,
            used=False
        ).order_by(PasswordResetCode.created_at.desc()).first()
        
        if not reset_code or not reset_code.is_valid():
            flash('Código inválido ou expirado. Solicite um novo código.', 'danger')
            return render_template('auth/reset_password.html', email=email)
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Usuário não encontrado.', 'danger')
            return render_template('auth/reset_password.html', email=email)
        
        try:
            # Atualizar senha
            user.set_password(new_password)

            # Marcar código como usado
            reset_code.mark_as_used()

            db.session.commit()

            flash('Senha redefinida com sucesso! Faça login com sua nova senha.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao redefinir senha: {e}')
            flash('Erro ao redefinir senha. Tente novamente.', 'danger')
    
    return render_template('auth/reset_password.html', email=email)
