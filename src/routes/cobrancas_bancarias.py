from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from html import escape

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from src.models import (
    AsaasContaConfig,
    AsaasCobranca,
    Entidade,
    FluxoContaModel,
    InterContaConfig,
    InterCobranca,
    Lancamento,
    NfseNacionalEmissao,
    ContaBanco,
    db,
)
from src.services.asaas_boleto import AsaasBoletoError, cancelar_boleto, gerar_boleto
from src.services.asaas_client import AsaasApiError
from src.services.inter_bolepix import InterBolePixError, gerar_bolepix
from src.services.brevo import brevo_service
from src.tenant import scoped_get_or_404, scoped_query, tenant_id

cobrancas_bancarias_bp = Blueprint(
    'cobrancas_bancarias',
    __name__,
    url_prefix='/cobrancas-bancarias',
)


def _contas_habilitadas():
    return (
        scoped_query(ContaBanco)
        .outerjoin(AsaasContaConfig)
        .outerjoin(InterContaConfig)
        .filter(
            ContaBanco.ativo.is_(True),
            or_(
                (
                    (ContaBanco.codigo_banco == '461')
                    & AsaasContaConfig.cobranca_habilitada.is_(True)
                    & or_(AsaasContaConfig.ativo.is_(True), AsaasContaConfig.ativo.is_(None))
                ),
                (
                    (ContaBanco.codigo_banco == '077')
                    & InterContaConfig.cobranca_habilitada.is_(True)
                    & or_(InterContaConfig.ativo.is_(True), InterContaConfig.ativo.is_(None))
                ),
            ),
        )
        .distinct()
        .all()
    )


@cobrancas_bancarias_bp.route('/')
@login_required
def index():
    empresa_id = tenant_id()
    lancamentos = (
        scoped_query(Lancamento)
        .join(FluxoContaModel)
        .filter(Lancamento.status == 'aberto', FluxoContaModel.tipo == 'R')
        .order_by(Lancamento.data_vencimento.asc())
        .limit(100)
        .all()
    )
    emissoes = (
        scoped_query(NfseNacionalEmissao)
        .filter(
            NfseNacionalEmissao.situacao_fiscal == 'AUTORIZADA',
            NfseNacionalEmissao.lancamento_id.isnot(None),
        )
        .order_by(NfseNacionalEmissao.id.desc())
        .limit(100)
        .all()
    )
    entidades = scoped_query(Entidade).filter_by(ativo=True).order_by(Entidade.nome.asc()).all()
    fluxos = scoped_query(FluxoContaModel).filter_by(ativo=True, tipo='R').all()
    cobrancas_asaas = (
        scoped_query(AsaasCobranca)
        .order_by(AsaasCobranca.criado_em.desc())
        .limit(50)
        .all()
    )
    cobrancas_inter = (
        scoped_query(InterCobranca)
        .order_by(InterCobranca.criado_em.desc())
        .limit(50)
        .all()
    )
    return render_template(
        'cobrancas_bancarias/index.html',
        contas_banco=_contas_habilitadas(),
        lancamentos=lancamentos,
        emissoes=emissoes,
        entidades=entidades,
        fluxos=fluxos,
        empresa_id=empresa_id,
        cobrancas_asaas=cobrancas_asaas,
        cobrancas_inter=cobrancas_inter,
    )


@cobrancas_bancarias_bp.route('/<int:id>/enviar-email', methods=['POST'])
@login_required
def enviar_email(id):
    cobranca = scoped_get_or_404(AsaasCobranca, id)
    entidade = cobranca.lancamento.entidade if cobranca.lancamento else None
    email = (entidade.email if entidade else '').strip()
    if not email:
        flash('O cliente não possui e-mail cadastrado.', 'danger')
        return redirect(url_for('cobrancas_bancarias.index'))
    link = (cobranca.bank_slip_url or cobranca.invoice_url or '').strip()
    if not link:
        flash('O Asaas não retornou um link para o boleto.', 'danger')
        return redirect(url_for('cobrancas_bancarias.index'))

    nome_cliente = entidade.nome if entidade else email
    empresa = getattr(current_user, 'empresa', None)
    nome_empresa = (getattr(empresa, 'nome_fantasia', None) or getattr(empresa, 'nome', None) or 'LiveSun Comercial')
    html_content = (
        f'<p>Olá, {escape(nome_cliente)}.</p>'
        f'<p>Segue o boleto referente à cobrança no valor de '
        f'<strong>R$ {cobranca.valor:,.2f}</strong>, com vencimento em '
        f'<strong>{cobranca.data_vencimento.strftime("%d/%m/%Y")}</strong>.</p>'
        f'<p><a href="{escape(link, quote=True)}">Abrir e imprimir boleto</a></p>'
        f'<p>Atenciosamente,<br>{escape(nome_empresa)}</p>'
    )
    enviado = brevo_service.send_transactional_email(
        email,
        nome_cliente,
        f'Boleto bancário - {nome_empresa}',
        html_content,
    )
    if enviado:
        flash(f'Boleto enviado para {email}.', 'success')
    else:
        flash('O Brevo não confirmou o envio do boleto. Verifique a configuração de e-mail.', 'danger')
    return redirect(url_for('cobrancas_bancarias.index'))


@cobrancas_bancarias_bp.route('/enviar-email-lote', methods=['POST'])
@login_required
def enviar_email_lote():
    ids = request.form.getlist('cobranca_ids', type=int)
    if not ids:
        flash('Selecione ao menos um boleto.', 'warning')
        return redirect(url_for('cobrancas_bancarias.index'))


    enviados = 0
    falhas = 0
    for cobranca in scoped_query(AsaasCobranca).filter(AsaasCobranca.id.in_(ids)).all():
        entidade = cobranca.lancamento.entidade if cobranca.lancamento else None
        email = (entidade.email if entidade else '').strip()
        link = (cobranca.bank_slip_url or cobranca.invoice_url or '').strip()
        if not email or not link:
            falhas += 1
            continue
        nome_cliente = entidade.nome if entidade else email
        empresa = getattr(current_user, 'empresa', None)
        nome_empresa = (
            getattr(empresa, 'nome_fantasia', None)
            or getattr(empresa, 'nome', None)
            or 'LiveSun Comercial'
        )
        html_content = (
            f'<p>Olá, {escape(nome_cliente)}.</p>'
            f'<p>Segue o boleto referente à cobrança no valor de '
            f'<strong>R$ {cobranca.valor:,.2f}</strong>, com vencimento em '
            f'<strong>{cobranca.data_vencimento.strftime("%d/%m/%Y")}</strong>.</p>'
            f'<p><a href="{escape(link, quote=True)}">Abrir e imprimir boleto</a></p>'
            f'<p>Atenciosamente,<br>{escape(nome_empresa)}</p>'
        )
        if brevo_service.send_transactional_email(
            email,
            nome_cliente,
            f'Boleto bancário - {nome_empresa}',
            html_content,
        ):
            enviados += 1
        else:
            falhas += 1

    if enviados:
        flash(f'{enviados} boleto(s) enviado(s) ao cliente.', 'success')
    if falhas:
        flash(f'{falhas} boleto(s) não puderam ser enviados.', 'warning')
    return redirect(url_for('cobrancas_bancarias.index'))


@cobrancas_bancarias_bp.route('/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar(id):
    cobranca = scoped_get_or_404(AsaasCobranca, id)
    try:
        cancelar_boleto(cobranca)
        flash('Boleto cancelado com sucesso.', 'success')
    except (AsaasBoletoError, AsaasApiError) as exc:
        db.session.rollback()
        flash(str(exc), 'danger')
    return redirect(url_for('cobrancas_bancarias.index'))


@cobrancas_bancarias_bp.route('/gerar', methods=['POST'])
@login_required
def gerar():
    origem = (request.form.get('origem') or '').strip().lower()
    conta_banco_id = request.form.get('conta_banco_id', type=int)
    if origem not in {'nfse', 'lancamento', 'avulsa'}:
        flash('Selecione a origem da cobrança.', 'danger')
        return redirect(url_for('cobrancas_bancarias.index'))

    try:
        if origem == 'nfse':
            emissao = scoped_get_or_404(
                NfseNacionalEmissao,
                request.form.get('nfse_emissao_id', type=int),
            )
            if emissao.situacao_fiscal != 'AUTORIZADA' or not emissao.lancamento_id:
                raise AsaasBoletoError(
                    'A NFS-e deve estar autorizada e possuir lançamento financeiro vinculado.'
                )
            lancamento = scoped_get_or_404(Lancamento, emissao.lancamento_id)
            if conta_banco_id:
                lancamento.conta_banco_id = conta_banco_id
            if not lancamento.conta_banco_id:
                raise AsaasBoletoError('Selecione a conta Asaas para a cobrança.')
            nfse_id = emissao.id
        elif origem == 'lancamento':
            lancamento = scoped_get_or_404(
                Lancamento,
                request.form.get('lancamento_id', type=int),
            )
            if conta_banco_id:
                lancamento.conta_banco_id = conta_banco_id
            nfse_id = None
        else:
            lancamento = _criar_lancamento_avulso(request.form)
            nfse_id = None

        juros = _decimal_optional(request.form.get('juros_mensal_percentual'))
        multa = _decimal_optional(request.form.get('multa_percentual'))
        codigo_banco = str(getattr(lancamento.conta_banco, 'codigo_banco', '') or '').zfill(3)
        if codigo_banco == '461':
            cobranca = gerar_boleto(
                lancamento,
                origem=origem,
                nfse_emissao_id=nfse_id,
                juros_mensal_percentual=juros,
                multa_percentual=multa,
            )
            identificador = f'Asaas: {cobranca.asaas_payment_id}'
        elif codigo_banco == '077':
            cobranca = gerar_bolepix(
                lancamento,
                origem=origem,
                nfse_emissao_id=nfse_id,
                juros_mensal_percentual=juros,
                multa_percentual=multa,
            )
            identificador = f'Inter: {cobranca.codigo_solicitacao}'
        else:
            raise AsaasBoletoError('O código do banco selecionado não possui provedor de cobrança implementado.')
        flash(
            f'Cobrança gerada com sucesso. {identificador}.',
            'success',
        )
    except (AsaasBoletoError, AsaasApiError, InterBolePixError) as exc:
        db.session.rollback()
        flash(str(exc), 'danger')
    except (TypeError, ValueError):
        db.session.rollback()
        flash('Informe valores válidos para a cobrança.', 'danger')
    return redirect(url_for('cobrancas_bancarias.index'))


def _decimal_optional(value: str | None) -> Decimal | None:
    text = (value or '').strip().replace(',', '.')
    return Decimal(text) if text else None


def _criar_lancamento_avulso(form) -> Lancamento:
    entidade_id = form.get('entidade_id', type=int)
    conta_banco_id = form.get('conta_banco_id', type=int)
    fluxo_conta_id = form.get('fluxo_conta_id', type=int)
    valor = _decimal_optional(form.get('valor_real'))
    data_evento = datetime.strptime(form.get('data_evento'), '%Y-%m-%d').date()
    data_vencimento = datetime.strptime(form.get('data_vencimento'), '%Y-%m-%d').date()
    if not entidade_id or not conta_banco_id or not fluxo_conta_id or not valor or valor <= 0:
        raise AsaasBoletoError('Cliente, conta Asaas, fluxo, valor e datas são obrigatórios.')
    entidade = scoped_get_or_404(Entidade, entidade_id)
    conta = scoped_get_or_404(ContaBanco, conta_banco_id)
    fluxo = scoped_get_or_404(FluxoContaModel, fluxo_conta_id)
    if fluxo.tipo != 'R':
        raise AsaasBoletoError('A conta de fluxo da cobrança deve ser de recebimento.')
    lancamento = Lancamento(
        empresa_id=tenant_id(),
        data_evento=data_evento,
        data_vencimento=data_vencimento,
        status='aberto',
        entidade_id=entidade.id,
        fluxo_conta_id=fluxo.id,
        conta_banco_id=conta.id,
        valor_real=valor,
        valor_pago=Decimal('0'),
        numero_documento=(form.get('numero_documento') or '').strip() or None,
        observacoes=(form.get('observacoes') or '').strip() or None,
    )
    db.session.add(lancamento)
    db.session.flush()
    return lancamento
