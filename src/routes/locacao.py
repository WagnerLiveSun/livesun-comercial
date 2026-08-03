"""
Blueprint de Locação - Rotas e Lógica de Negócio
Módulo completo de aluguel de roupas e fantasias
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from src.models import db, Entidade, Lancamento, FluxoContaModel
from src.models.locacao import (
    LocacaoPeca, LocacaoKit, LocacaoKitItem,
    LocacaoDisponibilidade, LocacaoParametro,
    LocacaoEvento, LocacaoOrcamento, LocacaoOrcamentoItem,
    LocacaoReserva, LocacaoContrato,
    LocacaoRetirada, LocacaoRetiradaItem,
    LocacaoDevolucao, LocacaoInspecao,
    LocacaoManutencao,
    LocacaoTitulo, LocacaoCobranca, LocacaoDevolucaoCaucao,
    LocacaoFaturamento, LocacaoAuditoria
)
from src.tenant import tenant_id, scoped_query, validate_ownership
from src.access_control import require_permission

locacao_bp = Blueprint('locacao', __name__, url_prefix='/locacao', template_folder='../templates/locacao')


# ============================================================================
# UTILITÁRIOS E HELPERS
# ============================================================================

def _get_empresa():
    """Retorna a empresa do usuário autenticado"""
    if not current_user.is_authenticated:
        return None
    return current_user.empresa


def _get_parametro(chave, tipo='string', padrao=None):
    """Obtém um parâmetro de configuração da empresa"""
    empresa = _get_empresa()
    if not empresa:
        return padrao
    
    param = LocacaoParametro.query.filter_by(
        empresa_id=empresa.id,
        chave=chave
    ).first()
    
    if not param:
        return padrao
    
    if tipo == 'numeric':
        try:
            return float(param.valor)
        except (ValueError, TypeError):
            return padrao
    elif tipo == 'boolean':
        return param.valor.lower() in ('true', '1', 'sim', 'yes')
    else:
        return param.valor


def _criar_auditoria(tipo_entidade, id_entidade, tipo_acao, descricao='', dados_anteriores=None, dados_novos=None):
    """Cria registro de auditoria"""
    empresa = _get_empresa()
    if not empresa:
        return
    
    auditoria = LocacaoAuditoria(
        empresa_id=empresa.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        tipo_entidade=tipo_entidade,
        id_entidade=id_entidade,
        tipo_acao=tipo_acao,
        descricao=descricao,
        dados_anteriores=json.dumps(dados_anteriores) if dados_anteriores else None,
        dados_novos=json.dumps(dados_novos) if dados_novos else None,
    )
    db.session.add(auditoria)
    db.session.commit()


def _consultar_disponibilidade(peca_id, data_inicio, data_fim, empresa_id=None):
    """
    Consulta se uma peça está disponível em um período
    Retorna: (disponível: bool, motivo: str, bloqueio_id: int)
    """
    if not empresa_id:
        empresa_id = tenant_id()
    
    bloqueios = LocacaoDisponibilidade.query.filter(
        LocacaoDisponibilidade.empresa_id == empresa_id,
        LocacaoDisponibilidade.peca_id == peca_id,
        LocacaoDisponibilidade.data_inicio <= data_fim,
        LocacaoDisponibilidade.data_fim >= data_inicio
    ).all()
    
    if bloqueios:
        bloqueio = bloqueios[0]
        return False, f"Indisponível ({bloqueio.motivo})", bloqueio.id
    
    return True, "Disponível", None


def _bloquear_disponibilidade(peca_id, data_inicio, data_fim, motivo, referencia_id=None, referencia_tipo=''):
    """
    Bloqueia a disponibilidade de uma peça para um período
    """
    empresa_id = tenant_id()
    
    bloqueio = LocacaoDisponibilidade(
        empresa_id=empresa_id,
        peca_id=peca_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        motivo=motivo
    )
    
    if referencia_tipo == 'reserva':
        bloqueio.reserva_id = referencia_id
    elif referencia_tipo == 'manutencao':
        bloqueio.manutencao_id = referencia_id
    
    db.session.add(bloqueio)
    db.session.commit()
    
    return bloqueio


def _liberar_disponibilidade(peca_id, data_inicio, data_fim, motivo):
    """
    Remove bloqueios de disponibilidade
    """
    empresa_id = tenant_id()
    
    LocacaoDisponibilidade.query.filter(
        LocacaoDisponibilidade.empresa_id == empresa_id,
        LocacaoDisponibilidade.peca_id == peca_id,
        LocacaoDisponibilidade.motivo == motivo,
        LocacaoDisponibilidade.data_inicio >= data_inicio,
        LocacaoDisponibilidade.data_fim <= data_fim
    ).delete()
    
    db.session.commit()


def _calcular_dias_locacao(data_inicio, data_fim):
    """Calcula número de dias entre duas datas"""
    delta = data_fim - data_inicio
    return max(1, delta.days)


def _calcular_valor_aluguel(valor_diario, dias):
    """Calcula valor total de aluguel"""
    return Decimal(str(valor_diario)) * Decimal(str(dias))


def _calcular_multa_atraso(dias_atraso, valor_diario):
    """Calcula multa por atraso"""
    multa_diaria = _get_parametro('multa_atraso_diaria_valor', 'numeric', 0)
    multa_percentual = _get_parametro('multa_atraso_diaria_percentual', 'numeric', 0)
    
    multa = Decimal(str(dias_atraso)) * (Decimal(str(multa_diaria)) + Decimal(str(valor_diario)) * Decimal(str(multa_percentual)) / 100)
    return multa


def _gerar_numero_sequencial(prefixo, empresa_id=None):
    """Gera número sequencial para documentos"""
    if not empresa_id:
        empresa_id = tenant_id()
    
    # Implementação simplificada - em produção, usar sequência no BD
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefixo}-{timestamp}"


def _gerar_titulo_financeiro(contrato_id, cliente_id, tipo_titulo, valor, data_vencimento, descricao=''):
    """
    Gera um título financeiro (integração com módulo financeiro)
    """
    empresa_id = tenant_id()
    
    titulo = LocacaoTitulo(
        empresa_id=empresa_id,
        contrato_id=contrato_id,
        cliente_id=cliente_id,
        numero=_gerar_numero_sequencial(f'LOC-{tipo_titulo[:3].upper()}'),
        tipo_titulo=tipo_titulo,
        data_emissao=date.today(),
        data_vencimento=data_vencimento,
        valor_original=valor,
        valor_pago=Decimal('0.00'),
        valor_aberto=valor,
        status='aberto'
    )
    
    db.session.add(titulo)
    db.session.flush()
    
    # Gerar Lancamento correspondente (integração com financeiro)
    _gerar_lancamento_de_titulo(titulo)
    
    db.session.commit()
    return titulo


def _gerar_lancamento_de_titulo(titulo):
    """
    Gera um Lancamento no módulo financeiro a partir de um LocacaoTitulo
    """
    try:
        # Verificar se já existe lançamento
        lancamento_existente = Lancamento.query.filter_by(
            numero_documento=titulo.numero,
            fonte='locacao'
        ).first()
        
        if lancamento_existente:
            return lancamento_existente
        
        # Buscar conta padrão de recebimento
        conta = FluxoContaModel.query.filter_by(
            empresa_id=titulo.empresa_id,
            tipo='R',  # Recebimento
            ativo=True
        ).first()
        
        if not conta:
            # Se não houver conta ativa, usar a primeira conta de recebimento
            conta = FluxoContaModel.query.filter_by(
                empresa_id=titulo.empresa_id,
                tipo='R'
            ).first()
        
        if not conta:
            current_app.logger.warning(f"Nenhuma conta de recebimento encontrada para empresa {titulo.empresa_id}")
            return None
        
        # Criar lançamento
        lancamento = Lancamento(
            empresa_id=titulo.empresa_id,
            entidade_id=titulo.cliente_id,
            fluxo_conta_id=conta.id,
            numero_documento=titulo.numero,
            fonte='locacao',
            tipo='R',  # Recebimento
            data_evento=titulo.data_emissao,
            data_vencimento=titulo.data_vencimento,
            valor_real=titulo.valor_original,
            valor_pago=Decimal('0.00'),
            descricao=f"Locação - {titulo.tipo_titulo}",
            status='aberto'
        )
        
        db.session.add(lancamento)
        titulo.lancamento_id = lancamento.id
        db.session.commit()
        
        return lancamento
    
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar lançamento: {str(e)}")
        return None


# ============================================================================
# 1. ACERVO - PEÇAS E KITS
# ============================================================================

@locacao_bp.route('/acervo', methods=['GET'])
@login_required
@require_permission('locacao_acervo')
def acervo_lista():
    """Lista todas as peças do acervo"""
    empresa_id = tenant_id()
    
    # Filtros
    categoria = request.args.get('categoria', '')
    tema = request.args.get('tema', '')
    estado = request.args.get('estado', '')
    ativo = request.args.get('ativo', 'true') == 'true'
    
    query = LocacaoPeca.query.filter_by(empresa_id=empresa_id, ativo=ativo)
    
    if categoria:
        query = query.filter_by(categoria=categoria)
    if tema:
        query = query.filter_by(tema=tema)
    if estado:
        query = query.filter_by(estado_fisico=estado)
    
    pecas = query.order_by(LocacaoPeca.categoria, LocacaoPeca.descricao).all()
    
    # Estatísticas
    total_pecas = LocacaoPeca.query.filter_by(empresa_id=empresa_id, ativo=True).count()
    categorias = db.session.query(LocacaoPeca.categoria).filter_by(empresa_id=empresa_id, ativo=True).distinct().all()
    temas = db.session.query(LocacaoPeca.tema).filter_by(empresa_id=empresa_id, ativo=True).distinct().all()
    
    return render_template('acervo/lista.html',
        pecas=pecas,
        total_pecas=total_pecas,
        categorias=[c[0] for c in categorias if c[0]],
        temas=[t[0] for t in temas if t[0]],
        categoria_filtro=categoria,
        tema_filtro=tema,
        estado_filtro=estado
    )


@locacao_bp.route('/acervo/criar', methods=['GET', 'POST'])
@login_required
@require_permission('locacao_acervo')
def acervo_criar():
    """Cria nova peça no acervo"""
    empresa_id = tenant_id()
    
    if request.method == 'POST':
        try:
            peca = LocacaoPeca(
                empresa_id=empresa_id,
                codigo_interno=(request.form.get('codigo_interno') or '').strip(),
                codigo_barras=(request.form.get('codigo_barras') or '').strip(),
                descricao=(request.form.get('descricao') or '').strip(),
                categoria=(request.form.get('categoria') or '').strip(),
                tema=(request.form.get('tema') or '').strip(),
                tamanho=(request.form.get('tamanho') or '').strip(),
                cor=(request.form.get('cor') or '').strip(),
                tecido=(request.form.get('tecido') or '').strip(),
                marca_colecao=(request.form.get('marca_colecao') or '').strip(),
                valor_aquisicao=Decimal(request.form.get('valor_aquisicao', 0)),
                valor_reposicao=Decimal(request.form.get('valor_reposicao', 0)),
                preco_aluguel_diario=Decimal(request.form.get('preco_aluguel_diario', 0)),
                preco_venda=Decimal(request.form.get('preco_venda', 0)) if request.form.get('preco_venda') else None,
                estado_fisico=request.form.get('estado_fisico', 'novo'),
                serializado=request.form.get('serializado') == 'on',
                ativo=True
            )
            
            db.session.add(peca)
            db.session.commit()
            
            _criar_auditoria('peca', peca.id, 'criacao', f"Peça {peca.codigo_interno} criada")
            
            flash(f'Peça {peca.codigo_interno} criada com sucesso!', 'success')
            return redirect(url_for('locacao.acervo_lista'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar peça: {str(e)}', 'danger')
    
    return render_template('acervo/criar.html')


@locacao_bp.route('/acervo/<int:peca_id>/editar', methods=['GET', 'POST'])
@login_required
@require_permission('locacao_acervo')
@validate_ownership(LocacaoPeca)
def acervo_editar(peca_id):
    """Edita uma peça do acervo"""
    peca = LocacaoPeca.query.get_or_404(peca_id)
    
    if request.method == 'POST':
        try:
            dados_anteriores = {
                'descricao': peca.descricao,
                'preco_aluguel_diario': str(peca.preco_aluguel_diario),
                'estado_fisico': peca.estado_fisico
            }
            
            peca.descricao = (request.form.get('descricao') or '').strip()
            peca.categoria = (request.form.get('categoria') or '').strip()
            peca.tema = (request.form.get('tema') or '').strip()
            peca.tamanho = (request.form.get('tamanho') or '').strip()
            peca.cor = (request.form.get('cor') or '').strip()
            peca.tecido = (request.form.get('tecido') or '').strip()
            peca.marca_colecao = (request.form.get('marca_colecao') or '').strip()
            peca.valor_aquisicao = Decimal(request.form.get('valor_aquisicao', 0))
            peca.valor_reposicao = Decimal(request.form.get('valor_reposicao', 0))
            peca.preco_aluguel_diario = Decimal(request.form.get('preco_aluguel_diario', 0))
            peca.preco_venda = Decimal(request.form.get('preco_venda', 0)) if request.form.get('preco_venda') else None
            peca.estado_fisico = request.form.get('estado_fisico', 'novo')
            peca.ativo = request.form.get('ativo') == 'on'
            
            db.session.commit()
            
            dados_novos = {
                'descricao': peca.descricao,
                'preco_aluguel_diario': str(peca.preco_aluguel_diario),
                'estado_fisico': peca.estado_fisico
            }
            
            _criar_auditoria('peca', peca.id, 'atualizacao', f"Peça {peca.codigo_interno} atualizada", dados_anteriores, dados_novos)
            
            flash(f'Peça {peca.codigo_interno} atualizada com sucesso!', 'success')
            return redirect(url_for('locacao.acervo_lista'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar peça: {str(e)}', 'danger')
    
    return render_template('acervo/editar.html', peca=peca)


@locacao_bp.route('/acervo/<int:peca_id>/disponibilidade', methods=['GET'])
@login_required
@require_permission('locacao_acervo')
def acervo_disponibilidade(peca_id):
    """Consulta disponibilidade de uma peça"""
    peca = LocacaoPeca.query.get_or_404(peca_id)
    
    # Parâmetros de data
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    if data_inicio and data_fim:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            disponivel, motivo, bloqueio_id = _consultar_disponibilidade(peca_id, data_inicio, data_fim)
            
            return jsonify({
                'disponivel': disponivel,
                'motivo': motivo,
                'bloqueio_id': bloqueio_id
            })
        except ValueError:
            return jsonify({'erro': 'Datas inválidas'}), 400
    
    # Se não houver parâmetros, retornar calendário de bloqueios
    bloqueios = LocacaoDisponibilidade.query.filter_by(peca_id=peca_id).all()
    
    return render_template('acervo/disponibilidade.html', peca=peca, bloqueios=bloqueios)


# ============================================================================
# 2. ORÇAMENTOS
# ============================================================================

@locacao_bp.route('/orcamentos', methods=['GET'])
@login_required
@require_permission('locacao_contratos')
def orcamentos_lista():
    """Lista orçamentos"""
    empresa_id = tenant_id()
    
    status = request.args.get('status', '')
    cliente_id = request.args.get('cliente_id', '')
    
    query = LocacaoOrcamento.query.filter_by(empresa_id=empresa_id)
    
    if status:
        query = query.filter_by(status=status)
    if cliente_id:
        query = query.filter_by(cliente_id=int(cliente_id))
    
    orcamentos = query.order_by(desc(LocacaoOrcamento.data_emissao)).all()
    
    clientes = Entidade.query.filter_by(empresa_id=empresa_id, tipo='C', ativo=True).order_by(Entidade.nome).all()
    
    return render_template('orcamentos/lista.html',
        orcamentos=orcamentos,
        clientes=clientes,
        status_filtro=status,
        cliente_id_filtro=cliente_id
    )


@locacao_bp.route('/orcamentos/criar', methods=['GET', 'POST'])
@login_required
@require_permission('locacao_contratos')
def orcamentos_criar():
    """Cria novo orçamento"""
    empresa_id = tenant_id()
    
    if request.method == 'POST':
        try:
            cliente_id = int(request.form.get('cliente_id'))
            data_retirada = datetime.strptime(request.form.get('data_retirada'), '%Y-%m-%d').date()
            data_devolucao = datetime.strptime(request.form.get('data_devolucao'), '%Y-%m-%d').date()
            
            dias_locacao = _calcular_dias_locacao(data_retirada, data_devolucao)
            
            orcamento = LocacaoOrcamento(
                empresa_id=empresa_id,
                numero=_gerar_numero_sequencial('ORC'),
                cliente_id=cliente_id,
                data_emissao=date.today(),
                data_validade=date.today() + timedelta(days=7),
                data_retirada_prevista=data_retirada,
                data_devolucao_prevista=data_devolucao,
                dias_locacao=dias_locacao,
                valor_aluguel=Decimal('0.00'),
                valor_total=Decimal('0.00'),
                status='rascunho',
                criado_por_user_id=current_user.id
            )
            
            db.session.add(orcamento)
            db.session.commit()
            
            _criar_auditoria('orcamento', orcamento.id, 'criacao', f"Orçamento {orcamento.numero} criado")
            
            flash(f'Orçamento {orcamento.numero} criado! Adicione itens.', 'success')
            return redirect(url_for('locacao.orcamentos_editar', orcamento_id=orcamento.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar orçamento: {str(e)}', 'danger')
    
    clientes = Entidade.query.filter_by(empresa_id=empresa_id, tipo='C', ativo=True).order_by(Entidade.nome).all()
    
    return render_template('orcamentos/criar.html', clientes=clientes)


@locacao_bp.route('/orcamentos/<int:orcamento_id>/editar', methods=['GET', 'POST'])
@login_required
@require_permission('locacao_contratos')
@validate_ownership(LocacaoOrcamento)
def orcamentos_editar(orcamento_id):
    """Edita orçamento e adiciona itens"""
    orcamento = LocacaoOrcamento.query.get_or_404(orcamento_id)
    
    if request.method == 'POST':
        acao = request.form.get('acao', '')
        
        if acao == 'adicionar_item':
            try:
                tipo_item = request.form.get('tipo_item')
                quantidade = int(request.form.get('quantidade', 1))
                
                if tipo_item == 'P':  # Peça
                    peca_id = int(request.form.get('peca_id'))
                    peca = LocacaoPeca.query.get_or_404(peca_id)
                    valor_unitario = peca.preco_aluguel_diario * orcamento.dias_locacao
                    descricao = peca.descricao
                    
                    item = LocacaoOrcamentoItem(
                        empresa_id=orcamento.empresa_id,
                        orcamento_id=orcamento_id,
                        tipo_item='P',
                        peca_id=peca_id,
                        descricao=descricao,
                        quantidade=quantidade,
                        valor_unitario=valor_unitario,
                        valor_total=valor_unitario * quantidade
                    )
                
                elif tipo_item == 'K':  # Kit
                    kit_id = int(request.form.get('kit_id'))
                    kit = LocacaoKit.query.get_or_404(kit_id)
                    valor_unitario = kit.preco_aluguel_diario * orcamento.dias_locacao
                    descricao = kit.descricao
                    
                    item = LocacaoOrcamentoItem(
                        empresa_id=orcamento.empresa_id,
                        orcamento_id=orcamento_id,
                        tipo_item='K',
                        kit_id=kit_id,
                        descricao=descricao,
                        quantidade=quantidade,
                        valor_unitario=valor_unitario,
                        valor_total=valor_unitario * quantidade
                    )
                
                db.session.add(item)
                db.session.flush()
                
                # Recalcular totais
                _recalcular_orcamento(orcamento)
                
                db.session.commit()
                flash('Item adicionado ao orçamento!', 'success')
            
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao adicionar item: {str(e)}', 'danger')
        
        elif acao == 'remover_item':
            try:
                item_id = int(request.form.get('item_id'))
                item = LocacaoOrcamentoItem.query.filter_by(id=item_id, orcamento_id=orcamento_id).first_or_404()
                db.session.delete(item)
                db.session.flush()
                
                _recalcular_orcamento(orcamento)
                db.session.commit()
                
                flash('Item removido!', 'success')
            
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao remover item: {str(e)}', 'danger')
        
        elif acao == 'finalizar':
            try:
                orcamento.status = 'enviado'
                db.session.commit()
                flash('Orçamento enviado para cliente!', 'success')
                return redirect(url_for('locacao.orcamentos_lista'))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao finalizar orçamento: {str(e)}', 'danger')
    
    pecas = LocacaoPeca.query.filter_by(empresa_id=orcamento.empresa_id, ativo=True).all()
    kits = LocacaoKit.query.filter_by(empresa_id=orcamento.empresa_id, ativo=True).all()
    
    return render_template('orcamentos/editar.html',
        orcamento=orcamento,
        pecas=pecas,
        kits=kits
    )


def _recalcular_orcamento(orcamento):
    """Recalcula totais do orçamento"""
    valor_aluguel = sum(item.valor_total for item in orcamento.itens)
    
    percentual_sinal = _get_parametro('percentual_sinal', 'numeric', 30)
    percentual_caucao = _get_parametro('percentual_caucao', 'numeric', 20)
    
    valor_sinal = valor_aluguel * Decimal(str(percentual_sinal)) / 100
    valor_caucao = valor_aluguel * Decimal(str(percentual_caucao)) / 100
    
    orcamento.valor_aluguel = valor_aluguel
    orcamento.valor_sinal = valor_sinal
    orcamento.valor_caucao = valor_caucao
    orcamento.valor_total = valor_aluguel


@locacao_bp.route('/orcamentos/<int:orcamento_id>/converter-reserva', methods=['POST'])
@login_required
@require_permission('locacao_contratos')
def orcamentos_converter_reserva(orcamento_id):
    """Converte orçamento aprovado em reserva"""
    orcamento = LocacaoOrcamento.query.get_or_404(orcamento_id)
    
    if orcamento.status != 'aprovado':
        flash('Apenas orçamentos aprovados podem ser convertidos em reserva.', 'danger')
        return redirect(url_for('locacao.orcamentos_lista'))
    
    try:
        # Criar reserva
        reserva = LocacaoReserva(
            empresa_id=orcamento.empresa_id,
            numero=_gerar_numero_sequencial('RES'),
            cliente_id=orcamento.cliente_id,
            evento_id=orcamento.evento_id,
            orcamento_id=orcamento.id,
            data_reserva=date.today(),
            data_retirada=orcamento.data_retirada_prevista,
            data_devolucao=orcamento.data_devolucao_prevista,
            dias_locacao=orcamento.dias_locacao,
            valor_aluguel=orcamento.valor_aluguel,
            valor_desconto=orcamento.valor_desconto,
            valor_acrescimo=orcamento.valor_acrescimo,
            valor_total=orcamento.valor_total,
            status='confirmada',
            criado_por_user_id=current_user.id
        )
        
        db.session.add(reserva)
        db.session.flush()
        
        # Bloquear disponibilidade de peças
        for item in orcamento.itens:
            if item.peca_id:
                _bloquear_disponibilidade(
                    item.peca_id,
                    orcamento.data_retirada_prevista,
                    orcamento.data_devolucao_prevista,
                    'reserva',
                    reserva.id,
                    'reserva'
                )
        
        # Criar contrato
        contrato = LocacaoContrato(
            empresa_id=orcamento.empresa_id,
            numero=_gerar_numero_sequencial('CTR'),
            cliente_id=orcamento.cliente_id,
            evento_id=orcamento.evento_id,
            reserva_id=reserva.id,
            data_contrato=date.today(),
            data_retirada=orcamento.data_retirada_prevista,
            data_devolucao=orcamento.data_devolucao_prevista,
            valor_aluguel=orcamento.valor_aluguel,
            valor_sinal=orcamento.valor_sinal,
            valor_caucao=orcamento.valor_caucao,
            valor_total=orcamento.valor_total,
            multa_atraso_diaria=_get_parametro('multa_atraso_diaria_valor', 'numeric', 0),
            multa_avaria_percentual=_get_parametro('multa_avaria_percentual', 'numeric', 50),
            multa_perda_percentual=_get_parametro('multa_perda_percentual', 'numeric', 100),
            status='assinado',
            assinado_por_empresa=True,
            assinado_em=datetime.now(),
            criado_por_user_id=current_user.id
        )
        
        db.session.add(contrato)
        db.session.flush()
        
        # Gerar títulos financeiros
        data_vencimento_sinal = date.today() + timedelta(days=5)
        data_vencimento_saldo = orcamento.data_retirada_prevista
        
        if orcamento.valor_sinal > 0:
            _gerar_titulo_financeiro(
                contrato.id,
                orcamento.cliente_id,
                'sinal',
                orcamento.valor_sinal,
                data_vencimento_sinal,
                f"Sinal - {contrato.numero}"
            )
        
        if orcamento.valor_caucao > 0:
            _gerar_titulo_financeiro(
                contrato.id,
                orcamento.cliente_id,
                'caucao',
                orcamento.valor_caucao,
                data_vencimento_sinal,
                f"Caução - {contrato.numero}"
            )
        
        saldo = orcamento.valor_total - orcamento.valor_sinal - orcamento.valor_caucao
        if saldo > 0:
            _gerar_titulo_financeiro(
                contrato.id,
                orcamento.cliente_id,
                'saldo',
                saldo,
                data_vencimento_saldo,
                f"Saldo - {contrato.numero}"
            )
        
        # Atualizar status
        orcamento.status = 'convertido'
        
        db.session.commit()
        
        _criar_auditoria('orcamento', orcamento.id, 'conversao', f"Orçamento convertido em reserva {reserva.numero}")
        
        flash(f'Orçamento convertido em Reserva {reserva.numero} e Contrato {contrato.numero}!', 'success')
        return redirect(url_for('locacao.contratos_visualizar', contrato_id=contrato.id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao converter orçamento: {str(e)}', 'danger')
        return redirect(url_for('locacao.orcamentos_lista'))


# ============================================================================
# 3. CONTRATOS
# ============================================================================

@locacao_bp.route('/contratos', methods=['GET'])
@login_required
@require_permission('locacao_contratos')
def contratos_lista():
    """Lista contratos"""
    empresa_id = tenant_id()
    
    status = request.args.get('status', '')
    
    query = LocacaoContrato.query.filter_by(empresa_id=empresa_id)
    
    if status:
        query = query.filter_by(status=status)
    
    contratos = query.order_by(desc(LocacaoContrato.data_contrato)).all()
    
    return render_template('contratos/lista.html', contratos=contratos, status_filtro=status)


@locacao_bp.route('/contratos/<int:contrato_id>', methods=['GET'])
@login_required
@require_permission('locacao_contratos')
def contratos_visualizar(contrato_id):
    """Visualiza contrato"""
    contrato = LocacaoContrato.query.get_or_404(contrato_id)
    
    return render_template('contratos/visualizar.html', contrato=contrato)


# ============================================================================
# 4. OPERAÇÃO - RETIRADA E DEVOLUÇÃO
# ============================================================================

@locacao_bp.route('/operacao/agenda', methods=['GET'])
@login_required
@require_permission('locacao_operacao')
def operacao_agenda():
    """Agenda de retiradas e devoluções"""
    empresa_id = tenant_id()
    
    data = request.args.get('data')
    if not data:
        data = date.today()
    else:
        data = datetime.strptime(data, '%Y-%m-%d').date()
    
    # Retiradas do dia
    retiradas = LocacaoRetirada.query.filter(
        LocacaoRetirada.empresa_id == empresa_id,
        func.date(LocacaoRetirada.data_retirada) == data
    ).all()
    
    # Devoluções do dia
    devolucoes = LocacaoDevolucao.query.filter(
        LocacaoDevolucao.empresa_id == empresa_id,
        func.date(LocacaoDevolucao.data_devolucao) == data
    ).all()
    
    return render_template('operacao/agenda.html',
        data=data,
        retiradas=retiradas,
        devolucoes=devolucoes
    )


@locacao_bp.route('/operacao/retirada/<int:contrato_id>', methods=['GET', 'POST'])
@login_required
@require_permission('locacao_operacao')
def operacao_retirada(contrato_id):
    """Registra retirada de peças"""
    contrato = LocacaoContrato.query.get_or_404(contrato_id)
    
    if request.method == 'POST':
        try:
            retirada = LocacaoRetirada(
                empresa_id=contrato.empresa_id,
                numero=_gerar_numero_sequencial('RET'),
                contrato_id=contrato_id,
                data_retirada=datetime.now(),
                responsavel_retirada=(request.form.get('responsavel') or '').strip(),
                user_retirada_id=current_user.id,
                modo_retirada=request.form.get('modo_retirada', 'balcao'),
                status='registrada'
            )
            
            db.session.add(retirada)
            db.session.flush()
            
            # Adicionar itens
            for item in contrato.reserva.itens if contrato.reserva else []:
                retirada_item = LocacaoRetiradaItem(
                    empresa_id=contrato.empresa_id,
                    retirada_id=retirada.id,
                    peca_id=item.peca_id if hasattr(item, 'peca_id') else None,
                    kit_id=item.kit_id if hasattr(item, 'kit_id') else None,
                    quantidade=item.quantidade if hasattr(item, 'quantidade') else 1
                )
                db.session.add(retirada_item)
            
            # Atualizar status do contrato
            contrato.status = 'ativo'
            
            db.session.commit()
            
            _criar_auditoria('retirada', retirada.id, 'criacao', f"Retirada {retirada.numero} registrada")
            
            flash(f'Retirada {retirada.numero} registrada com sucesso!', 'success')
            return redirect(url_for('locacao.operacao_agenda'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar retirada: {str(e)}', 'danger')
    
    return render_template('operacao/retirada.html', contrato=contrato)


@locacao_bp.route('/operacao/devolucao/<int:contrato_id>', methods=['GET', 'POST'])
@login_required
@require_permission('locacao_operacao')
def operacao_devolucao(contrato_id):
    """Registra devolução de peças"""
    contrato = LocacaoContrato.query.get_or_404(contrato_id)
    
    if request.method == 'POST':
        try:
            data_devolucao = datetime.now()
            data_prevista = contrato.data_devolucao
            dias_atraso = max(0, (data_devolucao.date() - data_prevista).days)
            multa_atraso = _calcular_multa_atraso(dias_atraso, contrato.valor_aluguel / contrato.data_devolucao.day)
            
            devolucao = LocacaoDevolucao(
                empresa_id=contrato.empresa_id,
                numero=_gerar_numero_sequencial('DEV'),
                contrato_id=contrato_id,
                data_devolucao=data_devolucao,
                data_devolucao_prevista=data_prevista,
                dias_atraso=dias_atraso,
                multa_atraso=multa_atraso,
                responsavel_devolucao=(request.form.get('responsavel') or '').strip(),
                user_devolucao_id=current_user.id,
                tipo_devolucao=request.form.get('tipo_devolucao', 'total'),
                status='registrada'
            )
            
            db.session.add(devolucao)
            db.session.flush()
            
            # Se houver multa, gerar título
            if multa_atraso > 0:
                _gerar_titulo_financeiro(
                    contrato_id,
                    contrato.cliente_id,
                    'multa',
                    multa_atraso,
                    date.today() + timedelta(days=5),
                    f"Multa por atraso - {devolucao.numero}"
                )
            
            db.session.commit()
            
            _criar_auditoria('devolucao', devolucao.id, 'criacao', f"Devolução {devolucao.numero} registrada")
            
            flash(f'Devolução {devolucao.numero} registrada! Prossiga com inspeção.', 'success')
            return redirect(url_for('locacao.operacao_inspecao', devolucao_id=devolucao.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar devolução: {str(e)}', 'danger')
    
    return render_template('operacao/devolucao.html', contrato=contrato)


@locacao_bp.route('/operacao/inspecao/<int:devolucao_id>', methods=['GET', 'POST'])
@login_required
@require_permission('locacao_operacao')
def operacao_inspecao(devolucao_id):
    """Realiza inspeção de peças devolvidas"""
    devolucao = LocacaoDevolucao.query.get_or_404(devolucao_id)
    
    if request.method == 'POST':
        try:
            peca_id = int(request.form.get('peca_id'))
            classificacao = request.form.get('classificacao')
            
            inspecao = LocacaoInspecao(
                empresa_id=devolucao.empresa_id,
                devolucao_id=devolucao_id,
                peca_id=peca_id,
                classificacao=classificacao
            )
            
            # Calcular cobranças baseado na classificação
            peca = LocacaoPeca.query.get(peca_id)
            
            if classificacao == 'sujo':
                inspecao.valor_limpeza = _get_parametro('valor_limpeza_padrao', 'numeric', 25)
            elif classificacao == 'avariado':
                inspecao.valor_reparo = _get_parametro('valor_reparo_padrao', 'numeric', 50)
            elif classificacao in ('faltante', 'perdido'):
                inspecao.valor_reposicao = peca.valor_reposicao if peca else Decimal('0.00')
            
            inspecao.valor_total_cobranca = inspecao.valor_limpeza + inspecao.valor_reparo + inspecao.valor_reposicao
            
            db.session.add(inspecao)
            
            # Se houver cobrança, gerar título
            if inspecao.valor_total_cobranca > 0:
                tipo_cobranca = 'avaria' if classificacao == 'avariado' else 'perda' if classificacao in ('faltante', 'perdido') else 'limpeza'
                
                _gerar_titulo_financeiro(
                    devolucao.contrato_id,
                    devolucao.contrato.cliente_id,
                    tipo_cobranca,
                    inspecao.valor_total_cobranca,
                    date.today() + timedelta(days=5),
                    f"Cobrança por {tipo_cobranca} - {peca.descricao if peca else 'Item'}"
                )
            
            db.session.commit()
            
            flash(f'Inspeção de {peca.descricao if peca else "item"} registrada!', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar inspeção: {str(e)}', 'danger')
    
    # Peças devolvidas não inspecionadas ainda
    pecas_devolvidas = db.session.query(LocacaoPeca).join(
        LocacaoRetiradaItem, LocacaoPeca.id == LocacaoRetiradaItem.peca_id
    ).filter(
        LocacaoRetiradaItem.retirada_id.in_(
            db.session.query(LocacaoRetirada.id).filter_by(contrato_id=devolucao.contrato_id)
        )
    ).all()
    
    inspecoes_realizadas = LocacaoInspecao.query.filter_by(devolucao_id=devolucao_id).all()
    peca_ids_inspecionadas = [i.peca_id for i in inspecoes_realizadas]
    
    pecas_pendentes = [p for p in pecas_devolvidas if p.id not in peca_ids_inspecionadas]
    
    return render_template('operacao/inspecao.html',
        devolucao=devolucao,
        pecas_pendentes=pecas_pendentes,
        inspecoes_realizadas=inspecoes_realizadas
    )


# ============================================================================
# 5. RELATÓRIOS
# ============================================================================

@locacao_bp.route('/relatorios/disponibilidade', methods=['GET'])
@login_required
@require_permission('locacao_agenda')
def relatorio_disponibilidade():
    """Relatório de disponibilidade por período"""
    empresa_id = tenant_id()
    
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    if not data_inicio or not data_fim:
        data_inicio = date.today()
        data_fim = date.today() + timedelta(days=30)
    else:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    pecas = LocacaoPeca.query.filter_by(empresa_id=empresa_id, ativo=True).all()
    
    disponibilidade_data = {}
    for peca in pecas:
        disponivel, motivo, _ = _consultar_disponibilidade(peca.id, data_inicio, data_fim)
        disponibilidade_data[peca.id] = {
            'peca': peca,
            'disponivel': disponivel,
            'motivo': motivo
        }
    
    return render_template('relatorios/disponibilidade.html',
        data_inicio=data_inicio,
        data_fim=data_fim,
        disponibilidade=disponibilidade_data
    )


@locacao_bp.route('/relatorios/receita', methods=['GET'])
@login_required
@require_permission('locacao_contratos')
def relatorio_receita():
    """Relatório de receita por período"""
    empresa_id = tenant_id()
    
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    if not data_inicio or not data_fim:
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()
    else:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    faturamentos = LocacaoFaturamento.query.filter(
        LocacaoFaturamento.empresa_id == empresa_id,
        LocacaoFaturamento.data_faturamento >= data_inicio,
        LocacaoFaturamento.data_faturamento <= data_fim
    ).all()
    
    total_aluguel = sum(f.valor_aluguel for f in faturamentos)
    total_multas = sum(f.valor_multa for f in faturamentos)
    total_avarias = sum(f.valor_avaria for f in faturamentos)
    total_geral = sum(f.valor_total for f in faturamentos)
    
    return render_template('relatorios/receita.html',
        data_inicio=data_inicio,
        data_fim=data_fim,
        faturamentos=faturamentos,
        total_aluguel=total_aluguel,
        total_multas=total_multas,
        total_avarias=total_avarias,
        total_geral=total_geral
    )


# ============================================================================
# API ENDPOINTS (para AJAX)
# ============================================================================

@locacao_bp.route('/api/pecas', methods=['GET'])
@login_required
def api_pecas():
    """API para listar peças (JSON)"""
    empresa_id = tenant_id()
    categoria = request.args.get('categoria', '')
    
    query = LocacaoPeca.query.filter_by(empresa_id=empresa_id, ativo=True)
    
    if categoria:
        query = query.filter_by(categoria=categoria)
    
    pecas = query.all()
    
    return jsonify([{
        'id': p.id,
        'codigo': p.codigo_interno,
        'descricao': p.descricao,
        'preco_aluguel_diario': float(p.preco_aluguel_diario),
        'categoria': p.categoria
    } for p in pecas])


@locacao_bp.route('/api/kits', methods=['GET'])
@login_required
def api_kits():
    """API para listar kits (JSON)"""
    empresa_id = tenant_id()
    
    kits = LocacaoKit.query.filter_by(empresa_id=empresa_id, ativo=True).all()
    
    return jsonify([{
        'id': k.id,
        'codigo': k.codigo_interno,
        'descricao': k.descricao,
        'preco_aluguel_diario': float(k.preco_aluguel_diario)
    } for k in kits])


@locacao_bp.route('/api/clientes', methods=['GET'])
@login_required
def api_clientes():
    """API para listar clientes (JSON)"""
    empresa_id = tenant_id()
    
    clientes = Entidade.query.filter_by(empresa_id=empresa_id, tipo='C', ativo=True).order_by(Entidade.nome).all()
    
    return jsonify([{
        'id': c.id,
        'nome': c.nome,
        'cnpj_cpf': c.cnpj_cpf
    } for c in clientes])


@locacao_bp.route('/api/disponibilidade-peca', methods=['POST'])
@login_required
def api_disponibilidade_peca():
    """API para verificar disponibilidade de peça"""
    try:
        data = request.get_json()
        peca_id = data.get('peca_id')
        data_inicio = datetime.strptime(data.get('data_inicio'), '%Y-%m-%d').date()
        data_fim = datetime.strptime(data.get('data_fim'), '%Y-%m-%d').date()
        
        disponivel, motivo, _ = _consultar_disponibilidade(peca_id, data_inicio, data_fim)
        
        return jsonify({
            'disponivel': disponivel,
            'motivo': motivo
        })
    
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
