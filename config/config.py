import os
from datetime import timedelta
from pathlib import Path

from src.core.database_config import (
    build_database_uri,
    get_db_engine,
    sqlalchemy_engine_options,
)

BASE_DIR = Path(__file__).parent.parent

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload files
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Database (URI centralizada; DB_ENGINE ou DB_TYPE. Alias MYSQL_*/POSTGRES_*/DB_*)
    DB_TYPE = os.environ.get('DB_ENGINE', os.environ.get('DB_TYPE', 'mysql'))
    DB_HOST = os.environ.get('DB_HOST', os.environ.get('MYSQL_HOST', os.environ.get('POSTGRES_HOST', 'localhost')))
    DB_PORT = int(os.environ.get('DB_PORT', os.environ.get('MYSQL_PORT', os.environ.get('POSTGRES_PORT', '3306'))))
    DB_USER = os.environ.get('DB_USER', os.environ.get('MYSQL_USER', os.environ.get('POSTGRES_USER', 'root')))
    DB_PASSWORD = os.environ.get('DB_PASSWORD', os.environ.get('MYSQL_PASSWORD', os.environ.get('POSTGRES_PASSWORD', '')))
    DB_NAME = os.environ.get('DB_NAME', os.environ.get('MYSQL_DATABASE', os.environ.get('POSTGRES_DATABASE', 'comercial')))
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_ENGINE_OPTIONS = sqlalchemy_engine_options(SQLALCHEMY_DATABASE_URI)
    DB_ENGINE = get_db_engine()
    
    # Server
    SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
    
    # Security
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))

    # Asaas (Billing)
    ASAAS_ENABLED = os.environ.get('ASAAS_ENABLED', 'false').lower() == 'true'
    ASAAS_API_KEY = os.environ.get('ASAAS_API_KEY', '')
    ASAAS_BASE_URL = os.environ.get('ASAAS_BASE_URL', 'https://sandbox.asaas.com/api/v3')
    ASAAS_TIMEOUT_SECONDS = int(os.environ.get('ASAAS_TIMEOUT_SECONDS', 15))
    ASAAS_BILLING_TYPE = os.environ.get('ASAAS_BILLING_TYPE', 'BOLETO').upper()
    ASSINATURA_TRIAL_DIAS = int(os.environ.get('ASSINATURA_TRIAL_DIAS', 7))

    # Backoffice comercial (modulo externo ao menu principal)
    BACKOFFICE_ALLOWED_EMAILS = os.environ.get('BACKOFFICE_ALLOWED_EMAILS', '')
    BACKOFFICE_ALLOWED_USERNAMES = os.environ.get('BACKOFFICE_ALLOWED_USERNAMES', '')
    BACKOFFICE_ACCESS_KEY = os.environ.get('BACKOFFICE_ACCESS_KEY', '')

    # NFS-e (XSDs and certificate)
    # Default: use XSDs folder at repository root if present
    NFS_XSD_DIR = os.environ.get('NFS_XSD_DIR', str(BASE_DIR / 'XSD_PL_NFSe_1.00-Produção'))
    NFS_PFX_PATH = os.environ.get('NFS_PFX_PATH', '')
    NFS_PFX = os.environ.get('NFS_PFX', NFS_PFX_PATH)
    NFS_PFX_PASS = os.environ.get('NFS_PFX_PASS', '')
    NFS_VALIDATE_ON_SEND = os.environ.get('NFS_VALIDATE_ON_SEND', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }

# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
