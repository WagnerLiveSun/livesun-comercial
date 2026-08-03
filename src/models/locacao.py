"""
Modelos para o módulo de Locação de Roupas e Fantasias
Estrutura completa com Acervo, Disponibilidade, Contratos, Operação e Financeiro
"""

from datetime import datetime, timezone
from decimal import Decimal
from src.models import db

def _utcnow():
    return datetime.now(timezone.utc)


# ============================================================================
# 1. CADASTRO DO ACERVO
# ============================================================================

class LocacaoPeca(db.Model):
    """Peça, fantasia ou acessório no acervo de locação"""
    __tablename__ = 'locacao_pecas'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'codigo_interno', name='uq_locacao_peca_codigo'),
        db.Index('idx_locacao_peca_empresa_ativo', 'empresa_id', 'ativo'),
        db.Index('idx_locacao_peca_empresa_categoria', 'empresa_id', 'categoria'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_pecas')

    filial_id = db.Column(db.Integer, db.ForeignKey('filiais.id'), nullable=True, index=True)
    filial = db.relationship('Filial', foreign_keys=[filial_id])

    # Identificação
    codigo_interno = db.Column(db.String(50), nullable=False, index=True)
    codigo_barras = db.Column(db.String(50), nullable=True, index=True)
    qr_code = db.Column(db.String(255), nullable=True)
    
    # Descrição
    descricao = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(100), nullable=False, index=True)  # Vestido, Fantasia, Acessório, etc
    tema = db.Column(db.String(100), nullable=True)  # Carnaval, Halloween, Festa, etc
    
    # Características físicas
    tamanho = db.Column(db.String(20), nullable=True)  # P, M, G, GG, Único, etc
    cor = db.Column(db.String(50), nullable=True)
    tecido = db.Column(db.String(100), nullable=True)
    marca_colecao = db.Column(db.String(100), nullable=True)
    
    # Localização
    localizacao_fisica = db.Column(db.String(100), nullable=True)  # Prateleira, Armário, etc
    
    # Valores
    valor_aquisicao = db.Column(db.Numeric(15, 2), nullable=False)
    valor_reposicao = db.Column(db.Numeric(15, 2), nullable=False)  # Valor para substituição se perdida
    preco_aluguel_diario = db.Column(db.Numeric(15, 2), nullable=False)
    preco_venda = db.Column(db.Numeric(15, 2), nullable=True)  # Se permitir venda
    
    # Estado físico
    estado_fisico = db.Column(db.String(20), default='novo')  # novo, bom, regular, ruim, descartado
    
    # Controle
    ativo = db.Column(db.Boolean, default=True, index=True)
    serializado = db.Column(db.Boolean, default=True)  # True = item único, False = por grade
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoPeca {self.codigo_interno} - {self.descricao}>'


class LocacaoKit(db.Model):
    """Kit/Conjunto de peças para aluguel (ex: fantasia completa com acessórios)"""
    __tablename__ = 'locacao_kits'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'codigo_interno', name='uq_locacao_kit_codigo'),
        db.Index('idx_locacao_kit_empresa_ativo', 'empresa_id', 'ativo'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_kits')

    filial_id = db.Column(db.Integer, db.ForeignKey('filiais.id'), nullable=True, index=True)
    filial = db.relationship('Filial', foreign_keys=[filial_id])

    # Identificação
    codigo_interno = db.Column(db.String(50), nullable=False, index=True)
    descricao = db.Column(db.String(255), nullable=False)
    tema = db.Column(db.String(100), nullable=True)
    
    # Valores
    preco_aluguel_diario = db.Column(db.Numeric(15, 2), nullable=False)
    preco_venda = db.Column(db.Numeric(15, 2), nullable=True)
    
    # Controle
    ativo = db.Column(db.Boolean, default=True, index=True)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoKit {self.codigo_interno}>'


class LocacaoKitItem(db.Model):
    """Itens que compõem um kit de locação"""
    __tablename__ = 'locacao_kit_itens'
    __table_args__ = (
        db.UniqueConstraint('kit_id', 'peca_id', name='uq_locacao_kit_peca'),
        db.Index('idx_locacao_kit_item_kit', 'kit_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_kit_itens')

    kit_id = db.Column(db.Integer, db.ForeignKey('locacao_kits.id', ondelete='CASCADE'), nullable=False)
    kit = db.relationship('LocacaoKit', backref=db.backref('itens', cascade='all, delete-orphan', passive_deletes=True))

    peca_id = db.Column(db.Integer, db.ForeignKey('locacao_pecas.id'), nullable=False)
    peca = db.relationship('LocacaoPeca', foreign_keys=[peca_id])

    quantidade = db.Column(db.Integer, default=1)
    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoKitItem kit={self.kit_id} peca={self.peca_id}>'


# ============================================================================
# 2. DISPONIBILIDADE E AGENDA
# ============================================================================

class LocacaoDisponibilidade(db.Model):
    """Controle de disponibilidade de peças por período"""
    __tablename__ = 'locacao_disponibilidade'
    __table_args__ = (
        db.UniqueConstraint('peca_id', 'data_inicio', 'data_fim', name='uq_locacao_disp_peca_periodo'),
        db.Index('idx_locacao_disp_peca_data', 'peca_id', 'data_inicio', 'data_fim'),
        db.Index('idx_locacao_disp_empresa_data', 'empresa_id', 'data_inicio', 'data_fim'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_disponibilidades')

    peca_id = db.Column(db.Integer, db.ForeignKey('locacao_pecas.id'), nullable=False, index=True)
    peca = db.relationship('LocacaoPeca', backref='disponibilidades')

    # Período de bloqueio/indisponibilidade
    data_inicio = db.Column(db.Date, nullable=False, index=True)
    data_fim = db.Column(db.Date, nullable=False, index=True)

    # Motivo do bloqueio
    motivo = db.Column(db.String(50), nullable=False)  # reserva, manutencao, limpeza, avaria, extravio
    
    # Referências
    reserva_id = db.Column(db.Integer, db.ForeignKey('locacao_reservas.id'), nullable=True)
    reserva = db.relationship('LocacaoReserva', foreign_keys=[reserva_id])
    
    manutencao_id = db.Column(db.Integer, db.ForeignKey('locacao_manutencoes.id'), nullable=True)
    manutencao = db.relationship('LocacaoManutencao', foreign_keys=[manutencao_id])

    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoDisponibilidade peca={self.peca_id} {self.data_inicio} a {self.data_fim}>'


class LocacaoParametro(db.Model):
    """Parâmetros de configuração para locação (buffers, multas, etc)"""
    __tablename__ = 'locacao_parametros'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'chave', name='uq_locacao_param_empresa_chave'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_parametros')

    chave = db.Column(db.String(100), nullable=False)  # dias_buffer_antes, dias_buffer_depois, multa_atraso_diaria, etc
    valor = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), default='string')  # string, numeric, boolean
    descricao = db.Column(db.String(255), nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoParametro {self.chave}={self.valor}>'


# ============================================================================
# 3. COMERCIAL - ORÇAMENTO, RESERVA E CONTRATO
# ============================================================================

class LocacaoEvento(db.Model):
    """Evento associado a uma locação (casamento, festa, etc)"""
    __tablename__ = 'locacao_eventos'
    __table_args__ = (
        db.Index('idx_locacao_evento_empresa_cliente', 'empresa_id', 'cliente_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_eventos')

    cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    cliente = db.relationship('Entidade', foreign_keys=[cliente_id])

    # Informações do evento
    tipo_evento = db.Column(db.String(100), nullable=False)  # Casamento, Festa, Carnaval, etc
    data_evento = db.Column(db.Date, nullable=False, index=True)
    local = db.Column(db.String(255), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoEvento {self.tipo_evento} - {self.data_evento}>'


class LocacaoOrcamento(db.Model):
    """Orçamento de locação com validade"""
    __tablename__ = 'locacao_orcamentos'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'numero', name='uq_locacao_orcamento_numero'),
        db.Index('idx_locacao_orcamento_empresa_cliente', 'empresa_id', 'cliente_id'),
        db.Index('idx_locacao_orcamento_empresa_status', 'empresa_id', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_orcamentos')

    filial_id = db.Column(db.Integer, db.ForeignKey('filiais.id'), nullable=True, index=True)
    filial = db.relationship('Filial', foreign_keys=[filial_id])

    cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    cliente = db.relationship('Entidade', foreign_keys=[cliente_id], backref='locacao_orcamentos')

    evento_id = db.Column(db.Integer, db.ForeignKey('locacao_eventos.id'), nullable=True)
    evento = db.relationship('LocacaoEvento', foreign_keys=[evento_id])

    # Identificação
    numero = db.Column(db.String(50), nullable=False, index=True)
    data_emissao = db.Column(db.Date, nullable=False, index=True)
    data_validade = db.Column(db.Date, nullable=False, index=True)

    # Período de locação
    data_retirada_prevista = db.Column(db.Date, nullable=False)
    data_devolucao_prevista = db.Column(db.Date, nullable=False)
    dias_locacao = db.Column(db.Integer, nullable=False)

    # Valores
    valor_aluguel = db.Column(db.Numeric(15, 2), nullable=False)
    valor_desconto = db.Column(db.Numeric(15, 2), default=0.00)
    valor_acrescimo = db.Column(db.Numeric(15, 2), default=0.00)
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)

    # Caução e sinal
    valor_sinal = db.Column(db.Numeric(15, 2), default=0.00)
    percentual_sinal = db.Column(db.Numeric(5, 2), nullable=True)  # Se for percentual
    valor_caucao = db.Column(db.Numeric(15, 2), default=0.00)
    percentual_caucao = db.Column(db.Numeric(5, 2), nullable=True)

    # Status
    status = db.Column(db.String(20), default='rascunho')  # rascunho, enviado, aprovado, rejeitado, convertido
    observacoes = db.Column(db.Text, nullable=True)

    # Rastreabilidade
    criado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    criado_por = db.relationship('User', foreign_keys=[criado_por_user_id])

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoOrcamento {self.numero}>'


class LocacaoOrcamentoItem(db.Model):
    """Itens do orçamento de locação"""
    __tablename__ = 'locacao_orcamento_itens'
    __table_args__ = (
        db.Index('idx_locacao_orcamento_item_orcamento', 'orcamento_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_orcamento_itens')

    orcamento_id = db.Column(db.Integer, db.ForeignKey('locacao_orcamentos.id', ondelete='CASCADE'), nullable=False)
    orcamento = db.relationship('LocacaoOrcamento', backref=db.backref('itens', cascade='all, delete-orphan', passive_deletes=True))

    # Tipo de item
    tipo_item = db.Column(db.String(1), nullable=False)  # P = peça avulsa, K = kit
    
    peca_id = db.Column(db.Integer, db.ForeignKey('locacao_pecas.id'), nullable=True)
    peca = db.relationship('LocacaoPeca', foreign_keys=[peca_id])

    kit_id = db.Column(db.Integer, db.ForeignKey('locacao_kits.id'), nullable=True)
    kit = db.relationship('LocacaoKit', foreign_keys=[kit_id])

    # Descrição
    descricao = db.Column(db.String(255), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    
    # Valores
    valor_unitario = db.Column(db.Numeric(15, 2), nullable=False)
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoOrcamentoItem orcamento={self.orcamento_id}>'


class LocacaoReserva(db.Model):
    """Reserva confirmada de locação (conversão de orçamento)"""
    __tablename__ = 'locacao_reservas'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'numero', name='uq_locacao_reserva_numero'),
        db.Index('idx_locacao_reserva_empresa_cliente', 'empresa_id', 'cliente_id'),
        db.Index('idx_locacao_reserva_empresa_status', 'empresa_id', 'status'),
        db.Index('idx_locacao_reserva_empresa_datas', 'empresa_id', 'data_retirada', 'data_devolucao'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_reservas')

    filial_id = db.Column(db.Integer, db.ForeignKey('filiais.id'), nullable=True, index=True)
    filial = db.relationship('Filial', foreign_keys=[filial_id])

    cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    cliente = db.relationship('Entidade', foreign_keys=[cliente_id], backref='locacao_reservas')

    evento_id = db.Column(db.Integer, db.ForeignKey('locacao_eventos.id'), nullable=True)
    evento = db.relationship('LocacaoEvento', foreign_keys=[evento_id])

    orcamento_id = db.Column(db.Integer, db.ForeignKey('locacao_orcamentos.id'), nullable=True, unique=True)
    orcamento = db.relationship('LocacaoOrcamento', foreign_keys=[orcamento_id])

    # Identificação
    numero = db.Column(db.String(50), nullable=False, index=True)
    data_reserva = db.Column(db.Date, nullable=False, index=True)

    # Período de locação
    data_retirada = db.Column(db.Date, nullable=False, index=True)
    data_devolucao = db.Column(db.Date, nullable=False, index=True)
    dias_locacao = db.Column(db.Integer, nullable=False)

    # Valores
    valor_aluguel = db.Column(db.Numeric(15, 2), nullable=False)
    valor_desconto = db.Column(db.Numeric(15, 2), default=0.00)
    valor_acrescimo = db.Column(db.Numeric(15, 2), default=0.00)
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)

    # Caução e sinal
    valor_sinal_pago = db.Column(db.Numeric(15, 2), default=0.00)
    valor_caucao_retida = db.Column(db.Numeric(15, 2), default=0.00)

    # Status
    status = db.Column(db.String(20), default='confirmada')  # confirmada, retirada, devolvida, cancelada
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)

    # Rastreabilidade
    criado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    criado_por = db.relationship('User', foreign_keys=[criado_por_user_id])

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoReserva {self.numero}>'


class LocacaoContrato(db.Model):
    """Contrato formal de locação com cláusulas"""
    __tablename__ = 'locacao_contratos'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'numero', name='uq_locacao_contrato_numero'),
        db.Index('idx_locacao_contrato_empresa_cliente', 'empresa_id', 'cliente_id'),
        db.Index('idx_locacao_contrato_empresa_status', 'empresa_id', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_contratos')

    filial_id = db.Column(db.Integer, db.ForeignKey('filiais.id'), nullable=True, index=True)
    filial = db.relationship('Filial', foreign_keys=[filial_id])

    cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    cliente = db.relationship('Entidade', foreign_keys=[cliente_id], backref='locacao_contratos')

    reserva_id = db.Column(db.Integer, db.ForeignKey('locacao_reservas.id'), nullable=False, unique=True)
    reserva = db.relationship('LocacaoReserva', foreign_keys=[reserva_id])

    evento_id = db.Column(db.Integer, db.ForeignKey('locacao_eventos.id'), nullable=True)
    evento = db.relationship('LocacaoEvento', foreign_keys=[evento_id])

    # Identificação
    numero = db.Column(db.String(50), nullable=False, index=True)
    data_contrato = db.Column(db.Date, nullable=False, index=True)

    # Período
    data_retirada = db.Column(db.Date, nullable=False)
    data_devolucao = db.Column(db.Date, nullable=False)

    # Valores
    valor_aluguel = db.Column(db.Numeric(15, 2), nullable=False)
    valor_sinal = db.Column(db.Numeric(15, 2), default=0.00)
    valor_caucao = db.Column(db.Numeric(15, 2), default=0.00)
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)

    # Cláusulas e termos
    multa_atraso_diaria = db.Column(db.Numeric(15, 2), nullable=True)
    multa_avaria_percentual = db.Column(db.Numeric(5, 2), nullable=True)
    multa_perda_percentual = db.Column(db.Numeric(5, 2), nullable=True)
    condicoes_gerais = db.Column(db.Text, nullable=True)

    # Status
    status = db.Column(db.String(20), default='assinado')  # assinado, ativo, finalizado, cancelado
    
    # Assinatura
    assinado_em = db.Column(db.DateTime, nullable=True)
    assinado_por_cliente = db.Column(db.Boolean, default=False)
    assinado_por_empresa = db.Column(db.Boolean, default=False)

    # Rastreabilidade
    criado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    criado_por = db.relationship('User', foreign_keys=[criado_por_user_id])

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoContrato {self.numero}>'


# ============================================================================
# 4. OPERAÇÃO - RETIRADA E DEVOLUÇÃO
# ============================================================================

class LocacaoRetirada(db.Model):
    """Registro de retirada de peças"""
    __tablename__ = 'locacao_retiradas'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'numero', name='uq_locacao_retirada_numero'),
        db.Index('idx_locacao_retirada_empresa_contrato', 'empresa_id', 'contrato_id'),
        db.Index('idx_locacao_retirada_empresa_data', 'empresa_id', 'data_retirada'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_retiradas')

    contrato_id = db.Column(db.Integer, db.ForeignKey('locacao_contratos.id'), nullable=False, index=True)
    contrato = db.relationship('LocacaoContrato', backref='retiradas')

    # Identificação
    numero = db.Column(db.String(50), nullable=False, index=True)
    data_retirada = db.Column(db.DateTime, nullable=False, index=True)

    # Responsável
    responsavel_retirada = db.Column(db.String(150), nullable=True)
    user_retirada_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_retirada = db.relationship('User', foreign_keys=[user_retirada_id])

    # Modo de retirada
    modo_retirada = db.Column(db.String(20), nullable=False)  # balcao, entrega
    observacoes = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), default='registrada')  # registrada, confirmada

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoRetirada {self.numero}>'


class LocacaoRetiradaItem(db.Model):
    """Itens retirados"""
    __tablename__ = 'locacao_retirada_itens'
    __table_args__ = (
        db.Index('idx_locacao_retirada_item_retirada', 'retirada_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_retirada_itens')

    retirada_id = db.Column(db.Integer, db.ForeignKey('locacao_retiradas.id', ondelete='CASCADE'), nullable=False)
    retirada = db.relationship('LocacaoRetirada', backref=db.backref('itens', cascade='all, delete-orphan', passive_deletes=True))

    peca_id = db.Column(db.Integer, db.ForeignKey('locacao_pecas.id'), nullable=True)
    peca = db.relationship('LocacaoPeca', foreign_keys=[peca_id])

    kit_id = db.Column(db.Integer, db.ForeignKey('locacao_kits.id'), nullable=True)
    kit = db.relationship('LocacaoKit', foreign_keys=[kit_id])

    quantidade = db.Column(db.Integer, default=1)
    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f'<LocacaoRetiradaItem retirada={self.retirada_id}>'


class LocacaoDevolucao(db.Model):
    """Registro de devolução de peças"""
    __tablename__ = 'locacao_devolucoes'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'numero', name='uq_locacao_devolucao_numero'),
        db.Index('idx_locacao_devolucao_empresa_contrato', 'empresa_id', 'contrato_id'),
        db.Index('idx_locacao_devolucao_empresa_data', 'empresa_id', 'data_devolucao'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_devolucoes')

    contrato_id = db.Column(db.Integer, db.ForeignKey('locacao_contratos.id'), nullable=False, index=True)
    contrato = db.relationship('LocacaoContrato', backref='devolucoes')

    # Identificação
    numero = db.Column(db.String(50), nullable=False, index=True)
    data_devolucao = db.Column(db.DateTime, nullable=False, index=True)
    data_devolucao_prevista = db.Column(db.Date, nullable=False)

    # Responsável
    responsavel_devolucao = db.Column(db.String(150), nullable=True)
    user_devolucao_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_devolucao = db.relationship('User', foreign_keys=[user_devolucao_id])

    # Atraso
    dias_atraso = db.Column(db.Integer, default=0)
    multa_atraso = db.Column(db.Numeric(15, 2), default=0.00)

    # Tipo de devolução
    tipo_devolucao = db.Column(db.String(20), nullable=False)  # total, parcial
    observacoes = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), default='registrada')  # registrada, inspecionada, liberada

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoDevolucao {self.numero}>'


class LocacaoInspecao(db.Model):
    """Inspeção de peças devolvidas"""
    __tablename__ = 'locacao_inspecoes'
    __table_args__ = (
        db.Index('idx_locacao_inspecao_devolucao', 'devolucao_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_inspecoes')

    devolucao_id = db.Column(db.Integer, db.ForeignKey('locacao_devolucoes.id', ondelete='CASCADE'), nullable=False)
    devolucao = db.relationship('LocacaoDevolucao', backref=db.backref('inspecoes', cascade='all, delete-orphan', passive_deletes=True))

    peca_id = db.Column(db.Integer, db.ForeignKey('locacao_pecas.id'), nullable=False)
    peca = db.relationship('LocacaoPeca', foreign_keys=[peca_id])

    # Classificação
    classificacao = db.Column(db.String(20), nullable=False)  # ok, sujo, avariado, faltante, perdido
    
    # Valores de cobrança
    valor_limpeza = db.Column(db.Numeric(15, 2), default=0.00)
    valor_reparo = db.Column(db.Numeric(15, 2), default=0.00)
    valor_reposicao = db.Column(db.Numeric(15, 2), default=0.00)  # Se perdida/extraviada
    valor_total_cobranca = db.Column(db.Numeric(15, 2), default=0.00)

    observacoes = db.Column(db.Text, nullable=True)

    # Encaminhamento
    encaminhamento = db.Column(db.String(50), nullable=True)  # higienizacao, manutencao, descarte
    manutencao_id = db.Column(db.Integer, db.ForeignKey('locacao_manutencoes.id'), nullable=True)
    manutencao = db.relationship('LocacaoManutencao', foreign_keys=[manutencao_id])

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoInspecao peca={self.peca_id} classificacao={self.classificacao}>'


# ============================================================================
# 5. MANUTENÇÃO E HIGIENIZAÇÃO
# ============================================================================

class LocacaoManutencao(db.Model):
    """Registro de manutenção, limpeza ou reparo de peças"""
    __tablename__ = 'locacao_manutencoes'
    __table_args__ = (
        db.Index('idx_locacao_manutencao_empresa_peca', 'empresa_id', 'peca_id'),
        db.Index('idx_locacao_manutencao_empresa_status', 'empresa_id', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_manutencoes')

    peca_id = db.Column(db.Integer, db.ForeignKey('locacao_pecas.id'), nullable=False, index=True)
    peca = db.relationship('LocacaoPeca', backref='manutencoes')

    # Tipo de serviço
    tipo_servico = db.Column(db.String(50), nullable=False)  # higienizacao, reparo, manutencao_preventiva
    
    # Datas
    data_entrada = db.Column(db.Date, nullable=False, index=True)
    data_saida_prevista = db.Column(db.Date, nullable=True)
    data_saida = db.Column(db.Date, nullable=True)

    # Valores
    valor_servico = db.Column(db.Numeric(15, 2), default=0.00)
    valor_material = db.Column(db.Numeric(15, 2), default=0.00)
    valor_total = db.Column(db.Numeric(15, 2), default=0.00)

    # Status
    status = db.Column(db.String(20), default='pendente')  # pendente, em_andamento, concluida, cancelada

    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoManutencao peca={self.peca_id} tipo={self.tipo_servico}>'


# ============================================================================
# 6. FINANCEIRO - TÍTULOS E COBRANÇAS
# ============================================================================

class LocacaoTitulo(db.Model):
    """Título financeiro gerado a partir de contrato/pedido de locação"""
    __tablename__ = 'locacao_titulos'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'numero', name='uq_locacao_titulo_numero'),
        db.Index('idx_locacao_titulo_empresa_contrato', 'empresa_id', 'contrato_id'),
        db.Index('idx_locacao_titulo_empresa_status', 'empresa_id', 'status'),
        db.Index('idx_locacao_titulo_empresa_vencimento', 'empresa_id', 'data_vencimento'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_titulos')

    contrato_id = db.Column(db.Integer, db.ForeignKey('locacao_contratos.id'), nullable=False, index=True)
    contrato = db.relationship('LocacaoContrato', backref='titulos')

    cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    cliente = db.relationship('Entidade', foreign_keys=[cliente_id], backref='locacao_titulos')

    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id'), nullable=True, unique=True)
    lancamento = db.relationship('Lancamento', foreign_keys=[lancamento_id])

    # Identificação
    numero = db.Column(db.String(50), nullable=False, index=True)
    tipo_titulo = db.Column(db.String(50), nullable=False)  # sinal, caucao, saldo, multa, avaria, venda_complementar, estorno
    
    # Datas
    data_emissao = db.Column(db.Date, nullable=False, index=True)
    data_vencimento = db.Column(db.Date, nullable=False, index=True)
    data_pagamento = db.Column(db.Date, nullable=True)

    # Valores
    valor_original = db.Column(db.Numeric(15, 2), nullable=False)
    valor_pago = db.Column(db.Numeric(15, 2), default=0.00)
    valor_aberto = db.Column(db.Numeric(15, 2), nullable=False)

    # Status
    status = db.Column(db.String(20), default='aberto')  # aberto, pago, vencido, cancelado, estornado
    
    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoTitulo {self.numero}>'


class LocacaoCobranca(db.Model):
    """Cobrança adicional por atraso, avaria, perda ou limpeza extra"""
    __tablename__ = 'locacao_cobrancas'
    __table_args__ = (
        db.Index('idx_locacao_cobranca_empresa_contrato', 'empresa_id', 'contrato_id'),
        db.Index('idx_locacao_cobranca_empresa_tipo', 'empresa_id', 'tipo_cobranca'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_cobrancas')

    contrato_id = db.Column(db.Integer, db.ForeignKey('locacao_contratos.id'), nullable=False, index=True)
    contrato = db.relationship('LocacaoContrato', backref='cobrancas')

    inspecao_id = db.Column(db.Integer, db.ForeignKey('locacao_inspecoes.id'), nullable=True)
    inspecao = db.relationship('LocacaoInspecao', foreign_keys=[inspecao_id])

    titulo_id = db.Column(db.Integer, db.ForeignKey('locacao_titulos.id'), nullable=True)
    titulo = db.relationship('LocacaoTitulo', foreign_keys=[titulo_id])

    # Tipo de cobrança
    tipo_cobranca = db.Column(db.String(50), nullable=False)  # atraso, avaria, perda, limpeza, outro
    
    # Valores
    valor_cobranca = db.Column(db.Numeric(15, 2), nullable=False)
    valor_pago = db.Column(db.Numeric(15, 2), default=0.00)
    
    # Status
    status = db.Column(db.String(20), default='pendente')  # pendente, pago, cancelado

    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoCobranca {self.tipo_cobranca}>'


class LocacaoDevolucaoCaucao(db.Model):
    """Registro de devolução de caução ao cliente"""
    __tablename__ = 'locacao_devolucao_caucao'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'contrato_id', name='uq_locacao_dev_caucao_contrato'),
        db.Index('idx_locacao_dev_caucao_empresa_contrato', 'empresa_id', 'contrato_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_devolucoes_caucao')

    contrato_id = db.Column(db.Integer, db.ForeignKey('locacao_contratos.id'), nullable=False, index=True)
    contrato = db.relationship('LocacaoContrato', backref='devolucoes_caucao')

    cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    cliente = db.relationship('Entidade', foreign_keys=[cliente_id])

    titulo_id = db.Column(db.Integer, db.ForeignKey('locacao_titulos.id'), nullable=True)
    titulo = db.relationship('LocacaoTitulo', foreign_keys=[titulo_id])

    # Valores
    valor_caucao_original = db.Column(db.Numeric(15, 2), nullable=False)
    valor_descontos = db.Column(db.Numeric(15, 2), default=0.00)  # Descontos por avaria, etc
    valor_devolucao = db.Column(db.Numeric(15, 2), nullable=False)

    # Datas
    data_devolucao_prevista = db.Column(db.Date, nullable=False)
    data_devolucao_efetiva = db.Column(db.Date, nullable=True)

    status = db.Column(db.String(20), default='pendente')  # pendente, processando, devolvida, cancelada

    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoDevolucaoCaucao contrato={self.contrato_id}>'


# ============================================================================
# 7. FATURAMENTO
# ============================================================================

class LocacaoFaturamento(db.Model):
    """Registro de faturamento de locação"""
    __tablename__ = 'locacao_faturamentos'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'numero_documento', name='uq_locacao_faturamento_numero'),
        db.Index('idx_locacao_faturamento_empresa_contrato', 'empresa_id', 'contrato_id'),
        db.Index('idx_locacao_faturamento_empresa_data', 'empresa_id', 'data_faturamento'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_faturamentos')

    contrato_id = db.Column(db.Integer, db.ForeignKey('locacao_contratos.id'), nullable=False, index=True)
    contrato = db.relationship('LocacaoContrato', backref='faturamentos')

    cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    cliente = db.relationship('Entidade', foreign_keys=[cliente_id])

    # Identificação
    numero_documento = db.Column(db.String(50), nullable=False, index=True)
    data_faturamento = db.Column(db.Date, nullable=False, index=True)
    evento_faturamento = db.Column(db.String(50), nullable=False)  # reserva, retirada, devolucao, fechamento

    # Valores por tipo
    valor_aluguel = db.Column(db.Numeric(15, 2), default=0.00)
    valor_venda = db.Column(db.Numeric(15, 2), default=0.00)
    valor_multa = db.Column(db.Numeric(15, 2), default=0.00)
    valor_avaria = db.Column(db.Numeric(15, 2), default=0.00)
    valor_caucao_retida = db.Column(db.Numeric(15, 2), default=0.00)
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)

    # Memória de cálculo
    memoria_calculo = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), default='emitido')  # emitido, refaturado, cancelado

    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<LocacaoFaturamento {self.numero_documento}>'


# ============================================================================
# 8. AUDITORIA E LOG
# ============================================================================

class LocacaoAuditoria(db.Model):
    """Log de auditoria para rastreabilidade completa"""
    __tablename__ = 'locacao_auditoria'
    __table_args__ = (
        db.Index('idx_locacao_auditoria_empresa_data', 'empresa_id', 'data_acao'),
        db.Index('idx_locacao_auditoria_usuario', 'user_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='locacao_auditorias')

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='locacao_auditorias')

    # Ação
    tipo_entidade = db.Column(db.String(50), nullable=False)  # contrato, retirada, devolucao, etc
    id_entidade = db.Column(db.Integer, nullable=False)
    tipo_acao = db.Column(db.String(50), nullable=False)  # criacao, atualizacao, cancelamento, etc

    # Detalhes
    descricao = db.Column(db.Text, nullable=True)
    dados_anteriores = db.Column(db.Text, nullable=True)
    dados_novos = db.Column(db.Text, nullable=True)

    data_acao = db.Column(db.DateTime, default=_utcnow, index=True)

    def __repr__(self):
        return f'<LocacaoAuditoria {self.tipo_entidade} {self.tipo_acao}>'
