"""
Modelos SQLAlchemy para o Módulo de Gestão de Contratos de Prestação de Serviços
"""

from datetime import datetime, timezone
from src.models import db


def _utcnow():
    return datetime.now(timezone.utc)


# ============================================================================
# 1. CLÁUSULAS CONTRATO PADRÃO (Biblioteca de Cláusulas)
# ============================================================================

class ClausulaContratoPadrao(db.Model):
    """Biblioteca central de cláusulas padrão que podem ser reutilizadas em múltiplos contratos."""
    __tablename__ = 'clausulas_contrato_padrao'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'codigo', name='uq_clausula_padrao_empresa_codigo'),
        db.Index('idx_clausula_padrao_empresa', 'empresa_id'),
        db.Index('idx_clausula_padrao_tipo', 'tipo'),
        db.Index('idx_clausula_padrao_categoria', 'categoria'),
        db.Index('idx_clausula_padrao_tipo_contrato', 'tipo_contrato'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='clausulas_contrato_padrao')

    # Identificação
    codigo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)

    # Conteúdo
    texto_base = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.Text)

    # Configuração
    tipo = db.Column(db.String(20), nullable=False, default='opcional')  # 'obrigatoria', 'opcional', 'condicional'
    editavel = db.Column(db.Boolean, nullable=False, default=True)
    ordem_padrao = db.Column(db.Integer, nullable=False, default=0)

    # Categorização
    categoria = db.Column(db.String(50))  # 'geral', 'financeiro', 'juridico', 'tecnico', 'trabalhista'
    tipo_contrato = db.Column(db.String(50))  # 'prestacao_servicos', 'fornecimento', 'parceria'

    # Controle
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    criado_por = db.relationship('User', foreign_keys=[criado_por_user_id])
    criado_em = db.Column(db.DateTime, nullable=False, default=_utcnow)
    atualizado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    atualizado_por = db.relationship('User', foreign_keys=[atualizado_por_user_id])
    atualizado_em = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<ClausulaContratoPadrao {self.codigo}>'


# ============================================================================
# 2. CONTRATOS (Contratos de Prestação de Serviços)
# ============================================================================

class Contrato(db.Model):
    """Registro principal de contratos de prestação de serviços gerados a partir de orçamentos."""
    __tablename__ = 'contratos'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'numero', 'serie', name='uq_contrato_empresa_numero_serie'),
        db.Index('idx_contrato_empresa', 'empresa_id'),
        db.Index('idx_contrato_orcamento', 'orcamento_id'),
        db.Index('idx_contrato_cliente', 'cliente_id'),
        db.Index('idx_contrato_status', 'status'),
        db.Index('idx_contrato_vigencia', 'data_inicio_vigencia', 'data_fim_vigencia'),
        db.Index('idx_contrato_numero', 'numero'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='contratos')

    # Identificação
    numero = db.Column(db.String(50), nullable=False)
    serie = db.Column(db.String(10), default='CTR')
    titulo = db.Column(db.String(200))

    # Vinculação
    orcamento_id = db.Column(db.Integer, db.ForeignKey('orcamentos.id'))
    orcamento = db.relationship('Orcamento', backref='contratos')
    cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False)
    cliente = db.relationship('Entidade', foreign_keys=[cliente_id], backref='contratos_cliente')
    vendedor_id = db.Column(db.Integer, db.ForeignKey('entidades.id'))
    vendedor = db.relationship('Entidade', foreign_keys=[vendedor_id], backref='contratos_vendedor')

    # Dados das partes
    contratada_entidade_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False)  # Empresa prestadora
    contratada = db.relationship('Entidade', foreign_keys=[contratada_entidade_id], backref='contratos_contratada')
    contratante_entidade_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False)  # Cliente
    contratante = db.relationship('Entidade', foreign_keys=[contratante_entidade_id], backref='contratos_contratante')

    # Dados comerciais
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)
    valor_mensal = db.Column(db.Numeric(15, 2))
    forma_pagamento = db.Column(db.String(100))
    periodicidade = db.Column(db.String(50))  # 'mensal', 'trimestral', 'semestral', 'anual', 'unico'
    data_inicio_vigencia = db.Column(db.Date, nullable=False)
    data_fim_vigencia = db.Column(db.Date)

    # Status e controle
    status = db.Column(db.String(30), nullable=False, default='rascunho')  # 'rascunho', 'aguardando_assinatura', 'assinado', 'cancelado', 'rescindido'
    motivo_cancelamento = db.Column(db.Text)

    # Descrição dos serviços
    descricao_servicos = db.Column(db.Text)
    objeto_contrato = db.Column(db.Text)

    # Metadados
    data_geracao = db.Column(db.DateTime, nullable=False, default=_utcnow)
    data_assinatura = db.Column(db.Date)
    gerado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gerado_por = db.relationship('User', foreign_keys=[gerado_por_user_id])
    assinado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assinado_por = db.relationship('User', foreign_keys=[assinado_por_user_id])

    criado_em = db.Column(db.DateTime, nullable=False, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<Contrato {self.numero}>'


# ============================================================================
# 3. CONTRATO_CLÁUSULAS (Instâncias de Cláusulas no Contrato)
# ============================================================================

class ContratoClausula(db.Model):
    """Cada cláusula incluída em um contrato específico, com seu texto personalizado."""
    __tablename__ = 'contrato_clausulas'
    __table_args__ = (
        db.UniqueConstraint('contrato_id', 'ordem', name='uq_contrato_clausula_ordem'),
        db.Index('idx_contrato_clausula_contrato', 'contrato_id'),
        db.Index('idx_contrato_clausula_padrao', 'clausula_padrao_id'),
        db.Index('idx_contrato_clausula_ordem', 'contrato_id', 'ordem'),
    )

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'), nullable=False)
    contrato = db.relationship('Contrato', backref=db.backref('clausulas', cascade='all, delete-orphan'))

    # Referência à cláusula padrão
    clausula_padrao_id = db.Column(db.Integer, db.ForeignKey('clausulas_contrato_padrao.id'))
    clausula_padrao = db.relationship('ClausulaContratoPadrao', backref='instancias')

    # Dados da cláusula no contrato
    titulo = db.Column(db.String(200), nullable=False)
    texto = db.Column(db.Text, nullable=False)

    # Configuração
    ordem = db.Column(db.Integer, nullable=False)
    editavel = db.Column(db.Boolean, nullable=False, default=True)
    obrigatoria = db.Column(db.Boolean, nullable=False, default=False)

    # Controle de alterações
    alterado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    alterado_por = db.relationship('User', foreign_keys=[alterado_por_user_id])
    data_alteracao = db.Column(db.DateTime)

    criado_em = db.Column(db.DateTime, nullable=False, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<ContratoClausula {self.titulo}>'


# ============================================================================
# 4. CONTRATO_HISTÓRICO (Versionamento de Contratos)
# ============================================================================

class ContratoHistorico(db.Model):
    """Histórico de alterações do contrato para auditoria e rastreabilidade."""
    __tablename__ = 'contrato_historico'
    __table_args__ = (
        db.UniqueConstraint('contrato_id', 'versao', name='uq_contrato_historico_versao'),
        db.Index('idx_contrato_historico_contrato', 'contrato_id'),
        db.Index('idx_contrato_historico_data', 'data_alteracao'),
        db.Index('idx_contrato_historico_acao', 'acao'),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'), nullable=False)
    contrato = db.relationship('Contrato', backref=db.backref('historico', cascade='all, delete-orphan'))

    # Versão
    versao = db.Column(db.Integer, nullable=False)
    acao = db.Column(db.String(50), nullable=False)  # 'criado', 'editado', 'assinado', 'cancelado', 'rescindido'

    # Estado do contrato naquele momento
    status_anterior = db.Column(db.String(20))
    status_novo = db.Column(db.String(20))

    # Detalhes da alteração
    descricao_alteracao = db.Column(db.Text)
    campos_alterados = db.Column(db.JSON)  # Lista de campos que foram alterados
    clausulas_alteradas = db.Column(db.JSON)  # Lista de cláusulas alteradas

    # Quem fez a alteração
    alterado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    alterado_por = db.relationship('User', foreign_keys=[alterado_por_user_id])
    data_alteracao = db.Column(db.DateTime, nullable=False, default=_utcnow)

    # Snapshot opcional do contrato completo
    snapshot_contrato = db.Column(db.JSON)

    def __repr__(self):
        return f'<ContratoHistorico v{self.versao} - {self.acao}>'


# ============================================================================
# 5. CONTRATO_ANEXOS (Anexos do Contrato)
# ============================================================================

class ContratoAnexo(db.Model):
    """Arquivos anexados ao contrato (PDF assinado, documentos complementares, etc.)."""
    __tablename__ = 'contrato_anexos'
    __table_args__ = (
        db.Index('idx_contrato_anexo_contrato', 'contrato_id'),
        db.Index('idx_contrato_anexo_tipo', 'tipo_anexo'),
    )

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'), nullable=False)
    contrato = db.relationship('Contrato', backref=db.backref('anexos', cascade='all, delete-orphan'))

    # Arquivo
    nome_arquivo = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(100), nullable=False)  # 'pdf', 'docx', 'jpg', etc.
    tamanho_bytes = db.Column(db.BigInteger)
    caminho_arquivo = db.Column(db.String(500), nullable=False)

    # Descrição
    descricao = db.Column(db.String(255))
    tipo_anexo = db.Column(db.String(50), nullable=False)  # 'contrato_assinado', 'documento_identificacao', 'comprovante', 'outro'

    # Controle
    criado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    criado_por = db.relationship('User', foreign_keys=[criado_por_user_id])
    criado_em = db.Column(db.DateTime, nullable=False, default=_utcnow)

    def __repr__(self):
        return f'<ContratoAnexo {self.nome_arquivo}>'


# ============================================================================
# 6. CONTRATO_PARÂMETROS (Parâmetros de Substituição)
# ============================================================================

class ContratoParametro(db.Model):
    """Definição de parâmetros/variáveis que podem ser usados nas cláusulas para substituição dinâmica."""
    __tablename__ = 'contrato_parametros'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'codigo', name='uq_contrato_parametro_empresa_codigo'),
        db.Index('idx_contrato_parametro_empresa', 'empresa_id'),
        db.Index('idx_contrato_parametro_origem', 'origem'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='contrato_parametros')

    # Identificação
    codigo = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)

    # Configuração
    tipo_dado = db.Column(db.String(20), nullable=False, default='texto')  # 'texto', 'numero', 'data', 'moeda', 'boolean'
    valor_padrao = db.Column(db.Text)
    origem = db.Column(db.String(50))  # 'empresa', 'cliente', 'orcamento', 'manual'

    # Controle
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<ContratoParametro {self.codigo}>'


# ============================================================================
# 7. CONTRATO_PARÂMETROS_VALORES (Valores de Parâmetros por Contrato)
# ============================================================================

class ContratoParametroValor(db.Model):
    """Valores específicos dos parâmetros para cada contrato."""
    __tablename__ = 'contrato_parametros_valores'
    __table_args__ = (
        db.UniqueConstraint('contrato_id', 'parametro_id', name='uq_contrato_parametro_valor'),
        db.Index('idx_contrato_parametro_valor_contrato', 'contrato_id'),
        db.Index('idx_contrato_parametro_valor_parametro', 'parametro_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'), nullable=False)
    contrato = db.relationship('Contrato', backref=db.backref('parametros_valores', cascade='all, delete-orphan'))
    parametro_id = db.Column(db.Integer, db.ForeignKey('contrato_parametros.id'), nullable=False)
    parametro = db.relationship('ContratoParametro', backref='valores')

    valor = db.Column(db.Text, nullable=False)

    criado_em = db.Column(db.DateTime, nullable=False, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<ContratoParametroValor {self.parametro.codigo}={self.valor}>'
