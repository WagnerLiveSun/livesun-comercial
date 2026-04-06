from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from src.models import db, ContaBanco, ConciliacaoBancaria, ConciliacaoItem, Lancamento
from src.services.conciliacao import criar_conciliacao_ofx, reconciliar_conciliacao
from src.tenant import scoped_query, scoped_get_or_404

conciliacao_bp = Blueprint('conciliacao', __name__, url_prefix='/conciliacao')


@conciliacao_bp.route('/')
@login_required
def index():
    conciliacoes = ConciliacaoBancaria.query.filter_by(empresa_id=current_user.empresa_id).order_by(ConciliacaoBancaria.id.desc()).all()
    return render_template('conciliacao/index.html', conciliacoes=conciliacoes)


@conciliacao_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    contas = scoped_query(ContaBanco).filter_by(ativo=True).all()

    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        conta_banco_id = request.form.get('conta_banco_id', type=int)

        if not arquivo or not arquivo.filename:
            flash('Selecione um arquivo OFX.', 'danger')
            return redirect(url_for('conciliacao.nova'))

        if not conta_banco_id:
            flash('Selecione uma conta bancária.', 'danger')
            return redirect(url_for('conciliacao.nova'))

        try:
            conciliacao = criar_conciliacao_ofx(
                empresa_id=current_user.empresa_id,
                conta_banco_id=conta_banco_id,
                ofx_content=arquivo.read().decode('utf-8', errors='ignore'),
                criado_por_user_id=current_user.id,
            )
            resultado = reconciliar_conciliacao(conciliacao.id, current_user.empresa_id)
            flash(
                f'Conciliação criada e processada: {resultado["conciliados"]} conciliados, {resultado["pendentes"]} pendentes, {resultado["divergentes"]} divergentes.',
                'success' if resultado['conciliados'] else 'warning'
            )
            return redirect(url_for('conciliacao.detalhe', conciliacao_id=conciliacao.id))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao processar conciliação: {exc}', 'danger')
            return redirect(url_for('conciliacao.nova'))

    return render_template('conciliacao/nova.html', contas=contas)


@conciliacao_bp.route('/<int:conciliacao_id>')
@login_required
def detalhe(conciliacao_id):
    conciliacao = scoped_get_or_404(ConciliacaoBancaria, conciliacao_id)
    return render_template('conciliacao/detalhe.html', conciliacao=conciliacao)


@conciliacao_bp.route('/<int:conciliacao_id>/reconciliar', methods=['POST'])
@login_required
def reconciliar(conciliacao_id):
    try:
        resultado = reconciliar_conciliacao(conciliacao_id, current_user.empresa_id)
        flash(
            f'Reconciliação executada: {resultado["conciliados"]} conciliados, {resultado["pendentes"]} pendentes, {resultado["divergentes"]} divergentes.',
            'success'
        )
    except Exception as exc:
        flash(f'Erro ao reconciliar: {exc}', 'danger')
    return redirect(url_for('conciliacao.detalhe', conciliacao_id=conciliacao_id))


@conciliacao_bp.route('/<int:conciliacao_id>/itens/<int:item_id>/vincular/<int:lancamento_id>', methods=['POST'])
@login_required
def vincular_item(conciliacao_id, item_id, lancamento_id):
    conciliacao = ConciliacaoBancaria.query.filter_by(
        id=conciliacao_id,
        empresa_id=current_user.empresa_id,
    ).first_or_404()

    item = ConciliacaoItem.query.filter_by(
        id=item_id,
        conciliacao_id=conciliacao.id,
        empresa_id=current_user.empresa_id,
    ).first_or_404()

    lancamento = Lancamento.query.filter_by(
        id=lancamento_id,
        empresa_id=current_user.empresa_id,
    ).first_or_404()

    if lancamento.conta_banco_id != conciliacao.conta_banco_id:
        flash('O lançamento selecionado não pertence à mesma conta bancária da conciliação.', 'danger')
        return redirect(url_for('conciliacao.detalhe', conciliacao_id=conciliacao.id))

    if item.valor_extrato < 0 and lancamento.fluxo_conta and not lancamento.fluxo_conta.is_pagamento():
        flash('Para débito no extrato, selecione um lançamento de Pagamento (tipo P).', 'warning')
        return redirect(url_for('conciliacao.detalhe', conciliacao_id=conciliacao.id))

    if item.valor_extrato > 0 and lancamento.fluxo_conta and not lancamento.fluxo_conta.is_recebimento():
        flash('Para crédito no extrato, selecione um lançamento de Recebimento (tipo R).', 'warning')
        return redirect(url_for('conciliacao.detalhe', conciliacao_id=conciliacao.id))

    item.lancamento_id = lancamento.id
    item.status = 'conciliado'
    item.motivo_divergencia = 'vinculado_manual'

    lancamento.status = 'pago'
    lancamento.data_pagamento = item.data_movimento
    lancamento.valor_pago = abs(item.valor_extrato)
    lancamento.referencia_banco = item.referencia_banco or lancamento.referencia_banco
    lancamento.fonte = 'ofx'

    db.session.commit()
    flash(f'Item #{item.id} conciliado manualmente com o lançamento #{lancamento.id}.', 'success')
    return redirect(url_for('conciliacao.detalhe', conciliacao_id=conciliacao.id))


@conciliacao_bp.route('/<int:conciliacao_id>/itens/<int:item_id>/desvincular', methods=['POST'])
@login_required
def desvincular_item(conciliacao_id, item_id):
    conciliacao = ConciliacaoBancaria.query.filter_by(
        id=conciliacao_id,
        empresa_id=current_user.empresa_id,
    ).first_or_404()

    item = ConciliacaoItem.query.filter_by(
        id=item_id,
        conciliacao_id=conciliacao.id,
        empresa_id=current_user.empresa_id,
    ).first_or_404()

    if not item.lancamento_id:
        flash('Este item já está sem vínculo de lançamento.', 'info')
        return redirect(url_for('conciliacao.detalhe', conciliacao_id=conciliacao.id))

    item.lancamento_id = None
    item.status = 'pendente'
    item.motivo_divergencia = 'ajuste_manual_desvinculado'

    db.session.commit()
    flash(f'Vínculo do item #{item.id} removido. Se necessário, vincule novamente ao lançamento correto.', 'success')
    return redirect(url_for('conciliacao.detalhe', conciliacao_id=conciliacao.id))
