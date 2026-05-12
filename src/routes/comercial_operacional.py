from decimal import Decimal
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from src.models import (
    db,
    Filial,
    Produto,
    Servico,
    EstoqueMovimento,
    Entidade,
    FluxoContaModel,
    ContaBanco,
    Lancamento,
    CompraNFManual,
    CompraNFItem,
    CompraNFLancamento,
    DocumentoVenda,
    DocumentoVendaItem,
)
from src.tenant import scoped_query, scoped_get_or_404, tenant_id


comercial_bp = Blueprint('comercial_operacional', __name__, url_prefix='/comercial')


def _parse_decimal(value, default: Decimal = Decimal('0.00')) -> Decimal:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return Decimal(text.replace(',', '.'))
    except Exception:
        return default


@comercial_bp.route('/filiais')
@login_required
def filiais_index():
    page = request.args.get('page', 1, type=int)
    busca = (request.args.get('busca') or '').strip()

    query = scoped_query(Filial)
    if busca:
        query = query.filter(
            (Filial.codigo.ilike(f'%{busca}%')) |
            (Filial.nome.ilike(f'%{busca}%')) |
            (Filial.cnpj.ilike(f'%{busca}%'))
        )

    pagination = query.order_by(Filial.codigo.asc()).paginate(page=page, per_page=20)
    return render_template(
        'comercial/filiais_index.html',
        filiais=pagination.items,
        pagination=pagination,
        busca=busca,
    )


@comercial_bp.route('/filiais/nova', methods=['GET', 'POST'])
@login_required
def filiais_criar():
    if request.method == 'POST':
        try:
            filial = Filial(
                empresa_id=tenant_id(),
                codigo=(request.form.get('codigo') or '').strip(),
                nome=(request.form.get('nome') or '').strip(),
                cnpj=(request.form.get('cnpj') or '').strip() or None,
                endereco_rua=request.form.get('endereco_rua') or None,
                endereco_numero=request.form.get('endereco_numero') or None,
                endereco_bairro=request.form.get('endereco_bairro') or None,
                endereco_cidade=request.form.get('endereco_cidade') or None,
                endereco_uf=request.form.get('endereco_uf') or None,
                endereco_cep=request.form.get('endereco_cep') or None,
                ativo=request.form.get('ativo') == 'on',
            )
            if not filial.codigo or not filial.nome:
                raise ValueError('Codigo e nome sao obrigatorios.')

            db.session.add(filial)
            db.session.commit()
            flash('Filial criada com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.filiais_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao criar filial: {exc}', 'danger')

    return render_template('comercial/filiais_form.html', action='criar', filial=None)


@comercial_bp.route('/filiais/<int:filial_id>/editar', methods=['GET', 'POST'])
@login_required
def filiais_editar(filial_id):
    filial = scoped_get_or_404(Filial, filial_id)

    if request.method == 'POST':
        try:
            filial.codigo = (request.form.get('codigo') or '').strip()
            filial.nome = (request.form.get('nome') or '').strip()
            filial.cnpj = (request.form.get('cnpj') or '').strip() or None
            filial.endereco_rua = request.form.get('endereco_rua') or None
            filial.endereco_numero = request.form.get('endereco_numero') or None
            filial.endereco_bairro = request.form.get('endereco_bairro') or None
            filial.endereco_cidade = request.form.get('endereco_cidade') or None
            filial.endereco_uf = request.form.get('endereco_uf') or None
            filial.endereco_cep = request.form.get('endereco_cep') or None
            filial.ativo = request.form.get('ativo') == 'on'

            if not filial.codigo or not filial.nome:
                raise ValueError('Codigo e nome sao obrigatorios.')

            db.session.commit()
            flash('Filial atualizada com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.filiais_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao atualizar filial: {exc}', 'danger')

    return render_template('comercial/filiais_form.html', action='editar', filial=filial)


@comercial_bp.route('/filiais/<int:filial_id>/deletar', methods=['POST'])
@login_required
def filiais_deletar(filial_id):
    filial = scoped_get_or_404(Filial, filial_id)

    try:
        filial.ativo = False
        db.session.commit()
        flash('Filial desativada com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao desativar filial: {exc}', 'danger')

    return redirect(url_for('comercial_operacional.filiais_index'))


@comercial_bp.route('/produtos')
@login_required
def produtos_index():
    page = request.args.get('page', 1, type=int)
    busca = (request.args.get('busca') or '').strip()
    filial_id = request.args.get('filial_id', type=int)

    query = scoped_query(Produto)
    if filial_id:
        query = query.filter_by(filial_id=filial_id)
    if busca:
        query = query.filter(
            (Produto.codigo_interno.ilike(f'%{busca}%')) |
            (Produto.descricao_resumida.ilike(f'%{busca}%')) |
            (Produto.ncm.ilike(f'%{busca}%'))
        )

    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()
    pagination = query.order_by(Produto.descricao_resumida.asc()).paginate(page=page, per_page=20)

    return render_template(
        'comercial/produtos_index.html',
        produtos=pagination.items,
        pagination=pagination,
        busca=busca,
        filial_id=filial_id,
        filiais=filiais,
    )


@comercial_bp.route('/produtos/novo', methods=['GET', 'POST'])
@login_required
def produtos_criar():
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()

    if request.method == 'POST':
        try:
            produto = Produto(
                empresa_id=tenant_id(),
                filial_id=request.form.get('filial_id', type=int) or None,
                codigo_interno=(request.form.get('codigo_interno') or '').strip(),
                descricao_resumida=(request.form.get('descricao_resumida') or '').strip(),
                descricao_completa=request.form.get('descricao_completa') or None,
                unidade_medida=request.form.get('unidade_medida') or None,
                codigo_barras=request.form.get('codigo_barras') or None,
                gtin=request.form.get('gtin') or None,
                ncm=request.form.get('ncm') or None,
                ex_tipi=request.form.get('ex_tipi') or None,
                cest=request.form.get('cest') or None,
                ipi_classe=request.form.get('ipi_classe') or None,
                origem_mercadoria=request.form.get('origem_mercadoria') or None,
                tipo_item=request.form.get('tipo_item') or None,
                controla_estoque=request.form.get('controla_estoque') == 'on',
                estoque_atual=Decimal((request.form.get('estoque_inicial') or '0').replace(',', '.')),
                estoque_minimo=Decimal((request.form.get('estoque_minimo') or '0').replace(',', '.')),
                valor_custo=Decimal((request.form.get('valor_custo') or '0').replace(',', '.')),
                valor_venda_padrao=Decimal((request.form.get('valor_venda_padrao') or '0').replace(',', '.')),
                ativo=request.form.get('ativo') == 'on',
            )
            if not produto.codigo_interno or not produto.descricao_resumida:
                raise ValueError('Codigo interno e descricao sao obrigatorios.')

            db.session.add(produto)
            db.session.commit()
            flash('Produto criado com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.produtos_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao criar produto: {exc}', 'danger')

    return render_template('comercial/produtos_form.html', action='criar', produto=None, filiais=filiais)


@comercial_bp.route('/produtos/<int:produto_id>/editar', methods=['GET', 'POST'])
@login_required
def produtos_editar(produto_id):
    produto = scoped_get_or_404(Produto, produto_id)
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()

    if request.method == 'POST':
        try:
            produto.filial_id = request.form.get('filial_id', type=int) or None
            produto.codigo_interno = (request.form.get('codigo_interno') or '').strip()
            produto.descricao_resumida = (request.form.get('descricao_resumida') or '').strip()
            produto.descricao_completa = request.form.get('descricao_completa') or None
            produto.unidade_medida = request.form.get('unidade_medida') or None
            produto.codigo_barras = request.form.get('codigo_barras') or None
            produto.gtin = request.form.get('gtin') or None
            produto.ncm = request.form.get('ncm') or None
            produto.ex_tipi = request.form.get('ex_tipi') or None
            produto.cest = request.form.get('cest') or None
            produto.ipi_classe = request.form.get('ipi_classe') or None
            produto.origem_mercadoria = request.form.get('origem_mercadoria') or None
            produto.tipo_item = request.form.get('tipo_item') or None
            produto.controla_estoque = request.form.get('controla_estoque') == 'on'
            produto.estoque_minimo = Decimal((request.form.get('estoque_minimo') or '0').replace(',', '.'))
            produto.valor_custo = Decimal((request.form.get('valor_custo') or '0').replace(',', '.'))
            produto.valor_venda_padrao = Decimal((request.form.get('valor_venda_padrao') or '0').replace(',', '.'))
            produto.ativo = request.form.get('ativo') == 'on'

            if not produto.codigo_interno or not produto.descricao_resumida:
                raise ValueError('Codigo interno e descricao sao obrigatorios.')

            db.session.commit()
            flash('Produto atualizado com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.produtos_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao atualizar produto: {exc}', 'danger')

    return render_template('comercial/produtos_form.html', action='editar', produto=produto, filiais=filiais)


@comercial_bp.route('/produtos/<int:produto_id>/deletar', methods=['POST'])
@login_required
def produtos_deletar(produto_id):
    produto = scoped_get_or_404(Produto, produto_id)

    try:
        produto.ativo = False
        db.session.commit()
        flash('Produto desativado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao desativar produto: {exc}', 'danger')

    return redirect(url_for('comercial_operacional.produtos_index'))


@comercial_bp.route('/servicos')
@login_required
def servicos_index():
    page = request.args.get('page', 1, type=int)
    busca = (request.args.get('busca') or '').strip()
    filial_id = request.args.get('filial_id', type=int)

    query = scoped_query(Servico)
    if filial_id:
        query = query.filter_by(filial_id=filial_id)
    if busca:
        query = query.filter(
            (Servico.codigo_interno.ilike(f'%{busca}%')) |
            (Servico.descricao.ilike(f'%{busca}%')) |
            (Servico.codigo_servico.ilike(f'%{busca}%'))
        )

    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()
    pagination = query.order_by(Servico.descricao.asc()).paginate(page=page, per_page=20)

    return render_template(
        'comercial/servicos_index.html',
        servicos=pagination.items,
        pagination=pagination,
        busca=busca,
        filial_id=filial_id,
        filiais=filiais,
    )


@comercial_bp.route('/servicos/novo', methods=['GET', 'POST'])
@login_required
def servicos_criar():
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()

    if request.method == 'POST':
        try:
            servico = Servico(
                empresa_id=tenant_id(),
                filial_id=request.form.get('filial_id', type=int) or None,
                codigo_interno=(request.form.get('codigo_interno') or '').strip(),
                descricao=(request.form.get('descricao') or '').strip(),
                codigo_servico=request.form.get('codigo_servico') or None,
                nbs=request.form.get('nbs') or None,
                natureza_servico=request.form.get('natureza_servico') or None,
                indicador_incidencia=request.form.get('indicador_incidencia') or None,
                ativo=request.form.get('ativo') == 'on',
            )
            if not servico.codigo_interno or not servico.descricao:
                raise ValueError('Codigo interno e descricao sao obrigatorios.')

            db.session.add(servico)
            db.session.commit()
            flash('Servico criado com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.servicos_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao criar servico: {exc}', 'danger')

    return render_template('comercial/servicos_form.html', action='criar', servico=None, filiais=filiais)


@comercial_bp.route('/servicos/<int:servico_id>/editar', methods=['GET', 'POST'])
@login_required
def servicos_editar(servico_id):
    servico = scoped_get_or_404(Servico, servico_id)
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()

    if request.method == 'POST':
        try:
            servico.filial_id = request.form.get('filial_id', type=int) or None
            servico.codigo_interno = (request.form.get('codigo_interno') or '').strip()
            servico.descricao = (request.form.get('descricao') or '').strip()
            servico.codigo_servico = request.form.get('codigo_servico') or None
            servico.nbs = request.form.get('nbs') or None
            servico.natureza_servico = request.form.get('natureza_servico') or None
            servico.indicador_incidencia = request.form.get('indicador_incidencia') or None
            servico.ativo = request.form.get('ativo') == 'on'

            if not servico.codigo_interno or not servico.descricao:
                raise ValueError('Codigo interno e descricao sao obrigatorios.')

            db.session.commit()
            flash('Servico atualizado com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.servicos_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao atualizar servico: {exc}', 'danger')

    return render_template('comercial/servicos_form.html', action='editar', servico=servico, filiais=filiais)


@comercial_bp.route('/servicos/<int:servico_id>/deletar', methods=['POST'])
@login_required
def servicos_deletar(servico_id):
    servico = scoped_get_or_404(Servico, servico_id)

    try:
        servico.ativo = False
        db.session.commit()
        flash('Servico desativado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao desativar servico: {exc}', 'danger')

    return redirect(url_for('comercial_operacional.servicos_index'))


@comercial_bp.route('/estoque')
@login_required
def estoque_index():
    page = request.args.get('page', 1, type=int)
    produto_id = request.args.get('produto_id', type=int)
    tipo_movimento = (request.args.get('tipo_movimento') or '').strip()

    query = scoped_query(EstoqueMovimento)
    if produto_id:
        query = query.filter_by(produto_id=produto_id)
    if tipo_movimento:
        query = query.filter_by(tipo_movimento=tipo_movimento)

    produtos = scoped_query(Produto).filter_by(ativo=True).order_by(Produto.descricao_resumida.asc()).all()
    pagination = query.order_by(EstoqueMovimento.data_movimento.desc(), EstoqueMovimento.id.desc()).paginate(page=page, per_page=20)

    return render_template(
        'comercial/estoque_index.html',
        movimentos=pagination.items,
        pagination=pagination,
        produtos=produtos,
        produto_id=produto_id,
        tipo_movimento=tipo_movimento,
    )


@comercial_bp.route('/estoque/novo', methods=['GET', 'POST'])
@login_required
def estoque_criar():
    produtos = scoped_query(Produto).filter_by(ativo=True).order_by(Produto.descricao_resumida.asc()).all()
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()

    if request.method == 'POST':
        try:
            produto_id = request.form.get('produto_id', type=int)
            tipo_movimento = (request.form.get('tipo_movimento') or '').strip().lower()
            quantidade_raw = (request.form.get('quantidade') or '0').replace(',', '.')
            valor_unitario_raw = (request.form.get('valor_unitario') or '').replace(',', '.')
            data_movimento_str = (request.form.get('data_movimento') or '').strip()

            produto = scoped_get_or_404(Produto, produto_id)
            quantidade = Decimal(quantidade_raw)
            valor_unitario = Decimal(valor_unitario_raw) if valor_unitario_raw else None

            if quantidade <= 0:
                raise ValueError('Quantidade deve ser maior que zero.')

            if tipo_movimento not in {'entrada', 'saida', 'ajuste'}:
                raise ValueError('Tipo de movimento invalido.')

            delta = quantidade
            if tipo_movimento == 'saida':
                delta = -quantidade
                if produto.controla_estoque and produto.estoque_atual is not None:
                    estoque_atual = Decimal(str(produto.estoque_atual))
                    if estoque_atual + delta < 0:
                        raise ValueError('Estoque insuficiente para a saida informada.')
            elif tipo_movimento == 'ajuste':
                ajuste_sinal = (request.form.get('ajuste_sinal') or 'entrada').strip().lower()
                if ajuste_sinal not in {'entrada', 'saida'}:
                    raise ValueError('Ajuste invalido. Use entrada ou saida.')
                delta = quantidade if ajuste_sinal == 'entrada' else -quantidade
                if ajuste_sinal == 'saida' and produto.controla_estoque and produto.estoque_atual is not None:
                    estoque_atual = Decimal(str(produto.estoque_atual))
                    if estoque_atual + delta < 0:
                        raise ValueError('Estoque insuficiente para o ajuste de saida.')

            if data_movimento_str:
                data_movimento = datetime.strptime(data_movimento_str, '%Y-%m-%d').date()
            else:
                data_movimento = date.today()

            movimento = EstoqueMovimento(
                empresa_id=tenant_id(),
                filial_id=request.form.get('filial_id', type=int) or None,
                produto_id=produto.id,
                tipo_movimento=tipo_movimento,
                quantidade=abs(quantidade) if tipo_movimento != 'ajuste' else abs(delta),
                valor_unitario=valor_unitario,
                origem=(request.form.get('origem') or 'manual').strip().lower(),
                documento_ref=request.form.get('documento_ref') or None,
                data_movimento=data_movimento,
                criado_por_user_id=current_user.id,
            )
            db.session.add(movimento)

            if produto.controla_estoque:
                produto.estoque_atual = Decimal(str(produto.estoque_atual or 0)) + delta

            db.session.commit()
            flash('Movimento de estoque registrado com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.estoque_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao registrar movimento: {exc}', 'danger')

    return render_template(
        'comercial/estoque_form.html',
        produtos=produtos,
        filiais=filiais,
        today=date.today(),
    )


@comercial_bp.route('/compras')
@login_required
def compras_index():
    page = request.args.get('page', 1, type=int)
    numero_documento = (request.args.get('numero_documento') or '').strip()
    fornecedor_id = request.args.get('fornecedor_id', type=int)

    query = scoped_query(CompraNFManual)
    if numero_documento:
        query = query.filter(CompraNFManual.numero_documento.ilike(f'%{numero_documento}%'))
    if fornecedor_id:
        query = query.filter_by(fornecedor_id=fornecedor_id)

    fornecedores = scoped_query(Entidade).filter_by(tipo='F', ativo=True).order_by(Entidade.nome.asc()).all()
    pagination = query.order_by(CompraNFManual.data_emissao.desc(), CompraNFManual.id.desc()).paginate(page=page, per_page=20)

    return render_template(
        'comercial/compras_index.html',
        compras=pagination.items,
        pagination=pagination,
        numero_documento=numero_documento,
        fornecedor_id=fornecedor_id,
        fornecedores=fornecedores,
    )


@comercial_bp.route('/compras/nova', methods=['GET', 'POST'])
@login_required
def compras_criar():
    fornecedores = scoped_query(Entidade).filter_by(tipo='F', ativo=True).order_by(Entidade.nome.asc()).all()
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()
    produtos = scoped_query(Produto).filter_by(ativo=True).order_by(Produto.descricao_resumida.asc()).all()
    contas_banco = scoped_query(ContaBanco).filter_by(ativo=True).order_by(ContaBanco.nome.asc()).all()
    contas_fluxo = scoped_query(FluxoContaModel).filter_by(ativo=True, tipo='P').order_by(FluxoContaModel.codigo.asc()).all()
    
    # Buscar conta de fluxo padrão para compras (1.01.01 ou primeira conta P)
    conta_fluxo_padrao = None
    if contas_fluxo:
        conta_fluxo_padrao = next((c for c in contas_fluxo if c.codigo == '1.01.01'), contas_fluxo[0])

    if request.method == 'POST':
        try:
            fornecedor_id = request.form.get('fornecedor_id', type=int)
            numero_documento = (request.form.get('numero_documento') or '').strip()
            serie = (request.form.get('serie') or '').strip() or None
            data_emissao = datetime.strptime(request.form.get('data_emissao') or '', '%Y-%m-%d').date()
            data_entrada = datetime.strptime(request.form.get('data_entrada') or '', '%Y-%m-%d').date()

            fluxo_conta_id = request.form.get('fluxo_conta_id', type=int)
            conta_banco_id = request.form.get('conta_banco_id', type=int)
            data_vencimento = datetime.strptime(request.form.get('data_vencimento') or '', '%Y-%m-%d').date()
            data_pagamento_str = (request.form.get('data_pagamento') or '').strip()
            data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date() if data_pagamento_str else None
            parcelas = request.form.get('parcelas', type=int) or 1
            intervalo_dias = request.form.get('intervalo_dias', type=int) or 30

            if parcelas < 1:
                parcelas = 1
            if parcelas > 1 and data_pagamento:
                raise ValueError('Nao informe pagamento quando houver parcelamento.')

            if not fornecedor_id or not numero_documento:
                raise ValueError('Fornecedor e numero do documento sao obrigatorios.')

            if not fluxo_conta_id or not conta_banco_id:
                raise ValueError('Conta de fluxo e conta bancaria sao obrigatorias.')

            fluxo_conta = scoped_get_or_404(FluxoContaModel, fluxo_conta_id)
            if not fluxo_conta.is_pagamento():
                raise ValueError('Conta de fluxo deve ser do tipo Pagamento (P).')

            itens = []
            total = Decimal('0.00')

            produto_ids = request.form.getlist('item_produto_id')
            descricoes = request.form.getlist('item_descricao')
            quantidades = request.form.getlist('item_quantidade')
            valores = request.form.getlist('item_valor_unitario')
            ncms = request.form.getlist('item_ncm')
            cfops = request.form.getlist('item_cfop')
            csts = request.form.getlist('item_cst')
            csosns = request.form.getlist('item_csosn')

            for idx in range(len(quantidades)):
                produto_id_raw = (produto_ids[idx] or '').strip() if idx < len(produto_ids) else ''
                descricao = (descricoes[idx] or '').strip() if idx < len(descricoes) else ''
                quantidade = _parse_decimal(quantidades[idx] if idx < len(quantidades) else '0')
                valor_unitario = _parse_decimal(valores[idx] if idx < len(valores) else '0')

                if not produto_id_raw and not descricao:
                    continue
                if quantidade <= 0:
                    raise ValueError('Quantidade deve ser maior que zero.')

                produto_id = int(produto_id_raw) if produto_id_raw else None
                total_item = quantidade * valor_unitario
                total += total_item

                itens.append({
                    'produto_id': produto_id,
                    'descricao_livre': descricao or None,
                    'quantidade': quantidade,
                    'valor_unitario': valor_unitario,
                    'total_item': total_item,
                    'ncm': (ncms[idx] or '').strip() if idx < len(ncms) else None,
                    'cfop': (cfops[idx] or '').strip() if idx < len(cfops) else None,
                    'cst': (csts[idx] or '').strip() if idx < len(csts) else None,
                    'csosn': (csosns[idx] or '').strip() if idx < len(csosns) else None,
                })

            if not itens:
                raise ValueError('Informe ao menos um item na compra.')
            
            # Validar valor mínimo da nota
            if total <= 0:
                raise ValueError('O valor total da nota deve ser maior que zero.')
            
            # Capturar outros custos (frete, seguro, etc)
            outros_custos = Decimal((request.form.get('outros_custos') or '0').replace(',', '.'))
            valor_total_nota = total + outros_custos

            compra = CompraNFManual(
                empresa_id=tenant_id(),
                filial_id=request.form.get('filial_id', type=int) or None,
                fornecedor_id=fornecedor_id,
                lancamento_id=None,
                numero_documento=numero_documento,
                serie=serie,
                data_emissao=data_emissao,
                data_entrada=data_entrada,
                valor_total=valor_total_nota,
                valor_outros_custos=outros_custos,
                observacoes=request.form.get('observacoes') or None,
                criado_por_user_id=current_user.id,
            )
            db.session.add(compra)
            db.session.flush()

            valor_base = (valor_total_nota / parcelas).quantize(Decimal('0.01')) if parcelas > 1 else valor_total_nota
            valor_restante = total - (valor_base * parcelas)

            for parcela in range(1, parcelas + 1):
                vencimento_parcela = data_vencimento + timedelta(days=intervalo_dias * (parcela - 1))
                valor_parcela = valor_base
                if parcela == parcelas:
                    valor_parcela += valor_restante

                lancamento = Lancamento(
                    empresa_id=tenant_id(),
                    data_evento=data_emissao,
                    data_vencimento=vencimento_parcela,
                    data_pagamento=None,
                    status='aberto',
                    fluxo_conta_id=fluxo_conta_id,
                    conta_banco_id=conta_banco_id,
                    entidade_id=fornecedor_id,
                    valor_real=valor_parcela,
                    valor_pago=Decimal('0.00'),
                    valor_imposto=Decimal('0.00'),
                    valor_outros_custos=Decimal('0.00'),
                    numero_documento=numero_documento,
                    observacoes=f'Compra NF manual - parcela {parcela}/{parcelas}',
                    fonte='manual',
                )

                if parcelas == 1 and data_pagamento:
                    lancamento.data_pagamento = data_pagamento
                    lancamento.status = 'pago'
                    lancamento.valor_pago = valor_parcela

                db.session.add(lancamento)
                db.session.flush()

                link = CompraNFLancamento(
                    empresa_id=tenant_id(),
                    compra_id=compra.id,
                    lancamento_id=lancamento.id,
                    parcela_numero=parcela,
                    parcela_total=parcelas,
                    valor_parcela=valor_parcela,
                    data_vencimento=vencimento_parcela,
                )
                db.session.add(link)

            for item in itens:
                compra_item = CompraNFItem(
                    empresa_id=tenant_id(),
                    compra_id=compra.id,
                    produto_id=item['produto_id'],
                    descricao_livre=item['descricao_livre'],
                    quantidade=item['quantidade'],
                    valor_unitario=item['valor_unitario'],
                    total_item=item['total_item'],
                    ncm=item['ncm'],
                    cfop=item['cfop'],
                    cst=item['cst'],
                    csosn=item['csosn'],
                )
                db.session.add(compra_item)

                if item['produto_id']:
                    produto = scoped_get_or_404(Produto, item['produto_id'])
                    if produto.controla_estoque:
                        produto.estoque_atual = Decimal(str(produto.estoque_atual or 0)) + item['quantidade']
                        movimento = EstoqueMovimento(
                            empresa_id=tenant_id(),
                            filial_id=compra.filial_id,
                            produto_id=produto.id,
                            tipo_movimento='entrada',
                            quantidade=item['quantidade'],
                            valor_unitario=item['valor_unitario'],
                            origem='compra',
                            documento_ref=numero_documento,
                            data_movimento=data_entrada,
                            criado_por_user_id=current_user.id,
                        )
                        db.session.add(movimento)

            db.session.commit()
            flash('Compra registrada com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.compras_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao registrar compra: {exc}', 'danger')

    return render_template(
        'comercial/compras_form.html',
        fornecedores=fornecedores,
        filiais=filiais,
        produtos=produtos,
        contas_banco=contas_banco,
        contas_fluxo=contas_fluxo,
        conta_fluxo_padrao=conta_fluxo_padrao,
        today=date.today(),
    )


@comercial_bp.route('/compras/<int:compra_id>')
@login_required
def compras_detalhe(compra_id):
    compra = scoped_get_or_404(CompraNFManual, compra_id)
    return render_template('comercial/compras_detalhe.html', compra=compra)


@comercial_bp.route('/compras/<int:compra_id>/editar', methods=['GET', 'POST'])
@login_required
def compras_editar(compra_id):
    """Edita NF de compra (apenas dados básicos, não itens nem valores)."""
    compra = scoped_get_or_404(CompraNFManual, compra_id)
    
    # Verificar se já foi paga (tem lançamentos pagos)
    links = scoped_query(CompraNFLancamento).filter_by(compra_id=compra.id).all()
    tem_pagamento = False
    for link in links:
        lancamento = Lancamento.query.get(link.lancamento_id)
        if lancamento and lancamento.status == 'pago':
            tem_pagamento = True
            break
    
    if tem_pagamento:
        flash('Não é possível editar compra que já possui pagamentos efetuados.', 'warning')
        return redirect(url_for('comercial_operacional.compras_detalhe', compra_id=compra.id))
    
    fornecedores = scoped_query(Entidade).filter_by(tipo='F', ativo=True).order_by(Entidade.nome.asc()).all()
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()
    
    if request.method == 'POST':
        try:
            compra.fornecedor_id = request.form.get('fornecedor_id', type=int)
            compra.numero_documento = (request.form.get('numero_documento') or '').strip()
            compra.serie = (request.form.get('serie') or '').strip() or None
            compra.data_emissao = datetime.strptime(request.form.get('data_emissao') or '', '%Y-%m-%d').date()
            compra.data_entrada = datetime.strptime(request.form.get('data_entrada') or '', '%Y-%m-%d').date()
            compra.filial_id = request.form.get('filial_id', type=int) or None
            compra.observacoes = request.form.get('observacoes') or None
            
            db.session.commit()
            flash('Compra atualizada com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.compras_detalhe', compra_id=compra.id))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao atualizar compra: {exc}', 'danger')
    
    return render_template(
        'comercial/compras_editar.html',
        compra=compra,
        fornecedores=fornecedores,
        filiais=filiais,
    )


@comercial_bp.route('/compras/<int:compra_id>/excluir', methods=['POST'])
@login_required
def compras_excluir(compra_id):
    """Exclui NF de compra e seus itens/lançamentos (se não estiver paga)."""
    compra = scoped_get_or_404(CompraNFManual, compra_id)
    
    try:
        # Verificar se já foi paga
        links = scoped_query(CompraNFLancamento).filter_by(compra_id=compra.id).all()
        for link in links:
            lancamento = Lancamento.query.get(link.lancamento_id)
            if lancamento and lancamento.status == 'pago':
                flash('Não é possível excluir compra que já possui pagamentos efetuados.', 'warning')
                return redirect(url_for('comercial_operacional.compras_detalhe', compra_id=compra.id))
        
        # Reverter estoque dos itens
        itens = scoped_query(CompraNFItem).filter_by(compra_id=compra.id).all()
        for item in itens:
            if item.produto_id:
                produto = Produto.query.get(item.produto_id)
                if produto and produto.controla_estoque:
                    produto.estoque_atual = Decimal(str(produto.estoque_atual or 0)) - item.quantidade
            db.session.delete(item)
        
        # Excluir lançamentos e links
        for link in links:
            lancamento = Lancamento.query.get(link.lancamento_id)
            if lancamento:
                db.session.delete(lancamento)
            db.session.delete(link)
        
        db.session.delete(compra)
        db.session.commit()
        flash('Compra excluída com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao excluir compra: {exc}', 'danger')
    
    return redirect(url_for('comercial_operacional.compras_index'))


@comercial_bp.route('/documentos')
@login_required
def documentos_index():
    page = request.args.get('page', 1, type=int)
    numero_documento = (request.args.get('numero_documento') or '').strip()
    cliente_id = request.args.get('cliente_id', type=int)

    query = scoped_query(DocumentoVenda)
    if numero_documento:
        query = query.filter(DocumentoVenda.numero_documento.ilike(f'%{numero_documento}%'))
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)

    clientes = scoped_query(Entidade).filter_by(tipo='C', ativo=True).order_by(Entidade.nome.asc()).all()
    pagination = query.order_by(DocumentoVenda.data_emissao.desc(), DocumentoVenda.id.desc()).paginate(page=page, per_page=20)

    return render_template(
        'comercial/documentos_index.html',
        documentos=pagination.items,
        pagination=pagination,
        numero_documento=numero_documento,
        cliente_id=cliente_id,
        clientes=clientes,
    )


@comercial_bp.route('/documentos/novo', methods=['GET', 'POST'])
@login_required
def documentos_criar():
    clientes = scoped_query(Entidade).filter_by(tipo='C', ativo=True).order_by(Entidade.nome.asc()).all()
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()
    produtos = scoped_query(Produto).filter_by(ativo=True).order_by(Produto.descricao_resumida.asc()).all()
    servicos = scoped_query(Servico).filter_by(ativo=True).order_by(Servico.descricao.asc()).all()
    contas_banco = scoped_query(ContaBanco).filter_by(ativo=True).order_by(ContaBanco.nome.asc()).all()
    contas_fluxo = scoped_query(FluxoContaModel).filter_by(ativo=True, tipo='R').order_by(FluxoContaModel.codigo.asc()).all()

    if request.method == 'POST':
        try:
            cliente_id = request.form.get('cliente_id', type=int)
            numero_documento = (request.form.get('numero_documento') or '').strip()
            data_emissao = datetime.strptime(request.form.get('data_emissao') or '', '%Y-%m-%d').date()
            data_vencimento = datetime.strptime(request.form.get('data_vencimento') or '', '%Y-%m-%d').date()
            data_pagamento_str = (request.form.get('data_pagamento') or '').strip()
            data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date() if data_pagamento_str else None

            fluxo_conta_id = request.form.get('fluxo_conta_id', type=int)
            conta_banco_id = request.form.get('conta_banco_id', type=int)

            if not cliente_id or not numero_documento:
                raise ValueError('Cliente e numero do documento sao obrigatorios.')

            if not fluxo_conta_id or not conta_banco_id:
                raise ValueError('Conta de fluxo e conta bancaria sao obrigatorias.')

            fluxo_conta = scoped_get_or_404(FluxoContaModel, fluxo_conta_id)
            if not fluxo_conta.is_recebimento():
                raise ValueError('Conta de fluxo deve ser do tipo Recebimento (R).')

            tipos = request.form.getlist('item_tipo')
            produto_ids = request.form.getlist('item_produto_id')
            servico_ids = request.form.getlist('item_servico_id')
            descricoes = request.form.getlist('item_descricao')
            quantidades = request.form.getlist('item_quantidade')
            valores = request.form.getlist('item_valor_unitario')

            itens = []
            total = Decimal('0.00')

            for idx in range(len(quantidades)):
                tipo_item = (tipos[idx] or '').strip().upper() if idx < len(tipos) else ''
                quantidade = _parse_decimal(quantidades[idx] if idx < len(quantidades) else '0')
                valor_unitario = _parse_decimal(valores[idx] if idx < len(valores) else '0')
                descricao = (descricoes[idx] or '').strip() if idx < len(descricoes) else ''

                produto_id_raw = (produto_ids[idx] or '').strip() if idx < len(produto_ids) else ''
                servico_id_raw = (servico_ids[idx] or '').strip() if idx < len(servico_ids) else ''

                if quantidade <= 0:
                    continue

                if tipo_item not in {'P', 'S'}:
                    raise ValueError('Tipo de item invalido. Use P ou S.')

                produto_id = int(produto_id_raw) if produto_id_raw else None
                servico_id = int(servico_id_raw) if servico_id_raw else None

                if tipo_item == 'P' and not produto_id:
                    raise ValueError('Produto obrigatorio para item do tipo produto.')
                if tipo_item == 'S' and not servico_id:
                    raise ValueError('Servico obrigatorio para item do tipo servico.')

                total_item = quantidade * valor_unitario
                total += total_item

                itens.append({
                    'tipo_item': tipo_item,
                    'produto_id': produto_id,
                    'servico_id': servico_id,
                    'descricao': descricao or None,
                    'quantidade': quantidade,
                    'valor_unitario': valor_unitario,
                    'total_item': total_item,
                })

            if not itens:
                raise ValueError('Informe ao menos um item na venda.')

            lancamento = Lancamento(
                empresa_id=tenant_id(),
                data_evento=data_emissao,
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento,
                status='pago' if data_pagamento else 'aberto',
                fluxo_conta_id=fluxo_conta_id,
                conta_banco_id=conta_banco_id,
                entidade_id=cliente_id,
                valor_real=total,
                valor_pago=total if data_pagamento else Decimal('0.00'),
                valor_imposto=Decimal('0.00'),
                valor_outros_custos=Decimal('0.00'),
                numero_documento=numero_documento,
                observacoes='Documento nao fiscal',
                fonte='manual',
            )
            db.session.add(lancamento)
            db.session.flush()

            documento = DocumentoVenda(
                empresa_id=tenant_id(),
                filial_id=request.form.get('filial_id', type=int) or None,
                cliente_id=cliente_id,
                lancamento_id=lancamento.id,
                numero_documento=numero_documento,
                data_emissao=data_emissao,
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento,
                valor_total=total,
                observacoes=request.form.get('observacoes') or None,
                status='pago' if data_pagamento else 'emitido',
                criado_por_user_id=current_user.id,
            )
            db.session.add(documento)
            db.session.flush()

            for item in itens:
                doc_item = DocumentoVendaItem(
                    empresa_id=tenant_id(),
                    documento_id=documento.id,
                    tipo_item=item['tipo_item'],
                    produto_id=item['produto_id'],
                    servico_id=item['servico_id'],
                    descricao=item['descricao'],
                    quantidade=item['quantidade'],
                    valor_unitario=item['valor_unitario'],
                    total_item=item['total_item'],
                )
                db.session.add(doc_item)

                if item['produto_id']:
                    produto = scoped_get_or_404(Produto, item['produto_id'])
                    if produto.controla_estoque:
                        estoque_atual = Decimal(str(produto.estoque_atual or 0))
                        if estoque_atual - item['quantidade'] < 0:
                            raise ValueError('Estoque insuficiente para o produto selecionado.')
                        produto.estoque_atual = estoque_atual - item['quantidade']
                        movimento = EstoqueMovimento(
                            empresa_id=tenant_id(),
                            filial_id=documento.filial_id,
                            produto_id=produto.id,
                            tipo_movimento='saida',
                            quantidade=item['quantidade'],
                            valor_unitario=item['valor_unitario'],
                            origem='venda',
                            documento_ref=numero_documento,
                            data_movimento=data_emissao,
                            criado_por_user_id=current_user.id,
                        )
                        db.session.add(movimento)

            db.session.commit()
            flash('Documento emitido com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.documentos_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao emitir documento: {exc}', 'danger')

    return render_template(
        'comercial/documentos_form.html',
        clientes=clientes,
        filiais=filiais,
        produtos=produtos,
        servicos=servicos,
        contas_banco=contas_banco,
        contas_fluxo=contas_fluxo,
        today=date.today(),
    )


@comercial_bp.route('/documentos/<int:documento_id>')
@login_required
def documentos_detalhe(documento_id):
    documento = scoped_get_or_404(DocumentoVenda, documento_id)
    return render_template('comercial/documentos_detalhe.html', documento=documento)


# =============================================================================
# TABELAS DE PREÇO
# =============================================================================
from src.models import TabelaPreco, TabelaPrecoItem


@comercial_bp.route('/tabelas-preco')
@login_required
def tabelas_preco_index():
    page = request.args.get('page', 1, type=int)
    busca = (request.args.get('busca') or '').strip()

    query = scoped_query(TabelaPreco)
    if busca:
        query = query.filter(
            (TabelaPreco.codigo.ilike(f'%{busca}%')) |
            (TabelaPreco.nome.ilike(f'%{busca}%'))
        )

    pagination = query.order_by(TabelaPreco.data_inicio.desc(), TabelaPreco.codigo.asc()).paginate(page=page, per_page=20)
    return render_template(
        'comercial/tabelas_preco_index.html',
        tabelas=pagination.items,
        pagination=pagination,
        busca=busca,
    )


@comercial_bp.route('/tabelas-preco/nova', methods=['GET', 'POST'])
@login_required
def tabelas_preco_criar():
    if request.method == 'POST':
        try:
            tabela = TabelaPreco(
                empresa_id=tenant_id(),
                codigo=(request.form.get('codigo') or '').strip(),
                nome=(request.form.get('nome') or '').strip(),
                descricao=request.form.get('descricao') or None,
                data_inicio=datetime.strptime(request.form.get('data_inicio') or '', '%Y-%m-%d').date(),
                data_fim=datetime.strptime(request.form.get('data_fim') or '', '%Y-%m-%d').date() if request.form.get('data_fim') else None,
                tipo=request.form.get('tipo') or 'venda',
                markup_padrao=Decimal((request.form.get('markup_padrao') or '0').replace(',', '.')),
                ativo=request.form.get('ativo') == 'on',
            )
            if not tabela.codigo or not tabela.nome:
                raise ValueError('Codigo e nome sao obrigatorios.')

            db.session.add(tabela)
            db.session.commit()
            flash('Tabela de preco criada com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.tabelas_preco_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao criar tabela: {exc}', 'danger')

    return render_template('comercial/tabelas_preco_form.html', action='criar', tabela=None, today=date.today())


@comercial_bp.route('/tabelas-preco/<int:tabela_id>/editar', methods=['GET', 'POST'])
@login_required
def tabelas_preco_editar(tabela_id):
    tabela = scoped_get_or_404(TabelaPreco, tabela_id)

    if request.method == 'POST':
        try:
            tabela.codigo = (request.form.get('codigo') or '').strip()
            tabela.nome = (request.form.get('nome') or '').strip()
            tabela.descricao = request.form.get('descricao') or None
            tabela.data_inicio = datetime.strptime(request.form.get('data_inicio') or '', '%Y-%m-%d').date()
            tabela.data_fim = datetime.strptime(request.form.get('data_fim') or '', '%Y-%m-%d').date() if request.form.get('data_fim') else None
            tabela.tipo = request.form.get('tipo') or 'venda'
            tabela.markup_padrao = Decimal((request.form.get('markup_padrao') or '0').replace(',', '.'))
            tabela.ativo = request.form.get('ativo') == 'on'

            if not tabela.codigo or not tabela.nome:
                raise ValueError('Codigo e nome sao obrigatorios.')

            db.session.commit()
            flash('Tabela de preco atualizada com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.tabelas_preco_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao atualizar tabela: {exc}', 'danger')

    return render_template('comercial/tabelas_preco_form.html', action='editar', tabela=tabela, today=date.today())


@comercial_bp.route('/tabelas-preco/<int:tabela_id>/itens')
@login_required
def tabelas_preco_itens(tabela_id):
    tabela = scoped_get_or_404(TabelaPreco, tabela_id)
    page = request.args.get('page', 1, type=int)

    query = scoped_query(TabelaPrecoItem).filter_by(tabela_preco_id=tabela_id)
    pagination = query.order_by(TabelaPrecoItem.id.asc()).paginate(page=page, per_page=50)

    produtos = scoped_query(Produto).filter_by(ativo=True).order_by(Produto.descricao_resumida.asc()).all()
    servicos = scoped_query(Servico).filter_by(ativo=True).order_by(Servico.descricao.asc()).all()

    return render_template(
        'comercial/tabelas_preco_itens.html',
        tabela=tabela,
        itens=pagination.items,
        pagination=pagination,
        produtos=produtos,
        servicos=servicos,
    )


@comercial_bp.route('/tabelas-preco/<int:tabela_id>/itens/adicionar', methods=['POST'])
@login_required
def tabelas_preco_itens_adicionar(tabela_id):
    tabela = scoped_get_or_404(TabelaPreco, tabela_id)

    try:
        produto_id = request.form.get('produto_id', type=int)
        servico_id = request.form.get('servico_id', type=int)
        preco_custo = Decimal((request.form.get('preco_custo') or '0').replace(',', '.'))
        preco_venda = Decimal((request.form.get('preco_venda') or '0').replace(',', '.'))
        markup = Decimal((request.form.get('markup') or '0').replace(',', '.'))
        desconto_maximo = Decimal((request.form.get('desconto_maximo') or '0').replace(',', '.'))

        if not produto_id and not servico_id:
            raise ValueError('Selecione um produto ou servico.')
        if preco_venda <= 0:
            raise ValueError('Preco de venda deve ser maior que zero.')

        item = TabelaPrecoItem(
            empresa_id=tenant_id(),
            tabela_preco_id=tabela.id,
            produto_id=produto_id,
            servico_id=servico_id,
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            markup=markup,
            desconto_maximo=desconto_maximo,
            ativo=True,
        )
        db.session.add(item)
        db.session.commit()
        flash('Item adicionado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao adicionar item: {exc}', 'danger')

    return redirect(url_for('comercial_operacional.tabelas_preco_itens', tabela_id=tabela_id))


@comercial_bp.route('/tabelas-preco/itens/<int:item_id>/remover', methods=['POST'])
@login_required
def tabelas_preco_itens_remover(item_id):
    item = scoped_get_or_404(TabelaPrecoItem, item_id)
    tabela_id = item.tabela_preco_id

    try:
        db.session.delete(item)
        db.session.commit()
        flash('Item removido com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao remover item: {exc}', 'danger')

    return redirect(url_for('comercial_operacional.tabelas_preco_itens', tabela_id=tabela_id))


# =============================================================================
# ORÇAMENTOS
# =============================================================================
from src.models import Orcamento, OrcamentoItem


def _gerar_numero_orcamento():
    """Gera número sequencial para orçamento."""
    from datetime import datetime
    ultimo = scoped_query(Orcamento).order_by(Orcamento.id.desc()).first()
    sequencia = (ultimo.id + 1) if ultimo else 1
    return f"ORC{datetime.now().year}{sequencia:06d}"


@comercial_bp.route('/orcamentos')
@login_required
def orcamentos_index():
    page = request.args.get('page', 1, type=int)
    cliente_id = request.args.get('cliente_id', type=int)
    status = (request.args.get('status') or '').strip()

    query = scoped_query(Orcamento)
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    if status:
        query = query.filter_by(status=status)

    clientes = scoped_query(Entidade).filter_by(tipo='C', ativo=True).order_by(Entidade.nome.asc()).all()
    pagination = query.order_by(Orcamento.data_emissao.desc(), Orcamento.id.desc()).paginate(page=page, per_page=20)

    return render_template(
        'comercial/orcamentos_index.html',
        orcamentos=pagination.items,
        pagination=pagination,
        clientes=clientes,
        cliente_id=cliente_id,
        status=status,
    )


@comercial_bp.route('/orcamentos/novo', methods=['GET', 'POST'])
@login_required
def orcamentos_criar():
    clientes = scoped_query(Entidade).filter_by(tipo='C', ativo=True).order_by(Entidade.nome.asc()).all()
    vendedores = scoped_query(Entidade).filter_by(tipo='V', ativo=True).order_by(Entidade.nome.asc()).all()
    tabelas = scoped_query(TabelaPreco).filter_by(ativo=True).order_by(TabelaPreco.nome.asc()).all()
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()
    
    # Converter objetos para dicionários para serialização JSON
    produtos_db = scoped_query(Produto).filter_by(ativo=True).order_by(Produto.descricao_resumida.asc()).all()
    servicos_db = scoped_query(Servico).filter_by(ativo=True).order_by(Servico.descricao.asc()).all()
    produtos = [{'id': p.id, 'codigo_interno': p.codigo_interno, 'descricao_resumida': p.descricao_resumida} for p in produtos_db]
    servicos = [{'id': s.id, 'codigo_interno': s.codigo_interno, 'descricao': s.descricao} for s in servicos_db]

    if request.method == 'POST':
        try:
            orcamento = Orcamento(
                empresa_id=tenant_id(),
                filial_id=request.form.get('filial_id', type=int) or None,
                numero=_gerar_numero_orcamento(),
                cliente_id=request.form.get('cliente_id', type=int),
                vendedor_id=request.form.get('vendedor_id', type=int) or None,
                data_emissao=datetime.strptime(request.form.get('data_emissao') or '', '%Y-%m-%d').date(),
                data_validade=datetime.strptime(request.form.get('data_validade') or '', '%Y-%m-%d').date(),
                tabela_preco_id=request.form.get('tabela_preco_id', type=int) or None,
                observacoes=request.form.get('observacoes') or None,
                observacoes_internas=request.form.get('observacoes_internas') or None,
                status='emitido',
                valor_produtos=Decimal('0.00'),
                valor_servicos=Decimal('0.00'),
                valor_desconto=Decimal('0.00'),
                valor_total=Decimal('0.00'),
                criado_por_user_id=current_user.id,
            )

            if not orcamento.cliente_id:
                raise ValueError('Cliente e obrigatorio.')

            db.session.add(orcamento)
            db.session.flush()

            # Processar itens
            tipos = request.form.getlist('item_tipo')
            produtos = request.form.getlist('item_produto_id')
            servicos = request.form.getlist('item_servico_id')
            descricoes = request.form.getlist('item_descricao')
            qtds = request.form.getlist('item_quantidade')
            valores = request.form.getlist('item_valor_unitario')
            descontos = request.form.getlist('item_desconto')

            total = Decimal('0.00')
            for i in range(len(qtds)):
                if not qtds[i]:
                    continue
                qtd = Decimal(qtds[i].replace(',', '.'))
                if qtd <= 0:
                    continue

                tipo = tipos[i] if i < len(tipos) else 'P'
                prod_id = int(produtos[i]) if i < len(produtos) and produtos[i] else None
                serv_id = int(servicos[i]) if i < len(servicos) and servicos[i] else None
                desc = descricoes[i] if i < len(descricoes) and descricoes[i] else '-'
                valor = Decimal(valores[i].replace(',', '.')) if i < len(valores) and valores[i] else Decimal('0')
                desc_item = Decimal(descontos[i].replace(',', '.')) if i < len(descontos) and descontos[i] else Decimal('0')

                total_item = (qtd * valor) - desc_item

                item = OrcamentoItem(
                    empresa_id=tenant_id(),
                    orcamento_id=orcamento.id,
                    tipo_item=tipo,
                    produto_id=prod_id if tipo == 'P' else None,
                    servico_id=serv_id if tipo == 'S' else None,
                    descricao=desc,
                    quantidade=qtd,
                    valor_unitario=valor,
                    valor_desconto=desc_item,
                    percentual_desconto=Decimal('0.00'),
                    valor_total=total_item,
                )
                db.session.add(item)

                if tipo == 'P':
                    orcamento.valor_produtos += total_item
                else:
                    orcamento.valor_servicos += total_item
                total += total_item

            orcamento.valor_total = total
            db.session.commit()
            flash('Orcamento criado com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.orcamentos_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao criar orcamento: {exc}', 'danger')

    return render_template(
        'comercial/orcamentos_form.html',
        action='criar',
        orcamento=None,
        clientes=clientes,
        vendedores=vendedores,
        tabelas=tabelas,
        filiais=filiais,
        produtos=produtos,
        servicos=servicos,
        today=date.today(),
    )


@comercial_bp.route('/orcamentos/<int:orcamento_id>')
@login_required
def orcamentos_detalhe(orcamento_id):
    orcamento = scoped_get_or_404(Orcamento, orcamento_id)
    return render_template('comercial/orcamentos_detalhe.html', orcamento=orcamento)


@comercial_bp.route('/orcamentos/<int:orcamento_id>/converter', methods=['POST'])
@login_required
def orcamentos_converter(orcamento_id):
    orcamento = scoped_get_or_404(Orcamento, orcamento_id)

    if orcamento.status != 'emitido':
        flash('Apenas orcamentos emitidos podem ser convertidos.', 'warning')
        return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento_id))

    try:
        # Criar pedido a partir do orçamento
        pedido = PedidoVenda(
            empresa_id=orcamento.empresa_id,
            filial_id=orcamento.filial_id,
            numero=f"PED{datetime.now().year}{orcamento.id:06d}",
            serie='1',
            orcamento_id=orcamento.id,
            cliente_id=orcamento.cliente_id,
            vendedor_id=orcamento.vendedor_id,
            data_emissao=date.today(),
            data_entrega=None,
            status='aprovado',
            valor_produtos=orcamento.valor_produtos,
            valor_servicos=orcamento.valor_servicos,
            valor_desconto=orcamento.valor_desconto,
            valor_frete=Decimal('0.00'),
            valor_total=orcamento.valor_total,
            observacoes=orcamento.observacoes,
            criado_por_user_id=current_user.id,
        )
        db.session.add(pedido)
        db.session.flush()

        # Copiar itens
        for item in orcamento.itens:
            pedido_item = PedidoVendaItem(
                empresa_id=item.empresa_id,
                pedido_id=pedido.id,
                orcamento_item_id=item.id,
                tipo_item=item.tipo_item,
                produto_id=item.produto_id,
                servico_id=item.servico_id,
                descricao=item.descricao,
                quantidade=item.quantidade,
                quantidade_atendida=Decimal('0.000'),
                valor_unitario=item.valor_unitario,
                valor_desconto=item.valor_desconto,
                percentual_desconto=item.percentual_desconto,
                valor_total=item.valor_total,
            )
            db.session.add(pedido_item)

        orcamento.status = 'convertido'
        orcamento.pedido_id = pedido.id
        orcamento.data_aprovacao = date.today()

        db.session.commit()
        flash(f'Orcamento convertido em pedido {pedido.numero} com sucesso.', 'success')
        return redirect(url_for('comercial_operacional.pedidos_detalhe', pedido_id=pedido.id))
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao converter orcamento: {exc}', 'danger')
        return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento_id))


# =============================================================================
# PEDIDOS DE VENDA
# =============================================================================
from src.models import PedidoVenda, PedidoVendaItem


@comercial_bp.route('/pedidos')
@login_required
def pedidos_index():
    page = request.args.get('page', 1, type=int)
    cliente_id = request.args.get('cliente_id', type=int)
    status = (request.args.get('status') or '').strip()

    query = scoped_query(PedidoVenda)
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    if status:
        query = query.filter_by(status=status)

    clientes = scoped_query(Entidade).filter_by(tipo='C', ativo=True).order_by(Entidade.nome.asc()).all()
    pagination = query.order_by(PedidoVenda.data_emissao.desc(), PedidoVenda.id.desc()).paginate(page=page, per_page=20)

    return render_template(
        'comercial/pedidos_index.html',
        pedidos=pagination.items,
        pagination=pagination,
        clientes=clientes,
        cliente_id=cliente_id,
        status=status,
    )


@comercial_bp.route('/pedidos/<int:pedido_id>')
@login_required
def pedidos_detalhe(pedido_id):
    pedido = scoped_get_or_404(PedidoVenda, pedido_id)
    contas_banco = scoped_query(ContaBanco).filter_by(ativo=True).order_by(ContaBanco.nome.asc()).all()
    contas_fluxo = scoped_query(FluxoContaModel).filter_by(ativo=True, tipo='R').order_by(FluxoContaModel.codigo.asc()).all()

    return render_template(
        'comercial/pedidos_detalhe.html',
        pedido=pedido,
        contas_banco=contas_banco,
        contas_fluxo=contas_fluxo,
    )


@comercial_bp.route('/pedidos/<int:pedido_id>/faturar', methods=['POST'])
@login_required
def pedidos_faturar(pedido_id):
    pedido = scoped_get_or_404(PedidoVenda, pedido_id)

    if pedido.status not in ['aprovado', 'em_producao', 'pronto']:
        flash('Pedido nao pode ser faturado neste status.', 'warning')
        return redirect(url_for('comercial_operacional.pedidos_detalhe', pedido_id=pedido_id))

    try:
        conta_banco_id = request.form.get('conta_banco_id', type=int)
        fluxo_conta_id = request.form.get('fluxo_conta_id', type=int)
        data_vencimento = datetime.strptime(request.form.get('data_vencimento') or '', '%Y-%m-%d').date()
        gerar_documento = request.form.get('gerar_documento') == 'on'

        if not conta_banco_id or not fluxo_conta_id:
            raise ValueError('Selecione a conta bancaria e a conta de fluxo.')

        # Criar lançamento financeiro
        lancamento = Lancamento(
            empresa_id=tenant_id(),
            data_evento=date.today(),
            data_vencimento=data_vencimento,
            status='aberto',
            entidade_id=pedido.cliente_id,
            fluxo_conta_id=fluxo_conta_id,
            conta_banco_id=conta_banco_id,
            valor_real=pedido.valor_total,
            valor_pago=Decimal('0.00'),
            valor_imposto=Decimal('0.00'),
            valor_outros_custos=Decimal('0.00'),
            numero_documento=pedido.numero,
            observacoes=f'Faturamento do pedido {pedido.numero}',
            fonte='pedido',
        )
        db.session.add(lancamento)

        documento = None
        if gerar_documento:
            # Criar documento de venda
            documento = DocumentoVenda(
                empresa_id=tenant_id(),
                filial_id=pedido.filial_id,
                cliente_id=pedido.cliente_id,
                lancamento_id=None,  # Será atualizado após flush
                numero_documento=f"DOC{pedido.numero}",
                data_emissao=date.today(),
                data_vencimento=data_vencimento,
                valor_total=pedido.valor_total,
                status='emitido',
                criado_por_user_id=current_user.id,
            )
            db.session.add(documento)
            db.session.flush()
            lancamento.numero_documento = documento.numero_documento

        db.session.flush()

        if documento:
            documento.lancamento_id = lancamento.id
            pedido.documento_venda_id = documento.id

        pedido.status = 'faturado'
        pedido.data_faturamento = date.today()

        db.session.commit()
        flash('Pedido faturado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao faturar pedido: {exc}', 'danger')

    return redirect(url_for('comercial_operacional.pedidos_detalhe', pedido_id=pedido_id))


# =============================================================================
# PDV / CAIXA
# =============================================================================
from src.models import PDVSessao, PDVVenda, PDVItem


def _gerar_numero_pdv_venda(sessao_id):
    """Gera número sequencial para venda no PDV."""
    data = datetime.now()
    ultimo = scoped_query(PDVVenda).filter_by(sessao_id=sessao_id).order_by(PDVVenda.id.desc()).first()
    sequencia = int(ultimo.id) + 1 if ultimo else 1
    return f"PV{data.strftime('%Y%m%d')}{sequencia:04d}"


@comercial_bp.route('/pdv')
@login_required
def pdv_index():
    """Lista sessões de caixa."""
    page = request.args.get('page', 1, type=int)
    status = (request.args.get('status') or '').strip()

    query = scoped_query(PDVSessao)
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(PDVSessao.data_abertura.desc()).paginate(page=page, per_page=20)

    # Verificar se há sessão aberta para o usuário atual
    sessao_aberta = scoped_query(PDVSessao).filter_by(user_id=current_user.id, status='aberto').first()

    return render_template(
        'comercial/pdv_index.html',
        sessoes=pagination.items,
        pagination=pagination,
        status=status,
        sessao_aberta=sessao_aberta,
    )


@comercial_bp.route('/pdv/abrir', methods=['GET', 'POST'])
@login_required
def pdv_abrir():
    """Abre nova sessão de caixa."""
    # Verificar se já existe sessão aberta
    sessao_existente = scoped_query(PDVSessao).filter_by(user_id=current_user.id, status='aberto').first()
    if sessao_existente:
        flash('Voce ja possui uma sessao de caixa aberta.', 'warning')
        return redirect(url_for('comercial_operacional.pdv_vender', sessao_id=sessao_existente.id))

    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()

    if request.method == 'POST':
        try:
            data = datetime.now()
            ultimo = scoped_query(PDVSessao).order_by(PDVSessao.id.desc()).first()
            sequencia = (ultimo.id + 1) if ultimo else 1

            sessao = PDVSessao(
                empresa_id=tenant_id(),
                filial_id=request.form.get('filial_id', type=int) or None,
                user_id=current_user.id,
                numero=f"SESSAO{data.strftime('%Y%m%d')}{sequencia:04d}",
                pdv_nome=(request.form.get('pdv_nome') or '').strip() or 'PDV Principal',
                data_abertura=data,
                status='aberto',
                valor_abertura=Decimal((request.form.get('valor_abertura') or '0').replace(',', '.')),
            )

            db.session.add(sessao)
            db.session.commit()
            flash('Caixa aberto com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.pdv_vender', sessao_id=sessao.id))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao abrir caixa: {exc}', 'danger')

    return render_template('comercial/pdv_abrir.html', filiais=filiais, today=date.today())


@comercial_bp.route('/pdv/<int:sessao_id>/vender')
@login_required
def pdv_vender(sessao_id):
    """Interface de vendas do PDV."""
    sessao = scoped_get_or_404(PDVSessao, sessao_id)

    if sessao.user_id != current_user.id and not current_user.is_admin:
        flash('Acesso negado a esta sessao de caixa.', 'danger')
        return redirect(url_for('comercial_operacional.pdv_index'))

    if sessao.status != 'aberto':
        flash('Esta sessao de caixa esta fechada.', 'warning')
        return redirect(url_for('comercial_operacional.pdv_index'))

    # Converter produtos para dicionários (para serialização JSON)
    produtos_db = scoped_query(Produto).filter_by(ativo=True).order_by(Produto.descricao_resumida.asc()).all()
    produtos = [{
        'id': p.id,
        'codigo_interno': p.codigo_interno,
        'codigo_barras': p.codigo_barras or '',
        'descricao_resumida': p.descricao_resumida,
        'valor_venda_padrao': float(p.valor_venda_padrao or 0)
    } for p in produtos_db]

    servicos_db = scoped_query(Servico).filter_by(ativo=True).order_by(Servico.descricao.asc()).all()
    servicos = [{'id': s.id, 'codigo_interno': s.codigo_interno, 'descricao': s.descricao} for s in servicos_db]

    clientes = scoped_query(Entidade).filter_by(tipo='C', ativo=True).order_by(Entidade.nome.asc()).all()

    # Tabelas de preço ativas
    tabelas = scoped_query(TabelaPreco).filter_by(ativo=True).order_by(TabelaPreco.nome.asc()).all()

    # Preços por tabela (organizados para fácil acesso no JS)
    tabelas_preco_itens = {}
    for tabela in tabelas:
        itens_tabela = scoped_query(TabelaPrecoItem).filter_by(
            tabela_preco_id=tabela.id, ativo=True
        ).all()
        tabelas_preco_itens[tabela.id] = {}
        for item in itens_tabela:
            if item.produto_id:
                tabelas_preco_itens[tabela.id][item.produto_id] = float(item.preco_venda or 0)
            elif item.servico_id:
                tabelas_preco_itens[tabela.id][item.servico_id] = float(item.preco_venda or 0)

    # Venda em andamento (se houver)
    venda_atual = scoped_query(PDVVenda).filter_by(sessao_id=sessao_id, status='em_andamento').first()

    return render_template(
        'comercial/pdv_vender.html',
        sessao=sessao,
        produtos=produtos,
        servicos=servicos,
        clientes=clientes,
        tabelas=tabelas,
        tabelas_preco_itens=tabelas_preco_itens,
        venda_atual=venda_atual,
    )


@comercial_bp.route('/pdv/<int:sessao_id>/venda/adicionar-item', methods=['POST'])
@login_required
def pdv_venda_adicionar_item(sessao_id):
    """Adiciona item à venda atual."""
    sessao = scoped_get_or_404(PDVSessao, sessao_id)

    try:
        # Buscar ou criar venda em andamento
        venda = scoped_query(PDVVenda).filter_by(sessao_id=sessao_id, status='em_andamento').first()
        if not venda:
            venda = PDVVenda(
                empresa_id=tenant_id(),
                filial_id=sessao.filial_id,
                sessao_id=sessao_id,
                numero=_gerar_numero_pdv_venda(sessao_id),
                data_venda=datetime.now(),
                status='em_andamento',
                subtotal=Decimal('0.00'),
                valor_total=Decimal('0.00'),
            )
            db.session.add(venda)
            db.session.flush()

        # Dados do item
        tipo_item = request.form.get('tipo_item', 'P')
        produto_id = request.form.get('produto_id', type=int)
        servico_id = request.form.get('servico_id', type=int)
        codigo_barras = request.form.get('codigo_barras') or None

        quantidade_str = (request.form.get('quantidade') or '1').strip().replace(',', '.')
        valor_unitario_str = (request.form.get('valor_unitario') or '0').strip().replace(',', '.')

        quantidade = Decimal(quantidade_str)
        valor_unitario = Decimal(valor_unitario_str)

        if quantidade <= 0:
            raise ValueError('Quantidade deve ser maior que zero.')

        if valor_unitario <= 0:
            raise ValueError('Valor unitário deve ser maior que zero.')

        descricao = ''
        codigo = ''

        if tipo_item == 'P':
            if not produto_id:
                raise ValueError('Produto não informado.')

            produto = Produto.query.get(produto_id)
            if not produto:
                raise ValueError('Produto não encontrado.')

            descricao = produto.descricao_resumida
            codigo = produto.codigo_interno

        elif tipo_item == 'S':
            if not servico_id:
                raise ValueError('Serviço não informado.')

            servico = Servico.query.get(servico_id)
            if not servico:
                raise ValueError('Serviço não encontrado.')

            descricao = servico.descricao
            codigo = servico.codigo_interno

        else:
            raise ValueError('Tipo de item inválido.')

        valor_total_item = quantidade * valor_unitario

        # Próxima sequência
        ultimo_item = (
            PDVItem.query
            .filter_by(venda_id=venda.id)
            .order_by(PDVItem.sequencia.desc())
            .first()
        )
        sequencia = (ultimo_item.sequencia + 1) if ultimo_item else 1

        item = PDVItem(
            empresa_id=tenant_id(),
            venda_id=venda.id,
            sequencia=sequencia,
            tipo_item=tipo_item,
            produto_id=produto_id if tipo_item == 'P' else None,
            servico_id=servico_id if tipo_item == 'S' else None,
            codigo=codigo,
            descricao=descricao,
            quantidade=quantidade,
            valor_unitario=valor_unitario,
            valor_total=valor_total_item,
            codigo_barras=codigo_barras,
        )
        db.session.add(item)

        # Atualizar totais da venda
        venda.subtotal = Decimal(str(venda.subtotal or 0)) + valor_total_item
        venda.valor_total = venda.subtotal - Decimal(str(venda.valor_desconto or 0))

        db.session.commit()
        return {'sucesso': True, 'mensagem': 'Item adicionado.', 'venda_id': venda.id}

    except Exception as exc:
        db.session.rollback()
        return {'sucesso': False, 'mensagem': str(exc)}, 400

@comercial_bp.route('/pdv/venda/<int:venda_id>/finalizar', methods=['POST'])
@login_required
def pdv_venda_finalizar(venda_id):
    """Finaliza venda do PDV."""
    venda = scoped_get_or_404(PDVVenda, venda_id)

    try:
        venda.cliente_id = request.form.get('cliente_id', type=int) or None
        venda.valor_desconto = Decimal((request.form.get('valor_desconto') or '0').replace(',', '.'))
        venda.valor_total = Decimal(str(venda.subtotal or 0)) - venda.valor_desconto

        # Formas de pagamento
        venda.valor_dinheiro = Decimal((request.form.get('valor_dinheiro') or '0').replace(',', '.'))
        venda.valor_cartao_credito = Decimal((request.form.get('valor_cartao_credito') or '0').replace(',', '.'))
        venda.valor_cartao_debito = Decimal((request.form.get('valor_cartao_debito') or '0').replace(',', '.'))
        venda.valor_pix = Decimal((request.form.get('valor_pix') or '0').replace(',', '.'))
        venda.valor_recebido = Decimal((request.form.get('valor_recebido') or '0').replace(',', '.'))
        venda.valor_troco = venda.valor_recebido - venda.valor_total if venda.valor_recebido > venda.valor_total else Decimal('0')

        venda.status = 'concluida'

        # Atualizar sessão
        sessao = PDVSessao.query.get(venda.sessao_id)
        sessao.valor_vendas = Decimal(str(sessao.valor_vendas or 0)) + venda.valor_total

        db.session.commit()
        flash(f'Venda {venda.numero} finalizada com sucesso.', 'success')

        # Redirecionar para página de impressão do documento não fiscal
        return redirect(url_for('comercial_operacional.pdv_venda_imprimir', venda_id=venda.id))
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao finalizar venda: {exc}', 'danger')

    return redirect(url_for('comercial_operacional.pdv_vender', sessao_id=venda.sessao_id))


@comercial_bp.route('/pdv/venda/<int:venda_id>/imprimir')
@login_required
def pdv_venda_imprimir(venda_id):
    """Exibe documento não fiscal para impressão (doc simplificado)."""
    venda = scoped_get_or_404(PDVVenda, venda_id)
    itens = scoped_query(PDVItem).filter_by(venda_id=venda.id).order_by(PDVItem.sequencia.asc()).all()
    return render_template('comercial/pdv_imprimir.html', venda=venda, itens=itens)

@comercial_bp.route('/pdv/<int:sessao_id>/fechar', methods=['GET', 'POST'])
@login_required
def pdv_fechar(sessao_id):
    """Fecha sessão de caixa."""
    sessao = scoped_get_or_404(PDVSessao, sessao_id)

    if sessao.user_id != current_user.id and not current_user.is_admin:
        flash('Acesso negado a esta sessao de caixa.', 'danger')
        return redirect(url_for('comercial_operacional.pdv_index'))

    if sessao.status != 'aberto':
        flash('Esta sessao ja esta fechada.', 'warning')
        return redirect(url_for('comercial_operacional.pdv_index'))

    # Verificar se há vendas em andamento
    venda_aberta = scoped_query(PDVVenda).filter_by(sessao_id=sessao_id, status='em_andamento').first()
    if venda_aberta:
        flash('Finalize ou cancele a venda em andamento antes de fechar o caixa.', 'warning')
        return redirect(url_for('comercial_operacional.pdv_vender', sessao_id=sessao_id))

    if request.method == 'POST':
        try:
            sessao.valor_fechamento = Decimal((request.form.get('valor_fechamento') or '0').replace(',', '.'))
            sessao.data_fechamento = datetime.now()
            sessao.status = 'fechado'
            sessao.observacoes = request.form.get('observacoes') or None

            db.session.commit()
            flash('Caixa fechado com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.pdv_index'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao fechar caixa: {exc}', 'danger')

    # Resumo da sessão
    vendas = scoped_query(PDVVenda).filter_by(sessao_id=sessao_id, status='concluida').all()

    return render_template(
        'comercial/pdv_fechar.html',
        sessao=sessao,
        vendas=vendas,
        total_vendas=sum(v.valor_total for v in vendas),
        total_dinheiro=sum(v.valor_dinheiro for v in vendas),
        total_cartao=sum(v.valor_cartao_credito + v.valor_cartao_debito for v in vendas),
        total_pix=sum(v.valor_pix for v in vendas),
    )
