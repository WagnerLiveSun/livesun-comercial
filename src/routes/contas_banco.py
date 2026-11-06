from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from flask_login import current_user
from src.models import db, ContaBanco, FluxoContaModel, InstituicaoBancaria, Lancamento
from src.services.asaas_boleto import AsaasBoletoError, configurar_conta_asaas
from src.services.inter_bolepix import InterBolePixError, configurar_conta_inter
from src.tenant import scoped_query, scoped_get_or_404, tenant_id

contas_banco_bp = Blueprint('contas_banco', __name__, url_prefix='/contas-banco')


def _codigo_banco(value: str | None) -> str:
    digits = ''.join(char for char in str(value or '') if char.isdigit())
    return digits.zfill(3) if digits else ''


def _atualizar_dados_bancarios(form, conta: ContaBanco) -> None:
    tipo_conta = (form.get('tipo') or '').strip()
    codigo = _codigo_banco(form.get('codigo_banco'))
    instituicao = InstituicaoBancaria.query.filter_by(codigo_banco=codigo).first() if codigo else None
    if tipo_conta not in {'Conta Corrente', 'Conta Poupança', 'Caixa'}:
        raise ValueError('Selecione o tipo de conta.')
    if tipo_conta in {'Conta Corrente', 'Conta Poupança'} and not instituicao:
        raise ValueError('Selecione um código de banco válido para contas corrente ou poupança.')
    conta.tipo = tipo_conta
    conta.codigo_banco = codigo or None
    conta.banco = instituicao.nome_banco if instituicao else 'Caixa'


def _configurar_cobranca(conta: ContaBanco, form) -> None:
    habilitada = form.get('cobranca_bancaria_habilitada') == 'on'
    codigo = _codigo_banco(conta.codigo_banco)
    if codigo == '461':
        configurar_conta_inter(
            conta_banco_id=conta.id,
            empresa_id=conta.empresa_id,
            habilitada=False,
            ambiente=None,
            client_id=None,
            client_secret=None,
            certificado=None,
            chave_privada=None,
            webhook_token=None,
        )
        configurar_conta_asaas(
            conta_banco_id=conta.id,
            empresa_id=conta.empresa_id,
            habilitada=habilitada,
            ambiente=form.get('asaas_ambiente'),
            api_key=form.get('asaas_api_key'),
            webhook_token=form.get('asaas_webhook_token'),
            juros_mensal_percentual=form.get('asaas_juros_mensal_percentual'),
            multa_percentual=form.get('asaas_multa_percentual'),
        )
    elif codigo == '077':
        configurar_conta_asaas(
            conta_banco_id=conta.id,
            empresa_id=conta.empresa_id,
            habilitada=False,
            ambiente=None,
            api_key=None,
            webhook_token=None,
        )
        configurar_conta_inter(
            conta_banco_id=conta.id,
            empresa_id=conta.empresa_id,
            habilitada=habilitada,
            ambiente=form.get('inter_ambiente'),
            client_id=form.get('inter_client_id'),
            client_secret=form.get('inter_client_secret'),
            certificado=form.get('inter_certificado'),
            chave_privada=form.get('inter_chave_privada'),
            webhook_token=form.get('inter_webhook_token'),
            juros_mensal_percentual=form.get('inter_juros_mensal_percentual'),
            multa_percentual=form.get('inter_multa_percentual'),
        )
    elif habilitada:
        raise AsaasBoletoError('Informe o código 077 para Banco Inter ou 461 para Asaas antes de habilitar a cobrança.')


@contas_banco_bp.route('/')
@login_required
def index():
    """List all bank accounts"""
    page = request.args.get('page', 1, type=int)
    
    pagination = scoped_query(ContaBanco).paginate(page=page, per_page=20)
    contas = pagination.items
    
    return render_template(
        'contas_banco/index.html',
        contas=contas,
        pagination=pagination
    )


@contas_banco_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def criar():
    """Create new bank account"""
    contas_fluxo = scoped_query(FluxoContaModel).filter_by(ativo=True).all()
    
    if request.method == 'POST':
        try:
            # Ensure current user has an associated company
            if not getattr(current_user, 'empresa_id', None):
                flash('Usuário não está associado a uma empresa.', 'danger')
                return redirect(url_for('contas_banco.criar'))

            is_principal = request.form.get('is_principal') == 'on'
            conta = ContaBanco(
                empresa_id=tenant_id(),
                nome=request.form.get('nome'),
                banco='Caixa',
                agencia=request.form.get('agencia'),
                numero_conta=request.form.get('numero_conta'),
                dv=request.form.get('dv'),
                fluxo_conta_id=request.form.get('fluxo_conta_id', type=int),
                saldo_inicial=request.form.get('saldo_inicial', type=float),
                ativo=request.form.get('ativo') == 'on',
                is_principal=is_principal
            )
            _atualizar_dados_bancarios(request.form, conta)
            if is_principal:
                # Desmarcar outras contas principais da mesma empresa
                ContaBanco.query.filter_by(empresa_id=conta.empresa_id, is_principal=True).update({'is_principal': False})
            else:
                # Se for a única conta da empresa, torna principal
                total_contas = ContaBanco.query.filter_by(empresa_id=conta.empresa_id).count()
                if total_contas == 0:
                    conta.is_principal = True
            db.session.add(conta)
            db.session.flush()
            _configurar_cobranca(conta, request.form)
            db.session.commit()
            
            flash(f'Conta bancária {conta.nome} criada com sucesso', 'success')
            return redirect(url_for('contas_banco.index'))
        
        except (AsaasBoletoError, InterBolePixError) as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.exception('Erro ao criar conta bancária: %s', e)
            flash('Erro ao criar conta bancária. Verifique os dados e tente novamente.', 'danger')
            return redirect(url_for('contas_banco.criar'))
    
    return render_template(
        'contas_banco/form.html',
        action='criar',
        contas_fluxo=contas_fluxo,
        instituicoes_bancarias=InstituicaoBancaria.query.order_by(InstituicaoBancaria.codigo_banco).all(),
        asaas_config=None,
        inter_config=None,
    )


@contas_banco_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edit bank account"""
    conta = scoped_get_or_404(ContaBanco, id)
    contas_fluxo = scoped_query(FluxoContaModel).filter_by(ativo=True).all()
    
    if request.method == 'POST':
        try:
            conta.nome = request.form.get('nome')
            conta.agencia = request.form.get('agencia')
            conta.numero_conta = request.form.get('numero_conta')
            conta.dv = request.form.get('dv')
            _atualizar_dados_bancarios(request.form, conta)
            conta.fluxo_conta_id = request.form.get('fluxo_conta_id', type=int)
            conta.saldo_inicial = request.form.get('saldo_inicial', type=float)
            conta.ativo = request.form.get('ativo') == 'on'
            is_principal = request.form.get('is_principal') == 'on'
            if is_principal:
                # Desmarcar outras contas principais da mesma empresa
                ContaBanco.query.filter(ContaBanco.empresa_id==conta.empresa_id, ContaBanco.id!=conta.id, ContaBanco.is_principal==True).update({'is_principal': False})
                conta.is_principal = True
            else:
                # Se for a única conta da empresa, mantém principal
                total_contas = ContaBanco.query.filter_by(empresa_id=conta.empresa_id).count()
                if total_contas == 1:
                    conta.is_principal = True
                else:
                    conta.is_principal = False
            _configurar_cobranca(conta, request.form)
            db.session.commit()
            
            flash(f'Conta bancária {conta.nome} atualizada com sucesso', 'success')
            return redirect(url_for('contas_banco.index'))
        
        except (AsaasBoletoError, InterBolePixError) as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao atualizar conta bancária: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao atualizar conta bancária: {str(e)}', 'danger')
    
    return render_template(
        'contas_banco/form.html',
        action='editar',
        conta=conta,
        contas_fluxo=contas_fluxo,
        instituicoes_bancarias=InstituicaoBancaria.query.order_by(InstituicaoBancaria.codigo_banco).all(),
        asaas_config=conta.asaas_config,
        inter_config=conta.inter_config,
    )


@contas_banco_bp.route('/<int:id>/ver')
@login_required
def ver(id):
    """View bank account details"""
    conta = scoped_get_or_404(ContaBanco, id)
    lancamentos = conta.lancamentos.order_by(Lancamento.data_evento.desc()).limit(20).all()
    
    return render_template(
        'contas_banco/details.html',
        conta=conta,
        lancamentos=lancamentos
    )


@contas_banco_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
def deletar(id):
    """Delete bank account"""
    conta = scoped_get_or_404(ContaBanco, id)
    
    try:
        conta.ativo = False
        db.session.commit()
        flash(f'Conta bancária {conta.nome} desativada com sucesso', 'success')
    except Exception as e:
        import logging, traceback
        db.session.rollback()
        logging.error('Erro ao deletar conta bancária: %s\n%s', e, traceback.format_exc())
        flash(f'Erro ao deletar conta bancária: {str(e)}', 'danger')
    
    return redirect(url_for('contas_banco.index'))


@contas_banco_bp.route('/api/search')
@login_required
def api_search():
    """API for bank accounts search"""
    termo = request.args.get('q', '')
    
    query = scoped_query(ContaBanco).filter(ContaBanco.ativo == True)
    
    if termo:
        query = query.filter(
            (ContaBanco.nome.ilike(f'%{termo}%')) |
            (ContaBanco.numero_conta.ilike(f'%{termo}%'))
        )
    
    contas = query.limit(10).all()
    
    return jsonify([{
        'id': c.id,
        'text': f'{c.nome} - {c.banco}',
        'nome': c.nome,
        'banco': c.banco
    } for c in contas])
