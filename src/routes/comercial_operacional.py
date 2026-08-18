from decimal import Decimal
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user

from src.models import (
    db,
    Filial,
    Produto,
    Servico,
    NfseServicoNacionalReferencia,
    NfseNbsReferencia,
    EstoqueMovimento,
    Entidade,
    FluxoContaModel,
    ContaBanco,
    Lancamento,
    CompraNFManual,
    CompraNFItem,
    CompraNFLancamento,
    CompraNFXMLImport,
    CompraNFXMLItem,
    DocumentoVenda,
    DocumentoVendaItem,
    PedidoVenda,
)
from src.tenant import scoped_query, scoped_get_or_404, tenant_id
from src.services.nfe_parser import parse_nfe_xml, formatar_cnpj
from src.services.pedido_faturamento import (
    separar_itens_por_natureza,
    validar_faturamento_pedido,
    formatar_erros_validacao,
)


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


def _nfse_codigo_servico_opcoes():
    return [
        {
            'valor': item.codigo_tributacao_nacional,
            'rotulo': f"{item.codigo_tributacao_nacional} - {item.descricao}",
        }
        for item in NfseServicoNacionalReferencia.query.filter_by(ativo=True)
        .filter(NfseServicoNacionalReferencia.codigo_tributacao_nacional.isnot(None))
        .order_by(NfseServicoNacionalReferencia.codigo_tributacao_nacional.asc())
        .all()
    ]


def _nfse_nbs_opcoes():
    return [
        {
            'valor': item.codigo_nbs,
            'rotulo': f"{item.codigo_nbs} - {item.descricao}",
        }
        for item in NfseNbsReferencia.query.filter_by(ativo=True)
        .order_by(NfseNbsReferencia.codigo_nbs.asc())
        .all()
    ]


def _normaliza_codigo_numerico(valor):
    return ''.join(ch for ch in str(valor or '') if ch.isdigit())


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
    codigo_servico_opcoes = _nfse_codigo_servico_opcoes()
    nbs_opcoes = _nfse_nbs_opcoes()

    if request.method == 'POST':
        try:
            codigo_servico = (request.form.get('codigo_servico') or '').strip()
            nbs = (request.form.get('nbs') or '').strip()
            if codigo_servico:
                codigo_servico_normalizado = _normaliza_codigo_numerico(codigo_servico)
                if not NfseServicoNacionalReferencia.query.filter_by(codigo_tributacao_nacional=codigo_servico_normalizado, ativo=True).first():
                    raise ValueError('Codigo fiscal nao encontrado no catalogo de servicos nacionais.')
                codigo_servico = codigo_servico_normalizado
            if nbs:
                nbs_normalizado = _normaliza_codigo_numerico(nbs)
                if not NfseNbsReferencia.query.filter_by(codigo_nbs=nbs_normalizado, ativo=True).first():
                    raise ValueError('NBS nao encontrado no catalogo de referencia.')
                # Validação relaxada: apenas avisa se não corresponder, mas permite cadastro
                if codigo_servico:
                    codigo_servico_padded = codigo_servico.zfill(6)
                    if len(nbs_normalizado) >= 6 and nbs_normalizado[:6] != codigo_servico_padded:
                        import logging
                        logging.warning(f'NBS ({nbs_normalizado}) nao corresponde ao codigo fiscal ({codigo_servico_padded}), mas cadastro permitido.')
                nbs = nbs_normalizado

            servico = Servico(
                empresa_id=tenant_id(),
                filial_id=request.form.get('filial_id', type=int) or None,
                codigo_interno=(request.form.get('codigo_interno') or '').strip(),
                descricao=(request.form.get('descricao') or '').strip(),
                codigo_servico=codigo_servico or None,
                nbs=nbs or None,
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

    return render_template(
        'comercial/servicos_form.html',
        action='criar',
        servico=None,
        filiais=filiais,
        codigo_servico_opcoes=codigo_servico_opcoes,
        nbs_opcoes=nbs_opcoes,
    )


@comercial_bp.route('/servicos/<int:servico_id>/editar', methods=['GET', 'POST'])
@login_required
def servicos_editar(servico_id):
    servico = scoped_get_or_404(Servico, servico_id)
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()
    codigo_servico_opcoes = _nfse_codigo_servico_opcoes()
    nbs_opcoes = _nfse_nbs_opcoes()

    if request.method == 'POST':
        try:
            codigo_servico = (request.form.get('codigo_servico') or '').strip()
            nbs = (request.form.get('nbs') or '').strip()
            if codigo_servico:
                codigo_servico_normalizado = _normaliza_codigo_numerico(codigo_servico)
                if not NfseServicoNacionalReferencia.query.filter_by(codigo_tributacao_nacional=codigo_servico_normalizado, ativo=True).first():
                    raise ValueError('Codigo fiscal nao encontrado no catalogo de servicos nacionais.')
                codigo_servico = codigo_servico_normalizado
            if nbs:
                nbs_normalizado = _normaliza_codigo_numerico(nbs)
                if not NfseNbsReferencia.query.filter_by(codigo_nbs=nbs_normalizado, ativo=True).first():
                    raise ValueError('NBS nao encontrado no catalogo de referencia.')
                # Validação relaxada: apenas avisa se não corresponder, mas permite cadastro
                if codigo_servico:
                    codigo_servico_padded = codigo_servico.zfill(6)
                    if len(nbs_normalizado) >= 6 and nbs_normalizado[:6] != codigo_servico_padded:
                        import logging
                        logging.warning(f'NBS ({nbs_normalizado}) nao corresponde ao codigo fiscal ({codigo_servico_padded}), mas cadastro permitido.')
                nbs = nbs_normalizado

            servico.filial_id = request.form.get('filial_id', type=int) or None
            servico.codigo_interno = (request.form.get('codigo_interno') or '').strip()
            servico.descricao = (request.form.get('descricao') or '').strip()
            servico.codigo_servico = codigo_servico or None
            servico.nbs = nbs or None
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

    return render_template('comercial/servicos_form.html', action='editar', servico=servico, filiais=filiais, codigo_servico_opcoes=codigo_servico_opcoes, nbs_opcoes=nbs_opcoes)


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


@comercial_bp.route('/compras/importar-xml', methods=['GET', 'POST'])
@login_required
def compras_importar_xml():
    if request.method == 'POST':
        try:
            if 'xml_file' not in request.files:
                raise ValueError('Nenhum arquivo XML enviado.')
            
            xml_file = request.files['xml_file']
            if xml_file.filename == '':
                raise ValueError('Nenhum arquivo selecionado.')
            
            if not xml_file.filename.endswith('.xml'):
                raise ValueError('O arquivo deve ser um XML.')
            
            # Ler conteúdo do XML
            xml_content = xml_file.read().decode('utf-8')
            
            # Parsear XML
            dados_nfe = parse_nfe_xml(xml_content)
            
            # Verificar se fornecedor existe pelo CNPJ
            cnpj_emitente = formatar_cnpj(dados_nfe['emitente']['CNPJ'])
            fornecedor = scoped_query(Entidade).filter_by(
                cnpj_cpf=cnpj_emitente,
                tipo='F'
            ).first()
            
            # Se fornecedor não existir, criar automaticamente
            if not fornecedor:
                endereco_emitente = dados_nfe['emitente'].get('endereco', {})
                fornecedor = Entidade(
                    empresa_id=tenant_id(),
                    nome=dados_nfe['emitente']['xNome'],
                    tipo='F',
                    cnpj_cpf=cnpj_emitente,
                    inscricao_estadual=dados_nfe['emitente'].get('IE'),
                    endereco_rua=endereco_emitente.get('xLgr'),
                    endereco_numero=endereco_emitente.get('nro'),
                    endereco_bairro=endereco_emitente.get('xBairro'),
                    endereco_cidade=endereco_emitente.get('xMun'),
                    endereco_uf=endereco_emitente.get('UF'),
                    endereco_cep=endereco_emitente.get('CEP'),
                    telefone=endereco_emitente.get('fone'),
                    ativo=True,
                )
                db.session.add(fornecedor)
                db.session.flush()
            
            # Criar registro de importação
            importacao = CompraNFXMLImport(
                empresa_id=tenant_id(),
                fornecedor_id=fornecedor.id,
                xml_original=xml_content,
                dados_parseados=dados_nfe,
                status='pendente',
                criado_por_user_id=current_user.id,
            )
            db.session.add(importacao)
            db.session.flush()
            
            # Criar itens da importação
            for item in dados_nfe['itens']:
                item_import = CompraNFXMLItem(
                    empresa_id=tenant_id(),
                    import_id=importacao.id,
                    dados_item=item,
                    confirmado=False,
                )
                db.session.add(item_import)
            
            db.session.commit()
            flash('XML importado com sucesso. Revise os dados antes de confirmar.', 'success')
            return redirect(url_for('comercial_operacional.compras_xml_validar', import_id=importacao.id))
            
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao importar XML: {exc}', 'danger')
    
    return render_template('comercial/compras_xml_importar.html')


@comercial_bp.route('/compras/importar-xml/<int:import_id>/validar', methods=['GET'])
@login_required
def compras_xml_validar(import_id):
    importacao = scoped_get_or_404(CompraNFXMLImport, import_id)
    
    if importacao.status != 'pendente':
        flash('Esta importação já foi processada.', 'warning')
        return redirect(url_for('comercial_operacional.compras_index'))
    
    fornecedores = scoped_query(Entidade).filter_by(tipo='F', ativo=True).order_by(Entidade.nome.asc()).all()
    filiais = scoped_query(Filial).filter_by(ativo=True).order_by(Filial.codigo.asc()).all()
    produtos = scoped_query(Produto).filter_by(ativo=True).order_by(Produto.descricao_resumida.asc()).all()
    contas_banco = scoped_query(ContaBanco).filter_by(ativo=True).order_by(ContaBanco.nome.asc()).all()
    contas_fluxo = scoped_query(FluxoContaModel).filter_by(ativo=True, tipo='P').order_by(FluxoContaModel.codigo.asc()).all()
    
    # Buscar conta de fluxo padrão para compras
    conta_fluxo_padrao = None
    if contas_fluxo:
        conta_fluxo_padrao = next((c for c in contas_fluxo if c.codigo == '1.01.01'), contas_fluxo[0])
    
    return render_template(
        'comercial/compras_xml_validar.html',
        importacao=importacao,
        dados=importacao.dados_parseados,
        fornecedores=fornecedores,
        filiais=filiais,
        produtos=produtos,
        contas_banco=contas_banco,
        contas_fluxo=contas_fluxo,
        conta_fluxo_padrao=conta_fluxo_padrao,
    )


@comercial_bp.route('/compras/importar-xml/<int:import_id>/confirmar', methods=['POST'])
@login_required
def compras_xml_confirmar(import_id):
    importacao = scoped_get_or_404(CompraNFXMLImport, import_id)
    
    if importacao.status != 'pendente':
        flash('Esta importação já foi processada.', 'warning')
        return redirect(url_for('comercial_operacional.compras_index'))
    
    try:
        dados = importacao.dados_parseados
        cabecalho = dados['cabecalho']
        
        # Obter dados do formulário
        fornecedor_id = request.form.get('fornecedor_id', type=int) or importacao.fornecedor_id
        filial_id = request.form.get('filial_id', type=int) or None
        fluxo_conta_id = request.form.get('fluxo_conta_id', type=int)
        conta_banco_id = request.form.get('conta_banco_id', type=int)
        data_vencimento = datetime.strptime(request.form.get('data_vencimento') or '', '%Y-%m-%d').date()
        data_pagamento_str = (request.form.get('data_pagamento') or '').strip()
        data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date() if data_pagamento_str else None
        parcelas = request.form.get('parcelas', type=int) or 1
        intervalo_dias = request.form.get('intervalo_dias', type=int) or 30
        observacoes = request.form.get('observacoes') or None
        
        if parcelas < 1:
            parcelas = 1
        if parcelas > 1 and data_pagamento:
            raise ValueError('Nao informe pagamento quando houver parcelamento.')
        
        if not fluxo_conta_id or not conta_banco_id:
            raise ValueError('Conta de fluxo e conta bancaria sao obrigatorias.')
        
        fluxo_conta = scoped_get_or_404(FluxoContaModel, fluxo_conta_id)
        if not fluxo_conta.is_pagamento():
            raise ValueError('Conta de fluxo deve ser do tipo Pagamento (P).')
        
        # Processar itens confirmados
        item_ids = request.form.getlist('item_confirmado')
        produto_ids = request.form.getlist('item_produto_id')
        
        if not item_ids:
            raise ValueError('Selecione ao menos um item para confirmar.')
        
        itens_confirmados = []
        total = Decimal('0.00')
        
        for item_id in item_ids:
            item_import = scoped_query(CompraNFXMLItem).filter_by(id=int(item_id), import_id=importacao.id).first()
            if not item_import:
                continue
            
            item_dados = item_import.dados_item
            produto_id = request.form.get(f'produto_id_{item_id}', type=int) or None
            
            quantidade = Decimal(str(item_dados.get('qCom', 0)))
            valor_unitario = Decimal(str(item_dados.get('vUnCom', 0)))
            total_item = quantidade * valor_unitario
            total += total_item
            
            itens_confirmados.append({
                'produto_id': produto_id,
                'descricao_livre': item_dados.get('xProd'),
                'quantidade': quantidade,
                'valor_unitario': valor_unitario,
                'total_item': total_item,
                'ncm': item_dados.get('NCM'),
                'cfop': item_dados.get('CFOP'),
                'cst': None,
                'csosn': None,
            })
            
            # Atualizar item da importação
            item_import.produto_id = produto_id
            item_import.confirmado = True
        
        if total <= 0:
            raise ValueError('O valor total da nota deve ser maior que zero.')
        
        valor_total_nota = Decimal(str(dados['totais'].get('vNF', total)))
        
        # Criar compra
        numero_documento = cabecalho.get('nNF', '')
        serie = cabecalho.get('serie', '')
        data_emissao_str = cabecalho.get('data_emissao')
        if data_emissao_str:
            data_emissao = datetime.strptime(data_emissao_str, '%Y-%m-%d').date()
        else:
            data_emissao = date.today()
        data_entrada = data_emissao
        
        compra = CompraNFManual(
            empresa_id=tenant_id(),
            filial_id=filial_id,
            fornecedor_id=fornecedor_id,
            lancamento_id=None,
            numero_documento=numero_documento,
            serie=serie,
            data_emissao=data_emissao,
            data_entrada=data_entrada,
            valor_total=valor_total_nota,
            observacoes=observacoes,
            status='registrada',
            criado_por_user_id=current_user.id,
        )
        db.session.add(compra)
        db.session.flush()
        
        # Gerar lançamentos financeiros
        valor_base = (valor_total_nota / parcelas).quantize(Decimal('0.01')) if parcelas > 1 else valor_total_nota
        
        for parcela in range(1, parcelas + 1):
            vencimento = data_vencimento + timedelta(days=(parcela - 1) * intervalo_dias)
            
            if parcelas == 1 and data_pagamento:
                status_lancamento = 'pago'
                data_pagamento_lancamento = data_pagamento
            else:
                status_lancamento = 'aberto'
                data_pagamento_lancamento = None
            
            lancamento = Lancamento(
                empresa_id=tenant_id(),
                entidade_id=fornecedor_id,
                fluxo_conta_id=fluxo_conta_id,
                conta_banco_id=conta_banco_id,
                data_evento=data_entrada,
                data_vencimento=vencimento,
                data_pagamento=data_pagamento_lancamento,
                status=status_lancamento,
                valor_real=valor_base,
                valor_pago=valor_base if data_pagamento_lancamento else Decimal('0.00'),
                valor_imposto=Decimal('0.00'),
                valor_outros_custos=Decimal('0.00'),
                numero_documento=numero_documento,
                observacoes=f'Compra NF XML - parcela {parcela}/{parcelas}',
                fonte='xml',
            )
            db.session.add(lancamento)
            db.session.flush()
            
            link = CompraNFLancamento(
                empresa_id=tenant_id(),
                compra_id=compra.id,
                lancamento_id=lancamento.id,
                parcela_numero=parcela,
                parcela_total=parcelas,
                valor_parcela=valor_base,
                data_vencimento=vencimento,
            )
            db.session.add(link)
        
        # Criar itens da compra
        for item in itens_confirmados:
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
                        origem='compra_xml',
                        documento_ref=numero_documento,
                        data_movimento=data_entrada,
                        criado_por_user_id=current_user.id,
                    )
                    db.session.add(movimento)
        
        # Atualizar status da importação
        importacao.status = 'confirmada'
        
        db.session.commit()
        flash('Compra gerada com sucesso a partir do XML.', 'success')
        return redirect(url_for('comercial_operacional.compras_detalhe', compra_id=compra.id))
        
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao confirmar importação: {exc}', 'danger')
        return redirect(url_for('comercial_operacional.compras_xml_validar', import_id=import_id))


@comercial_bp.route('/compras/importar-xml/<int:import_id>/cancelar', methods=['POST'])
@login_required
def compras_xml_cancelar(import_id):
    importacao = scoped_get_or_404(CompraNFXMLImport, import_id)
    
    if importacao.status != 'pendente':
        flash('Esta importação já foi processada.', 'warning')
        return redirect(url_for('comercial_operacional.compras_index'))
    
    try:
        importacao.status = 'cancelada'
        db.session.commit()
        flash('Importação cancelada com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao cancelar importação: {exc}', 'danger')
    
    return redirect(url_for('comercial_operacional.compras_index'))


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


@comercial_bp.route('/propostas/aprovacao')
@login_required
def propostas_aprovacao():
    page = request.args.get('page', 1, type=int)
    cliente_id = request.args.get('cliente_id', type=int)

    query = scoped_query(Orcamento).filter_by(status='emitido')
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)

    clientes = scoped_query(Entidade).filter_by(tipo='C', ativo=True).order_by(Entidade.nome.asc()).all()
    pagination = query.order_by(Orcamento.data_emissao.desc(), Orcamento.id.desc()).paginate(page=page, per_page=20)

    return render_template(
        'comercial/propostas_aprovacao.html',
        propostas=pagination.items,
        pagination=pagination,
        clientes=clientes,
        cliente_id=cliente_id,
    )


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
                validade_precos=request.form.get('validade_precos') or None,
                condicoes_pagamento=request.form.get('condicoes_pagamento') or None,
                termos_compra=request.form.get('termos_compra') or None,
                detalhes_tecnicos=request.form.get('detalhes_tecnicos') or None,
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
        timedelta=timedelta,
        orcamento_itens=[],
    )


@comercial_bp.route('/orcamentos/<int:orcamento_id>/editar', methods=['GET', 'POST'])
@login_required
def orcamentos_editar(orcamento_id):
    orcamento = scoped_get_or_404(Orcamento, orcamento_id)

    if orcamento.empresa_id != tenant_id():
        flash('Não autorizado', 'danger')
        return redirect(url_for('comercial_operacional.orcamentos_index'))

    # Verificar se pode editar (não convertido em pedido)
    if orcamento.status == 'convertido':
        flash('Não é possível editar orçamento já convertido em pedido.', 'warning')
        return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento.id))

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
            # Atualizar dados do orçamento
            orcamento.filial_id = request.form.get('filial_id', type=int) or None
            orcamento.cliente_id = request.form.get('cliente_id', type=int)
            orcamento.vendedor_id = request.form.get('vendedor_id', type=int) or None
            orcamento.data_emissao = datetime.strptime(request.form.get('data_emissao') or '', '%Y-%m-%d').date()
            orcamento.data_validade = datetime.strptime(request.form.get('data_validade') or '', '%Y-%m-%d').date()
            orcamento.tabela_preco_id = request.form.get('tabela_preco_id', type=int) or None
            orcamento.observacoes = request.form.get('observacoes') or None
            orcamento.observacoes_internas = request.form.get('observacoes_internas') or None
            orcamento.validade_precos = request.form.get('validade_precos') or None
            orcamento.condicoes_pagamento = request.form.get('condicoes_pagamento') or None
            orcamento.termos_compra = request.form.get('termos_compra') or None
            orcamento.detalhes_tecnicos = request.form.get('detalhes_tecnicos') or None

            if not orcamento.cliente_id:
                raise ValueError('Cliente é obrigatório.')

            # Remover itens existentes
            for item in orcamento.itens:
                db.session.delete(item)

            # Zerar totais
            orcamento.valor_produtos = Decimal('0.00')
            orcamento.valor_servicos = Decimal('0.00')
            orcamento.valor_desconto = Decimal('0.00')
            orcamento.valor_total = Decimal('0.00')

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
            flash('Orçamento atualizado com sucesso.', 'success')
            return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento.id))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao atualizar orçamento: {exc}', 'danger')

    return render_template(
        'comercial/orcamentos_form.html',
        action='editar',
        orcamento=orcamento,
        clientes=clientes,
        vendedores=vendedores,
        tabelas=tabelas,
        filiais=filiais,
        produtos=produtos,
        servicos=servicos,
        today=date.today(),
        timedelta=timedelta,
        orcamento_itens=[{
            'tipo_item': item.tipo_item,
            'produto_id': item.produto_id,
            'servico_id': item.servico_id,
            'descricao': item.descricao,
            'quantidade': float(item.quantidade) if item.quantidade else 0,
            'valor_unitario': float(item.valor_unitario) if item.valor_unitario else 0,
            'valor_desconto': float(item.valor_desconto) if item.valor_desconto else 0,
        } for item in orcamento.itens],
    )


@comercial_bp.route('/orcamentos/<int:orcamento_id>')
@login_required
def orcamentos_detalhe(orcamento_id):
    orcamento = scoped_get_or_404(Orcamento, orcamento_id)
    return render_template('comercial/orcamentos_detalhe.html', orcamento=orcamento)


@comercial_bp.route('/orcamentos/<int:orcamento_id>/aprovar', methods=['POST'])
@login_required
def orcamentos_aprovar(orcamento_id):
    orcamento = scoped_get_or_404(Orcamento, orcamento_id)

    if orcamento.status != 'emitido':
        flash('Apenas orçamentos emitidos podem ser aprovados.', 'warning')
        return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento_id))

    try:
        orcamento.status = 'aprovado'
        orcamento.data_aprovacao = date.today()
        db.session.commit()
        flash('Orçamento aprovado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao aprovar orçamento: {exc}', 'danger')

    return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento_id))


@comercial_bp.route('/orcamentos/<int:orcamento_id>/reprovar', methods=['POST'])
@login_required
def orcamentos_reprovar(orcamento_id):
    orcamento = scoped_get_or_404(Orcamento, orcamento_id)

    if orcamento.status != 'emitido':
        flash('Apenas orçamentos emitidos podem ser reprovados.', 'warning')
        return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento_id))

    try:
        orcamento.status = 'reprovado'
        db.session.commit()
        flash('Orçamento reprovado.', 'warning')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao reprovar orçamento: {exc}', 'danger')

    return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento_id))


@comercial_bp.route('/orcamentos/<int:orcamento_id>/exportar-pdf', methods=['GET'])
@login_required
def orcamentos_exportar_pdf(orcamento_id):
    from fpdf import FPDF
    from flask import current_app, send_file, flash, redirect, url_for
    import io
    import os
    import re
    from decimal import Decimal

    orcamento = scoped_get_or_404(Orcamento, orcamento_id)

    if orcamento.empresa_id != tenant_id():
        flash('Não autorizado', 'danger')
        return redirect(url_for('comercial_operacional.orcamentos_index'))

    try:
        empresa = current_user.empresa if getattr(current_user, 'empresa', None) else None

        def txt(valor, default=""):
            if valor is None:
                return default
            s = str(valor).strip()
            # Remove caracteres Unicode problemáticos que não podem ser codificados em latin-1
            s = s.encode('latin-1', 'ignore').decode('latin-1')
            return s if s else default

        def brl(valor):
            valor = Decimal(str(valor or 0))
            s = f"{valor:,.2f}"
            return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

        def qtd_fmt(valor):
            valor = Decimal(str(valor or 0))
            if valor == valor.to_integral():
                return str(int(valor))
            return f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

        def format_cep(cep):
            cep = re.sub(r"\D", "", txt(cep))
            if len(cep) == 8:
                return f"{cep[:2]}.{cep[2:5]}-{cep[5:]}"
            return txt(cep)

        def format_fone(fone):
            dig = re.sub(r"\D", "", txt(fone))
            if len(dig) == 11:
                return f"({dig[:2]}) {dig[2:7]}-{dig[7:]}"
            if len(dig) == 10:
                return f"({dig[:2]}) {dig[2:6]}-{dig[6:]}"
            return txt(fone)

        def linha(*partes):
            vals = [txt(p) for p in partes if txt(p)]
            return ", ".join(vals)

        def endereco_bloco(entidade):
            if not entidade:
                return []
            l1 = linha(getattr(entidade, "endereco_rua", None), getattr(entidade, "endereco_numero", None))
            bairro = txt(getattr(entidade, "endereco_bairro", None))
            if bairro:
                l1 = f"{l1} - {bairro}"
            cidade = txt(getattr(entidade, "endereco_cidade", None))
            cep = format_cep(getattr(entidade, "endereco_cep", None))
            uf = txt(getattr(entidade, "endereco_uf", None))
            
            # Se o endereço for muito longo, coloca CEP na mesma linha
            if len(l1) > 50 and cep:
                l1 = f"{l1} - {cep}"
                l2 = cidade
            else:
                l2 = linha(cep, cidade)
            
            l3 = f"{uf} - Brasil" if uf else "Brasil"
            return [x for x in [l1, l2, l3] if x]

        def dados_cliente(cliente):
            if not cliente:
                return ["-"]
            nome = txt(getattr(cliente, "nome", None), "-")
            email = txt(getattr(cliente, "email", None))
            telefone = format_fone(getattr(cliente, "telefone", None))
            return [nome] + [x for x in [email, telefone] if x]

        def dados_emitente(empresa_obj, vendedor):
            nome_vendedor = txt(getattr(vendedor, "nome", None))
            email = txt(getattr(vendedor, "email", None) or getattr(empresa_obj, "email", None))
            telefone = format_fone(getattr(vendedor, "telefone", None) or getattr(empresa_obj, "telefone", None))
            linhas = [f"Preparado por: {nome_vendedor}" if nome_vendedor else "Preparado por"]
            if email:
                linhas.append(email)
            if telefone:
                linhas.append(telefone)
            return linhas

        def item_descricao(item):
            desc = txt(getattr(item, "descricao", None))
            if desc and desc != "-":
                return desc
            if getattr(item, "produto", None):
                return txt(
                    getattr(item.produto, "descricao_resumida", None)
                    or getattr(item.produto, "nome", None),
                    "-"
                )
            if getattr(item, "servico", None):
                return txt(getattr(item.servico, "descricao", None), "-")
            return "-"

        def item_total(item):
            if getattr(item, "valor_total", None) is not None:
                return Decimal(str(item.valor_total or 0))
            qtd = Decimal(str(getattr(item, "quantidade", 0) or 0))
            vu = Decimal(str(getattr(item, "valor_unitario", 0) or 0))
            desconto = Decimal(str(getattr(item, "valor_desconto", 0) or 0))
            total = (qtd * vu) - desconto
            return total if total > 0 else Decimal("0.00")

        def texto_valido(s):
            s = txt(s).strip()
            return s and s not in {"-", "1.1", "Detalhes Técnicos Itens"}

        def localizar_logo():
            candidatos = [
                os.path.join(current_app.root_path, "static", "images", "logo_sem fundo2.png"),
                os.path.join(current_app.root_path, "static", "images", "logo_sem_fundo2.png"),
                os.path.join(current_app.root_path, "static", "images", "logo.png"),
                os.path.join(current_app.root_path, "static", "img", "logo.png"),
                os.path.join("src", "static", "images", "logo_sem fundo2.png"),
                os.path.join("src", "static", "images", "logo.png"),
            ]
            for caminho in candidatos:
                if os.path.exists(caminho):
                    return caminho
            return None

        class PDFOrcamento(FPDF):
            def __init__(self):
                super().__init__(orientation="P", unit="mm", format="A4")
                self.set_auto_page_break(auto=True, margin=12)
                self.set_margins(14, 10, 14)
                self.logo = localizar_logo()
                self.azul = (59, 83, 116)
                self.texto = (92, 104, 121)
                self.borda = (126, 146, 171)

            def footer(self):
                self.set_y(-8)
                self.set_font("Helvetica", "", 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 4, f"Página {self.page_no()}", 0, 0, "R")

            def box(self, x, y, w, h):
                self.set_draw_color(*self.borda)
                self.rect(x, y, w, h)

            def section_title(self, x, y, texto):
                self.set_xy(x, y)
                self.set_font("Helvetica", "B", 12)
                self.set_text_color(*self.azul)
                self.cell(0, 6, texto, 0, 1)

            def body_text(self, x, y, w, texto, size=10, line_h=5.8):
                self.set_xy(x, y)
                self.set_font("Helvetica", "", size)
                self.set_text_color(*self.texto)
                self.multi_cell(w, line_h, txt(texto, "-"))

            def write_lines(self, x, y, w, lines, first_bold=False, line_h=6, color=None):
                yy = y
                for i, line in enumerate(lines):
                    self.set_xy(x, yy)
                    self.set_font("Helvetica", "B" if first_bold and i == 0 else "", 10)
                    self.set_text_color(*(color or self.texto))
                    self.multi_cell(w, line_h, txt(line, "-"))
                    yy = self.get_y()

        pdf = PDFOrcamento()
        pdf.add_page()

        def ensure_space(current_pdf, needed_height, start_new_page=True):
            if current_pdf.get_y() + needed_height > 282:
                if start_new_page:
                    current_pdf.add_page()
                return False
            return True

        def add_text_block(current_pdf, title, body, title_size=12, body_size=10, line_h=5.8, gap_after=8):
            y = current_pdf.get_y()
            approx_lines = max(1, len(txt(body)) // 85 + body.count("\n") + 1)
            needed = 8 + (approx_lines * line_h) + gap_after
            ensure_space(current_pdf, needed)
            current_pdf.set_xy(20, current_pdf.get_y())
            current_pdf.set_font("Helvetica", "B", title_size)
            current_pdf.set_text_color(*current_pdf.azul)
            current_pdf.cell(0, 6, title, 0, 1)
            current_pdf.ln(2)
            current_pdf.set_x(20)
            current_pdf.set_font("Helvetica", "", body_size)
            current_pdf.set_text_color(*current_pdf.texto)
            current_pdf.multi_cell(166, line_h, txt(body))
            current_pdf.ln(gap_after - 2)

        if pdf.logo:
            try:
                pdf.image(pdf.logo, x=14, y=13, w=36)
            except Exception:
                pass

        pdf.set_xy(0, 38)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*pdf.azul)
        pdf.cell(210, 10, "Proposta comercial / Orçamento", 0, 1, "C")

        left_x = 14
        right_x = 132
        top_y = 60
        left_w = 92
        right_w = 62

        cliente = getattr(orcamento, "cliente", None)
        vendedor = getattr(orcamento, "vendedor", None)

        pdf.write_lines(left_x, top_y, left_w, [txt(getattr(cliente, "nome", None), "-")] + endereco_bloco(cliente), True, 6, pdf.azul)
        pdf.write_lines(right_x, top_y, right_w, [txt(getattr(empresa, "nome", None), "LiveSun Comercial")] + endereco_bloco(empresa), True, 6, pdf.azul)

        # Calcular altura ocupada pelos endereços para evitar sobreposição
        endereco_cliente = [txt(getattr(cliente, "nome", None), "-")] + endereco_bloco(cliente)
        endereco_empresa = [txt(getattr(empresa, "nome", None), "LiveSun Comercial")] + endereco_bloco(empresa)
        max_linhas = max(len(endereco_cliente), len(endereco_empresa))
        contact_y = top_y + (max_linhas * 6) + 6

        pdf.write_lines(left_x, contact_y, left_w, dados_cliente(cliente), True, 6, pdf.azul)
        pdf.write_lines(right_x, contact_y, right_w, dados_emitente(empresa, vendedor), True, 6, pdf.azul)

        ref_y = contact_y + 36
        pdf.set_xy(left_x, ref_y)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*pdf.texto)
        pdf.cell(0, 6, f"Referência: {txt(getattr(orcamento, 'numero', None), '-')}", 0, 1)
        pdf.set_x(left_x)
        pdf.cell(0, 6, f"Orçamento criado: {orcamento.data_emissao.strftime('%d/%m/%Y') if getattr(orcamento, 'data_emissao', None) else '-'}", 0, 1)
        pdf.set_x(left_x)
        pdf.cell(0, 6, f"O orçamento expira em: {orcamento.data_validade.strftime('%d/%m/%Y') if getattr(orcamento, 'data_validade', None) else '-'}", 0, 1)

        total_geral = Decimal(str(getattr(orcamento, "valor_total", 0) or 0))
        if total_geral <= 0:
            total_geral = sum((item_total(i) for i in orcamento.itens), Decimal("0.00"))

        top_total_y = ref_y + 28
        pdf.set_xy(left_x, top_total_y)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*pdf.azul)
        pdf.cell(35, 8, "Total", 0, 0, "L")
        pdf.cell(65, 8, brl(total_geral), 0, 1, "R")
        pdf.set_draw_color(*pdf.borda)
        pdf.line(left_x, top_total_y + 8, left_x + 92, top_total_y + 8)

        table_y = top_total_y + 14
        x0 = 14
        w_desc = 128
        w_qtd = 24
        w_preco = 38
        h_header = 10
        h_item = 36
        h_resumo_t = 9
        h_resumo_l = 11

        pdf.rect(x0, table_y, w_desc, h_header)
        pdf.rect(x0 + w_desc, table_y, w_qtd, h_header)
        pdf.rect(x0 + w_desc + w_qtd, table_y, w_preco, h_header)

        pdf.set_xy(x0 + 2, table_y + 2.5)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*pdf.azul)
        pdf.cell(w_desc - 4, 5, "PRODUTOS E SERVIÇOS", 0, 0, "L")

        pdf.set_xy(x0 + w_desc, table_y + 2.5)
        pdf.cell(w_qtd, 5, "QUANTIDADE", 0, 0, "C")

        pdf.set_xy(x0 + w_desc + w_qtd, table_y + 2.5)
        pdf.cell(w_preco - 2, 5, "PREÇO", 0, 0, "R")

        primeiro_item = orcamento.itens[0] if orcamento.itens else None
        desc = item_descricao(primeiro_item) if primeiro_item else "-"
        qtd = qtd_fmt(getattr(primeiro_item, "quantidade", 0) if primeiro_item else 0)
        preco = brl(item_total(primeiro_item) if primeiro_item else total_geral)

        item_y = table_y + h_header
        pdf.rect(x0, item_y, w_desc, h_item)
        pdf.rect(x0 + w_desc, item_y, w_qtd, h_item)
        pdf.rect(x0 + w_desc + w_qtd, item_y, w_preco, h_item)

        pdf.set_xy(x0 + 4, item_y + 6)
        pdf.set_font("Helvetica", "", 9.6)
        pdf.set_text_color(*pdf.texto)
        pdf.multi_cell(w_desc - 8, 6.5, desc)

        pdf.set_xy(x0 + w_desc, item_y + 9)
        pdf.cell(w_qtd, 6, qtd, 0, 0, "C")

        pdf.set_xy(x0 + w_desc + w_qtd + 2, item_y + 9)
        pdf.cell(w_preco - 4, 6, preco, 0, 0, "R")

        resumo_y = item_y + h_item
        pdf.rect(x0, resumo_y, w_desc + w_qtd + w_preco, h_resumo_t)
        pdf.set_xy(x0 + 2, resumo_y + 2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*pdf.azul)
        pdf.cell(50, 5, "RESUMO", 0, 1, "L")

        resumo2_y = resumo_y + h_resumo_t
        pdf.rect(x0, resumo2_y, w_desc + w_qtd, h_resumo_l)
        pdf.rect(x0 + w_desc + w_qtd, resumo2_y, w_preco, h_resumo_l)

        pdf.set_xy(x0 + 2, resumo2_y + 3)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*pdf.texto)
        pdf.cell(50, 5, "Subtotal Único", 0, 0, "L")

        pdf.set_xy(x0 + w_desc + w_qtd + 2, resumo2_y + 3)
        pdf.cell(w_preco - 4, 5, brl(total_geral), 0, 0, "R")

        final_y = resumo2_y + h_resumo_l + 4
        final_x = 100
        final_w_label = 56
        final_w_value = 48
        final_h = 12

        pdf.rect(final_x, final_y, final_w_label, final_h)
        pdf.rect(final_x + final_w_label, final_y, final_w_value, final_h)
        pdf.set_xy(final_x, final_y + 3)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*pdf.azul)
        pdf.cell(final_w_label, 5, "Total", 0, 0, "C")
        pdf.set_xy(final_x + final_w_label, final_y + 3)
        pdf.cell(final_w_value - 3, 5, brl(total_geral), 0, 0, "R")

        # PÁGINA 2
        pdf.add_page()

        y = 28
        pdf.section_title(20, y, "Condições comerciais")
        y += 14

        if texto_valido(getattr(orcamento, "observacoes", None)):
            pdf.set_xy(20, y)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*pdf.azul)
            pdf.cell(0, 6, "Escopo do Projeto", 0, 1)
            y += 6
            pdf.set_xy(20, y)
            pdf.set_font("Helvetica", "", 9.8)
            pdf.set_text_color(*pdf.texto)
            # Usar write em vez de multi_cell para evitar quebra automática
            texto_obs = txt(orcamento.observacoes)
            linhas_obs = pdf.multi_cell(166, 5.4, texto_obs, split_only=True)
            for linha in linhas_obs:
                if y > 270:
                    pdf.add_page()
                    y = 28
                pdf.set_xy(20, y)
                pdf.cell(166, 5.4, linha, 0, 1)
                y += 5.4
            y += 8

        if texto_valido(getattr(orcamento, "validade_precos", None)):
            # Verificar espaço antes de adicionar
            if y + 30 > 280:
                pdf.add_page()
                y = 28
            pdf.set_xy(20, y)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*pdf.azul)
            pdf.cell(0, 6, "Validade da proposta", 0, 1)
            y += 6
            pdf.set_xy(20, y)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*pdf.texto)
            texto_val = txt(orcamento.validade_precos)
            linhas_val = pdf.multi_cell(166, 5.5, texto_val, split_only=True)
            for linha in linhas_val:
                if y > 270:
                    pdf.add_page()
                    y = 28
                pdf.set_xy(20, y)
                pdf.cell(166, 5.5, linha, 0, 1)
                y += 5.5
            y += 5

        if texto_valido(getattr(orcamento, "condicoes_pagamento", None)):
            # Verificar espaço antes de adicionar
            if y + 30 > 280:
                pdf.add_page()
                y = 28
            pdf.set_xy(20, y)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*pdf.azul)
            pdf.cell(0, 6, "Condições de Pagamento/Faturamento", 0, 1)
            y += 6
            pdf.set_xy(20, y)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*pdf.texto)
            texto_cond = txt(orcamento.condicoes_pagamento)
            linhas_cond = pdf.multi_cell(166, 5.5, texto_cond, split_only=True)
            for linha in linhas_cond:
                if y > 270:
                    pdf.add_page()
                    y = 28
                pdf.set_xy(20, y)
                pdf.cell(166, 5.5, linha, 0, 1)
                y += 5.5
            y += 6

        # Verificar espaço antes de adicionar detalhes técnicos itens
        if y + 40 > 280:
            pdf.add_page()
            y = 28

        pdf.set_xy(20, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*pdf.azul)
        pdf.cell(0, 6, "Detalhes Técnicos Itens", 0, 1)
        y += 7

        detalhes_itens = []
        for idx, item in enumerate(orcamento.itens, start=1):
            detalhes_itens.append(f"1.{idx}  {item_descricao(item)} - {qtd_fmt(getattr(item, 'quantidade', 0))}")

        pdf.set_xy(20, y)
        pdf.set_font("Helvetica", "", 9.8)
        pdf.set_text_color(*pdf.texto)
        texto_detalhes = "\n".join(detalhes_itens) if detalhes_itens else "-"
        linhas_detalhes = pdf.multi_cell(166, 5.5, texto_detalhes, split_only=True)
        for linha in linhas_detalhes:
            if y > 270:
                pdf.add_page()
                y = 28
            pdf.set_xy(20, y)
            pdf.cell(166, 5.5, linha, 0, 1)
            y += 5.5
        y += 6

        if texto_valido(getattr(orcamento, "termos_compra", None)):
            # Verificar espaço antes de adicionar termos de compra
            if y + 30 > 280:
                pdf.add_page()
                y = 28
            pdf.set_xy(20, y)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*pdf.azul)
            pdf.cell(0, 6, "Termos de compra", 0, 1)
            y += 6
            pdf.set_xy(20, y)
            pdf.set_font("Helvetica", "", 9.8)
            pdf.set_text_color(*pdf.texto)
            texto_termos = txt(orcamento.termos_compra)
            linhas_termos = pdf.multi_cell(166, 5.4, texto_termos, split_only=True)
            for linha in linhas_termos:
                if y > 270:
                    pdf.add_page()
                    y = 28
                pdf.set_xy(20, y)
                pdf.cell(166, 5.4, linha, 0, 1)
                y += 5.4
            y += 8

        # INFORMAÇÕES TÉCNICAS - CONTINUA NA MESMA PÁGINA SE HOUVER ESPAÇO
        conteudo_tecnico = txt(getattr(orcamento, "detalhes_tecnicos", None))
        if texto_valido(conteudo_tecnico):
            # Verificar espaço antes de adicionar informações técnicas
            if y + 50 > 280:
                pdf.add_page()
                y = 28
            pdf.set_y(y)
            pdf.section_title(20, pdf.get_y(), "Informações Técnicas")
            y = pdf.get_y() + 10

            titulo_item = item_descricao(primeiro_item) if primeiro_item else ""
            if titulo_item and titulo_item != "-":
                pdf.set_x(20)
                pdf.set_font("Helvetica", "B", 10.5)
                pdf.set_text_color(*pdf.azul)
                pdf.multi_cell(166, 6.0, titulo_item)
                y = pdf.get_y() + 3

            pdf.set_x(20)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*pdf.texto)
            pdf.multi_cell(166, 5.6, conteudo_tecnico)
            y = pdf.get_y() + 10

        # Reativar quebra automática de página para os blocos finais
        # pdf.set_auto_page_break(True, 12)  # Mantém desativado para controle manual

        # BLOCOS FINAIS CONTINUAM NA MESMA PÁGINA SE COUBER
        # Verificar espaço antes de adicionar despesas acessórias
        if y + 40 > 280:
            pdf.add_page()
            y = 28
        pdf.set_xy(20, y)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*pdf.azul)
        pdf.cell(0, 6, "Despesas acessórias", 0, 1)
        y += 8
        pdf.set_xy(20, y)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*pdf.texto)
        pdf.multi_cell(166, 5.8, "Despesas acessórias relativas a transporte, hospedagem, locomoção e alimentação, "
            "ocorridas durante os atendimentos presenciais (quando houver) serão por conta do cliente.\n\n"
            "Os valores, quando pagos pela LiveSun serão repassados ao cliente de acordo com os "
            "comprovantes efetivamente gastos, apurados no período.")
        y = pdf.get_y() + 8

        # Verificar espaço antes de adicionar termo de responsabilidade
        if y + 40 > 280:
            pdf.add_page()
            y = 28
        pdf.set_xy(20, y)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*pdf.azul)
        pdf.cell(0, 6, "Termo de responsabilidade e sigilo", 0, 1)
        y += 8
        pdf.set_xy(20, y)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*pdf.texto)
        pdf.multi_cell(166, 5.8, "A presente proposta tem caráter exclusivo e confidencial específica para a sua finalidade "
            "e objeto principal.\n\n"
            "Não deverá ser publicada, copiada ou divulgada sem prévio entendimento e acordo das empresas. "
            "A quebra de sigilo poderá acarretar em processos administrativos quando cabíveis.")
        y = pdf.get_y() + 8

        # Verificar espaço antes de adicionar termo de aceite
        if y + 40 > 280:
            pdf.add_page()
            y = 28
        pdf.set_xy(20, y)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*pdf.azul)
        pdf.cell(0, 6, "Termo de aceite", 0, 1)
        y += 8
        pdf.set_xy(20, y)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*pdf.texto)
        pdf.multi_cell(166, 5.8, "Estamos de acordo com a presente proposta conforme descrita neste documento o qual dou aceite abaixo.")
        y = pdf.get_y() + 10

        # Verificar espaço para o campo de assinatura
        if y + 50 > 280:
            pdf.add_page()
            y = 28

        pdf.set_x(20)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*pdf.texto)
        pdf.cell(110, 6, "Local e data: ____________________________________________", 0, 1, "L")
        pdf.ln(18)

        y_ass = pdf.get_y()
        pdf.set_draw_color(*pdf.borda)
        pdf.line(20, y_ass, 92, y_ass)
        pdf.line(114, y_ass, 186, y_ass)

        pdf.set_xy(20, y_ass + 3)
        pdf.cell(72, 6, "Cliente / Responsável", 0, 0, "C")
        pdf.set_xy(114, y_ass + 3)
        pdf.cell(72, 6, "LiveSun", 0, 0, "C")

        buffer = io.BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        buffer.write(pdf_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'proposta_orcamento_{txt(getattr(orcamento, "numero", "sem_numero"))}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        flash(f'Erro ao exportar PDF: {str(e)}', 'danger')
        return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento.id))


@comercial_bp.route('/orcamentos/<int:orcamento_id>/exportar-pdf-resumido', methods=['GET'])
@login_required
def orcamentos_exportar_pdf_resumido(orcamento_id):
    from fpdf import FPDF
    from flask import current_app, send_file, flash, redirect, url_for
    import io
    import os
    import re
    from decimal import Decimal

    orcamento = scoped_get_or_404(Orcamento, orcamento_id)

    if orcamento.empresa_id != tenant_id():
        flash('Não autorizado', 'danger')
        return redirect(url_for('comercial_operacional.orcamentos_index'))

    try:
        empresa = current_user.empresa if getattr(current_user, 'empresa', None) else None

        def txt(valor, default=""):
            if valor is None:
                return default
            s = str(valor).strip()
            return s if s else default

        def brl(valor):
            valor = Decimal(str(valor or 0))
            s = f"{valor:,.2f}"
            return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

        def qtd_fmt(valor):
            valor = Decimal(str(valor or 0))
            if valor == valor.to_integral():
                return f"{int(valor)}"
            return f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

        def format_cep(cep):
            raw = str(cep or "").strip()
            digits = re.sub(r"\D", "", raw)
            if len(digits) == 8:
                return f"{digits[:5]}-{digits[5:]}"
            return raw

        def format_fone(fone):
            dig = re.sub(r"\D", "", str(fone or "").strip())
            if len(dig) == 11:
                return f"({dig[:2]}) {dig[2:7]}-{dig[7:]}"
            if len(dig) == 10:
                return f"({dig[:2]}) {dig[2:6]}-{dig[6:]}"
            return str(fone or "").strip()

        def endereco_linha(entidade):
            if not entidade:
                return "-"
            partes = [
                txt(getattr(entidade, "endereco_rua", None)),
                txt(getattr(entidade, "endereco_numero", None)),
                txt(getattr(entidade, "endereco_bairro", None)),
                txt(getattr(entidade, "endereco_cidade", None)),
                txt(getattr(entidade, "endereco_uf", None)),
            ]
            partes = [p for p in partes if p]
            cep = format_cep(getattr(entidade, "endereco_cep", None))
            if cep:
                partes.append(f"CEP: {cep}")
            return ", ".join(partes) if partes else "-"

        def documento_cliente(cliente):
            return txt(
                getattr(cliente, "cnpj_cpf", None)
                or getattr(cliente, "cnpjcpf", None)
                or getattr(cliente, "cnpj", None)
                or getattr(cliente, "cpf", None),
                "-"
            )

        def item_descricao(item):
            desc = txt(getattr(item, "descricao", None))
            if desc and desc != "-":
                return desc
            if getattr(item, "produto", None):
                return txt(
                    getattr(item.produto, "descricao_resumida", None)
                    or getattr(item.produto, "nome", None),
                    "-"
                )
            if getattr(item, "servico", None):
                return txt(getattr(item.servico, "descricao", None), "-")
            return "-"

        def item_codigo(item):
            if getattr(item, "produto", None):
                return txt(getattr(item.produto, "codigo_interno", None), "-")
            if getattr(item, "servico", None):
                return txt(getattr(item.servico, "codigo_interno", None), "-")
            return "-"

        def item_total(item):
            if getattr(item, "valor_total", None) is not None:
                return Decimal(str(item.valor_total or 0))
            qtd = Decimal(str(getattr(item, "quantidade", 0) or 0))
            vu = Decimal(str(getattr(item, "valor_unitario", 0) or 0))
            desconto = Decimal(str(getattr(item, "valor_desconto", 0) or 0))
            total = (qtd * vu) - desconto
            return total if total > 0 else Decimal("0.00")

        class PDFResumido(FPDF):
            def __init__(self):
                super().__init__(orientation="P", unit="mm", format="A4")
                self.set_auto_page_break(auto=True, margin=15)
                self.set_margins(16, 16, 16)

            def footer(self):
                self.set_y(-10)
                self.set_font("Helvetica", "", 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 5, f"Página {self.page_no()}", 0, 0, "R")

        pdf = PDFResumido()
        pdf.add_page()

        cliente = getattr(orcamento, "cliente", None)
        vendedor = getattr(orcamento, "vendedor", None)

        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)
        pdf.cell(0, 10, "PROPOSTA COMERCIAL / ORÇAMENTO", 0, 1, "C")
        pdf.ln(8)

        def titulo_secao(titulo):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, titulo, 0, 1, "L")

        def linha_texto(label, valor):
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 6.2, f"{label} {txt(valor, '-')}")

        titulo_secao("Emitente:")
        linha_texto("Razão Social:", txt(getattr(empresa, "nome", None), "LiveSun Comercial"))
        linha_texto("CNPJ:", txt(getattr(empresa, "cnpj_cpf", None), "27907386000176"))
        linha_texto("Endereço:", endereco_linha(empresa))
        linha_texto("Telefone:", format_fone(getattr(empresa, "telefone", None)))
        linha_texto("E-mail:", txt(getattr(empresa, "email", None), "-"))
        pdf.ln(5)

        titulo_secao("Dados do Orçamento:")
        linha_texto("Número:", txt(getattr(orcamento, "numero", None), "-"))
        linha_texto("Data de Emissão:", orcamento.data_emissao.strftime('%d/%m/%Y') if getattr(orcamento, 'data_emissao', None) else "-")
        linha_texto("Validade:", orcamento.data_validade.strftime('%d/%m/%Y') if getattr(orcamento, 'data_validade', None) else "-")
        pdf.ln(5)

        titulo_secao("Cliente:")
        linha_texto("Nome:", txt(getattr(cliente, "nome", None), "-"))
        linha_texto("CNPJ/CPF:", documento_cliente(cliente))
        linha_texto("Endereço:", endereco_linha(cliente))
        linha_texto("Telefone:", format_fone(getattr(cliente, "telefone", None)))
        linha_texto("E-mail:", txt(getattr(cliente, "email", None), "-"))
        pdf.ln(5)

        titulo_secao("Vendedor:")
        linha_texto("Nome:", txt(getattr(vendedor, "nome", None), "-"))
        if txt(getattr(vendedor, "email", None)):
            linha_texto("E-mail:", txt(getattr(vendedor, "email", None)))
        if txt(getattr(vendedor, "telefone", None)):
            linha_texto("Telefone:", format_fone(getattr(vendedor, "telefone", None)))
        pdf.ln(8)

        titulo_secao("Itens da Proposta:")
        pdf.ln(2)

        x = 20
        y = pdf.get_y()
        w_codigo = 26
        w_desc = 84
        w_qtd = 18
        w_unit = 28
        w_total = 32
        h_head = 8

        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_draw_color(60, 60, 60)

        pdf.rect(x, y, w_codigo, h_head)
        pdf.rect(x + w_codigo, y, w_desc, h_head)
        pdf.rect(x + w_codigo + w_desc, y, w_qtd, h_head)
        pdf.rect(x + w_codigo + w_desc + w_qtd, y, w_unit, h_head)
        pdf.rect(x + w_codigo + w_desc + w_qtd + w_unit, y, w_total, h_head)

        pdf.set_xy(x, y + 2)
        pdf.cell(w_codigo, 4, "Código", 0, 0, "L")
        pdf.cell(w_desc, 4, "Descrição", 0, 0, "L")
        pdf.cell(w_qtd, 4, "Qtd", 0, 0, "C")
        pdf.cell(w_unit, 4, "Unitário", 0, 0, "C")
        pdf.cell(w_total, 4, "Total", 0, 1, "C")

        y += h_head
        total_geral = Decimal("0.00")
        itens = list(getattr(orcamento, "itens", []))

        if not itens:
            itens = []

        for item in itens[:6]:
            total_item = item_total(item)
            total_geral += total_item

            codigo = item_codigo(item)
            descricao = item_descricao(item)
            qtd = qtd_fmt(getattr(item, "quantidade", 0))
            unit = brl(getattr(item, "valor_unitario", 0))
            total = brl(total_item)

            pdf.set_font("Helvetica", "", 10)
            linhas_desc = max(1, len(descricao) // 45 + 1)
            h_row = max(8, linhas_desc * 5.5)

            pdf.rect(x, y, w_codigo, h_row)
            pdf.rect(x + w_codigo, y, w_desc, h_row)
            pdf.rect(x + w_codigo + w_desc, y, w_qtd, h_row)
            pdf.rect(x + w_codigo + w_desc + w_qtd, y, w_unit, h_row)
            pdf.rect(x + w_codigo + w_desc + w_qtd + w_unit, y, w_total, h_row)

            pdf.set_xy(x + 1, y + 2)
            pdf.cell(w_codigo - 2, 4, codigo, 0, 0, "L")

            pdf.set_xy(x + w_codigo + 1, y + 1.8)
            pdf.multi_cell(w_desc - 2, 5, descricao, 0, "L")

            pdf.set_xy(x + w_codigo + w_desc, y + 2)
            pdf.cell(w_qtd, 4, qtd, 0, 0, "C")

            pdf.set_xy(x + w_codigo + w_desc + w_qtd, y + 2)
            pdf.cell(w_unit, 4, unit, 0, 0, "C")

            pdf.set_xy(x + w_codigo + w_desc + w_qtd + w_unit, y + 2)
            pdf.cell(w_total, 4, total, 0, 0, "C")

            y += h_row

        if total_geral == 0:
            total_geral = Decimal(str(getattr(orcamento, "valor_total", 0) or 0))

        pdf.set_y(y + 10)
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 8, f"Total da Proposta:  {brl(total_geral)}", 0, 1, "R")

        pdf.ln(18)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "Esta proposta é válida até a data de validade indicada acima.", 0, 1, "C")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, "Agradecemos a preferência.", 0, 1, "C")

        buffer = io.BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        buffer.write(pdf_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'orcamento_resumido_{txt(getattr(orcamento, "numero", "sem_numero"))}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        flash(f'Erro ao exportar PDF resumido: {str(e)}', 'danger')
        return redirect(url_for('comercial_operacional.orcamentos_detalhe', orcamento_id=orcamento.id))


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


@comercial_bp.route('/pedidos/<int:pedido_id>/faturar', methods=['GET'])
@login_required
def pedidos_faturar_previa(pedido_id):
    """Exibe prévia do faturamento com separação fiscal."""
    pedido = scoped_get_or_404(PedidoVenda, pedido_id)

    if pedido.status not in ['aprovado', 'em_producao', 'pronto']:
        flash('Pedido nao pode ser faturado neste status.', 'warning')
        return redirect(url_for('comercial_operacional.pedidos_detalhe', pedido_id=pedido_id))

    # Separar itens por natureza
    itens_por_natureza = separar_itens_por_natureza(pedido)

    # Validar faturamento
    valido, erros = validar_faturamento_pedido(pedido)

    return render_template(
        'comercial/pedidos_faturar_previa.html',
        pedido=pedido,
        itens_por_natureza=itens_por_natureza,
        erros=erros,
        valido=valido,
        contas_banco=scoped_query(ContaBanco).filter_by(ativo=True).order_by(ContaBanco.nome.asc()).all(),
        contas_fluxo=scoped_query(FluxoContaModel).filter_by(ativo=True, tipo='R').order_by(FluxoContaModel.codigo.asc()).all(),
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

        # Validar faturamento com separação fiscal
        if gerar_documento:
            valido, erros = validar_faturamento_pedido(pedido)
            if not valido:
                mensagens = formatar_erros_validacao(erros)
                flash(f'Erro de validação: {"; ".join(mensagens)}', 'danger')
                return redirect(url_for('comercial_operacional.pedidos_detalhe', pedido_id=pedido_id))

        # Separar itens por natureza
        itens_por_natureza = separar_itens_por_natureza(pedido)

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

        documento_venda = None
        documento_nfse = None

        if gerar_documento:
            # Se houver itens de produto, criar DocumentoVenda
            if itens_por_natureza['produtos']:
                documento_venda = DocumentoVenda(
                    empresa_id=tenant_id(),
                    filial_id=pedido.filial_id,
                    cliente_id=pedido.cliente_id,
                    lancamento_id=None,  # Será atualizado após flush
                    numero_documento=f"DOC{pedido.numero}",
                    data_emissao=date.today(),
                    data_vencimento=data_vencimento,
                    valor_total=itens_por_natureza['valor_produtos'],
                    status='emitido',
                    pedido_id=pedido.id,
                    origem_tipo='PEDIDO',
                    criado_por_user_id=current_user.id,
                )
                db.session.add(documento_venda)
                db.session.flush()
                lancamento.numero_documento = documento_venda.numero_documento

                # Criar itens do documento
                for item in itens_por_natureza['produtos']:
                    documento_item = DocumentoVendaItem(
                        empresa_id=tenant_id(),
                        documento_id=documento_venda.id,
                        tipo_item=item.tipo_item,
                        produto_id=item.produto_id,
                        servico_id=item.servico_id,
                        descricao=item.descricao,
                        quantidade=item.quantidade,
                        valor_unitario=item.valor_unitario,
                        valor_desconto=item.valor_desconto,
                        percentual_desconto=item.percentual_desconto,
                        valor_total=item.valor_total,
                    )
                    db.session.add(documento_item)
                    
                    # Atualizar referência no item do pedido
                    item.documento_item_id = documento_item.id
                    item.tipo_documento = 'VENDA'

            # Se houver itens de serviço, apenas informar (não emitir automaticamente)
            if itens_por_natureza['servicos']:
                flash(f'Atenção: {len(itens_por_natureza["servicos"])} itens de serviço identificados. Emita NFS-e manualmente pelo menu NFS-e Nacional.', 'info')

        db.session.flush()

        if documento_venda:
            documento_venda.lancamento_id = lancamento.id
            pedido.documento_venda_id = documento_venda.id

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
