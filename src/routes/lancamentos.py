from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from src.models import db, Lancamento, Entidade, FluxoContaModel, ContaBanco
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace
from urllib.parse import urlsplit
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload
from src.services.fluxo_consolidado import consolidar_fluxo_caixa
from src.services.planos import is_basic_plan, normalize_plan
from src.tenant import scoped_query, scoped_get_or_404, tenant_id

lancamentos_bp = Blueprint('lancamentos', __name__, url_prefix='/lancamentos')


def _return_url():
    """Aceita somente retorno à listagem local; nunca redireciona para fora."""
    target = request.values.get('next', '')
    parsed = urlsplit(target)
    if not parsed.scheme and not parsed.netloc and parsed.path == url_for('lancamentos.index') and '\\' not in target and not any(ord(c) < 32 for c in target):
        return target
    return url_for('lancamentos.index')


def _money(field, label, default=None, positive=False):
    raw = (request.form.get(field) or '').strip()
    if not raw:
        if default is None:
            raise ValueError(f'{label} é obrigatório.')
        raw = str(default)
    try:
        value = Decimal(raw)
        if not value.is_finite() or value < 0 or value >= Decimal('10000000000000'):
            raise ValueError()
        if value != value.quantize(Decimal('0.01')) or (positive and value <= 0):
            raise ValueError()
    except (InvalidOperation, ValueError):
        raise ValueError(f'{label} deve ser um valor válido, {"maior que zero" if positive else "não negativo"}, com até duas casas decimais.')
    return value.quantize(Decimal('0.01'))


def _related_id(model, field, label, original=None):
    selected = request.form.get(field, type=int)
    record = scoped_query(model).filter(model.id == selected).first() if selected else None
    if not record or (not record.ativo and selected != original):
        raise ValueError(f'{label}: selecione um cadastro válido da empresa.')
    return selected


def _form_options(model, original=None):
    return scoped_query(model).filter(or_(model.ativo.is_(True), model.id == original)).order_by(model.id).all()


def _save_form(lancamento, plano_basico):
    """Valida todos os campos antes de modificar o lançamento."""
    values = {
        'data_evento': datetime.strptime(request.form.get('data_evento') or '', '%Y-%m-%d').date(),
        'data_vencimento': datetime.strptime(request.form.get('data_vencimento') or '', '%Y-%m-%d').date(),
        'entidade_id': _related_id(Entidade, 'entidade_id', 'Entidade', lancamento.entidade_id),
        'conta_banco_id': _related_id(ContaBanco, 'conta_banco_id', 'Conta bancária', lancamento.conta_banco_id),
        'valor_real': _money('valor_real', 'Valor Real', positive=True),
        'valor_imposto': _money('valor_imposto', 'Valor Imposto', default=0),
        'valor_outros_custos': _money('valor_outros_custos', 'Outros Custos', default=0),
        'numero_documento': (request.form.get('numero_documento') or '').strip(),
        'observacoes': request.form.get('observacoes', ''),
    }
    if not values['numero_documento'] or len(values['numero_documento']) > 50:
        raise ValueError('Informe um número de documento com até 50 caracteres.')
    if plano_basico:
        tipo = request.form.get('tipo_movimentacao', '').upper()
        if tipo not in {'P', 'R'}:
            raise ValueError('Selecione Pagamento ou Recebimento.')
        values['fluxo_conta_id'] = _get_default_fluxo_conta_id(tipo)
    else:
        values['fluxo_conta_id'] = _related_id(FluxoContaModel, 'fluxo_conta_id', 'Conta de fluxo', lancamento.fluxo_conta_id)
    payment_date = request.form.get('data_pagamento')
    if payment_date:
        values.update(data_pagamento=datetime.strptime(payment_date, '%Y-%m-%d').date(),
                      valor_pago=_money('valor_pago', 'Valor Pago/Recebido', default=values['valor_real'], positive=True), status='pago')
    else:
        if request.form.get('valor_pago') and _money('valor_pago', 'Valor Pago/Recebido', default=0) > 0:
            raise ValueError('Informe a data da baixa para registrar o valor pago/recebido.')
        values.update(data_pagamento=None, valor_pago=Decimal('0.00'), status='aberto')
    for key, value in values.items():
        setattr(lancamento, key, value)


def _form_record(lancamento=None):
    """Mantém o que foi digitado após erro de validação, sem persistir dados."""
    if request.method != 'POST':
        return lancamento
    fields = ('data_evento', 'data_vencimento', 'data_pagamento', 'valor_real', 'valor_pago',
              'valor_imposto', 'valor_outros_custos', 'numero_documento', 'observacoes')
    values = {field: request.form.get(field, '') for field in fields}
    for field in ('entidade_id', 'fluxo_conta_id', 'conta_banco_id'):
        values[field] = request.form.get(field, type=int)
    values['fluxo_conta'] = lancamento.fluxo_conta if lancamento else None
    return SimpleNamespace(**values)


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
    query = scoped_query(Lancamento).options(
        joinedload(Lancamento.entidade), joinedload(Lancamento.fluxo_conta),
        joinedload(Lancamento.conta_banco), selectinload(Lancamento.asaas_cobrancas),
        selectinload(Lancamento.inter_cobrancas),
    )

    if status:
        query = query.filter(Lancamento.status == status)

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

    pagination = query.order_by(Lancamento.data_vencimento.desc(), Lancamento.id.desc()).paginate(page=max(page, 1), per_page=20, error_out=False)
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
        return_url=request.full_path.rstrip('?'),
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
            lancamento = Lancamento(empresa_id=tenant_id())
            _save_form(lancamento, plano_basico)
            
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
        lancamento=_form_record(),
        return_url=_return_url(),
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
    entidades = _form_options(Entidade, lancamento.entidade_id)
    contas_fluxo = _form_options(FluxoContaModel, lancamento.fluxo_conta_id)
    contas_banco = _form_options(ContaBanco, lancamento.conta_banco_id)
    
    if request.method == 'POST':
        try:
            _save_form(lancamento, plano_basico)
            
            db.session.commit()
            consolidar_fluxo_caixa(current_user.empresa_id)
            
            flash(f'Lançamento {lancamento.numero_documento} atualizado com sucesso', 'success')
            return redirect(_return_url())
        
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao atualizar lançamento: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao atualizar lançamento: {str(e)}', 'danger')
    
    return render_template(
        'lancamentos/form.html',
        action='editar',
        plano_basico=plano_basico,
        lancamento=_form_record(lancamento),
        return_url=_return_url(),
        entidades=entidades,
        contas_fluxo=contas_fluxo,
        contas_banco=contas_banco
    )


@lancamentos_bp.route('/<int:id>/pagar', methods=['POST'])
@login_required
def pagar(id):
    """Mark lancamento as paid"""
    lancamento = scoped_get_or_404(Lancamento, id)

    if lancamento.status == 'pago':
        flash('Este lançamento já possui baixa. Use Editar para manutenção.', 'warning')
        return redirect(_return_url())

    try:
        payment_date = datetime.strptime(request.form.get('data_pagamento') or date.today().isoformat(), '%Y-%m-%d').date()
        payment_value = _money('valor_pago', 'Valor Pago/Recebido', default=lancamento.valor_real, positive=True)
        lancamento.data_pagamento = payment_date
        lancamento.valor_pago = payment_value
        lancamento.status = 'pago'
        
        db.session.commit()
        consolidar_fluxo_caixa(current_user.empresa_id)
        
        flash(f'Lançamento {lancamento.numero_documento} marcado como pago', 'success')
    except Exception as e:
        import logging, traceback
        db.session.rollback()
        logging.error('Erro ao pagar lançamento: %s\n%s', e, traceback.format_exc())
        flash(f'Erro ao pagar lançamento: {str(e)}', 'danger')
    
    return redirect(_return_url())


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
    
    return redirect(_return_url())
