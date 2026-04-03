"""
Rotas para gerenciamento de comissões
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import desc

from src.models import db, Comissao, Entidade, Lancamento, ParametroSistema
from src.services.comissoes import ServicoComissoes
from src.extensions import require_role

comissoes_bp = Blueprint('comissoes', __name__, url_prefix='/comissoes')


@comissoes_bp.before_request
@login_required
def antes_requisicao():
    """Verificar autenticação antes de cada requisição"""
    pass


@comissoes_bp.route('/')
@login_required
def listar():
    """Lista comissões com filtros"""
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    vendedor_id = request.args.get('vendedor_id', type=int)
    cliente_id = request.args.get('cliente_id', type=int)
    
    try:
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    except ValueError:
        data_inicio = None
        data_fim = None
    
    # Se não houver data, usar últimos 90 dias
    if not data_fim:
        data_fim = datetime.now().date()
    if not data_inicio:
        data_inicio = data_fim - timedelta(days=90)
    
    # Obter comissões
    comissoes = ServicoComissoes.obter_comissoes_filtradas(
        current_user.empresa_id,
        data_inicio,
        data_fim,
        vendedor_id,
        cliente_id
    ).order_by(desc(Comissao.dt_pagamento_recebimento)).all()
    
    # Obter vendedores e clientes para filtro
    vendedores = Entidade.query.filter_by(
        empresa_id=current_user.empresa_id,
        tipo='V',
        ativo=True
    ).order_by(Entidade.nome).all()
    
    clientes = Entidade.query.filter_by(
        empresa_id=current_user.empresa_id,
        tipo='C',
        ativo=True
    ).order_by(Entidade.nome).all()
    
    # Calcular totais
    total_notas = sum(c.vl_nota for c in comissoes) or Decimal('0.00')
    total_liquido = sum(c.vl_liquido for c in comissoes) or Decimal('0.00')
    total_repasse = sum(c.vl_repasse for c in comissoes) or Decimal('0.00')
    total_comissoes = sum(c.vl_comissao for c in comissoes) or Decimal('0.00')
    
    return render_template(
        'comissoes/index.html',
        comissoes=comissoes,
        vendedores=vendedores,
        clientes=clientes,
        data_inicio=data_inicio.strftime('%Y-%m-%d') if data_inicio else '',
        data_fim=data_fim.strftime('%Y-%m-%d') if data_fim else '',
        vendedor_id=vendedor_id,
        cliente_id=cliente_id,
        total_notas=total_notas,
        total_liquido=total_liquido,
        total_repasse=total_repasse,
        total_comissoes=total_comissoes,
        quantidade=len(comissoes)
    )


@comissoes_bp.route('/relatorio')
@login_required
def relatorio():
    """Relatório de comissões agrupado por vendedor"""
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    vendedor_id = request.args.get('vendedor_id', type=int)
    cliente_id = request.args.get('cliente_id', type=int)
    
    try:
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    except ValueError:
        data_inicio = None
        data_fim = None
    
    # Se não houver data, usar últimos 90 dias
    if not data_fim:
        data_fim = datetime.now().date()
    if not data_inicio:
        data_inicio = data_fim - timedelta(days=90)
    
    # Obter resumo por vendedor
    resumo_vendedores = ServicoComissoes.obter_resumo_por_vendedor(
        current_user.empresa_id,
        data_inicio,
        data_fim,
        vendedor_id,
        cliente_id
    )
    
    # Calcular totais gerais
    total_geral = {
        'total_notas': Decimal('0.00'),
        'total_liquido': Decimal('0.00'),
        'total_repasse': Decimal('0.00'),
        'total_comissoes': Decimal('0.00'),
        'quantidade_lancamentos': 0
    }
    
    for resumo in resumo_vendedores:
        total_geral['total_notas'] += resumo['total_notas']
        total_geral['total_liquido'] += resumo['total_liquido']
        total_geral['total_repasse'] += resumo['total_repasse']
        total_geral['total_comissoes'] += resumo['total_comissoes']
        total_geral['quantidade_lancamentos'] += resumo['quantidade_lancamentos']
    
    # Obter vendedores para filtro
    vendedores = Entidade.query.filter_by(
        empresa_id=current_user.empresa_id,
        tipo='V',
        ativo=True
    ).order_by(Entidade.nome).all()
    
    clientes = Entidade.query.filter_by(
        empresa_id=current_user.empresa_id,
        tipo='C',
        ativo=True
    ).order_by(Entidade.nome).all()
    
    return render_template(
        'comissoes/relatorio.html',
        resumo_vendedores=resumo_vendedores,
        total_geral=total_geral,
        data_inicio=data_inicio.strftime('%Y-%m-%d') if data_inicio else '',
        data_fim=data_fim.strftime('%Y-%m-%d') if data_fim else '',
        vendedores=vendedores,
        clientes=clientes,
        vendedor_id=vendedor_id,
        cliente_id=cliente_id
    )


@comissoes_bp.route('/apurar', methods=['GET', 'POST'])
@login_required
@require_role('admin', 'operator')
def apurar():
    """Executa apuração de comissões"""
    
    if request.method == 'GET':
        # Formulário de apuração
        return render_template('comissoes/apurar.html')
    
    # POST - Executar apuração
    try:
        data_inicio_str = request.form.get('data_inicio')
        data_fim_str = request.form.get('data_fim')
        
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date() if data_inicio_str else None
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date() if data_fim_str else None
        
        if not data_inicio or not data_fim:
            flash('Datas de início e fim são obrigatórias', 'danger')
            return redirect(url_for('comissoes.apurar'))
        
        if data_inicio > data_fim:
            flash('Data de início não pode ser maior que data de fim', 'danger')
            return redirect(url_for('comissoes.apurar'))
        
        # Executar apuração
        resultado = ServicoComissoes.apurar_comissoes(
            current_user.empresa_id,
            data_inicio,
            data_fim
        )
        
        if resultado['sucesso']:
            flash(
                f"✓ Apuração concluída! {resultado['registros_criados']} comissões geradas. "
                f"Total: R$ {resultado['total_comissoes']}",
                'success'
            )
        else:
            flash(f"✗ Erro: {resultado['mensagem']}", 'danger')
        
        return redirect(url_for('comissoes.listar'))
    
    except Exception as e:
        flash(f"Erro ao processar apuração: {str(e)}", 'danger')
        return redirect(url_for('comissoes.apurar'))


@comissoes_bp.route('/parametros', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def parametros():
    """Gerenciar parâmetros de comissão"""
    
    if request.method == 'GET':
        # Obter parâmetro atual
        param = ParametroSistema.query.filter_by(
            empresa_id=current_user.empresa_id,
            chave='aliquota_comissao_padrao'
        ).first()
        
        aliquota_padrao = Decimal(param.valor) if param else Decimal('0')
        
        return render_template(
            'comissoes/parametros.html',
            aliquota_padrao=aliquota_padrao
        )
    
    # POST - Salvar parâmetros
    try:
        aliquota = request.form.get('aliquota_padrao', '0')
        
        # Validar
        try:
            aliquota = Decimal(aliquota)
            if aliquota < 0 or aliquota > 100:
                flash('Alíquota deve estar entre 0 e 100', 'danger')
                return redirect(url_for('comissoes.parametros'))
        except:
            flash('Alíquota inválida', 'danger')
            return redirect(url_for('comissoes.parametros'))
        
        # Atualizar ou criar parâmetro
        param = ParametroSistema.query.filter_by(
            empresa_id=current_user.empresa_id,
            chave='aliquota_comissao_padrao'
        ).first()
        
        if param:
            param.valor = str(aliquota)
        else:
            param = ParametroSistema(
                empresa_id=current_user.empresa_id,
                chave='aliquota_comissao_padrao',
                valor=str(aliquota),
                tipo='numeric',
                descricao='Alíquota padrão de comissão sobre vendas'
            )
            db.session.add(param)
        
        db.session.commit()
        flash(f'✓ Alíquota padrão atualizada para {aliquota}%', 'success')
        
        return redirect(url_for('comissoes.parametros'))
    
    except Exception as e:
        flash(f"Erro ao salvar parâmetros: {str(e)}", 'danger')
        return redirect(url_for('comissoes.parametros'))


@comissoes_bp.route('/exportar-csv')
@login_required
def exportar_csv():
    """Exportar comissões para CSV"""
    
    from io import StringIO
    import csv
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    vendedor_id = request.args.get('vendedor_id', type=int)
    cliente_id = request.args.get('cliente_id', type=int)
    
    try:
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    except ValueError:
        data_inicio = None
        data_fim = None
    
    if not data_fim:
        data_fim = datetime.now().date()
    if not data_inicio:
        data_inicio = data_fim - timedelta(days=90)
    
    # Obter comissões
    resumo_vendedores = ServicoComissoes.obter_resumo_por_vendedor(
        current_user.empresa_id,
        data_inicio,
        data_fim,
        vendedor_id,
        cliente_id
    )
    
    # Criar CSV
    output = StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Cabeçalho
    writer.writerow([
        'Vendedor',
        'Quantidade de Lançamentos',
        'Total de Notas',
        'Total de Repasse',
        'Total Líquido',
        'Total de Comissões'
    ])
    
    # Dados
    for resumo in resumo_vendedores:
        writer.writerow([
            resumo['vendedor'].nome,
            resumo['quantidade_lancamentos'],
            f"{resumo['total_notas']:.2f}".replace('.', ','),
            f"{resumo['total_repasse']:.2f}".replace('.', ','),
            f"{resumo['total_liquido']:.2f}".replace('.', ','),
            f"{resumo['total_comissoes']:.2f}".replace('.', ',')
        ])
    
    # Retornar como arquivo
    from flask import send_file
    from io import BytesIO
    
    csv_bytes = BytesIO(output.getvalue().encode('utf-8-sig'))
    csv_bytes.seek(0)
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"comissoes_{data_inicio}_{data_fim}.csv"
    )
