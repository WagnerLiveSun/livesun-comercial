from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from src.models import db, User, Empresa
from src.extensions import limiter, require_role
from src.access_control import (
    PERMISSION_CATALOG,
    build_operator_permissions,
    build_user_overrides_matrix,
    save_operator_permissions,
    save_user_overrides,
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _normalize_document(value):
    if not value:
        return ''
    return ''.join(ch for ch in value if ch.isdigit())

@auth_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
@require_role('admin')
@limiter.limit('10/minute')
def add_user():
    # Plano premium (temporário): sem limite de usuários.
    # Futuro: aplicar limite conforme plano comercial (básico/intermediário/premium).

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
                username = request.form.get('username')
                password = request.form.get('password')
                if not empresa_cnpj or not username or not password:
                    flash('Preencha empresa, usuário e senha', 'danger')
                    return redirect(url_for('auth.login'))
                
                empresa = Empresa.query.filter_by(cnpj=empresa_cnpj).first()
                if empresa is None:
                    flash('Empresa, usuário ou senha inválidos', 'danger')
                    return redirect(url_for('auth.login'))
                
                user = User.query.filter_by(empresa_id=empresa.id, username=username).first()
                if user is None or not user.check_password(password):
                    flash('Empresa, usuário ou senha inválidos', 'danger')
                    return redirect(url_for('auth.login'))
                if not user.is_active:
                    flash('Empresa, usuário ou senha inválidos', 'danger')
                    return redirect(url_for('auth.login'))
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
            empresa = Empresa(nome=empresa_nome, cnpj=empresa_cnpj)
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

            flash('Empresa e usuário administrador criados com sucesso. Faça login para continuar.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro no cadastro de empresa/usuário: %s\n%s', e, traceback.format_exc())
            flash('Erro interno ao cadastrar empresa/usuário. Tente novamente ou contate o suporte.', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')


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

        if dias_grafico < 7 or dias_grafico > 365:
            flash('Informe um periodo entre 7 e 365 dias.', 'warning')
        else:
            current_user.dashboard_chart_days = dias_grafico
            db.session.commit()
            flash('Preferencias atualizadas com sucesso.', 'success')

    return render_template('auth/perfil.html')
