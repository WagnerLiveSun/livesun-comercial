import os
import logging
from decimal import Decimal, InvalidOperation
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime

# Load environment variables
load_dotenv()

# Import configuration
from config.config import config

# Import models
from src.models import db, User, Entidade, FluxoContaModel, ContaBanco, Lancamento, ConciliacaoBancaria, ConciliacaoItem
from src.access_control import current_user_has_permission
from src.services.planos import (
    get_plan_config,
    get_plan_label,
    is_basic_plan,
    is_intermediate_plan,
    is_premium_plan,
    plan_allows_endpoint,
    normalize_plan,
)

# Setup logging
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app_errors.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


ENDPOINT_PERMISSION_MAP = {
    'dashboard.index': 'dashboard',

    'entidades.index': 'entidades',
    'entidades.criar': 'entidades',
    'entidades.editar': 'entidades',
    'entidades.ver': 'entidades',
    'entidades.deletar': 'entidades',
    'entidades.api_search': 'entidades',

    'fluxo.index': 'fluxo',
    'fluxo.criar': 'fluxo',
    'fluxo.editar': 'fluxo',
    'fluxo.deletar': 'fluxo',
    'fluxo.api_search': 'fluxo',

    'contas_banco.index': 'contas_banco',
    'contas_banco.criar': 'contas_banco',
    'contas_banco.editar': 'contas_banco',
    'contas_banco.ver': 'contas_banco',
    'contas_banco.deletar': 'contas_banco',
    'contas_banco.api_search': 'contas_banco',

    'lancamentos.index': 'lancamentos',
    'lancamentos.criar': 'lancamentos',
    'lancamentos.editar': 'lancamentos',
    'lancamentos.pagar': 'lancamentos',
    'lancamentos.deletar': 'lancamentos',

    'comissoes.listar': 'comissoes',
    'comissoes.apurar': 'comissoes',
    'comissoes.relatorio': 'comissoes',
    'comissoes.parametros': 'comissoes',
    'comissoes.exportar_csv': 'comissoes',

    'relatorios.listagem_lancamentos': 'relatorios',
    'relatorios.export_listagem_lancamentos': 'relatorios',
    'relatorios.listagem_notas_nfse': 'relatorios',
    'relatorios.export_listagem_notas_nfse': 'relatorios',
    'relatorios.fluxo_caixa': 'relatorios',
    'relatorios.fluxo_caixa_csv': 'relatorios',
    'relatorios.export_fluxo_caixa_csv': 'relatorios',
    'relatorios.export_fluxo_caixa': 'relatorios',
    'relatorios.fluxo_caixa_previsto': 'relatorios',
    'relatorios.fluxo_caixa_realizado': 'relatorios',
    'relatorio_fluxo.index': 'relatorios',
    'relatorio_fluxo.exportar': 'relatorios',

    'importacoes.importar_nfse': 'importar_nfse',
    'importacoes.importar_ofx': 'importar_ofx',

    'conciliacao.index': 'conciliacao',
    'conciliacao.nova': 'conciliacao',
    'conciliacao.detalhe': 'conciliacao',
    'conciliacao.reconciliar': 'conciliacao',
    'conciliacao.vincular_item': 'conciliacao',
    'conciliacao.desvincular_item': 'conciliacao',
    'auth.add_user': 'usuarios',
    'auth.controle_acesso': 'controle_acesso',
    'auth.controle_processos': 'controle_acesso',
    'auth.controle_usuario_permissoes': 'controle_acesso',
}


def _validate_production_settings(config_name: str):
    if config_name != 'production':
        return

    required_env = ['SECRET_KEY', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing = [name for name in required_env if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            'Configuracao insegura para producao. Variaveis ausentes: '
            + ', '.join(missing)
        )

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    _validate_production_settings(config_name)
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    # Add SQLAlchemy engine options to improve resilience against dropped MySQL connections
    app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {})
    app.config['SQLALCHEMY_ENGINE_OPTIONS'].update({
        'pool_pre_ping': True,
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '1800')),
    })
    app.config.setdefault('RATELIMIT_ENABLED', config_name != 'testing')

    db.init_app(app)
    
    # Initialize Flask-WTF CSRF Protection
    from src.extensions import csrf
    csrf.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = None
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.dashboard import dashboard_bp
    from src.routes.entidades import entidades_bp
    from src.routes.fluxo import fluxo_bp
    from src.routes.contas_banco import contas_banco_bp
    from src.routes.lancamentos import lancamentos_bp
    from src.routes.relatorio_fluxo import relatorio_fluxo_bp
    from src.routes.relatorios import relatorios_bp
    from src.routes.comissoes import comissoes_bp
    from src.routes.importacoes import importacoes_bp
    from src.routes.conciliacao import conciliacao_bp
    from src.routes.comercial import comercial_webhook_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(entidades_bp)
    app.register_blueprint(fluxo_bp)
    app.register_blueprint(contas_banco_bp)
    app.register_blueprint(lancamentos_bp)
    app.register_blueprint(relatorio_fluxo_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(comissoes_bp)
    app.register_blueprint(importacoes_bp)
    app.register_blueprint(conciliacao_bp)
    app.register_blueprint(comercial_webhook_bp)

    @app.route('/suporte')
    def suporte():
        return render_template('suporte.html')

    @app.template_filter('brl')
    def format_brl(value):
        """Format numeric values using pt-BR currency style."""
        if value is None:
            value = 0
        try:
            num = Decimal(str(value)).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError, TypeError):
            num = Decimal('0.00')
        formatted = f"{num:,.2f}"
        return formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Register context processors
    @app.context_processor
    def inject_user():
        from flask import url_for
        from werkzeug.routing import BuildError

        def safe_url_for(endpoint, **values):
            try:
                return url_for(endpoint, **values)
            except BuildError:
                return None

        return {
            'current_user': current_user,
            'year': datetime.now().year,
            'current_year': datetime.now().year,
            'powered_by': 'LiveSun Controller',
            'safe_url_for': safe_url_for,
            'has_permission': current_user_has_permission,
            'current_plan': normalize_plan(getattr(getattr(current_user, 'empresa', None), 'plano', 'premium')),
            'current_plan_label': get_plan_label(getattr(getattr(current_user, 'empresa', None), 'plano', 'premium')),
            'current_plan_config': get_plan_config(getattr(getattr(current_user, 'empresa', None), 'plano', 'premium')),
            'is_basic_plan': is_basic_plan(getattr(getattr(current_user, 'empresa', None), 'plano', 'premium')),
            'is_intermediate_plan': is_intermediate_plan(getattr(getattr(current_user, 'empresa', None), 'plano', 'premium')),
            'is_premium_plan': is_premium_plan(getattr(getattr(current_user, 'empresa', None), 'plano', 'premium')),
            'plan_allows_endpoint': lambda endpoint_name: plan_allows_endpoint(getattr(getattr(current_user, 'empresa', None), 'plano', 'premium'), endpoint_name),
        }

    @app.before_request
    def enforce_process_permissions():
        if not current_user.is_authenticated:
            return None

        from flask import request, flash
        endpoint_name = request.endpoint
        if not endpoint_name:
            return None

        company_plan = normalize_plan(getattr(getattr(current_user, 'empresa', None), 'plano', 'premium'))
        if not plan_allows_endpoint(company_plan, endpoint_name):
            flash('Este recurso não está disponível no seu plano atual.', 'warning')
            return redirect(url_for('dashboard.index'))

        permission_key = ENDPOINT_PERMISSION_MAP.get(endpoint_name)
        if not permission_key:
            return None

        if not current_user_has_permission(permission_key):
            flash('Acesso negado para este processo no seu papel atual.', 'danger')
            return redirect(url_for('dashboard.index'))

        # Viewer é estritamente leitura: bloqueia qualquer tentativa de escrita.
        # Mantemos essa regra central para evitar lacunas em rotas individuais.
        user_role = (getattr(current_user, 'role', 'viewer') or 'viewer').strip().lower()
        if (
            not getattr(current_user, 'is_admin', False)
            and user_role == 'viewer'
            and request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}
        ):
            flash('Seu perfil Viewer possui acesso apenas para consulta (somente leitura).', 'warning')
            return redirect(url_for('dashboard.index'))

        return None
    
    # Create database tables
    with app.app_context():
        db.create_all()
        _ensure_schema_compatibility()
        _bootstrap_admin_user()
        logger.info('Database tables created successfully')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        logger.error('Erro interno no servidor: %s\n%s', error, traceback.format_exc())
        db.session.rollback()
        mensagem = "Ocorreu um erro inesperado. Nossa equipe já foi notificada. Tente novamente ou entre em contato com o suporte."
        return render_template('errors/500.html', mensagem=mensagem), 500
    
    # Shell context for flask shell
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'Entidade': Entidade,
            'FluxoContaModel': FluxoContaModel,
            'ContaBanco': ContaBanco,
            'Lancamento': Lancamento,
            'ConciliacaoBancaria': ConciliacaoBancaria,
            'ConciliacaoItem': ConciliacaoItem
        }
    
    logger.info(f'Application created with {config_name} configuration')
    
    return app


def _bootstrap_admin_user():
    """Bootstrap admin user only when explicitly enabled via env vars."""
    if os.getenv('ENABLE_BOOTSTRAP_ADMIN', 'false').lower() != 'true':
        return

    from src.models import Empresa

    company_name = os.getenv('BOOTSTRAP_COMPANY_NAME', 'Empresa Inicial')
    company_cnpj = os.getenv('BOOTSTRAP_COMPANY_CNPJ', '')
    admin_username = os.getenv('BOOTSTRAP_ADMIN_USERNAME', 'owner')
    admin_email = os.getenv('BOOTSTRAP_ADMIN_EMAIL', '')
    admin_password = os.getenv('BOOTSTRAP_ADMIN_PASSWORD', '')

    if not company_cnpj or not admin_email or not admin_password:
        logger.warning(
            'Bootstrap admin habilitado, mas variaveis obrigatorias ausentes. '
            'Defina BOOTSTRAP_COMPANY_CNPJ, BOOTSTRAP_ADMIN_EMAIL e BOOTSTRAP_ADMIN_PASSWORD.'
        )
        return

    if len(admin_password) < 10:
        logger.warning('Bootstrap admin ignorado: senha deve ter ao menos 10 caracteres.')
        return

    empresa = Empresa.query.filter_by(cnpj=company_cnpj).first()
    if not empresa:
        empresa = Empresa(nome=company_name, cnpj=company_cnpj)
        db.session.add(empresa)
        db.session.commit()

    admin_user = User.query.filter_by(empresa_id=empresa.id, username=admin_username).first()
    if admin_user:
        return

    existing_global_admin = User.query.filter_by(username=admin_username).first()
    if existing_global_admin:
        return

    admin_user = User(
        username=admin_username,
        email=admin_email,
        full_name='Administrador',
        is_admin=True,
        is_active=True,
        empresa_id=empresa.id
    )
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def _ensure_schema_compatibility():
    """Ensure required columns exist in databases created before recent releases."""
    try:
        _ensure_columns(
            'users',
            {
                'dashboard_chart_days': 'dashboard_chart_days INTEGER DEFAULT 30',
                'role': "role VARCHAR(20) DEFAULT 'viewer'"
            }
        )

        _ensure_columns(
            'empresas',
            {
                'plano': "plano VARCHAR(20) DEFAULT 'premium'"
            }
        )

        _ensure_columns(
            'entidades',
            {
                'aliquota_comissao_especifica': 'aliquota_comissao_especifica DECIMAL(5,2) NULL',
                'valor_repasse': 'valor_repasse DECIMAL(10,2) DEFAULT 0.00',
                'vendedor_id': 'vendedor_id INTEGER NULL'
            }
        )

        _ensure_columns(
            'lancamentos',
            {
                'valor_imposto': 'valor_imposto DECIMAL(15,2) DEFAULT 0.00',
                'valor_outros_custos': 'valor_outros_custos DECIMAL(15,2) DEFAULT 0.00'
            }
        )

        _ensure_column_type(
            'importacao_nfse',
            'descricao_servico',
            'TEXT'
        )
    except Exception as exc:
        import traceback
        logger.error('Erro ao verificar/atualizar compatibilidade de schema: %s\n%s', exc, traceback.format_exc())


def _ensure_columns(table_name, expected_columns):
    """Add missing columns to an existing table without dropping data."""
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    if table_name not in existing_tables:
        return

    existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
    with db.engine.begin() as conn:
        for column_name, column_def in expected_columns.items():
            if column_name in existing_columns:
                continue
            conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {column_def}'))
            logger.info('Coluna adicionada: %s.%s', table_name, column_name)


def _ensure_column_type(table_name, column_name, column_type):
    """Adjust an existing column type when the backend supports it."""
    if db.engine.dialect.name != 'mysql':
        return

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    if table_name not in existing_tables:
        return

    existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
    if column_name not in existing_columns:
        return

    with db.engine.begin() as conn:
        conn.execute(text(f'ALTER TABLE {table_name} MODIFY COLUMN {column_name} {column_type}'))
        logger.info('Coluna convertida para %s.%s -> %s', table_name, column_name, column_type)



# Exporta o app para o Gunicorn
app = create_app()

if __name__ == '__main__':
    # Run application
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('SERVER_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    print(f'\n{"="*60} - app.py:190')
    print(f'LiveSun Controller  Plataforma de Gestão Financeira - app.py:191')
    print(f'Servidor rodando em: http://localhost:{port} - app.py:192')
    print(f'{"="*60}\n - app.py:194')
    
    app.run(host=host, port=port, debug=debug)
