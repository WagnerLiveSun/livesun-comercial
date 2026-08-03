from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from src.models import db, Lancamento, Entidade, FluxoContaModel, ContaBanco
from datetime import datetime, date
from src.services.fluxo_consolidado import consolidar_fluxo_caixa
from src.services.planos import is_basic_plan, normalize_plan
from src.tenant import scoped_query, scoped_get_or_404, tenant_id

lancamentos_bp = Blueprint('lancamentos', __name__, url_prefix='/lancamentos')


def _is_basic_company_plan() -> bool:
    plano_empresa = normalize_plan(getattr(getattr(current_user, 'empresa', None), 'plano', 'premium'))
    return is_basic_plan(plano_empresa)


def _get_default_fluxo_conta_id(tipo_movimentacao: str) -> int | None:
    # Regra do plano Básico: usar conta sintética padrão do modelo.
    # Recebimento -> código "1" | Pagamento -> código "2".
    codigo_padrao = '1' if tipo_movimentacao == 'R' else '2'
    descricao_padrao = 'Entradas de Caixa' if tipo_movimentacao == 'R' else 'Saídas de Caixa'

    conta = (
        scoped_query(FluxoContaModel)
        .filter_by(tipo=tipo_movimentacao, codigo=codigo_padrao)
        .order_by(FluxoContaModel.ativo.desc(), FluxoContaModel.id.asc())
        .first()
    )
    if conta:
        if not conta.ativo:
            conta.ativo = True
            db.session.flush()
        return conta.id

    # Se não existir a sintética padrão, cria automaticamente para evitar bloqueio operacional no Básico.
    conta = FluxoContaModel(
        empresa_id=tenant_id(),
        codigo=codigo_padrao,
        descricao=descricao_padrao,
        tipo=tipo_movimentacao,
        nivel_sintetico=1,
        nivel_analitico=None,
        ativo=True,
    )
    db.session.add(conta)
    db.session.flush()
    if conta.id:
        return conta.id

    conta = (
        scoped_query(FluxoContaModel)
        .filter_by(ativo=True, tipo=tipo_movimentacao, codigo=codigo_padrao)
        .order_by(FluxoContaModel.id.asc())
        .first()
    )
    if conta:
        return conta.id

    # Fallback seguro para ambientes onde o plano padrão ainda não foi carregado.
    conta = (
        scoped_query(FluxoContaModel)
        .filter_by(ativo=True, tipo=tipo_movimentacao)
        .filter(FluxoContaModel.nivel_analitico.isnot(None))
        .order_by(FluxoContaModel.codigo.asc())
        .first()
    )
    if conta:
        return conta.id

    conta = (
        scoped_query(FluxoContaModel)
        .filter_by(ativo=True, tipo=tipo_movimentacao)
        .order_by(FluxoContaModel.codigo.asc())
        .first()
    )
    return conta.id if conta else None


@lancamentos_bp.route('/')
@login_required
def index():
    """List all lancamentos"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    tipo = request.args.get('tipo', '')  # P para Pagamento, R para Recebimento
    conta_banco_id = request.args.get('conta_banco_id', type=int)
    data_evento = request.args.get('data_evento', '')
    select_mode = request.args.get('select_mode', '') == '1'
    conciliacao_id = request.args.get('conciliacao_id', type=int)
    item_id = request.args.get('item_id', type=int)
    
    # Join explícito com Entidade para garantir acesso ao nome e tipo
    query = scoped_query(Lancamento).join(Entidade, isouter=True)

    if status:
        query = query.filter_by(status=status)

    if tipo:
        query = query.join(FluxoContaModel).filter(FluxoContaModel.tipo == tipo)

    if conta_banco_id:
        query = query.filter(Lancamento.conta_banco_id == conta_banco_id)

    if data_evento:
        try:
            dt_evento = datetime.strptime(data_evento, '%Y-%m-%d').date()
            query = query.filter(Lancamento.data_evento == dt_evento)
        except ValueError:
            flash('Data de evento inválida para filtro.', 'warning')

    pagination = query.order_by(Lancamento.data_vencimento.desc()).paginate(page=page, per_page=20)
    lancamentos = pagination.items
    contas_banco = scoped_query(ContaBanco).filter_by(ativo=True).all()

    return render_template(
        'lancamentos/index.html',
        lancamentos=lancamentos,
        pagination=pagination,
        status=status,
        tipo=tipo,
        conta_banco_id=conta_banco_id,
        data_evento=data_evento,
        contas_banco=contas_banco,
        select_mode=select_mode,
        conciliacao_id=conciliacao_id,
        item_id=item_id,
    )


@lancamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def criar():
    """Create new lancamento"""
    plano_basico = _is_basic_company_plan()
    entidades = scoped_query(Entidade).filter_by(ativo=True).all()
    contas_fluxo = scoped_query(FluxoContaModel).filter_by(ativo=True).all()
    contas_banco = scoped_query(ContaBanco).filter_by(ativo=True).all()
    if request.method == 'POST':
        try:
            valor_real_raw = (request.form.get('valor_real') or '').strip()
            if not valor_real_raw:
                raise ValueError('Valor Real é obrigatório.')

            valor_real = float(valor_real_raw)
            if valor_real <= 0:
                raise ValueError('Valor Real deve ser maior que zero.')

            fluxo_conta_id = request.form.get('fluxo_conta_id', type=int)
            if plano_basico:
                tipo_movimentacao = (request.form.get('tipo_movimentacao') or '').strip().upper()
                if tipo_movimentacao not in {'P', 'R'}:
                    raise ValueError('No plano Básico, selecione o tipo da movimentação (Pagamento ou Recebimento).')
                fluxo_conta_id = _get_default_fluxo_conta_id(tipo_movimentacao)
                if not fluxo_conta_id:
                    raise ValueError(
                        f'Não foi encontrada conta de fluxo padrão ativa para {"Pagamento" if tipo_movimentacao == "P" else "Recebimento"}. '
                        'Cadastre ao menos uma conta de fluxo desse tipo.'
                    )
            elif not fluxo_conta_id:
                raise ValueError('Conta de Fluxo é obrigatória.')

            lancamento = Lancamento(
                empresa_id=tenant_id(),
                data_evento=datetime.strptime(request.form.get('data_evento'), '%Y-%m-%d').date(),
                data_vencimento=datetime.strptime(request.form.get('data_vencimento'), '%Y-%m-%d').date(),
                data_pagamento=None,
                status='aberto' if not request.form.get('data_pagamento') else 'pago',
                fluxo_conta_id=fluxo_conta_id,
                conta_banco_id=request.form.get('conta_banco_id', type=int),
                entidade_id=request.form.get('entidade_id', type=int),
                valor_real=valor_real,
                valor_pago=0.00 if not request.form.get('data_pagamento') else valor_real,
                valor_imposto=float(request.form.get('valor_imposto') or 0),
                valor_outros_custos=float(request.form.get('valor_outros_custos') or 0),
                numero_documento=request.form.get('numero_documento'),
                observacoes=request.form.get('observacoes')
            )
            
            # Se houver data de pagamento, converter
            if request.form.get('data_pagamento'):
                lancamento.data_pagamento = datetime.strptime(request.form.get('data_pagamento'), '%Y-%m-%d').date()
                lancamento.status = 'pago'
                lancamento.valor_pago = valor_real
            
            db.session.add(lancamento)
            db.session.commit()
            consolidar_fluxo_caixa(current_user.empresa_id)
            
            flash(f'Lançamento {lancamento.numero_documento} criado com sucesso', 'success')
            return redirect(url_for('lancamentos.index'))
        
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao criar lançamento: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao criar lançamento: {str(e)}', 'danger')
    
    return render_template(
        'lancamentos/form.html',
        action='criar',
        plano_basico=plano_basico,
        entidades=entidades,
        contas_fluxo=contas_fluxo,
        contas_banco=contas_banco
    )


@lancamentos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edit lancamento"""
    plano_basico = _is_basic_company_plan()
    lancamento = scoped_get_or_404(Lancamento, id)
    entidades = scoped_query(Entidade).filter_by(ativo=True).all()
    contas_fluxo = scoped_query(FluxoContaModel).filter_by(ativo=True).all()
    contas_banco = scoped_query(ContaBanco).filter_by(ativo=True).all()
    
    if request.method == 'POST':
        try:
            valor_real_raw = (request.form.get('valor_real') or '').strip()
            if not valor_real_raw:
                raise ValueError('Valor Real é obrigatório.')

            valor_real = float(valor_real_raw)
            if valor_real <= 0:
                raise ValueError('Valor Real deve ser maior que zero.')

            fluxo_conta_id = request.form.get('fluxo_conta_id', type=int)
            if plano_basico:
                tipo_movimentacao = (request.form.get('tipo_movimentacao') or '').strip().upper()
                if tipo_movimentacao not in {'P', 'R'}:
                    raise ValueError('No plano Básico, selecione o tipo da movimentação (Pagamento ou Recebimento).')
                fluxo_conta_id = _get_default_fluxo_conta_id(tipo_movimentacao)
                if not fluxo_conta_id:
                    raise ValueError(
                        f'Não foi encontrada conta de fluxo padrão ativa para {"Pagamento" if tipo_movimentacao == "P" else "Recebimento"}. '
                        'Cadastre ao menos uma conta de fluxo desse tipo.'
                    )
            elif not fluxo_conta_id:
                raise ValueError('Conta de Fluxo é obrigatória.')

            lancamento.data_evento = datetime.strptime(request.form.get('data_evento'), '%Y-%m-%d').date()
            lancamento.data_vencimento = datetime.strptime(request.form.get('data_vencimento'), '%Y-%m-%d').date()
            lancamento.fluxo_conta_id = fluxo_conta_id
            lancamento.conta_banco_id = request.form.get('conta_banco_id', type=int)
            lancamento.entidade_id = request.form.get('entidade_id', type=int)
            lancamento.valor_real = valor_real
            lancamento.valor_imposto = float(request.form.get('valor_imposto') or 0)
            lancamento.valor_outros_custos = float(request.form.get('valor_outros_custos') or 0)
            lancamento.numero_documento = request.form.get('numero_documento')
            lancamento.observacoes = request.form.get('observacoes')
            
            # Handle payment
            if request.form.get('data_pagamento'):
                lancamento.data_pagamento = datetime.strptime(request.form.get('data_pagamento'), '%Y-%m-%d').date()
                lancamento.status = 'pago'
                lancamento.valor_pago = float(request.form.get('valor_pago') or lancamento.valor_real)
            else:
                lancamento.data_pagamento = None
                lancamento.valor_pago = 0.00
                lancamento.status = 'aberto'
            
            db.session.commit()
            consolidar_fluxo_caixa(current_user.empresa_id)
            
            flash(f'Lançamento {lancamento.numero_documento} atualizado com sucesso', 'success')
            return redirect(url_for('lancamentos.index'))
        
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao atualizar lançamento: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao atualizar lançamento: {str(e)}', 'danger')
    
    return render_template(
        'lancamentos/form.html',
        action='editar',
        plano_basico=plano_basico,
        lancamento=lancamento,
        entidades=entidades,
        contas_fluxo=contas_fluxo,
        contas_banco=contas_banco
    )


@lancamentos_bp.route('/<int:id>/pagar', methods=['POST'])
@login_required
def pagar(id):
    """Mark lancamento as paid"""
    lancamento = scoped_get_or_404(Lancamento, id)
    
    try:
        lancamento.data_pagamento = date.today()
        lancamento.valor_pago = float(lancamento.valor_real)
        lancamento.status = 'pago'
        
        db.session.commit()
        consolidar_fluxo_caixa(current_user.empresa_id)
        
        flash(f'Lançamento {lancamento.numero_documento} marcado como pago', 'success')
    except Exception as e:
        import logging, traceback
        db.session.rollback()
        logging.error('Erro ao pagar lançamento: %s\n%s', e, traceback.format_exc())
        flash(f'Erro ao pagar lançamento: {str(e)}', 'danger')
    
    return redirect(url_for('lancamentos.index'))


@lancamentos_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
def deletar(id):
    """Delete lancamento"""
    lancamento = scoped_get_or_404(Lancamento, id)
    
    try:
        db.session.delete(lancamento)
        db.session.commit()
        # Recalcula o consolidado para remover reflexos do lançamento excluído
        from src.services.fluxo_consolidado import consolidar_fluxo_caixa
        consolidar_fluxo_caixa(current_user.empresa_id)
        flash(f'Lançamento deletado com sucesso', 'success')
    except Exception as e:
        import logging, traceback
        db.session.rollback()
        logging.error('Erro ao deletar lançamento: %s\n%s', e, traceback.format_exc())
        flash(f'Erro ao deletar lançamento: {str(e)}', 'danger')
    
    return redirect(url_for('lancamentos.index'))
