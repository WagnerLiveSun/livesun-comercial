from __future__ import annotations

import json
from datetime import datetime, date
from decimal import Decimal

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from src.models import (
    ContaBanco,
    db,
    Entidade,
    Empresa,
    FluxoContaModel,
    Lancamento,
    NfseNacionalCertificado,
    NfseNacionalConfiguracao,
    NfseNacionalEmissao,
    NfseNacionalEvento,
    NfseNacionalFila,
    NfseNacionalIntegracaoOrigem,
    Servico,
)
from src.services.nfse_nacional import (
    build_dps_xml,
    build_idempotency_hash,
    cancelar_emissao,
    generate_internal_number,
    transmitir_emissao,
)
from src.tenant import scoped_get_or_404, scoped_query, tenant_id


nfse_nacional_bp = Blueprint('nfse_nacional', __name__, url_prefix='/nfse-nacional')


def _decimal(value, default: Decimal = Decimal('0.00')) -> Decimal:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return Decimal(text.replace(',', '.'))
    except Exception:
        return default


def _date_from_request(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except Exception:
        return None


def _get_or_create_fluxo_recebimento(empresa_id: int) -> int | None:
    conta = (
        scoped_query(FluxoContaModel)
        .filter(FluxoContaModel.tipo == 'R')
        .order_by(FluxoContaModel.ativo.desc(), FluxoContaModel.id.asc())
        .first()
    )
    if conta:
        return conta.id

    conta = FluxoContaModel(
        empresa_id=empresa_id,
        codigo='1',
        descricao='Recebimentos NFS-e',
        tipo='R',
        nivel_sintetico=1,
        nivel_analitico=None,
        ativo=True,
    )
    db.session.add(conta)
    db.session.flush()
    return conta.id


def _get_or_create_conta_banco_principal(empresa_id: int) -> ContaBanco | None:
    conta = ContaBanco.query.filter_by(empresa_id=empresa_id, is_principal=True).first()
    if conta:
        return conta
    return ContaBanco.query.filter_by(empresa_id=empresa_id, ativo=True).order_by(ContaBanco.id.asc()).first()


def _get_or_create_config(empresa_id: int, ambiente: str) -> NfseNacionalConfiguracao:
    configuracao = NfseNacionalConfiguracao.query.filter_by(empresa_id=empresa_id, ambiente=ambiente).first()
    if configuracao:
        return configuracao

    configuracao = NfseNacionalConfiguracao(
        empresa_id=empresa_id,
        ambiente=ambiente,
        emissor_ativo=True,
        versao_layout='1.0',
    )
    db.session.add(configuracao)
    db.session.flush()
    return configuracao


def _get_or_create_tomador(empresa_id: int, payload: dict) -> Entidade:
    entidade_id = payload.get('tomador_id') or payload.get('entidade_id')
    if entidade_id:
        entidade = scoped_get_or_404(Entidade, int(entidade_id))
        entidade.tipo = 'C'
        if not entidade.fluxo_conta_id:
            entidade.fluxo_conta_id = _get_or_create_fluxo_recebimento(empresa_id)
        return entidade

    documento = ''.join(ch for ch in str(payload.get('tomador_documento') or payload.get('cnpj_cpf') or '') if ch.isdigit())
    if not documento:
        raise ValueError('Informe o CPF/CNPJ do tomador.')

    entidade = Entidade.query.filter_by(empresa_id=empresa_id, cnpj_cpf=documento).first()
    if entidade:
        if entidade.tipo != 'C':
            entidade.tipo = 'C'
        if not entidade.fluxo_conta_id:
            entidade.fluxo_conta_id = _get_or_create_fluxo_recebimento(empresa_id)
        return entidade

    nome = (payload.get('tomador_nome') or payload.get('razao_nome') or payload.get('nome') or f'Tomador {documento}').strip()
    entidade = Entidade(
        empresa_id=empresa_id,
        nome=nome,
        cnpj_cpf=documento,
        tipo='C',
        fluxo_conta_id=_get_or_create_fluxo_recebimento(empresa_id),
        ativo=True,
    )
    db.session.add(entidade)
    db.session.flush()
    return entidade


def _get_or_create_servico(empresa_id: int, payload: dict) -> Servico:
    servico_id = payload.get('servico_id')
    if servico_id:
        return scoped_get_or_404(Servico, int(servico_id))

    empresa = Empresa.query.get_or_404(empresa_id)

    codigo_interno = (payload.get('codigo_interno') or payload.get('servico_codigo_interno') or '').strip()
    descricao = (payload.get('descricao') or payload.get('servico_descricao') or '').strip()
    if not codigo_interno:
        raise ValueError('Informe o código interno do serviço.')
    if not descricao:
        raise ValueError('Informe a descrição do serviço.')

    servico = Servico.query.filter_by(empresa_id=empresa_id, codigo_interno=codigo_interno).first()
    if servico:
        servico.descricao = descricao or servico.descricao
        servico.codigo_servico = (
            payload.get('codigo_servico')
            or payload.get('servico_codigo_nacional')
            or servico.codigo_servico
            or empresa.fiscal_principal_valor('codigo_servico')
        )
        servico.nbs = (
            payload.get('nbs')
            or payload.get('servico_nbs')
            or servico.nbs
            or empresa.fiscal_principal_valor('nbs')
        )
        servico.natureza_servico = payload.get('natureza_servico') or servico.natureza_servico
        servico.indicador_incidencia = payload.get('indicador_incidencia') or servico.indicador_incidencia
        return servico

    servico = Servico(
        empresa_id=empresa_id,
        codigo_interno=codigo_interno,
        descricao=descricao,
        codigo_servico=payload.get('codigo_servico') or payload.get('servico_codigo_nacional') or empresa.fiscal_principal_valor('codigo_servico'),
        nbs=payload.get('nbs') or payload.get('servico_nbs') or empresa.fiscal_principal_valor('nbs'),
        natureza_servico=payload.get('natureza_servico'),
        indicador_incidencia=payload.get('indicador_incidencia'),
        ativo=str(payload.get('ativo', True)).lower() in {'1', 'true', 'on', 'sim'},
    )
    db.session.add(servico)
    db.session.flush()
    return servico


def _ensure_integration_origin(empresa_id: int, payload: dict, hash_idempotencia: str) -> NfseNacionalIntegracaoOrigem:
    origem = NfseNacionalIntegracaoOrigem.query.filter_by(
        empresa_id=empresa_id,
        origem_tipo=payload.get('origem_tipo') or 'MANUAL',
        origem_id=str(payload.get('origem_id') or '') or None,
        canal_origem=payload.get('canal_origem') or 'manual',
    ).first()
    if origem:
        origem.origem_referencia = payload.get('origem_referencia') or origem.origem_referencia
        origem.payload_origem = json.dumps(payload, ensure_ascii=False, default=str)
        origem.hash_idempotencia = hash_idempotencia
        return origem

    origem = NfseNacionalIntegracaoOrigem(
        empresa_id=empresa_id,
        origem_tipo=payload.get('origem_tipo') or 'MANUAL',
        origem_id=str(payload.get('origem_id') or '') or None,
        origem_referencia=payload.get('origem_referencia') or None,
        canal_origem=payload.get('canal_origem') or 'manual',
        payload_origem=json.dumps(payload, ensure_ascii=False, default=str),
        hash_idempotencia=hash_idempotencia,
    )
    db.session.add(origem)
    db.session.flush()
    return origem


def _build_payload(empresa: Empresa, configuracao: NfseNacionalConfiguracao, tomador: Entidade, servico: Servico, payload: dict, numero_interno: str, hash_idempotencia: str) -> dict:
    valor_servico = _decimal(payload.get('valor_servico'))
    valor_deducoes = _decimal(payload.get('valor_deducoes'))
    aliquota = _decimal(payload.get('aliquota_iss'))
    valor_iss = _decimal(payload.get('valor_iss'))
    if valor_iss <= 0 and valor_servico > 0 and aliquota > 0:
        valor_iss = (valor_servico * aliquota / Decimal('100')).quantize(Decimal('0.01'))

    dados = {
        'empresa_id': empresa.id,
        'empresa_nome': empresa.nome,
        'empresa_cnpj': empresa.cnpj,
        'inscricao_municipal': configuracao.inscricao_municipal,
        'codigo_municipio': configuracao.codigo_municipio,
        'regime_tributario': configuracao.regime_tributario,
        'ambiente': configuracao.ambiente,
        'versao_layout': configuracao.versao_layout,
        'versao_xsd': '1.0',
        'numero_interno': numero_interno,
        'numero_nfse_sugerido': payload.get('numero_nfse_sugerido'),
        'hash_idempotencia': hash_idempotencia,
        'tomador_id': tomador.id,
        'tomador_nome': tomador.nome,
        'tomador_documento': tomador.cnpj_cpf,
        'tomador_tipo': tomador.tipo,
        'servico_id': servico.id,
        'servico_codigo_interno': servico.codigo_interno,
        'servico_codigo_nacional': servico.codigo_servico,
        'servico_nbs': servico.nbs,
        'servico_descricao': servico.descricao,
        'valor_servico': valor_servico,
        'valor_deducoes': valor_deducoes,
        'valor_iss': valor_iss,
        'origem_tipo': payload.get('origem_tipo') or 'MANUAL',
        'origem_id': payload.get('origem_id') or '',
        'origem_referencia': payload.get('origem_referencia') or '',
        'canal_origem': payload.get('canal_origem') or 'manual',
        'observacoes': payload.get('observacoes') or '',
    }
    dados['xml_dps'] = build_dps_xml(dados)
    return dados


@nfse_nacional_bp.route('/', methods=['GET'])
@login_required
def index():
    empresa_id = tenant_id()
    configuracoes = NfseNacionalConfiguracao.query.filter_by(empresa_id=empresa_id).order_by(NfseNacionalConfiguracao.ambiente.asc()).all()
    certificados = sorted(
        NfseNacionalCertificado.query.filter_by(empresa_id=empresa_id).all(),
        key=lambda certificado: (
            certificado.validade_em is None,
            -(certificado.validade_em.toordinal()) if certificado.validade_em else 0,
        ),
    )
    emissoes = scoped_query(NfseNacionalEmissao).order_by(NfseNacionalEmissao.criado_em.desc()).limit(8).all()
    total_emissoes = scoped_query(NfseNacionalEmissao).count()
    total_autorizadas = scoped_query(NfseNacionalEmissao).filter(NfseNacionalEmissao.situacao_fiscal == 'AUTORIZADA').count()
    total_rejeitadas = scoped_query(NfseNacionalEmissao).filter(NfseNacionalEmissao.situacao_fiscal == 'REJEITADA').count()

    return render_template(
        'nfse_nacional/index.html',
        configuracoes=configuracoes,
        certificados=certificados,
        emissoes=emissoes,
        total_emissoes=total_emissoes,
        total_autorizadas=total_autorizadas,
        total_rejeitadas=total_rejeitadas,
    )


@nfse_nacional_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    empresa_id = tenant_id()
    # acesso restrito a administradores
    if not getattr(current_user, 'is_admin', False):
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('nfse_nacional.index'))
    ambiente = (request.values.get('ambiente') or 'homologacao').strip().lower()
    configuracao = NfseNacionalConfiguracao.query.filter_by(empresa_id=empresa_id, ambiente=ambiente).first()
    certificados_ambiente = sorted(
        NfseNacionalCertificado.query.filter_by(empresa_id=empresa_id, ambiente=ambiente, ativo=True).all(),
        key=lambda certificado: (
            certificado.validade_em is None,
            -(certificado.validade_em.toordinal()) if certificado.validade_em else 0,
        ),
    )
    certificado = certificados_ambiente[0] if certificados_ambiente else None

    if request.method == 'POST':
        try:
            configuracao = configuracao or NfseNacionalConfiguracao(empresa_id=empresa_id, ambiente=ambiente)
            configuracao.inscricao_municipal = (request.form.get('inscricao_municipal') or '').strip() or None
            configuracao.codigo_municipio = (request.form.get('codigo_municipio') or '').strip() or None
            configuracao.regime_tributario = (request.form.get('regime_tributario') or '').strip() or None
            configuracao.serie = (request.form.get('serie') or '').strip() or '1'
            configuracao.versao_layout = (request.form.get('versao_layout') or '').strip() or '1.0'
            configuracao.endpoint_base = (request.form.get('endpoint_base') or '').strip() or None
            configuracao.emissor_ativo = request.form.get('emissor_ativo') == 'on'
            configuracao.observacoes = request.form.get('observacoes') or None
            db.session.add(configuracao)

            arquivo_nome = (request.form.get('arquivo_nome') or '').strip()
            validade_em = _date_from_request(request.form.get('validade_em'))
            caminho_arquivo = (request.form.get('caminho_arquivo') or '').strip() or None
            if arquivo_nome:
                if certificado is None:
                    certificado = NfseNacionalCertificado(
                        empresa_id=empresa_id,
                        ambiente=ambiente,
                        arquivo_nome=arquivo_nome,
                        caminho_arquivo=caminho_arquivo,
                        senha=(request.form.get('certificado_senha') or None),
                        validade_em=validade_em,
                        ativo=True,
                        observacoes=request.form.get('certificado_observacoes') or None,
                    )
                    db.session.add(certificado)
                else:
                    certificado.arquivo_nome = arquivo_nome
                    certificado.caminho_arquivo = caminho_arquivo
                    certificado.senha = (request.form.get('certificado_senha') or certificado.senha)
                    certificado.validade_em = validade_em
                    certificado.ativo = True
                    certificado.observacoes = request.form.get('certificado_observacoes') or None

            db.session.commit()
            flash('Configuração fiscal atualizada com sucesso.', 'success')
            return redirect(url_for('nfse_nacional.configuracoes', ambiente=ambiente))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao salvar configuração da NFS-e: {exc}', 'danger')

    return render_template(
        'nfse_nacional/configuracoes.html',
        configuracao=configuracao,
        certificado=certificado,
        ambiente=ambiente,
    )


@nfse_nacional_bp.route('/tomadores', methods=['GET', 'POST'])
@login_required
def tomadores():
    empresa_id = tenant_id()
    busca = (request.args.get('busca') or '').strip()
    query = scoped_query(Entidade).filter(Entidade.tipo == 'C')
    if busca:
        query = query.filter(
            (Entidade.nome.ilike(f'%{busca}%')) |
            (Entidade.cnpj_cpf.ilike(f'%{busca}%'))
        )

    if request.method == 'POST':
        try:
            entidade_id = request.form.get('entidade_id', type=int)
            if entidade_id:
                entidade = scoped_get_or_404(Entidade, entidade_id)
            else:
                entidade = Entidade(empresa_id=empresa_id)
                db.session.add(entidade)

            entidade.nome = (request.form.get('nome') or '').strip()
            entidade.cnpj_cpf = ''.join(ch for ch in (request.form.get('cnpj_cpf') or '') if ch.isdigit())
            entidade.tipo = 'C'
            entidade.fluxo_conta_id = entidade.fluxo_conta_id or _get_or_create_fluxo_recebimento(empresa_id)
            entidade.ativo = request.form.get('ativo') == 'on'

            if not entidade.nome or not entidade.cnpj_cpf:
                raise ValueError('Nome e CPF/CNPJ são obrigatórios.')

            db.session.commit()
            flash('Tomador salvo com sucesso.', 'success')
            return redirect(url_for('nfse_nacional.tomadores', busca=busca))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao salvar tomador: {exc}', 'danger')

    tomadores = query.order_by(Entidade.nome.asc()).all()
    return render_template('nfse_nacional/tomadores.html', tomadores=tomadores, busca=busca)


@nfse_nacional_bp.route('/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    empresa = Empresa.query.get_or_404(tenant_id())
    busca = (request.args.get('busca') or '').strip()
    query = scoped_query(Servico)
    if busca:
        query = query.filter(
            (Servico.codigo_interno.ilike(f'%{busca}%')) |
            (Servico.descricao.ilike(f'%{busca}%')) |
            (Servico.codigo_servico.ilike(f'%{busca}%')) |
            (Servico.nbs.ilike(f'%{busca}%'))
        )

    if request.method == 'POST':
        try:
            servico_id = request.form.get('servico_id', type=int)
            if servico_id:
                servico = scoped_get_or_404(Servico, servico_id)
            else:
                servico = Servico(empresa_id=tenant_id())
                db.session.add(servico)

            servico.codigo_interno = (request.form.get('codigo_interno') or '').strip()
            servico.descricao = (request.form.get('descricao') or '').strip()
            codigo_servico = (request.form.get('codigo_servico') or '').strip()
            nbs = (request.form.get('nbs') or '').strip()
            if not codigo_servico and not servico_id:
                codigo_servico = empresa.fiscal_principal_valor('codigo_servico') or ''
            if not nbs and not servico_id:
                nbs = empresa.fiscal_principal_valor('nbs') or ''
            servico.codigo_servico = codigo_servico or servico.codigo_servico
            servico.nbs = nbs or servico.nbs
            servico.natureza_servico = (request.form.get('natureza_servico') or '').strip() or None
            servico.indicador_incidencia = (request.form.get('indicador_incidencia') or '').strip() or None
            servico.ativo = request.form.get('ativo') == 'on'

            if not servico.codigo_interno or not servico.descricao:
                raise ValueError('Código interno e descrição são obrigatórios.')

            db.session.commit()
            flash('Serviço salvo com sucesso.', 'success')
            return redirect(url_for('nfse_nacional.servicos', busca=busca))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao salvar serviço: {exc}', 'danger')

    servicos = query.order_by(Servico.codigo_interno.asc()).all()
    fiscal_defaults = {
        'codigo_servico': empresa.fiscal_principal_valor('codigo_servico'),
        'nbs': empresa.fiscal_principal_valor('nbs'),
        'codigo_servico_opcoes': empresa.fiscal_valores_por_tipo('codigo_servico'),
        'nbs_opcoes': empresa.fiscal_valores_por_tipo('nbs'),
    }
    return render_template('nfse_nacional/servicos.html', servicos=servicos, busca=busca, fiscal_defaults=fiscal_defaults)


@nfse_nacional_bp.route('/emissoes', methods=['GET', 'POST'])
@login_required
def emissoes():
    empresa_id = tenant_id()
    empresa = Empresa.query.get_or_404(empresa_id)
    filtro_status = (request.args.get('status') or '').strip()
    filtro_busca = (request.args.get('busca') or '').strip()

    if request.method == 'GET':
        query = scoped_query(NfseNacionalEmissao).order_by(NfseNacionalEmissao.criado_em.desc())
        if filtro_status:
            query = query.filter(NfseNacionalEmissao.status_processamento == filtro_status)
        if filtro_busca:
            query = query.join(Entidade, NfseNacionalEmissao.tomador).filter(
                (NfseNacionalEmissao.numero_interno.ilike(f'%{filtro_busca}%')) |
                (NfseNacionalEmissao.numero_nfse.ilike(f'%{filtro_busca}%')) |
                (Entidade.nome.ilike(f'%{filtro_busca}%')) |
                (Entidade.cnpj_cpf.ilike(f'%{filtro_busca}%'))
            )
        emissoes = query.limit(50).all()
        tomadores = scoped_query(Entidade).filter(Entidade.tipo == 'C', Entidade.ativo.is_(True)).order_by(Entidade.nome.asc()).all()
        servicos = scoped_query(Servico).filter(Servico.ativo.is_(True)).order_by(Servico.descricao.asc()).all()
        configuracoes = NfseNacionalConfiguracao.query.filter_by(empresa_id=empresa_id).order_by(NfseNacionalConfiguracao.ambiente.asc()).all()
        fiscal_defaults = {
            'codigo_servico': empresa.fiscal_principal_valor('codigo_servico'),
            'nbs': empresa.fiscal_principal_valor('nbs'),
            'codigo_servico_opcoes': empresa.fiscal_valores_por_tipo('codigo_servico'),
            'nbs_opcoes': empresa.fiscal_valores_por_tipo('nbs'),
        }
        return render_template(
            'nfse_nacional/emissoes.html',
            emissoes=emissoes,
            tomadores=tomadores,
            servicos=servicos,
            configuracoes=configuracoes,
            filtro_status=filtro_status,
            filtro_busca=filtro_busca,
            fiscal_defaults=fiscal_defaults,
        )

    data = request.get_json(silent=True) if request.is_json else request.form
    try:
        ambiente = (data.get('ambiente') or 'homologacao').strip().lower()
        configuracao = _get_or_create_config(empresa_id, ambiente)
        tomador = _get_or_create_tomador(empresa_id, data)
        servico = _get_or_create_servico(empresa_id, data)

        valor_servico = _decimal(data.get('valor_servico') or data.get('valor_total'))
        if valor_servico <= 0:
            raise ValueError('Informe um valor de serviço maior que zero.')

        valor_deducoes = _decimal(data.get('valor_deducoes'))
        aliquota_iss = _decimal(data.get('aliquota_iss'))
        valor_iss = _decimal(data.get('valor_iss'))
        if valor_iss <= 0 and valor_servico > 0 and aliquota_iss > 0:
            valor_iss = (valor_servico * aliquota_iss / Decimal('100')).quantize(Decimal('0.01'))

        numero_interno = (data.get('numero_interno') or generate_internal_number(empresa_id)).strip()
        origem_tipo = (data.get('origem_tipo') or 'MANUAL').strip().upper()
        origem_id = data.get('origem_id')
        origem_referencia = data.get('origem_referencia')
        canal_origem = (data.get('canal_origem') or 'manual').strip().lower()
        observacoes = data.get('observacoes') or data.get('descricao') or ''

        hash_base = {
            'empresa_id': empresa_id,
            'ambiente': ambiente,
            'tomador_documento': tomador.cnpj_cpf,
            'servico_codigo': servico.codigo_interno,
            'valor_servico': str(valor_servico),
            'valor_deducoes': str(valor_deducoes),
            'valor_iss': str(valor_iss),
            'origem_tipo': origem_tipo,
            'origem_id': origem_id,
            'origem_referencia': origem_referencia,
            'canal_origem': canal_origem,
            'numero_interno': numero_interno,
        }
        hash_idempotencia = build_idempotency_hash(hash_base)

        existente = scoped_query(NfseNacionalEmissao).filter_by(hash_idempotencia=hash_idempotencia).first()
        if existente:
            if request.is_json:
                return jsonify({
                    'emissao_id': str(existente.id),
                    'status': existente.status_processamento,
                    'situacao_fiscal': existente.situacao_fiscal,
                    'protocolo': existente.protocolo,
                    'nfse': {
                        'numero': existente.numero_nfse,
                        'codigo_verificacao': existente.codigo_verificacao,
                        'xml_armazenado': bool(existente.xml_nfse),
                    },
                }), 200
            flash('Uma emissão com os mesmos dados já foi processada.', 'info')
            return redirect(url_for('nfse_nacional.emissao_detalhe', emissao_id=existente.id))

        origem = _ensure_integration_origin(empresa_id, {
            'origem_tipo': origem_tipo,
            'origem_id': origem_id,
            'origem_referencia': origem_referencia,
            'canal_origem': canal_origem,
            **dict(data),
        }, hash_idempotencia)

        emissao = NfseNacionalEmissao(
            empresa_id=empresa_id,
            configuracao=configuracao,
            ambiente=ambiente,
            numero_interno=numero_interno,
            tomador=tomador,
            servico=servico,
            integracao_origem=origem,
            status_processamento='PENDENTE',
            situacao_fiscal='PENDENTE',
            valor_servico=valor_servico,
            valor_deducoes=valor_deducoes,
            valor_iss=valor_iss,
            observacoes=observacoes,
            hash_idempotencia=hash_idempotencia,
            versao_layout=configuracao.versao_layout or '1.0',
            versao_xsd='1.0',
            origem_tipo=origem_tipo,
            origem_referencia=origem_referencia,
            canal_origem=canal_origem,
            criado_por_user_id=current_user.id,
        )
        db.session.add(emissao)
        db.session.flush()

        payload = _build_payload(empresa, configuracao, tomador, servico, {
            'valor_servico': valor_servico,
            'valor_deducoes': valor_deducoes,
            'valor_iss': valor_iss,
            'ambiente': ambiente,
            'numero_interno': numero_interno,
            'hash_idempotencia': hash_idempotencia,
            'origem_tipo': origem_tipo,
            'origem_id': origem_id,
            'origem_referencia': origem_referencia,
            'canal_origem': canal_origem,
            'observacoes': observacoes,
            'numero_nfse_sugerido': data.get('numero_nfse_sugerido'),
        }, numero_interno, hash_idempotencia)

        emissao.xml_dps = payload.pop('xml_dps')
        emissao.payload_envio = json.dumps(payload, ensure_ascii=False, default=str)

        fila = NfseNacionalFila(
            empresa_id=empresa_id,
            emissao=emissao,
            status_fila='PROCESSANDO',
            tentativas=1,
            payload=emissao.payload_envio,
        )
        db.session.add(fila)

        resultado = transmitir_emissao(payload, configuracao)
        emissao.status_processamento = resultado['status']
        emissao.situacao_fiscal = resultado['situacao_fiscal']
        emissao.protocolo = resultado.get('protocolo')
        emissao.numero_nfse = resultado.get('numero_nfse')
        emissao.codigo_verificacao = resultado.get('codigo_verificacao')
        emissao.chave_nfse = resultado.get('chave_nfse')
        emissao.xml_nfse = resultado.get('xml_nfse')
        emissao.payload_retorno = json.dumps(resultado.get('payload_retorno'), ensure_ascii=False, default=str)
        emissao.log_tecnico = resultado.get('mensagem')
        if not resultado.get('sucesso'):
            emissao.erro_retorno = resultado.get('mensagem')

        fila.status_fila = 'CONCLUIDO' if resultado.get('sucesso') else 'ERRO'
        fila.processado_em = datetime.utcnow()
        fila.ultimo_erro = None if resultado.get('sucesso') else resultado.get('mensagem')
        fila.payload = emissao.payload_envio

        evento = NfseNacionalEvento(
            empresa_id=empresa_id,
            emissao=emissao,
            tipo_evento='EMISSAO',
            status_evento='processado' if resultado.get('sucesso') else 'erro',
            protocolo=resultado.get('protocolo'),
            mensagem=resultado.get('mensagem'),
            payload_envio=emissao.payload_envio,
            payload_retorno=emissao.payload_retorno,
            criado_por_user_id=current_user.id,
        )
        db.session.add(evento)

        if resultado.get('sucesso'):
            conta_banco = _get_or_create_conta_banco_principal(empresa_id)
            fluxo_conta_id = tomador.fluxo_conta_id or _get_or_create_fluxo_recebimento(empresa_id)
            if conta_banco and fluxo_conta_id:
                lancamento = Lancamento(
                    empresa_id=empresa_id,
                    data_evento=_date_from_request(data.get('data_emissao')) or datetime.utcnow().date(),
                    data_vencimento=_date_from_request(data.get('data_vencimento')) or _date_from_request(data.get('data_emissao')) or datetime.utcnow().date(),
                    data_pagamento=None,
                    status='aberto',
                    entidade_id=tomador.id,
                    fluxo_conta_id=fluxo_conta_id,
                    conta_banco_id=conta_banco.id,
                    valor_real=valor_servico,
                    valor_pago=Decimal('0.00'),
                    valor_imposto=valor_iss,
                    valor_outros_custos=Decimal('0.00'),
                    numero_documento=emissao.numero_nfse or numero_interno,
                    observacoes=observacoes or servico.descricao,
                    fonte='nfse_nacional',
                )
                db.session.add(lancamento)
                db.session.flush()
                emissao.lancamento = lancamento
            else:
                emissao.log_tecnico = (emissao.log_tecnico or '') + ' | Emissão autorizada sem lançamento financeiro por ausência de conta bancária principal.'

        db.session.commit()

        resposta = {
            'emissao_id': str(emissao.id),
            'status': emissao.status_processamento,
            'situacao_fiscal': emissao.situacao_fiscal,
            'protocolo': emissao.protocolo,
            'nfse': {
                'numero': emissao.numero_nfse,
                'codigo_verificacao': emissao.codigo_verificacao,
                'xml_armazenado': bool(emissao.xml_nfse),
            },
        }
        if request.is_json:
            return jsonify(resposta), 201 if resultado.get('sucesso') else 202

        flash('Emissão processada com sucesso.' if resultado.get('sucesso') else 'Emissão registrada com ressalvas.', 'success' if resultado.get('sucesso') else 'warning')
        return redirect(url_for('nfse_nacional.emissao_detalhe', emissao_id=emissao.id))
    except Exception as exc:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(exc)}), 400
        flash(f'Erro ao emitir NFS-e: {exc}', 'danger')
        return redirect(url_for('nfse_nacional.emissoes'))


@nfse_nacional_bp.route('/emissoes/<int:emissao_id>', methods=['GET'])
@login_required
def emissao_detalhe(emissao_id: int):
    emissao = scoped_get_or_404(NfseNacionalEmissao, emissao_id)
    return render_template('nfse_nacional/emissao_detalhe.html', emissao=emissao)


@nfse_nacional_bp.route('/emissoes/<int:emissao_id>/cancelar', methods=['POST'])
@login_required
def emissao_cancelar(emissao_id: int):
    emissao = scoped_get_or_404(NfseNacionalEmissao, emissao_id)
    if emissao.situacao_fiscal == 'CANCELADA':
        flash('A emissão já está cancelada.', 'info')
        return redirect(url_for('nfse_nacional.emissao_detalhe', emissao_id=emissao.id))

    try:
        motivo = (request.form.get('motivo') if not request.is_json else (request.get_json(silent=True) or {}).get('motivo')) or 'Cancelamento solicitado pelo usuário.'
        payload = {
            'empresa_id': emissao.empresa_id,
            'emissao_id': emissao.id,
            'numero_nfse': emissao.numero_nfse,
            'protocolo': emissao.protocolo,
            'motivo': motivo,
            'hash_idempotencia': emissao.hash_idempotencia,
        }
        resultado = cancelar_emissao(payload, emissao.configuracao)
        emissao.status_processamento = resultado['status']
        emissao.situacao_fiscal = resultado['situacao_fiscal']
        emissao.log_tecnico = resultado.get('mensagem')
        emissao.payload_retorno = json.dumps(resultado.get('payload_retorno'), ensure_ascii=False, default=str)

        evento = NfseNacionalEvento(
            empresa_id=emissao.empresa_id,
            emissao=emissao,
            tipo_evento='CANCELAMENTO',
            status_evento='processado' if resultado.get('sucesso') else 'erro',
            protocolo=resultado.get('protocolo'),
            mensagem=resultado.get('mensagem'),
            payload_envio=json.dumps(payload, ensure_ascii=False, default=str),
            payload_retorno=emissao.payload_retorno,
            criado_por_user_id=current_user.id,
        )
        db.session.add(evento)
        db.session.commit()

        if request.is_json:
            return jsonify({
                'emissao_id': str(emissao.id),
                'status': emissao.status_processamento,
                'situacao_fiscal': emissao.situacao_fiscal,
                'protocolo': emissao.protocolo,
            }), 200

        flash('Cancelamento processado com sucesso.', 'success')
        return redirect(url_for('nfse_nacional.emissao_detalhe', emissao_id=emissao.id))
    except Exception as exc:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(exc)}), 400
        flash(f'Erro ao cancelar emissão: {exc}', 'danger')
        return redirect(url_for('nfse_nacional.emissao_detalhe', emissao_id=emissao.id))