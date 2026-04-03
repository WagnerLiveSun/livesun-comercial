from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from src.models import db, FluxoContaModel
from src.tenant import scoped_query, scoped_get_or_404, tenant_id

fluxo_bp = Blueprint('fluxo', __name__, url_prefix='/fluxo')


@fluxo_bp.route('/')
@login_required
def index():
    """List all chart of accounts"""
    page = request.args.get('page', 1, type=int)
    tipo = request.args.get('tipo', '')
    conta_ini = request.args.get('conta_ini', '')
    conta_fim = request.args.get('conta_fim', '')
    entidade_id = request.args.get('entidade_id', '')

    from src.models import Entidade
    entidades = scoped_query(Entidade).order_by(Entidade.nome).all()

    query = scoped_query(FluxoContaModel)
    if tipo:
        query = query.filter_by(tipo=tipo)
    # Filtro de conta (intervalo)
    # Filtro de conta (intervalo real, considerando códigos com subníveis)
    if conta_ini or conta_fim:
        contas_todas = scoped_query(FluxoContaModel).order_by(FluxoContaModel.codigo).all()
        def in_intervalo(codigo):
            if conta_ini and codigo < conta_ini:
                return False
            if conta_fim and codigo > conta_fim:
                return False
            return True
        codigos_intervalo = [c.codigo for c in contas_todas if in_intervalo(c.codigo)]
        query = query.filter(FluxoContaModel.codigo.in_(codigos_intervalo))
    # Filtro de entidade: mostrar apenas contas que possuem lançamentos para a entidade
    if entidade_id:
        from src.models import Lancamento
        contas_ids = db.session.query(Lancamento.fluxo_conta_id).filter(
            Lancamento.empresa_id == current_user.empresa_id,
            Lancamento.entidade_id == entidade_id
        ).distinct()
        query = query.filter(FluxoContaModel.id.in_(contas_ids))

    # Exibir sintéticas ao filtrar por conta analítica
    if conta_ini and conta_fim:
        contas_intervalo = scoped_query(FluxoContaModel).filter(
            FluxoContaModel.codigo >= conta_ini,
            FluxoContaModel.codigo <= conta_fim
        ).all()
        codigos_intervalo = [c.codigo for c in contas_intervalo]
        sint_codigos = set()
        for cod in codigos_intervalo:
            partes = cod.split('.')
            for i in range(1, len(partes)):
                sint_codigos.add('.'.join(partes[:i]))
        if sint_codigos:
            query = query.union(
                scoped_query(FluxoContaModel).filter(
                    FluxoContaModel.codigo.in_(sint_codigos)
                )
            )

    pagination = query.order_by(FluxoContaModel.codigo).paginate(page=page, per_page=20)
    contas = pagination.items

    return render_template(
        'fluxo/index.html',
        contas=contas,
        pagination=pagination,
        tipo=tipo,
        conta_ini=conta_ini,
        conta_fim=conta_fim,
        entidade_id=entidade_id,
        entidades=entidades
    )


@fluxo_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def criar():
    """Create new chart of account"""
    if request.method == 'POST':
        try:
            conta = FluxoContaModel(
                empresa_id=tenant_id(),
                codigo=request.form.get('codigo'),
                descricao=request.form.get('descricao'),
                tipo=request.form.get('tipo'),  # P ou R
                mascara=request.form.get('mascara'),
                nivel_sintetico=request.form.get('nivel_sintetico', type=int),
                nivel_analitico=request.form.get('nivel_analitico', type=int),
                ativo=request.form.get('ativo') == 'on'
            )
            
            db.session.add(conta)
            db.session.commit()
            
            flash(f'Conta {conta.codigo} criada com sucesso', 'success')
            return redirect(url_for('fluxo.index'))
        
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao criar conta: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao criar conta: {str(e)}', 'danger')
    
    return render_template('fluxo/form.html', action='criar')


@fluxo_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edit chart of account"""
    conta = scoped_get_or_404(FluxoContaModel, id)
    
    if request.method == 'POST':
        try:
            conta.codigo = request.form.get('codigo')
            conta.descricao = request.form.get('descricao')
            conta.tipo = request.form.get('tipo')
            conta.mascara = request.form.get('mascara')
            conta.nivel_sintetico = request.form.get('nivel_sintetico', type=int)
            conta.nivel_analitico = request.form.get('nivel_analitico', type=int)
            conta.ativo = request.form.get('ativo') == 'on'
            
            db.session.commit()
            
            flash(f'Conta {conta.codigo} atualizada com sucesso', 'success')
            return redirect(url_for('fluxo.index'))
        
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao atualizar conta: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao atualizar conta: {str(e)}', 'danger')
    
    return render_template('fluxo/form.html', action='editar', conta=conta)


@fluxo_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
def deletar(id):
    """Delete chart of account"""
    conta = scoped_get_or_404(FluxoContaModel, id)
    
    try:
        conta.ativo = False
        db.session.commit()
        flash(f'Conta {conta.codigo} desativada com sucesso', 'success')
    except Exception as e:
        import logging, traceback
        db.session.rollback()
        logging.error('Erro ao deletar conta: %s\n%s', e, traceback.format_exc())
        flash(f'Erro ao deletar conta: {str(e)}', 'danger')
    
    return redirect(url_for('fluxo.index'))


@fluxo_bp.route('/api/search')
@login_required
def api_search():
    """API for chart of accounts search"""
    termo = request.args.get('q', '')
    tipo = request.args.get('tipo', '')
    
    query = scoped_query(FluxoContaModel).filter(FluxoContaModel.ativo == True)
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    if termo:
        query = query.filter(
            (FluxoContaModel.codigo.ilike(f'%{termo}%')) |
            (FluxoContaModel.descricao.ilike(f'%{termo}%'))
        )
    
    contas = query.limit(20).all()
    
    return jsonify([{
        'id': c.id,
        'text': f'{c.codigo} - {c.descricao}',
        'codigo': c.codigo,
        'tipo': c.tipo
    } for c in contas])
