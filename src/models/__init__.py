
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()


def _utcnow():
    return datetime.now(timezone.utc)

# Modelo de Entidade (restaurado)
class Entidade(db.Model):
    __tablename__ = 'entidades'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='entidades')
    nome = db.Column(db.String(150), nullable=False)
    cnpj_cpf = db.Column(db.String(18), nullable=False, index=True)

    tipo = db.Column(db.String(1))
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'), nullable=True)
    fluxo_conta = db.relationship('FluxoContaModel', foreign_keys=[fluxo_conta_id])
    # Campos de comissão
    aliquota_comissao_especifica = db.Column(db.Numeric(5, 2), nullable=True)  # Percentual específico
    valor_repasse = db.Column(db.Numeric(10, 2), default=0.00)  # Valor fixo de repasse ao fornecedor
    vendedor_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=True)  # Vendedor padrão
    vendedor = db.relationship('Entidade', remote_side='Entidade.id', foreign_keys=[vendedor_id], backref='clientes_vinculados')
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    ativo = db.Column(db.Boolean, default=True)

    def get_tipo_descricao(self):
        """Retorna a descrição do tipo da entidade (C=Cliente, F=Fornecedor, V=Vendedor, L=Funcionário, etc)."""
        if self.tipo == 'C':
            return 'Cliente'
        elif self.tipo == 'F':
            return 'Fornecedor'
        elif self.tipo == 'V':
            return 'Vendedor'
        elif self.tipo == 'L':
            return 'Funcionário'
        elif self.tipo:
            return self.tipo
        return 'Não definido'

    def __repr__(self):
        return f'<Entidade {self.nome}>'

# Modelo de Usuário para autenticação
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'username', name='uq_users_empresa_username'),
    )
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='users')
    username = db.Column(db.String(80), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='viewer')  # 'admin', 'operator', 'viewer'
    dashboard_chart_days = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class RolePermission(db.Model):
    """Permissões por papel e empresa para controlar acesso aos processos."""
    __tablename__ = 'role_permissions'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'role', 'permission_key', name='uq_role_permission_empresa_role_key'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='role_permissions')

    role = db.Column(db.String(20), nullable=False, index=True)
    permission_key = db.Column(db.String(80), nullable=False, index=True)
    allowed = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<RolePermission empresa={self.empresa_id} role={self.role} key={self.permission_key} allowed={self.allowed}>'


class UserPermissionOverride(db.Model):
    """Excecao de permissao por usuario, sobrepondo a permissao do papel."""
    __tablename__ = 'user_permission_overrides'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'user_id', 'permission_key', name='uq_user_permission_override_empresa_user_key'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='user_permission_overrides')

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user = db.relationship('User', backref='permission_overrides')

    permission_key = db.Column(db.String(80), nullable=False, index=True)
    allowed = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<UserPermissionOverride empresa={self.empresa_id} user={self.user_id} key={self.permission_key} allowed={self.allowed}>'

# Modelo Empresa para multi-tenant
class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, unique=True)
    cnpj = db.Column(db.String(18), unique=True)
    plano = db.Column(db.String(20), nullable=False, default='premium')
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<Empresa {self.nome}>'


class Comissao(db.Model):
    """Commission Records - Registro de Comissões"""
    __tablename__ = 'comissoes'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='comissoes')
    
    # Identificação de apuração
    id_apuracao = db.Column(db.Integer, nullable=False, index=True)  # Sequence da apuração
    # Relacionamentos
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id'), nullable=False, index=True)
    lancamento = db.relationship('Lancamento', foreign_keys=[lancamento_id])
    
    entidade_cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    entidade_vendedor_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    
    # Datas
    dt_lancamento = db.Column(db.Date, nullable=False, index=True)
    dt_vencimento = db.Column(db.Date, nullable=False, index=True)
    dt_pagamento_recebimento = db.Column(db.Date, nullable=False, index=True)  # data_pagamento do lancamento
    
    # Valores
    vl_nota = db.Column(db.Numeric(15, 2), nullable=False)  # valor_real
    vl_imposto = db.Column(db.Numeric(15, 2), default=0.00)
    vl_outros_custos = db.Column(db.Numeric(15, 2), default=0.00)
    vl_repasse = db.Column(db.Numeric(15, 2), default=0.00)  # Valor de repasse
    vl_liquido = db.Column(db.Numeric(15, 2), nullable=False)  # Base de cálculo
    aliquota_aplicada = db.Column(db.Numeric(5, 2), nullable=False)  # Percentual aplicado
    vl_comissao = db.Column(db.Numeric(15, 2), nullable=False)  # Valor da comissão
    
    # Situação
    situacao = db.Column(db.String(20), default='ativo')  # ativo, estornado, reapurado
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    
    __table_args__ = (
        db.Index('idx_comissao_empresa_apuracao', 'empresa_id', 'id_apuracao'),
        db.Index('idx_comissao_empresa_lancamento', 'empresa_id', 'lancamento_id', 'entidade_cliente_id', 'entidade_vendedor_id'),
    )
    
    def __repr__(self):
        return f'<Comissao {self.id} - Apuração {self.id_apuracao} - R$ {self.vl_comissao}>'

# -------------------
# Importação de NFSe
# -------------------
class ImportacaoNFSe(db.Model):
    __tablename__ = 'importacao_nfse'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='importacoes_nfse')
    chave_nota = db.Column(db.String(60), nullable=False, index=True)
    numero_nota = db.Column(db.String(30), nullable=False)
    data_emissao = db.Column(db.Date, nullable=False)
    cnpj_tomador = db.Column(db.String(20), nullable=False)
    entidade_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=True, index=True)
    entidade = db.relationship('Entidade', foreign_keys=[entidade_id], backref='importacoes_nfse')

    # Relacionamento reverso para facilitar exclusão em cascata
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id', ondelete='CASCADE'), nullable=True, index=True)
    lancamento = db.relationship('Lancamento', backref=db.backref('importacao_nfse', cascade='all, delete-orphan', passive_deletes=True), foreign_keys=[lancamento_id])
    valor_bruto = db.Column(db.Numeric(15, 2), nullable=False)
    valor_impostos = db.Column(db.Numeric(15, 2))
    descricao_servico = db.Column(db.Text)
    status_importacao = db.Column(db.String(20), default='sucesso')
    mensagem_erro = db.Column(db.String(255))
    data_importacao = db.Column(db.DateTime, default=_utcnow)
    # Armazena o XML original importado
    # xml_original removido (não armazenar XML no banco)
    
    def __repr__(self):
        return f'<ImportacaoNFSe {self.chave_nota} - {self.numero_nota}>'
    
    # Endereço
    endereco_rua = db.Column(db.String(150))
    endereco_numero = db.Column(db.String(10))
    endereco_bairro = db.Column(db.String(100))
    endereco_cidade = db.Column(db.String(100))
    endereco_uf = db.Column(db.String(2))
    endereco_cep = db.Column(db.String(8))
    
    # Contato
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Contrato/Produto
    contrato_produto = db.Column(db.Text)
    
    # Alíquota do ISS extraída do XML
    aliquota_iss = db.Column(db.Numeric(5, 2), nullable=True)  # Alíquota ISS (%)
    # Campos para comissão (aplicável apenas a CLIENTE)
    aliquota_comissao_especifica = db.Column(db.Numeric(5, 2), nullable=True)  # Percentual específico
    valor_repasse = db.Column(db.Numeric(10, 2), default=0.00)  # Valor fixo de repasse ao fornecedor

    entidade_vendedor_padrao_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=True)  # Vendedor padrão
    entidade_vendedor_padrao = db.relationship('Entidade', foreign_keys=[entidade_vendedor_padrao_id], backref='importacoes_nfse_vendedor_padrao')
    
    # Metadados
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    




class FluxoContaModel(db.Model):
    """Chart of Accounts for Cash Flow - Plano de Contas de Fluxo de Caixa"""
    __tablename__ = 'fluxo_contas_modelo'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='fluxo_contas')
    codigo = db.Column(db.String(20), nullable=False, index=True)  # 999 ou 9.99 format
    descricao = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(1), nullable=False)  # P-Pagamento, R-Recebimento
    mascara = db.Column(db.String(50))  # 999 ou 9.99
    nivel_sintetico = db.Column(db.Integer)  # Nível sintético da máscara
    nivel_analitico = db.Column(db.Integer)  # Nível analítico da máscara
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    
    # Relacionamentos
    lancamentos = db.relationship('Lancamento', backref='fluxo_conta', lazy='dynamic')

    def is_pagamento(self):
        return self.tipo == 'P'

    def is_recebimento(self):
        return self.tipo == 'R'

    def get_tipo_descricao(self):
        if self.tipo == 'P':
            return 'Pagamento'
        if self.tipo == 'R':
            return 'Recebimento'
        return self.tipo or 'Não definido'
    
    def __repr__(self):
        return f'<FluxoContaModel {self.codigo} - {self.descricao}>'


class ContaBanco(db.Model):
    """Bank Account - Conta de Banco"""
    __tablename__ = 'contas_banco'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='contas_banco')
    nome = db.Column(db.String(150), nullable=False, index=True)
    banco = db.Column(db.String(50), nullable=False)
    agencia = db.Column(db.String(10), nullable=False)
    numero_conta = db.Column(db.String(20), nullable=False)
    dv = db.Column(db.String(2))  # Dígito verificador
    tipo = db.Column(db.String(20))  # Corrente, Poupança, etc
    
    # Relacionamento com conta de fluxo analítica
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'))
    fluxo_conta = db.relationship('FluxoContaModel', foreign_keys=[fluxo_conta_id])
    
    saldo_inicial = db.Column(db.Numeric(15, 2), default=0.00)
    is_principal = db.Column(db.Boolean, default=False, nullable=False, index=True)  # Indica se é a conta principal da entidade
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    
    # Relacionamentos
    lancamentos = db.relationship('Lancamento', backref='conta_banco', lazy='dynamic')
    
    def __repr__(self):
        return f'<ContaBanco {self.nome} ({self.banco})>'


class Lancamento(db.Model):
    """Expense/Income Record - Lançamento de Despesa/Receita"""
    __tablename__ = 'lancamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='lancamentos')
    
    # Datas
    data_evento = db.Column(db.Date, nullable=False, index=True)
    data_vencimento = db.Column(db.Date, nullable=False, index=True)
    data_pagamento = db.Column(db.Date, index=True)  # Nulo se não pago
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='aberto')  # aberto, pago, vencido
    
    # Relacionamentos
    entidade_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False)
    entidade = db.relationship('Entidade', backref='lancamentos')
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'), nullable=False)
    conta_banco_id = db.Column(db.Integer, db.ForeignKey('contas_banco.id'), nullable=False)
    
    # Valores
    valor_real = db.Column(db.Numeric(15, 2), nullable=False)  # Valor original
    valor_pago = db.Column(db.Numeric(15, 2), default=0.00)  # Valor efetivamente pago
    valor_imposto = db.Column(db.Numeric(15, 2), default=0.00)  # Imposto
    valor_outros_custos = db.Column(db.Numeric(15, 2), default=0.00)  # Outros custos
    
    # Documentação
    numero_documento = db.Column(db.String(50), index=True)
    observacoes = db.Column(db.Text)
    
    # Rastreabilidade de origem
    referencia_banco = db.Column(db.String(100), index=True)  # ID de transação bancária (OFX, etc)
    fonte = db.Column(db.String(50), default='manual')  # 'manual', 'ofx', 'nfse', etc
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    
    def __repr__(self):
        return f'<Lancamento {self.numero_documento} - R$ {self.valor_real}>'


class FluxoCaixaRealizado(db.Model):
    """Cash Flow Realized - Fluxo de Caixa Realizado"""
    __tablename__ = 'fluxo_caixa_realizado'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='fluxo_caixa_realizado')
    
    # Data
    data = db.Column(db.Date, nullable=False, index=True)
    
    # Relacionamento
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'), nullable=False)
    conta_banco_id = db.Column(db.Integer, db.ForeignKey('contas_banco.id'), nullable=False)
    
    fluxo_conta = db.relationship('FluxoContaModel', foreign_keys=[fluxo_conta_id])
    conta_banco = db.relationship('ContaBanco', foreign_keys=[conta_banco_id])
    
    # Valores
    saldo_anterior = db.Column(db.Numeric(15, 2), default=0.00)
    valor_pago = db.Column(db.Numeric(15, 2), default=0.00)  # Saída (Pagamento)
    valor_recebido = db.Column(db.Numeric(15, 2), default=0.00)  # Entrada (Recebimento)
    saldo_atual = db.Column(db.Numeric(15, 2), default=0.00)
    
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    
    def __repr__(self):
        return f'<FluxoCaixaRealizado {self.data}>'


class FluxoCaixaPrevisto(db.Model):
    """Cash Flow Forecast - Fluxo de Caixa Previsto"""
    __tablename__ = 'fluxo_caixa_previsto'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='fluxo_caixa_previsto')
    
    # Data
    data = db.Column(db.Date, nullable=False, index=True)
    
    # Relacionamento
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'), nullable=False)
    conta_banco_id = db.Column(db.Integer, db.ForeignKey('contas_banco.id'), nullable=False)
    
    fluxo_conta = db.relationship('FluxoContaModel', foreign_keys=[fluxo_conta_id])
    conta_banco = db.relationship('ContaBanco', foreign_keys=[conta_banco_id])
    
    # Valores
    saldo_anterior = db.Column(db.Numeric(15, 2), default=0.00)
    valor_previsto_pago = db.Column(db.Numeric(15, 2), default=0.00)  # Saída (Pagamento previsto)
    valor_previsto_recebido = db.Column(db.Numeric(15, 2), default=0.00)  # Entrada (Recebimento previsto)
    saldo_previsto = db.Column(db.Numeric(15, 2), default=0.00)
    
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    
    def __repr__(self):
        return f'<FluxoCaixaPrevisto {self.data}>'


class ParametroSistema(db.Model):
    """System Parameters - Parâmetros de Sistema"""
    __tablename__ = 'parametros_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='parametros_sistema')
    
    chave = db.Column(db.String(100), nullable=False)  # Nome do parâmetro
    valor = db.Column(db.Text, nullable=False)  # Valor armazenado como string
    tipo = db.Column(db.String(20), default='string')  # Tipo: string, numeric, boolean
    descricao = db.Column(db.String(255))
    
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    
    __table_args__ = (db.UniqueConstraint('empresa_id', 'chave', name='uq_parametro_chave'),)
    
    def __repr__(self):
        return f'<ParametroSistema {self.chave}={self.valor}>'


class ConciliacaoBancaria(db.Model):
    """Conciliação bancária por conta e período."""
    __tablename__ = 'conciliacao_bancaria'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='conciliacoes_bancarias')

    conta_banco_id = db.Column(db.Integer, db.ForeignKey('contas_banco.id'), nullable=False, index=True)
    conta_banco = db.relationship('ContaBanco', backref='conciliacoes')

    periodo_inicio = db.Column(db.Date, nullable=False, index=True)
    periodo_fim = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='aberta')
    observacoes = db.Column(db.Text)
    criado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    criado_por = db.relationship('User', foreign_keys=[criado_por_user_id])
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<ConciliacaoBancaria {self.id} - {self.periodo_inicio} a {self.periodo_fim}>'


class ConciliacaoItem(db.Model):
    """Item individual importado do extrato ou conciliado manualmente."""
    __tablename__ = 'conciliacao_item'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='conciliacao_itens')

    conciliacao_id = db.Column(db.Integer, db.ForeignKey('conciliacao_bancaria.id', ondelete='CASCADE'), nullable=False, index=True)
    conciliacao = db.relationship('ConciliacaoBancaria', backref='itens')

    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id', ondelete='SET NULL'), nullable=True, index=True)
    lancamento = db.relationship('Lancamento', foreign_keys=[lancamento_id])

    data_movimento = db.Column(db.Date, nullable=False, index=True)
    descricao_extrato = db.Column(db.String(255))
    referencia_banco = db.Column(db.String(120), index=True)
    valor_extrato = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pendente')
    motivo_divergencia = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<ConciliacaoItem {self.id} - {self.status}>'


class CatalogoPlanoComercial(db.Model):
    """Catalogo versionado de ofertas comerciais por plano e periodicidade."""
    __tablename__ = 'catalogo_planos_comercial'

    id = db.Column(db.Integer, primary_key=True)
    codigo_plano = db.Column(db.String(30), nullable=False, index=True)  # basic, intermediate, premium
    nome_exibicao = db.Column(db.String(80), nullable=False)
    versao_oferta = db.Column(db.Integer, nullable=False, default=1, index=True)
    periodicidade = db.Column(db.String(20), nullable=False, default='mensal', index=True)  # mensal, anual
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    moeda = db.Column(db.String(10), nullable=False, default='BRL')
    limite_usuarios = db.Column(db.Integer, nullable=True)
    recursos_json = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True, index=True)
    vigencia_inicio = db.Column(db.Date, nullable=True)
    vigencia_fim = db.Column(db.Date, nullable=True)
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        db.UniqueConstraint('codigo_plano', 'periodicidade', 'versao_oferta', name='uq_catalogo_plano_periodo_versao'),
    )

    def __repr__(self):
        return f'<CatalogoPlanoComercial {self.codigo_plano}/{self.periodicidade} v{self.versao_oferta}>'


class AssinaturaEmpresa(db.Model):
    """Estado comercial atual da assinatura por empresa."""
    __tablename__ = 'assinatura_empresa'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, unique=True, index=True)
    empresa = db.relationship('Empresa', backref='assinatura_atual')

    catalogo_plano_id = db.Column(db.Integer, db.ForeignKey('catalogo_planos_comercial.id'), nullable=True, index=True)
    catalogo_plano = db.relationship('CatalogoPlanoComercial', foreign_keys=[catalogo_plano_id])

    plano_codigo = db.Column(db.String(30), nullable=False, default='premium', index=True)
    ciclo_cobranca = db.Column(db.String(20), nullable=False, default='mensal')
    status = db.Column(db.String(20), nullable=False, default='trial', index=True)  # ativa, trial, suspensa, cancelada
    gateway = db.Column(db.String(30), nullable=False, default='asaas', index=True)
    gateway_customer_id = db.Column(db.String(120), nullable=True, index=True)
    gateway_subscription_id = db.Column(db.String(120), nullable=True, index=True)

    data_inicio = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False, index=True)
    data_renovacao = db.Column(db.Date, nullable=True, index=True)
    data_fim_trial = db.Column(db.Date, nullable=True, index=True)
    carencia_dias = db.Column(db.Integer, nullable=False, default=7)
    data_limite_carencia = db.Column(db.Date, nullable=True, index=True)

    bloqueio_nivel = db.Column(db.String(20), nullable=False, default='nenhum')  # nenhum, parcial, total
    bloqueado_desde = db.Column(db.DateTime, nullable=True)
    motivo_status = db.Column(db.String(255), nullable=True)

    politica_efetivacao_dias = db.Column(db.Integer, nullable=False, default=30)
    proximo_plano_codigo = db.Column(db.String(30), nullable=True)
    mudanca_plano_solicitada_em = db.Column(db.DateTime, nullable=True)
    mudanca_plano_efetivar_em = db.Column(db.DateTime, nullable=True, index=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<AssinaturaEmpresa empresa={self.empresa_id} status={self.status} plano={self.plano_codigo}>'


class CobrancaRecorrente(db.Model):
    """Cobrancas recorrentes geradas para uma assinatura."""
    __tablename__ = 'cobranca_recorrente'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='cobrancas_recorrentes')

    assinatura_id = db.Column(db.Integer, db.ForeignKey('assinatura_empresa.id'), nullable=False, index=True)
    assinatura = db.relationship('AssinaturaEmpresa', backref='cobrancas')

    gateway = db.Column(db.String(30), nullable=False, default='asaas', index=True)
    gateway_cobranca_id = db.Column(db.String(120), nullable=True, unique=True)
    referencia_interna = db.Column(db.String(120), nullable=False, unique=True)

    competencia_ano = db.Column(db.Integer, nullable=False, index=True)
    competencia_mes = db.Column(db.Integer, nullable=False, index=True)
    periodicidade = db.Column(db.String(20), nullable=False, default='mensal')

    valor_previsto = db.Column(db.Numeric(10, 2), nullable=False)
    valor_pago = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pendente', index=True)  # pendente, pago, vencido, falhou, cancelado, estornado

    data_emissao = db.Column(db.Date, nullable=True)
    data_vencimento = db.Column(db.Date, nullable=False, index=True)
    data_pagamento = db.Column(db.DateTime, nullable=True)

    tentativas_pagamento = db.Column(db.Integer, nullable=False, default=0)
    ultimo_erro = db.Column(db.String(255), nullable=True)
    payload_gateway = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        db.Index('idx_cobranca_empresa_status_venc', 'empresa_id', 'status', 'data_vencimento'),
    )

    def __repr__(self):
        return f'<CobrancaRecorrente {self.id} empresa={self.empresa_id} status={self.status}>'


class EventoCobranca(db.Model):
    """Eventos de webhook/auditoria de cobranca com idempotencia por event_id externo."""
    __tablename__ = 'evento_cobranca'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True, index=True)
    empresa = db.relationship('Empresa', backref='eventos_cobranca')

    assinatura_id = db.Column(db.Integer, db.ForeignKey('assinatura_empresa.id'), nullable=True, index=True)
    assinatura = db.relationship('AssinaturaEmpresa', foreign_keys=[assinatura_id])

    cobranca_id = db.Column(db.Integer, db.ForeignKey('cobranca_recorrente.id'), nullable=True, index=True)
    cobranca = db.relationship('CobrancaRecorrente', foreign_keys=[cobranca_id])

    gateway = db.Column(db.String(30), nullable=False, default='asaas', index=True)
    event_id_externo = db.Column(db.String(150), nullable=False)
    tipo_evento = db.Column(db.String(80), nullable=False, index=True)
    status_processamento = db.Column(db.String(20), nullable=False, default='recebido', index=True)  # recebido, processado, ignorado, erro

    recebido_em = db.Column(db.DateTime, default=_utcnow, index=True)
    processado_em = db.Column(db.DateTime, nullable=True)
    payload = db.Column(db.Text, nullable=True)
    mensagem_erro = db.Column(db.String(255), nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        db.UniqueConstraint('gateway', 'event_id_externo', name='uq_evento_cobranca_gateway_evento'),
    )

    def __repr__(self):
        return f'<EventoCobranca {self.gateway}:{self.event_id_externo} {self.status_processamento}>'


class HistoricoMudancaPlano(db.Model):
    """Historico de solicitacao e efetivacao de upgrade/downgrade."""
    __tablename__ = 'historico_mudanca_plano'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='historico_mudancas_plano')

    assinatura_id = db.Column(db.Integer, db.ForeignKey('assinatura_empresa.id'), nullable=False, index=True)
    assinatura = db.relationship('AssinaturaEmpresa', backref='historico_mudancas')

    plano_origem = db.Column(db.String(30), nullable=False)
    plano_destino = db.Column(db.String(30), nullable=False)
    tipo_mudanca = db.Column(db.String(20), nullable=False, index=True)  # upgrade, downgrade, lateral, manual
    regra_efetivacao = db.Column(db.String(30), nullable=False, default='apos_30_dias')

    solicitado_em = db.Column(db.DateTime, default=_utcnow, index=True)
    efetivado_em = db.Column(db.DateTime, nullable=True, index=True)

    solicitado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    solicitado_por = db.relationship('User', foreign_keys=[solicitado_por_user_id])
    executado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    executado_por = db.relationship('User', foreign_keys=[executado_por_user_id])

    observacoes = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<HistoricoMudancaPlano empresa={self.empresa_id} {self.plano_origem}->{self.plano_destino}>'


class NotificacaoComercial(db.Model):
    """Fila e historico de comunicacoes comerciais."""
    __tablename__ = 'notificacao_comercial'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='notificacoes_comerciais')

    assinatura_id = db.Column(db.Integer, db.ForeignKey('assinatura_empresa.id'), nullable=True, index=True)
    assinatura = db.relationship('AssinaturaEmpresa', foreign_keys=[assinatura_id])

    tipo = db.Column(db.String(50), nullable=False, index=True)  # pre_vencimento, falha_pagamento, reativacao, bloqueio
    canal = db.Column(db.String(20), nullable=False, default='email')  # email, sistema
    destinatario = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pendente', index=True)  # pendente, enviada, falha, cancelada

    agendada_para = db.Column(db.DateTime, nullable=True, index=True)
    enviada_em = db.Column(db.DateTime, nullable=True)
    tentativas = db.Column(db.Integer, nullable=False, default=0)
    erro = db.Column(db.String(255), nullable=True)
    payload = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=_utcnow)
    atualizado_em = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f'<NotificacaoComercial empresa={self.empresa_id} tipo={self.tipo} status={self.status}>'


