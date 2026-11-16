from datetime import datetime, timezone
from src.models import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CentralVinculo(db.Model):
    __tablename__ = 'central_vinculos_comercial'
    empresa_id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, nullable=False, unique=True)
    payload = db.Column(db.JSON, nullable=False, default=dict)
    assinatura_id = db.Column(db.Integer, nullable=False, default=0)
    versao = db.Column(db.Integer, nullable=False, default=0)
    valido_ate = db.Column(db.DateTime)


class CentralEvento(db.Model):
    __tablename__ = 'central_eventos_comercial'
    evento_id = db.Column(db.String(100), primary_key=True)
    recebido_em = db.Column(db.DateTime, nullable=False, default=utcnow)


class CentralConfiguracao(db.Model):
    __tablename__ = 'central_config_comercial'
    id = db.Column(db.Integer, primary_key=True)
    base_url = db.Column(db.String(500), nullable=False)
    token = db.Column(db.Text, nullable=False)
    hmac_secret = db.Column(db.Text, nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=False)
    cache_ttl = db.Column(db.Integer, nullable=False, default=900)
    purga_habilitada = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())


class CentralCadastroPendente(db.Model):
    __tablename__ = 'central_cadastros_pendentes'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, nullable=False, unique=True)
    evento_id = db.Column(db.String(50), nullable=False, unique=True)
    dados = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(25), nullable=False, default='PENDENTE_ENVIO')
    solicitacao_id = db.Column(db.Integer)
    tentativas = db.Column(db.Integer, nullable=False, default=0)
    erro = db.Column(db.String(100))
    proxima_tentativa = db.Column(db.DateTime, nullable=False, default=utcnow)
    criado_em = db.Column(db.DateTime, nullable=False, default=utcnow)
    vinculado_em = db.Column(db.DateTime)