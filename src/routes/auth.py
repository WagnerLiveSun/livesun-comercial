from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta

from src.models import (
    db,
    User,
    Empresa,
    CobrancaRecorrente,
    CatalogoPlanoComercial,
    HistoricoMudancaPlano,
    NotificacaoComercial,
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

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _normalize_document(value):
    if not value:
        return ''
    return ''.join(ch for ch in value if ch.isdigit())


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

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            is_active=True,
            is_admin=False,
            role='operator',
            empresa_id=current_user.empresa_id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Usuário criado com sucesso.', 'success')
        return redirect(url_for('dashboard.index'))

    # GET -> render form
    return render_template('auth/add_user.html')


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
                if not empresa_cnpj or not username or not password:
                    flash('Preencha empresa, usuário e senha', 'danger')
                    return redirect(url_for('auth.login'))
                
                empresa = _find_empresa_by_document(empresa_cnpj)
                if empresa is None:
                    flash('Empresa, usuário ou senha inválidos', 'danger')
                    return redirect(url_for('auth.login'))
                
                user = User.query.filter(
                    User.empresa_id == empresa.id,
                    func.lower(User.username) == username.lower(),
                ).first()
                if user is None or not user.check_password(password):
                    flash('Empresa, usuário ou senha inválidos', 'danger')
                    return redirect(url_for('auth.login'))
                if not user.is_active:
                    flash('Empresa, usuário ou senha inválidos', 'danger')
                    return redirect(url_for('auth.login'))

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
            empresa = Empresa(nome=empresa_nome, cnpj=empresa_cnpj, plano=empresa_plano)
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

        plano = normalize_plan(request.form.get('plano', current_user.empresa.plano if current_user.empresa else 'premium'))

        if dias_grafico < 7 or dias_grafico > 365:
            flash('Informe um periodo entre 7 e 365 dias.', 'warning')
        else:
            current_user.dashboard_chart_days = dias_grafico
            if current_user.empresa:
                current_user.empresa.plano = plano
            db.session.commit()
            flash('Preferencias atualizadas com sucesso.', 'success')

    return render_template('auth/perfil.html', plan_choices=PLAN_CHOICES)


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
