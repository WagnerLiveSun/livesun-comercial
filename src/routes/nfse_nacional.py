from __future__ import annotations

import os
import json
import logging
import re
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for, make_response, Response, current_app
from flask_login import current_user, login_required
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.x509.oid import NameOID
from werkzeug.utils import secure_filename

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
    NfseMunicipioReferencia,
    NfseCtribMunReferencia,
    NfseServicoNacionalReferencia,
    NfseNbsReferencia,
    Servico,
)
from src.services.nfse_nacional import (
    builddpsxml,
    buildidempotencyhash,
    generateinternalnumber,
    transmitiremissao,
    consultar_nfse,
    transmitireventocancelamentosubstituicao,
)
from src.tenant import scoped_get_or_404, scoped_query, tenant_id

nfse_nacional_bp = Blueprint("nfse_nacional", __name__, url_prefix="/nfse-nacional")


def _decimal(value, default: Decimal = Decimal("0.00")) -> Decimal:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return Decimal(text.replace(",", "."))
    except Exception:
        return default


def _json_safe(obj):
    if isinstance(obj, Decimal):
        return format(obj, "0.2f")
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_json_safe(v) for v in obj)
    return obj


def _date_from_request(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


# Códigos de tributação nacional que exigem local de incidência = local de prestação
CODIGOS_INCIDENCIA_PRESTACAO = [
    "030401", "030402", "030403", "030501",
    "070201", "070202", "070401", "070501", "070502", "070901", "070902",
    "071001", "071002", "071101", "071102", "071201", "071601", "071701", "071801", "071901",
    "110101", "110102", "110201", "110301", "110401", "110402",
    "120101", "120201", "120301", "120401", "120501", "120601", "120701", "120801",
    "120901", "120902", "120903", "121001", "121101", "121201", "121401", "121501", "121601", "121701",
    "160101", "160102", "160103", "160104", "160201",
    "171001", "171002",
    "220101"
]

# Códigos de tributação nacional que exigem local de incidência = município do tomador
CODIGOS_INCIDENCIA_TOMADOR = ["170501"]

# Códigos de tributação nacional que têm regras especiais (não seguem a regra padrão)
CODIGOS_REGRAS_ESPECIAIS = CODIGOS_INCIDENCIA_PRESTACAO + CODIGOS_INCIDENCIA_TOMADOR + ["990101"]


def _determinar_local_incidencia_issqn(
    codigo_nacional: str,
    trib_issqn: str,
    codigo_municipio_emitente: str,
    codigo_municipio_tomador: Optional[str],
    codigo_local_prestacao: str,
    tipo_emitente: int = 1  # 1 = Prestador, 2 = Tomador, 3 = Intermediário
) -> tuple[bool, str, str]:
    """
    Determina o local de incidência do ISSQN conforme regras do SNNFSE.
    
    Retorna: (sucesso, mensagem, codigo_ibge_incidencia)
    """
    # Se tribISSQN = 2, 3 ou 4 (Imunidade, Exportação ou Não Incidência), não informar local de incidência
    if trib_issqn in ["2", "3", "4"]:
        return True, "Operação não tributável (Imunidade/Exportação/Não Incidência), local de incidência não informado", ""
    
    # Se tribISSQN = 1 (Operação Tributável), é obrigatório informar local de incidência
    if trib_issqn != "1":
        return False, f"Valor inválido para tribISSQN: {trib_issqn}. Deve ser 1, 2, 3 ou 4."
    
    # Regra: Se cTribNac ≠ 200101 e cLocPrestacao = 0000000 (Águas Marítimas)
    if codigo_nacional != "200101" and codigo_local_prestacao == "0000000":
        return True, "Águas Marítimas (cLocPrestacao = 0000000), incidência = município do prestador", codigo_municipio_emitente
    
    # Regra: Códigos que exigem incidência = local de prestação
    if codigo_nacional in CODIGOS_INCIDENCIA_PRESTACAO:
        return True, f"Código {codigo_nacional} exige incidência = local de prestação", codigo_local_prestacao
    
    # Regra: Código 170501 exige incidência = município do tomador
    if codigo_nacional in CODIGOS_INCIDENCIA_TOMADOR:
        if not codigo_municipio_tomador:
            return False, f"Código {codigo_nacional} exige incidência = município do tomador, mas tomador não tem município configurado."
        return True, f"Código {codigo_nacional} exige incidência = município do tomador", codigo_municipio_tomador
    
    # Regra padrão: Para os demais códigos (exceto 990101 e os listados acima)
    if codigo_nacional not in CODIGOS_REGRAS_ESPECIAIS:
        # Se tpEmit = 1 (Prestador), incidência = município do emitente
        if tipo_emitente == 1:
            return True, f"Código {codigo_nacional} (regra padrão), incidência = município do emitente (tpEmit=1)", codigo_municipio_emitente
        # Se tpEmit = 2 ou 3 (Tomador ou Intermediário), incidência = município do prestador
        else:
            return True, f"Código {codigo_nacional} (regra padrão), incidência = município do prestador (tpEmit={tipo_emitente})", codigo_municipio_emitente
    
    # Código 990101 (Outros) - usar regra padrão
    return True, f"Código {codigo_nacional} (Outros), incidência = município do emitente", codigo_municipio_emitente


def _resolve_certificate_path(certificado: NfseNacionalCertificado | None) -> str | None:
    return (getattr(certificado, "caminho_arquivo", None) or "").strip() or None


def _save_certificate_upload(uploaded_file, empresa_id: int, ambiente: str) -> tuple[str, str]:
    filename = secure_filename(uploaded_file.filename or "")
    if not filename:
        raise ValueError("Envie um arquivo .pfx válido.")

    extension = Path(filename).suffix.lower()
    if extension not in {".pfx", ".p12"}:
        raise ValueError("O certificado deve ser um arquivo .pfx ou .p12.")

    base_folder = Path(current_app.config["UPLOAD_FOLDER"]) / "nfse_certificados" / str(empresa_id) / ambiente
    base_folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{Path(filename).stem}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{extension}"
    file_path = base_folder / stored_name
    uploaded_file.save(file_path)
    return str(file_path), filename


def _inspect_certificate(
    certificado: NfseNacionalCertificado | None,
    pfx_path: str | None = None,
    senha: str | None = None,
) -> tuple[date | None, str]:
    pfx_path = (pfx_path or _resolve_certificate_path(certificado) or "").strip()
    if not pfx_path:
        return None, "Certificado inválido: upload não configurado."

    caminho = Path(pfx_path)
    if not caminho.exists():
        return None, f"Certificado inválido: arquivo não encontrado em {pfx_path}."

    senha = (senha if senha is not None else os.environ.get("NFS_PFX_PASS") or getattr(certificado, "senha", None) or "").strip()

    try:
        with caminho.open("rb") as arquivo:
            conteudo = arquivo.read()

        private_key, x509_cert, _ = load_key_and_certificates(
            conteudo,
            senha.encode("utf-8") if senha else None,
        )

        if private_key is None or x509_cert is None:
            return None, "Certificado inválido: arquivo PFX sem chave privada ou certificado."

        validade_em = x509_cert.not_valid_after.date() if getattr(x509_cert, "not_valid_after", None) else None

        cert_serial = None
        try:
            attrs = x509_cert.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)
            if attrs:
                cert_serial = attrs[0].value
        except Exception:
            cert_serial = None

        if not cert_serial:
            try:
                subj = x509_cert.subject.rfc4514_string()
                m = re.search(r"serialNumber=([^,]+)", subj)
                if m:
                    cert_serial = m.group(1)
            except Exception:
                cert_serial = None

        cert_cnpj_digits = "".join(ch for ch in (cert_serial or "") if ch.isdigit())

        try:
            if certificado and getattr(certificado, "empresa_id", None):
                empresa = Empresa.query.get(certificado.empresa_id)
                emp_cnpj_digits = "".join(ch for ch in (empresa.cnpj or "") if ch.isdigit()) if empresa else ""
                if emp_cnpj_digits and cert_cnpj_digits and emp_cnpj_digits != cert_cnpj_digits:
                    return None, (
                        f"Certificado inválido: CNPJ do certificado ({cert_cnpj_digits}) "
                        f"não corresponde ao CNPJ da empresa ({emp_cnpj_digits})."
                    )
        except Exception:
            pass

        return validade_em, "Certificado A1 - Ativo e Disponível"
    except Exception as exc:
        return None, f"Certificado inválido: {exc}"


def _campos_obrigatorios_tomador_nfse(entidade: Entidade) -> list[str]:
    campos = [
        ("tipo", "Tipo"),
        ("cnpj_cpf", "CNPJ/CPF"),
        ("nome", "Nome/Razão Social"),
        ("endereco_rua", "Rua"),
        ("endereco_numero", "Número"),
        ("endereco_bairro", "Bairro"),
        ("endereco_cidade", "Cidade"),
        ("endereco_uf", "UF"),
        ("endereco_cep", "CEP"),
        ("email", "E-mail"),
    ]
    faltantes = []
    for attr, label in campos:
        valor = getattr(entidade, attr, None)
        if valor is None or str(valor).strip() == "":
            faltantes.append(label)
    return faltantes


def _mensagem_campos_obrigatorios_tomador(entidade: Entidade, faltantes: list[str]) -> str:
    if not faltantes:
        return ""
    nome = entidade.nome or "a entidade selecionada"
    lista = ", ".join(faltantes)
    return f"Para emitir NFS-e, complete o cadastro de {nome} com os campos obrigatórios: {lista}."


def _get_or_create_fluxo_recebimento(empresa_id: int) -> int | None:
    conta = (
        scoped_query(FluxoContaModel)
        .filter(FluxoContaModel.tipo == "R")
        .order_by(FluxoContaModel.ativo.desc(), FluxoContaModel.id.asc())
        .first()
    )
    if conta:
        return conta.id

    conta = FluxoContaModel(
        empresa_id=empresa_id,
        codigo="1",
        descricao="Recebimentos NFS-e",
        tipo="R",
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
        versao_layout="1.0",
    )
    db.session.add(configuracao)
    db.session.flush()
    return configuracao


def _get_or_create_tomador(empresa_id: int, payload: dict) -> Entidade:
    entidade_id = payload.get("tomador_id") or payload.get("entidade_id")
    if entidade_id:
        entidade = scoped_get_or_404(Entidade, int(entidade_id))
        entidade.tipo = "C"
        if not entidade.fluxo_conta_id:
            entidade.fluxo_conta_id = _get_or_create_fluxo_recebimento(empresa_id)
        return entidade

    documento = "".join(ch for ch in str(payload.get("tomador_documento") or payload.get("cnpj_cpf") or "") if ch.isdigit())
    if not documento:
        raise ValueError("Informe o CPF/CNPJ do tomador.")

    entidade = Entidade.query.filter_by(empresa_id=empresa_id, cnpj_cpf=documento).first()
    if entidade:
        if entidade.tipo != "C":
            entidade.tipo = "C"
        if not entidade.fluxo_conta_id:
            entidade.fluxo_conta_id = _get_or_create_fluxo_recebimento(empresa_id)
        return entidade

    nome = (payload.get("tomador_nome") or payload.get("razao_nome") or payload.get("nome") or f"Tomador {documento}").strip()
    entidade = Entidade(
        empresa_id=empresa_id,
        nome=nome,
        cnpj_cpf=documento,
        tipo="C",
        fluxo_conta_id=_get_or_create_fluxo_recebimento(empresa_id),
        ativo=True,
    )
    db.session.add(entidade)
    db.session.flush()
    return entidade


def _get_or_create_servico(empresa_id: int, payload: dict) -> Servico:
    servico_id = payload.get("servico_id")
    if servico_id:
        return scoped_get_or_404(Servico, int(servico_id))

    empresa = Empresa.query.get_or_404(empresa_id)

    codigo_interno = (payload.get("codigo_interno") or payload.get("servico_codigo_interno") or "").strip()
    descricao = (payload.get("descricao") or payload.get("servico_descricao") or "").strip()

    if not codigo_interno:
        raise ValueError("Informe o código interno do serviço.")
    if not descricao:
        raise ValueError("Informe a descrição do serviço.")

    servico = Servico.query.filter_by(empresa_id=empresa_id, codigo_interno=codigo_interno).first()
    if servico:
        servico.descricao = descricao or servico.descricao
        servico.codigo_servico = (
            payload.get("codigo_servico")
            or payload.get("servico_codigo_nacional")
            or servico.codigo_servico
            or empresa.fiscal_principal_valor("codigo_servico")
        )
        servico.nbs = (
            payload.get("nbs")
            or payload.get("servico_nbs")
            or servico.nbs
            or empresa.fiscal_principal_valor("nbs")
        )
        servico.natureza_servico = payload.get("natureza_servico") or servico.natureza_servico
        servico.indicador_incidencia = payload.get("indicador_incidencia") or servico.indicador_incidencia
        return servico

    servico = Servico(
        empresa_id=empresa_id,
        codigo_interno=codigo_interno,
        descricao=descricao,
        codigo_servico=payload.get("codigo_servico") or payload.get("servico_codigo_nacional") or empresa.fiscal_principal_valor("codigo_servico"),
        nbs=payload.get("nbs") or payload.get("servico_nbs") or empresa.fiscal_principal_valor("nbs"),
        natureza_servico=payload.get("natureza_servico"),
        indicador_incidencia=payload.get("indicador_incidencia"),
        ativo=str(payload.get("ativo", True)).lower() in {"1", "true", "on", "sim"},
    )
    db.session.add(servico)
    db.session.flush()
    return servico


def _ensure_integration_origin(empresa_id: int, payload: dict, hash_idempotencia: str) -> NfseNacionalIntegracaoOrigem:
    origem = NfseNacionalIntegracaoOrigem.query.filter_by(
        empresa_id=empresa_id,
        origem_tipo=payload.get("origem_tipo") or "MANUAL",
        origem_id=str(payload.get("origem_id") or "") or None,
        canal_origem=payload.get("canal_origem") or "manual",
    ).first()

    if origem:
        origem.origem_referencia = payload.get("origem_referencia") or origem.origem_referencia
        origem.payload_origem = json.dumps(payload, ensure_ascii=False, default=str)
        origem.hash_idempotencia = hash_idempotencia
        return origem

    origem = NfseNacionalIntegracaoOrigem(
        empresa_id=empresa_id,
        origem_tipo=payload.get("origem_tipo") or "MANUAL",
        origem_id=str(payload.get("origem_id") or "") or None,
        origem_referencia=payload.get("origem_referencia") or None,
        canal_origem=payload.get("canal_origem") or "manual",
        payload_origem=json.dumps(payload, ensure_ascii=False, default=str),
        hash_idempotencia=hash_idempotencia,
    )
    db.session.add(origem)
    db.session.flush()
    return origem


def _validar_emissao_nfse(
    empresa: Empresa,
    configuracao: NfseNacionalConfiguracao,
    tomador: Entidade,
    servico: Servico,
    payload: dict,
) -> tuple[bool, str]:
    """
    Valida pré-condições fiscais para emissão de NFS-e Nacional.
    
    Returns:
        tuple: (valido, mensagem_erro)
    """
    from src.services.nfse_nacional import validate_ctrib_mun
    
    # 1. Validar município IBGE do emitente
    if not getattr(empresa, "codigo_municipio_ibge", None):
        return False, "Empresa não possui código IBGE do município configurado. Configure em cadastro da empresa."
    
    municipio_emitente = NfseMunicipioReferencia.query.filter_by(
        codigo_ibge=empresa.codigo_municipio_ibge,
        ativo=True
    ).first()
    
    if not municipio_emitente:
        return False, f"Código IBGE {empresa.codigo_municipio_ibge} não encontrado na tabela de municípios."
    
    # 2. Validar código de serviço nacional (necessário para determinar local de incidência)
    codigo_nacional = payload.get("codigo_servico") or payload.get("servico_codigo_nacional") or servico.codigo_servico
    logging.info(f"Validando código nacional: '{codigo_nacional}'")
    if not codigo_nacional:
        return False, "Código de serviço nacional não informado."
    
    # 3. Determinar local de incidência do ISSQN conforme regras do SNNFSE
    # Obter tribISSQN do payload (padrão = 1 para operação tributável)
    trib_issqn = str(payload.get("tribISSQN") or "1")
    
    # Determinar local de prestação (usar município do emitente como padrão)
    servico_local_prestacao = payload.get("servico_local_prestacao", "emitente")
    if servico_local_prestacao == "emitente":
        codigo_local_prestacao = empresa.codigo_municipio_ibge
    elif servico_local_prestacao == "tomador":
        if not getattr(tomador, "codigo_municipio_ibge", None):
            return False, "Tomador não possui código IBGE do município configurado."
        codigo_local_prestacao = tomador.codigo_municipio_ibge
    else:
        return False, f"Valor inválido para servico_local_prestacao: {servico_local_prestacao}"
    
    # Obter município do tomador (se existir)
    codigo_municipio_tomador = getattr(tomador, "codigo_municipio_ibge", None)
    
    # Determinar local de incidência conforme regras do SNNFSE
    sucesso, msg_incidencia, codigo_ibge_incidencia = _determinar_local_incidencia_issqn(
        codigo_nacional=codigo_nacional,
        trib_issqn=trib_issqn,
        codigo_municipio_emitente=empresa.codigo_municipio_ibge,
        codigo_municipio_tomador=codigo_municipio_tomador,
        codigo_local_prestacao=codigo_local_prestacao,
        tipo_emitente=1  # Emitente é o prestador
    )
    
    if not sucesso:
        return False, msg_incidencia
    
    logging.info(f"Local de incidência do ISSQN determinado: {msg_incidencia}")
    if codigo_ibge_incidencia:
        municipio_incidencia = NfseMunicipioReferencia.query.filter_by(
            codigo_ibge=codigo_ibge_incidencia,
            ativo=True
        ).first()
        if municipio_incidencia:
            logging.info(f"Município de incidência: {codigo_ibge_incidencia} ({municipio_incidencia.nome_municipio})")
        else:
            logging.warning(f"Município de incidência {codigo_ibge_incidencia} não encontrado na tabela de municípios")
    
    # 4. Validar se o código nacional existe na tabela nacional
    servico_nacional = NfseServicoNacionalReferencia.query.filter_by(
        codigo_tributacao_nacional=codigo_nacional,
        ativo=True
    ).first()
    
    if not servico_nacional:
        # Se não encontrar, tentar buscar códigos similares para debug
        logging.warning(f"Código nacional {codigo_nacional} não encontrado. Buscando códigos similares...")
        codigos_similares = NfseServicoNacionalReferencia.query.filter(
            NfseServicoNacionalReferencia.codigo_tributacao_nacional.like(f"{codigo_nacional[:2]}%"),
            NfseServicoNacionalReferencia.ativo == True
        ).limit(10).all()
        logging.info(f"Códigos similares encontrados: {[s.codigo_tributacao_nacional for s in codigos_similares]}")
        return False, f"Código de serviço nacional {codigo_nacional} não encontrado na tabela oficial."
    
    logging.info(f"Serviço nacional encontrado: {servico_nacional.codigo_tributacao_nacional} - {servico_nacional.descricao}")
    
    # 4. Validar NBS quando exigido
    nbs = payload.get("nbs") or payload.get("servico_nbs") or servico.nbs
    if not nbs:
        return False, "NBS (Nomenclatura Brasileira de Serviços) não informado."
    
    nbs_valido = NfseNbsReferencia.query.filter_by(
        codigo_nbs=nbs,
        ativo=True
    ).first()
    
    if not nbs_valido:
        return False, f"NBS {nbs} não encontrado na tabela oficial."
    
    # 5. Validar cTribMun para município de incidência (não emitente)
    ctribmun = payload.get("cTribMun") or payload.get("codigo_tributacao_municipal")
    ctribmun_valido, msg_ctribmun = validate_ctrib_mun(codigo_ibge_incidencia, ctribmun)
    if not ctribmun_valido:
        return False, msg_ctribmun
    
    # 6. Validar CPF/CNPJ do tomador
    documento_tomador = tomador.cnpj_cpf
    if not documento_tomador or len(documento_tomador) not in [11, 14]:
        return False, "CPF/CNPJ do tomador inválido (deve ter 11 ou 14 dígitos)."
    
    # 7. Validar valor do serviço
    valor_servico = _decimal(payload.get("valor_servico"))
    if valor_servico <= 0:
        return False, "Valor do serviço deve ser maior que zero."
    
    # 8. Validar inscrição municipal quando exigida pelo município de incidência
    if municipio_incidencia.nome_municipio in ["Belo Horizonte", "Rio de Janeiro"]:
        if not getattr(empresa, "inscricao_municipal", None):
            return False, f"Município {municipio_incidencia.nome_municipio} exige inscrição municipal do prestador."
    
    return True, ""


def _build_payload(
    empresa: Empresa,
    configuracao: NfseNacionalConfiguracao,
    tomador: Entidade,
    servico: Servico,
    payload: dict,
    numero_interno: str,
    hash_idempotencia: str,
) -> dict:
    valor_servico = _decimal(payload.get("valor_servico"))
    valor_deducoes = _decimal(payload.get("valor_deducoes"))
    aliquota = _decimal(payload.get("aliquota_iss"))
    valor_iss = _decimal(payload.get("valor_iss"))

    if valor_iss <= 0 and valor_servico > 0 and aliquota > 0:
        valor_iss = (valor_servico * aliquota / Decimal("100")).quantize(Decimal("0.01"))

    empresa_cidade = empresa.endereco_cidade
    empresa_uf = empresa.endereco_uf
    empresa_codigo_municipio = None

    if getattr(empresa, "codigo_municipio_ibge", None):
        try:
            municipio = NfseMunicipioReferencia.query.filter_by(
                codigo_ibge=empresa.codigo_municipio_ibge,
                ativo=True
            ).first()
            if municipio:
                empresa_cidade = municipio.nome_municipio
                empresa_uf = municipio.uf_sigla
                empresa_codigo_municipio = municipio.codigo_ibge
        except Exception:
            empresa_cidade = empresa.endereco_cidade
            empresa_uf = empresa.endereco_uf

    dados = {
        "empresa_id": empresa.id,
        "empresa_nome": empresa.nome,
        "empresa_cnpj": empresa.cnpj,
        "empresa_endereco_rua": empresa.endereco_rua,
        "empresa_endereco_numero": empresa.endereco_numero,
        "empresa_endereco_bairro": empresa.endereco_bairro,
        "empresa_endereco_cidade": empresa_cidade,
        "empresa_endereco_uf": empresa_uf,
        "empresa_endereco_cep": empresa.endereco_cep,
        "empresa_codigo_municipio_ibge": empresa_codigo_municipio,
        "inscricao_municipal": configuracao.inscricao_municipal,
        "codigo_municipio": configuracao.codigo_municipio or (empresa_codigo_municipio or None),
        # Regime tributário Simples Nacional (usado da empresa)
        "op_simp_nac": getattr(empresa, "op_simp_nac", 3),
        "reg_ap_trib_sn": getattr(empresa, "reg_ap_trib_sn", 1),
        "ambiente": configuracao.ambiente,
        "versao_layout": configuracao.versao_layout,
        "versao_xsd": "1.0",
        "numero_interno": numero_interno,
        "numero_nfse_sugerido": payload.get("numero_nfse_sugerido"),
        "hash_idempotencia": hash_idempotencia,
        "tomador_id": tomador.id,
        "tomador_nome": tomador.nome,
        "tomador_documento": tomador.cnpj_cpf,
        "tomador_tipo": tomador.tipo,
        "tomador_email": payload.get("tomador_email") or payload.get("email_tomador") or "",
        "tomador_endereco_rua": payload.get("tomador_endereco_rua") or getattr(tomador, "endereco_rua", "") or "",
        "tomador_endereco_numero": payload.get("tomador_endereco_numero") or getattr(tomador, "endereco_numero", "") or "",
        "tomador_endereco_complemento": payload.get("tomador_endereco_complemento") or getattr(tomador, "endereco_complemento", "") or "",
        "tomador_endereco_bairro": payload.get("tomador_endereco_bairro") or getattr(tomador, "endereco_bairro", "") or "",
        "tomador_endereco_cidade": payload.get("tomador_endereco_cidade") or getattr(tomador, "endereco_cidade", "") or "",
        "tomador_endereco_uf": payload.get("tomador_endereco_uf") or getattr(tomador, "endereco_uf", "") or "",
        "tomador_endereco_cep": payload.get("tomador_endereco_cep") or getattr(tomador, "endereco_cep", "") or "",
        "tomador_codigo_municipio_ibge": payload.get("tomador_codigo_municipio_ibge") or getattr(tomador, "codigo_municipio_ibge", "") or "",
        "servico_id": servico.id,
        "servico_codigo_interno": servico.codigo_interno,
        "servico_codigo_nacional": payload.get("servico_codigo_nacional") or payload.get("codigo_servico") or servico.codigo_servico,
        "servico_nbs": payload.get("nbs") or servico.nbs,
        "servico_descricao": servico.descricao,
        "servico_local_prestacao": (payload.get("servico_local_prestacao") or "emitente").strip().lower(),
        "cTribMun": payload.get("cTribMun") or "",
        "tpRetISSQN": (payload.get("tpRetISSQN") or "1").strip(),
        "valor_servico": valor_servico,
        "valor_deducoes": valor_deducoes,
        "valor_iss": valor_iss,
        "origem_tipo": payload.get("origem_tipo") or "MANUAL",
        "origem_id": payload.get("origem_id") or "",
        "origem_referencia": payload.get("origem_referencia") or "",
        "canal_origem": payload.get("canal_origem") or "manual",
        "observacoes": payload.get("observacoes") or "",
    }

    dados["xml_dps"] = builddpsxml(dados)
    return dados


@nfse_nacional_bp.route("/", methods=["GET"])
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
    total_autorizadas = scoped_query(NfseNacionalEmissao).filter(NfseNacionalEmissao.situacao_fiscal == "AUTORIZADA").count()
    total_rejeitadas = scoped_query(NfseNacionalEmissao).filter(NfseNacionalEmissao.situacao_fiscal == "REJEITADA").count()

    return render_template(
        "nfse_nacional/index.html",
        configuracoes=configuracoes,
        certificados=certificados,
        emissoes=emissoes,
        total_emissoes=total_emissoes,
        total_autorizadas=total_autorizadas,
        total_rejeitadas=total_rejeitadas,
    )


@nfse_nacional_bp.route("/configuracoes", methods=["GET", "POST"])
@login_required
def configuracoes():
    empresa_id = tenant_id()

    if not getattr(current_user, "is_admin", False):
        flash("Acesso restrito a administradores.", "danger")
        return redirect(url_for("nfse_nacional.index"))

    ambiente = (request.values.get("ambiente") or "homologacao").strip().lower()
    configuracao = NfseNacionalConfiguracao.query.filter_by(empresa_id=empresa_id, ambiente=ambiente).first()

    certificados_ambiente = sorted(
        NfseNacionalCertificado.query.filter_by(empresa_id=empresa_id, ambiente=ambiente, ativo=True).all(),
        key=lambda certificado: (
            certificado.validade_em is None,
            -(certificado.validade_em.toordinal()) if certificado.validade_em else 0,
        ),
    )
    certificado = certificados_ambiente[0] if certificados_ambiente else None
    certificado_validade, certificado_status = _inspect_certificate(certificado)
    if certificado is not None:
        certificado.validade_em = certificado_validade
        certificado.observacoes = certificado_status

    if request.method == "POST":
        try:
            configuracao = configuracao or NfseNacionalConfiguracao(empresa_id=empresa_id, ambiente=ambiente)
            configuracao.inscricao_municipal = (request.form.get("inscricao_municipal") or "").strip() or None
            configuracao.codigo_municipio = (request.form.get("codigo_municipio") or "").strip() or None
            configuracao.versao_layout = (request.form.get("versao_layout") or "").strip() or "1.0"
            configuracao.emissor_ativo = request.form.get("emissor_ativo") == "on"
            configuracao.observacoes = request.form.get("observacoes") or None

            # Espelhar dados para a empresa
            empresa = Empresa.query.get(empresa_id)
            if empresa:
                if configuracao.inscricao_municipal:
                    empresa.inscricao_municipal = configuracao.inscricao_municipal
                if configuracao.codigo_municipio:
                    empresa.codigo_municipio_ibge = configuracao.codigo_municipio
                # Regime tributário não é espelhado pois usa op_simp_nac e reg_ap_trib_sn

            if configuracao.emissor_ativo:
                NfseNacionalConfiguracao.query.filter(
                    NfseNacionalConfiguracao.empresa_id == empresa_id,
                    NfseNacionalConfiguracao.ambiente != configuracao.ambiente,
                ).update({"emissor_ativo": False})

            db.session.add(configuracao)

            arquivo_upload = request.files.get("certificado_arquivo")
            caminho_arquivo = certificado.caminho_arquivo if certificado else None
            arquivo_nome = certificado.arquivo_nome if certificado else None
            senha_certificado = (request.form.get("certificado_senha") or (certificado.senha if certificado else None) or "").strip() or None

            if arquivo_upload and arquivo_upload.filename:
                caminho_arquivo, arquivo_nome_real = _save_certificate_upload(arquivo_upload, empresa_id, ambiente)
                arquivo_nome = arquivo_nome_real

            validade_em, certificado_status = _inspect_certificate(certificado, caminho_arquivo, senha_certificado)

            if "remover_certificado" in request.form:
                if certificado is None:
                    flash("Nenhum certificado cadastrado para remover.", "warning")
                else:
                    try:
                        if certificado.caminho_arquivo:
                            try:
                                os.remove(certificado.caminho_arquivo)
                            except Exception:
                                pass

                        certificado.ativo = False
                        certificado.senha = None
                        certificado.caminho_arquivo = None
                        certificado.validade_em = None
                        certificado.observacoes = "Certificado removido pelo usuário."

                        try:
                            certificado.removed_by_id = current_user.id
                            certificado.removed_by = getattr(current_user, "username", None) or getattr(current_user, "email", None)
                            certificado.removed_at = datetime.utcnow()
                        except Exception:
                            pass

                        db.session.add(certificado)
                        db.session.commit()
                        flash("Certificado removido com sucesso.", "success")
                    except Exception as exc:
                        db.session.rollback()
                        flash(f"Erro ao remover certificado: {exc}", "danger")

                return redirect(url_for("nfse_nacional.configuracoes", ambiente=ambiente))

            if arquivo_nome or caminho_arquivo:
                if certificado is None:
                    certificado = NfseNacionalCertificado(
                        empresa_id=empresa_id,
                        ambiente=ambiente,
                        arquivo_nome=arquivo_nome or "certificado.pfx",
                        caminho_arquivo=caminho_arquivo,
                        senha=senha_certificado,
                        validade_em=validade_em,
                        emissor_ativo=True,
                        observacoes=certificado_status,
                    )
                    db.session.add(certificado)
                else:
                    certificado.arquivo_nome = arquivo_nome or certificado.arquivo_nome
                    certificado.caminho_arquivo = caminho_arquivo or certificado.caminho_arquivo
                    certificado.senha = senha_certificado or certificado.senha
                    certificado.validade_em = validade_em
                    certificado.ativo = True
                    certificado.observacoes = certificado_status

            db.session.commit()
            flash("Configuração fiscal atualizada com sucesso.", "success")
            return redirect(url_for("nfse_nacional.configuracoes", ambiente=ambiente))

        except Exception as exc:
            db.session.rollback()
            flash(f"Erro ao salvar configuração da NFS-e: {exc}", "danger")

    configuracoes_list = NfseNacionalConfiguracao.query.filter_by(empresa_id=empresa_id).order_by(NfseNacionalConfiguracao.ambiente.asc()).all()
    return render_template(
        "nfse_nacional/configuracoes.html",
        configuracao=configuracao,
        certificado=certificado,
        ambiente=ambiente,
        configuracoes_list=configuracoes_list,
    )


@nfse_nacional_bp.route("/tomadores", methods=["GET", "POST"])
@login_required
def tomadores():
    empresa_id = tenant_id()
    busca = (request.args.get("busca") or "").strip()

    query = scoped_query(Entidade).filter(Entidade.tipo == "C")
    if busca:
        query = query.filter(
            (Entidade.nome.ilike(f"%{busca}%")) |
            (Entidade.cnpj_cpf.ilike(f"%{busca}%"))
        )

    if request.method == "POST":
        try:
            entidade_id = request.form.get("entidade_id", type=int)
            if entidade_id:
                entidade = scoped_get_or_404(Entidade, entidade_id)
            else:
                entidade = Entidade(empresa_id=empresa_id)
                db.session.add(entidade)

            entidade.nome = (request.form.get("nome") or "").strip()
            entidade.cnpj_cpf = "".join(ch for ch in (request.form.get("cnpj_cpf") or "") if ch.isdigit())
            entidade.tipo = "C"
            entidade.fluxo_conta_id = entidade.fluxo_conta_id or _get_or_create_fluxo_recebimento(empresa_id)
            entidade.ativo = request.form.get("ativo") == "on"

            if not entidade.nome or not entidade.cnpj_cpf:
                raise ValueError("Nome e CPF/CNPJ são obrigatórios.")

            db.session.commit()
            flash("Tomador salvo com sucesso.", "success")
            return redirect(url_for("nfse_nacional.tomadores", busca=busca))
        except Exception as exc:
            db.session.rollback()
            flash(f"Erro ao salvar tomador: {exc}", "danger")

    tomadores = query.order_by(Entidade.nome.asc()).all()
    return render_template("nfse_nacional/tomadores.html", tomadores=tomadores, busca=busca)


@nfse_nacional_bp.route("/servicos", methods=["GET", "POST"])
@login_required
def servicos():
    empresa = Empresa.query.get_or_404(tenant_id())
    busca = (request.args.get("busca") or "").strip()

    query = scoped_query(Servico)
    if busca:
        query = query.filter(
            (Servico.codigo_interno.ilike(f"%{busca}%")) |
            (Servico.descricao.ilike(f"%{busca}%")) |
            (Servico.codigo_servico.ilike(f"%{busca}%")) |
            (Servico.nbs.ilike(f"%{busca}%"))
        )

    if request.method == "POST":
        try:
            servico_id = request.form.get("servico_id", type=int)
            if servico_id:
                servico = scoped_get_or_404(Servico, servico_id)
            else:
                servico = Servico(empresa_id=tenant_id())
                db.session.add(servico)

            servico.codigo_interno = (request.form.get("codigo_interno") or "").strip()
            servico.descricao = (request.form.get("descricao") or "").strip()
            codigo_servico = (request.form.get("codigo_servico") or "").strip()
            nbs = (request.form.get("nbs") or "").strip()

            if not codigo_servico and not servico_id:
                codigo_servico = empresa.fiscal_principal_valor("codigo_servico") or ""
            if not nbs and not servico_id:
                nbs = empresa.fiscal_principal_valor("nbs") or ""

            servico.codigo_servico = codigo_servico or servico.codigo_servico
            servico.nbs = nbs or servico.nbs
            servico.natureza_servico = (request.form.get("natureza_servico") or "").strip() or None
            servico.indicador_incidencia = (request.form.get("indicador_incidencia") or "").strip() or None
            servico.ativo = request.form.get("ativo") == "on"

            if not servico.codigo_interno or not servico.descricao:
                raise ValueError("Código interno e descrição são obrigatórios.")

            db.session.commit()
            flash("Serviço salvo com sucesso.", "success")
            return redirect(url_for("nfse_nacional.servicos", busca=busca))
        except Exception as exc:
            db.session.rollback()
            flash(f"Erro ao salvar serviço: {exc}", "danger")

    servicos = query.order_by(Servico.codigo_interno.asc()).all()
    fiscal_defaults = {
        "codigo_servico": empresa.fiscal_principal_valor("codigo_servico"),
        "nbs": empresa.fiscal_principal_valor("nbs"),
        "codigo_servico_opcoes": empresa.fiscal_valores_por_tipo("codigo_servico"),
        "nbs_opcoes": empresa.fiscal_valores_por_tipo("nbs"),
    }
    return render_template("nfse_nacional/servicos.html", servicos=servicos, busca=busca, fiscal_defaults=fiscal_defaults)


@nfse_nacional_bp.route("/emissoes", methods=["GET", "POST"])
@login_required
def emissoes():
    empresa_id = tenant_id()
    empresa = Empresa.query.get_or_404(empresa_id)
    filtro_status = (request.args.get("status") or "").strip()
    filtro_busca = (request.args.get("busca") or "").strip()

    if request.method == "GET":
        query = scoped_query(NfseNacionalEmissao).order_by(NfseNacionalEmissao.criado_em.desc())

        if filtro_status:
            query = query.filter(NfseNacionalEmissao.status_processamento == filtro_status)

        if filtro_busca:
            query = query.join(Entidade, NfseNacionalEmissao.tomador).filter(
                (NfseNacionalEmissao.numero_interno.ilike(f"%{filtro_busca}%")) |
                (NfseNacionalEmissao.numero_nfse.ilike(f"%{filtro_busca}%")) |
                (Entidade.nome.ilike(f"%{filtro_busca}%")) |
                (Entidade.cnpj_cpf.ilike(f"%{filtro_busca}%"))
            )

        emissoes_list = query.limit(50).all()
        tomadores = scoped_query(Entidade).filter(Entidade.tipo == "C", Entidade.ativo.is_(True)).order_by(Entidade.nome.asc()).all()
        servicos_list = scoped_query(Servico).filter(Servico.ativo.is_(True)).order_by(Servico.descricao.asc()).all()
        configuracoes = NfseNacionalConfiguracao.query.filter_by(empresa_id=empresa_id).order_by(NfseNacionalConfiguracao.ambiente.asc()).all()

        ambiente_q = (request.args.get("ambiente") or "").strip().lower()
        if ambiente_q:
            ambiente_selecionado = ambiente_q
        else:
            ativo_cfg = next((c for c in configuracoes if c.emissor_ativo), None)
            if ativo_cfg:
                ambiente_selecionado = (ativo_cfg.ambiente or "homologacao").strip().lower()
            else:
                ambiente_selecionado = configuracoes[0].ambiente if configuracoes else "homologacao"

        fiscal_defaults = {
            "codigo_servico": empresa.fiscal_principal_valor("codigo_servico"),
            "nbs": empresa.fiscal_principal_valor("nbs"),
            "codigo_servico_opcoes": empresa.fiscal_valores_por_tipo("codigo_servico"),
            "nbs_opcoes": empresa.fiscal_valores_por_tipo("nbs"),
        }

        return render_template(
            "nfse_nacional/emissoes.html",
            emissoes=emissoes_list,
            tomadores=tomadores,
            servicos=servicos_list,
            configuracoes=configuracoes,
            ambiente_selecionado=ambiente_selecionado,
            filtro_status=filtro_status,
            filtro_busca=filtro_busca,
            fiscal_defaults=fiscal_defaults,
        )

    data = request.get_json(silent=True) if request.is_json else request.form

    try:
        ativo_cfg = NfseNacionalConfiguracao.query.filter_by(empresa_id=empresa_id, emissor_ativo=True).first()
        ambiente_payload = (data.get("ambiente") or "").strip().lower()

        if ativo_cfg:
            ambiente = ativo_cfg.ambiente
            logging.info(f"Ambiente da configuração ativa: {ambiente}")
        elif ambiente_payload:
            ambiente = ambiente_payload
            logging.info(f"Ambiente do payload: {ambiente}")
        else:
            ambiente = "homologacao"
            logging.info("Usando ambiente padrão: homologacao")

        logging.info(f"Ambiente final usado: {ambiente}")

        configuracao = _get_or_create_config(empresa_id, ambiente)
        tomador = _get_or_create_tomador(empresa_id, data)

        faltantes_tomador = _campos_obrigatorios_tomador_nfse(tomador)
        if faltantes_tomador:
            mensagem = _mensagem_campos_obrigatorios_tomador(tomador, faltantes_tomador)
            db.session.rollback()
            if request.is_json:
                return jsonify(_json_safe({
                    "error": mensagem,
                    "campos_obrigatorios": faltantes_tomador,
                    "tomador_id": tomador.id,
                })), 400
            flash(mensagem, "danger")
            return redirect(url_for("nfse_nacional.emissoes", ambiente=ambiente, status=filtro_status, busca=filtro_busca))

        servico = _get_or_create_servico(empresa_id, data)

        valor_servico = _decimal(data.get("valor_servico") or data.get("valor_total"))
        if valor_servico <= 0:
            raise ValueError("Informe um valor de serviço maior que zero.")

        valor_deducoes = _decimal(data.get("valor_deducoes"))
        aliquota_iss = _decimal(data.get("aliquota_iss"))
        valor_iss = _decimal(data.get("valor_iss"))

        if valor_iss <= 0 and valor_servico > 0 and aliquota_iss > 0:
            valor_iss = (valor_servico * aliquota_iss / Decimal("100")).quantize(Decimal("0.01"))

        numero_interno = (data.get("numero_interno") or generateinternalnumber(empresa_id)).strip()
        origem_tipo = (data.get("origem_tipo") or "MANUAL").strip().upper()
        origem_id = data.get("origem_id")
        origem_referencia = data.get("origem_referencia")
        canal_origem = (data.get("canal_origem") or "manual").strip().lower()
        observacoes = data.get("observacoes") or data.get("descricao") or ""

        hash_base = {
            "empresa_id": empresa_id,
            "ambiente": ambiente,
            "tomador_documento": tomador.cnpj_cpf,
            "servico_codigo": servico.codigo_interno,
            "servico_local_prestacao": (data.get("servico_local_prestacao") or "emitente").strip().lower(),
            "tpRetISSQN": (data.get("tpRetISSQN") or "1").strip(),
            "valor_servico": str(valor_servico),
            "valor_deducoes": str(valor_deducoes),
            "valor_iss": str(valor_iss),
            "origem_tipo": origem_tipo,
            "origem_id": origem_id,
            "origem_referencia": origem_referencia,
            "canal_origem": canal_origem,
            "numero_interno": numero_interno,
        }
        hash_idempotencia = buildidempotencyhash(hash_base)

        existente = scoped_query(NfseNacionalEmissao).filter_by(hash_idempotencia=hash_idempotencia).first()
        if existente:
            if request.is_json:
                return jsonify(_json_safe({
                    "emissao_id": str(existente.id),
                    "status": existente.status_processamento,
                    "situacao_fiscal": existente.situacao_fiscal,
                    "protocolo": existente.protocolo,
                    "nfse": {
                        "numero": existente.numero_nfse,
                        "codigo_verificacao": existente.codigo_verificacao,
                        "xml_armazenado": bool(existente.xml_nfse),
                    },
                })), 200
            flash("Uma emissão com os mesmos dados já foi processada.", "info")
            return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=existente.id))

        origem = _ensure_integration_origin(empresa_id, {
            "origem_tipo": origem_tipo,
            "origem_id": origem_id,
            "origem_referencia": origem_referencia,
            "canal_origem": canal_origem,
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
            status_processamento="PENDENTE",
            situacao_fiscal="PENDENTE",
            valor_servico=valor_servico,
            valor_deducoes=valor_deducoes,
            valor_iss=valor_iss,
            servico_local_prestacao=(data.get("servico_local_prestacao") or "emitente").strip().lower(),
            tp_ret_issqn=(data.get("tpRetISSQN") or "1").strip(),
            observacoes=observacoes,
            hash_idempotencia=hash_idempotencia,
            versao_layout=configuracao.versao_layout or "1.0",
            versao_xsd="1.0",
            origem_tipo=origem_tipo,
            origem_referencia=origem_referencia,
            canal_origem=canal_origem,
            criado_por_user_id=current_user.id,
        )
        db.session.add(emissao)
        db.session.flush()

        # Validar pré-condições fiscais antes de gerar XML
        # Debug: logar todos os dados recebidos do formulário
        logging.info(f"Dados recebidos do formulário: {list(data.keys())}")
        logging.info(f"Valor de cTribMun no formulário: '{data.get('cTribMun')}'")
        logging.info(f"Valor de codigo_tributacao_municipal no formulário: '{data.get('codigo_tributacao_municipal')}'")
        
        ctribmun_raw = data.get("cTribMun") or data.get("codigo_tributacao_municipal") or ""
        ctribmun_clean = str(ctribmun_raw).strip()
        
        payload_validacao = {
            "codigo_servico": servico.codigo_servico,  # Usar sempre o código do serviço, não do formulário
            "servico_codigo_nacional": servico.codigo_servico,  # Usar sempre o código do serviço
            "nbs": data.get("nbs") or servico.nbs,
            "cTribMun": ctribmun_clean,
            "valor_servico": valor_servico,
        }
        
        valido, msg_erro = _validar_emissao_nfse(empresa, configuracao, tomador, servico, payload_validacao)
        if not valido:
            # Adicionar informação de debug sobre o cTribMun recebido
            msg_erro_completa = f"{msg_erro} (cTribMun recebido: '{ctribmun_clean}' - raw: '{ctribmun_raw}' - campos disponíveis: {list(data.keys())})"
            db.session.rollback()
            if request.is_json:
                return jsonify(_json_safe({
                    "error": msg_erro_completa,
                })), 400
            flash(msg_erro_completa, "danger")
            return redirect(url_for("nfse_nacional.emissoes", ambiente=ambiente, status=filtro_status, busca=filtro_busca))
        
        # Log para verificar os valores atualizados no payload_validacao
        logging.info(f"Após validação - codigo_servico: '{payload_validacao.get('codigo_servico')}', servico_codigo_nacional: '{payload_validacao.get('servico_codigo_nacional')}', cTribMun: '{payload_validacao.get('cTribMun')}'")

        payload = _build_payload(empresa, configuracao, tomador, servico, {
            "valor_servico": valor_servico,
            "valor_deducoes": valor_deducoes,
            "valor_iss": valor_iss,
            "ambiente": ambiente,
            "numero_interno": numero_interno,
            "hash_idempotencia": hash_idempotencia,
            "origem_tipo": origem_tipo,
            "origem_id": origem_id,
            "origem_referencia": origem_referencia,
            "canal_origem": canal_origem,
            "observacoes": observacoes,
            "numero_nfse_sugerido": str(emissao.id),
            "codigo_servico": servico.codigo_servico,  # Usar sempre o código do serviço
            "servico_codigo_nacional": servico.codigo_servico,  # Usar sempre o código do serviço
            "nbs": payload_validacao.get("nbs") or data.get("nbs") or servico.nbs,
            "cTribMun": payload_validacao.get("cTribMun") or data.get("cTribMun"),
            "servico_local_prestacao": data.get("servico_local_prestacao", "emitente"),
        }, numero_interno, hash_idempotencia)

        emissao.xml_dps = payload.pop("xml_dps")
        emissao.payload_envio = json.dumps(payload, ensure_ascii=False, default=str)

        fila = NfseNacionalFila(
            empresa_id=empresa_id,
            emissao=emissao,
            status_fila="PROCESSANDO",
            tentativas=1,
            payload=emissao.payload_envio,
        )
        db.session.add(fila)

        resultado = transmitiremissao(payload, configuracao)

        emissao.status_processamento = resultado.get("status") or "ERRO"
        emissao.situacao_fiscal = resultado.get("situacao_fiscal") or "REJEITADA"
        emissao.protocolo = resultado.get("protocolo")
        emissao.numero_nfse = resultado.get("numero_nfse")
        emissao.codigo_verificacao = resultado.get("codigo_verificacao")
        emissao.chave_nfse = resultado.get("chave_nfse")
        emissao.xml_nfse = resultado.get("xml_nfse")
        emissao.payload_retorno = json.dumps(resultado.get("payload_retorno"), ensure_ascii=False, default=str)
        
        # Atualizar número do documento no lançamento financeiro com o número da NFS-e
        if emissao.lancamento and emissao.numero_nfse:
            emissao.lancamento.numero_documento = emissao.numero_nfse
            logging.info(f"Lançamento {emissao.lancamento.id} atualizado com número da NFS-e: {emissao.numero_nfse}")

        emissao.log_tecnico = resultado.get("mensagem")
        if resultado.get("errors"):
            try:
                detalhes = json.dumps(resultado.get("errors"), ensure_ascii=False, default=str)
            except Exception:
                detalhes = str(resultado.get("errors"))
            emissao.log_tecnico = f"{resultado.get('mensagem')} | detalhes={detalhes}"

        if not resultado.get("sucesso"):
            emissao.erro_retorno = emissao.log_tecnico

        fila.status_fila = "CONCLUIDO" if resultado.get("sucesso") else "ERRO"
        fila.processado_em = datetime.utcnow()
        fila.ultimo_erro = None if resultado.get("sucesso") else emissao.log_tecnico
        fila.payload = emissao.payload_envio

        evento = NfseNacionalEvento(
            empresa_id=empresa_id,
            emissao=emissao,
            tipo_evento="EMISSAO",
            status_evento="processado" if resultado.get("sucesso") else "erro",
            protocolo=resultado.get("protocolo"),
            mensagem=emissao.log_tecnico,
            payload_envio=emissao.payload_envio,
            payload_retorno=emissao.payload_retorno,
            criado_por_user_id=current_user.id,
        )
        db.session.add(evento)

        if resultado.get("sucesso"):
            conta_banco = _get_or_create_conta_banco_principal(empresa_id)
            fluxo_conta_id = tomador.fluxo_conta_id or _get_or_create_fluxo_recebimento(empresa_id)

            if conta_banco and fluxo_conta_id:
                lancamento = Lancamento(
                    empresa_id=empresa_id,
                    data_evento=_date_from_request(data.get("data_emissao")) or datetime.utcnow().date(),
                    data_vencimento=_date_from_request(data.get("data_vencimento")) or _date_from_request(data.get("data_emissao")) or datetime.utcnow().date(),
                    data_pagamento=None,
                    status="aberto",
                    entidade_id=tomador.id,
                    fluxo_conta_id=fluxo_conta_id,
                    conta_banco_id=conta_banco.id,
                    valor_real=valor_servico,
                    valor_pago=Decimal("0.00"),
                    valor_imposto=valor_iss,
                    valor_outros_custos=Decimal("0.00"),
                    numero_documento=emissao.numero_nfse or numero_interno,
                    observacoes=observacoes or servico.descricao,
                    fonte="nfse_nacional",
                )
                db.session.add(lancamento)
                db.session.flush()
                emissao.lancamento = lancamento
            else:
                emissao.log_tecnico = (emissao.log_tecnico or "") + " | Emissão autorizada sem lançamento financeiro por ausência de conta bancária principal."

        db.session.commit()

        resposta = {
            "emissao_id": str(emissao.id),
            "status": emissao.status_processamento,
            "situacao_fiscal": emissao.situacao_fiscal,
            "protocolo": emissao.protocolo,
            "nfse": {
                "numero": emissao.numero_nfse,
                "codigo_verificacao": emissao.codigo_verificacao,
                "xml_armazenado": bool(emissao.xml_nfse),
            },
        }

        if request.is_json:
            return jsonify(_json_safe(resposta)), 201 if resultado.get("sucesso") else 202

        flash(
            "Emissão processada com sucesso." if resultado.get("sucesso") else "Emissão registrada com ressalvas.",
            "success" if resultado.get("sucesso") else "warning",
        )
        return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=emissao.id))

    except Exception as exc:
        db.session.rollback()
        if request.is_json:
            return jsonify(_json_safe({"error": str(exc)})), 400
        flash(f"Erro ao emitir NFS-e: {exc}", "danger")
        return redirect(url_for("nfse_nacional.emissoes"))


@nfse_nacional_bp.route("/emissoes/<int:emissao_id>", methods=["GET"])
@login_required
def emissao_detalhe(emissao_id: int):
    emissao = scoped_get_or_404(NfseNacionalEmissao, emissao_id)
    return render_template("nfse_nacional/emissao_detalhe.html", emissao=emissao)


@nfse_nacional_bp.route("/emissoes/<int:emissao_id>/download/dps", methods=["GET"])
@login_required
def emissao_download_dps(emissao_id: int):
    emissao = scoped_get_or_404(NfseNacionalEmissao, emissao_id)
    xml = emissao.xml_dps or ""
    resp = make_response(xml)
    resp.headers["Content-Type"] = "application/xml; charset=utf-8"
    name = f"dps_{emissao.numero_interno or emissao.id}.xml"
    resp.headers["Content-Disposition"] = f'attachment; filename="{name}"'
    return resp


@nfse_nacional_bp.route("/emissoes/<int:emissao_id>/download/nfse", methods=["GET"])
@login_required
def emissao_download_nfse(emissao_id: int):
    emissao = scoped_get_or_404(NfseNacionalEmissao, emissao_id)

    xml = ""
    if emissao.xml_nfse:
        xml = emissao.xml_nfse
    elif emissao.payload_retorno:
        try:
            payload_retorno = json.loads(emissao.payload_retorno) if isinstance(emissao.payload_retorno, str) else emissao.payload_retorno
            if isinstance(payload_retorno, dict):
                # Tentar diferentes campos onde o XML pode estar
                response_body = payload_retorno.get("response_body", {})
                if isinstance(response_body, dict):
                    xml = response_body.get("nfseXmlGZipB64") or response_body.get("nfseXml") or response_body.get("xml") or ""
                    
                    # Se estiver comprimido em base64, descomprimir
                    if xml and isinstance(xml, str) and len(xml) > 100:
                        try:
                            import gzip
                            import base64
                            xml_comprimido = base64.b64decode(xml)
                            xml = gzip.decompress(xml_comprimido).decode("utf-8")
                        except Exception:
                            pass
                
                if not xml:
                    xml = payload_retorno.get("xml_nfse") or ""
        except Exception:
            xml = ""
    
    # Se ainda não tiver XML, tentar usar o XML do DPS como fallback
    if not xml and emissao.xml_dps:
        xml = emissao.xml_dps

    if not xml:
        flash("XML da NFS-e não disponível.", "warning")
        return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=emissao.id))

    resp = Response(xml, mimetype="application/xml; charset=utf-8")
    name = f"nfse_{emissao.numero_nfse or emissao.numero_interno or emissao.id}.xml"
    resp.headers["Content-Disposition"] = f'attachment; filename="{name}"'
    return resp


@nfse_nacional_bp.route("/emissoes/<int:emissao_id>/imprimir/danfs", methods=["GET"])
@login_required
def emissao_imprimir_danfs(emissao_id: int):
    emissao = scoped_get_or_404(NfseNacionalEmissao, emissao_id)
    empresa = emissao.empresa
    
    # Recarregar empresa do banco para garantir dados atualizados (incluindo logo)
    db.session.refresh(empresa)
    
    # Verificar se há eventos de cancelamento processados com sucesso
    from src.models import NfseNacionalEvento
    evento_cancelamento = NfseNacionalEvento.query.filter_by(
        emissao_id=emissao.id,
        tipo_evento='e101101',
        status_evento='SUCESSO'
    ).first()
    
    if evento_cancelamento:
        emissao.situacao_fiscal = 'CANCELADA'
        db.session.commit()
    
    # Tentar extrair o XML correto da NFS-e (não DPS)
    xml_nfse = None
    if emissao.xml_nfse and "NFSe" in emissao.xml_nfse:
        xml_nfse = emissao.xml_nfse
    elif emissao.payload_retorno:
        try:
            payload_retorno = json.loads(emissao.payload_retorno) if isinstance(emissao.payload_retorno, str) else emissao.payload_retorno
            if isinstance(payload_retorno, dict):
                response_body = payload_retorno.get("response_body", {})
                if isinstance(response_body, dict):
                    xml_nfse = response_body.get("nfseXmlGZipB64") or response_body.get("nfseXml") or response_body.get("xml") or ""
                    
                    # Se estiver comprimido em base64, descomprimir
                    if xml_nfse and isinstance(xml_nfse, str) and len(xml_nfse) > 100:
                        try:
                            import gzip
                            import base64
                            xml_comprimido = base64.b64decode(xml_nfse)
                            xml_nfse = gzip.decompress(xml_comprimido).decode("utf-8")
                        except Exception:
                            pass
                
                if not xml_nfse:
                    xml_nfse = payload_retorno.get("xml_nfse") or ""
        except Exception:
            pass
    
    # Se ainda não tiver XML, usar o XML do DPS como fallback
    if not xml_nfse and emissao.xml_dps:
        xml_nfse = emissao.xml_dps
    
    # Tentar extrair status do XML da NFS-e armazenado
    if xml_nfse:
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_nfse)
            
            # Debug: verificar se o XML tem o campo nNFSe
            import logging
            logging.info(f"XML tem {len(str(xml_nfse))} caracteres")
            
            # Tentar diferentes namespaces possíveis
            namespaces = [
                {'nfse': 'http://www.sped.fazenda.gov.br/nfse'},
                {'nfse': 'http://www.abrasf.org.br/nfse'},
                {'': ''}  # Sem namespace
            ]
            
            for ns in namespaces:
                # Extrair situação
                situacao_node = root.find('.//situacao', ns)
                if situacao_node is None:
                    situacao_node = root.find('.//nfse:situacao', ns)
                
                if situacao_node is not None and situacao_node.text:
                    emissao.situacao_fiscal = situacao_node.text.upper()
                
                # Extrair número da NFS-e - campo correto é nNFSe
                numero_node = root.find('.//nNFSe', ns)
                if numero_node is None:
                    numero_node = root.find('.//nfse:nNFSe', ns)
                
                if numero_node is not None and numero_node.text:
                    emissao.numero_nfse = numero_node.text.strip()
                    logging.info(f"Número extraído do XML: {emissao.numero_nfse}")
                
                # Extrair código de verificação
                codigo_verificacao_node = root.find('.//codigoVerificacao', ns)
                if codigo_verificacao_node is None:
                    codigo_verificacao_node = root.find('.//nfse:codigoVerificacao', ns)
                
                if codigo_verificacao_node is not None and codigo_verificacao_node.text:
                    emissao.codigo_verificacao = codigo_verificacao_node.text
                
                # Extrair chave de acesso do XML da NFS-e
                chave_acesso_node = root.find('.//chaveAcesso', ns)
                if chave_acesso_node is None:
                    chave_acesso_node = root.find('.//nfse:chaveAcesso', ns)
                
                if chave_acesso_node is not None and chave_acesso_node.text:
                    chave_extraida = chave_acesso_node.text.strip()
                    # A chave deve ter 50 dígitos numéricos
                    if len(chave_extraida) == 50 and chave_extraida.isdigit():
                        emissao.chave_nfse = chave_extraida
                        logging.info(f"Chave de acesso extraída do XML (50 dígitos): {emissao.chave_nfse}")
                    else:
                        logging.warning(f"Chave extraída do XML não tem 50 dígitos: {chave_extraida} (len={len(chave_extraida)})")
                
                # Extrair dados do tomador (endereço)
                tomador_endereco_node = root.find('.//endTom', ns)
                if tomador_endereco_node is None:
                    tomador_endereco_node = root.find('.//nfse:endTom', ns)
                
                if tomador_endereco_node is not None:
                    # Extrair endereço completo
                    x_lgr = tomador_endereco_node.find('.//xLgr', ns) or tomador_endereco_node.find('.//nfse:xLgr', ns)
                    nro = tomador_endereco_node.find('.//nro', ns) or tomador_endereco_node.find('.//nfse:nro', ns)
                    x_bairro = tomador_endereco_node.find('.//xBairro', ns) or tomador_endereco_node.find('.//nfse:xBairro', ns)
                    
                    if x_lgr is not None and nro is not None:
                        endereco_completo = f"{x_lgr.text}, {nro.text}"
                        if x_bairro is not None:
                            endereco_completo += f" - {x_bairro.text}"
                        emissao.tomador_endereco = endereco_completo
                
                # Extrair regime de tributação
                reg_trib_node = root.find('.//regTrib', ns)
                if reg_trib_node is None:
                    reg_trib_node = root.find('.//nfse:regTrib', ns)
                
                if reg_trib_node is not None:
                    op_simp_nac = reg_trib_node.find('.//opSimpNac', ns) or reg_trib_node.find('.//nfse:opSimpNac', ns)
                    if op_simp_nac is not None and op_simp_nac.text:
                        emissao.regime_tributacao = op_simp_nac.text
                
                # Extrair código de tributação nacional
                c_trib_nac_node = root.find('.//cTribNac', ns)
                if c_trib_nac_node is None:
                    c_trib_nac_node = root.find('.//nfse:cTribNac', ns)
                
                if c_trib_nac_node is not None and c_trib_nac_node.text:
                    emissao.codigo_tributacao_nacional = c_trib_nac_node.text
                
                # Extrair código de tributação municipal
                c_trib_mun_node = root.find('.//cTribMun', ns)
                if c_trib_mun_node is None:
                    c_trib_mun_node = root.find('.//nfse:cTribMun', ns)
                
                if c_trib_mun_node is not None and c_trib_mun_node.text:
                    emissao.codigo_tributacao_municipal = c_trib_mun_node.text
                
                # Extrair local de prestação
                c_loc_prestacao_node = root.find('.//cLocPrestacao', ns)
                if c_loc_prestacao_node is None:
                    c_loc_prestacao_node = root.find('.//nfse:cLocPrestacao', ns)
                
                if c_loc_prestacao_node is not None and c_loc_prestacao_node.text:
                    emissao.local_prestacao = c_loc_prestacao_node.text
                
                # Se encontrou algum dado, para o loop
                if situacao_node is not None or numero_node is not None:
                    db.session.commit()
                    break
        except Exception as e:
            logging.error(f"Erro ao extrair dados do XML: {e}")
    
    # Se não encontrou número no XML, tentar do payload_retorno
    if not emissao.numero_nfse and emissao.payload_retorno:
        try:
            payload_retorno = json.loads(emissao.payload_retorno) if isinstance(emissao.payload_retorno, str) else emissao.payload_retorno
            if isinstance(payload_retorno, dict):
                response_body = payload_retorno.get("response_body", {})
                if isinstance(response_body, dict):
                    numero = response_body.get("numero_nfse")
                    if numero:
                        emissao.numero_nfse = str(numero)
                        db.session.commit()
                        logging.info(f"Número extraído do payload_retorno: {emissao.numero_nfse}")
        except Exception as e:
            logging.error(f"Erro ao extrair número do payload_retorno: {e}")
    
    # Sempre tentar extrair chave de acesso do payload_retorno (atualizar se necessário)
    if emissao.payload_retorno:
        try:
            payload_retorno = json.loads(emissao.payload_retorno) if isinstance(emissao.payload_retorno, str) else emissao.payload_retorno
            if isinstance(payload_retorno, dict):
                # Tentar do response_body primeiro
                response_body = payload_retorno.get("response_body", {})
                if isinstance(response_body, dict):
                    chave = response_body.get("chaveAcesso")
                    if chave and len(str(chave)) == 50 and str(chave).isdigit():
                        emissao.chave_nfse = str(chave)
                        db.session.commit()
                        logging.info(f"Chave de acesso extraída do response_body: {emissao.chave_nfse}")
                # Se não encontrou, tentar do nível superior
                if not emissao.chave_nfse or len(emissao.chave_nfse) != 50:
                    chave = payload_retorno.get("chaveAcesso")
                    if chave and len(str(chave)) == 50 and str(chave).isdigit():
                        emissao.chave_nfse = str(chave)
                        db.session.commit()
                        logging.info(f"Chave de acesso extraída do payload_retorno: {emissao.chave_nfse}")
        except Exception as e:
            logging.error(f"Erro ao extrair chave do payload_retorno: {e}")
    
    # Construir URL do QRCode
    qr_code_url = None
    if emissao.chave_nfse and len(emissao.chave_nfse) == 50:
        qr_code_url = f"https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave={emissao.chave_nfse}"
    
    return render_template("nfse_nacional/danfs_print.html", emissao=emissao, empresa=empresa, qr_code_url=qr_code_url)


@nfse_nacional_bp.route("/cancelamento", methods=["GET", "POST"])
@login_required
def cancelamento():
    """
    Rota para cancelamento de NFS-e (evento e101101) pela chave de acesso.
    """
    empresa_id = tenant_id()
    empresa = Empresa.query.get_or_404(empresa_id)
    
    # Obter configurações disponíveis
    configuracoes = NfseNacionalConfiguracao.query.filter_by(
        empresa_id=empresa_id
    ).all()
    
    if request.method == "POST":
        chave_acesso = request.form.get("chave_acesso", "").strip()
        ambiente = request.form.get("ambiente", "homologacao")
        codigo_motivo = request.form.get("codigo_motivo", "1")
        descricao_motivo = request.form.get("descricao_motivo", "Erro na emissão")
        
        if not chave_acesso:
            flash("Informe a chave de acesso da NFS-e.", "danger")
            return render_template(
                "nfse_nacional/cancelamento.html",
                configuracoes=configuracoes,
                chave_acesso=chave_acesso,
            )
        
        # Obter configuração do ambiente selecionado
        configuracao = NfseNacionalConfiguracao.query.filter_by(
            empresa_id=empresa_id,
            ambiente=ambiente
        ).first()
        
        if not configuracao:
            flash(f"Configuração não encontrada para o ambiente: {ambiente}", "danger")
            return render_template(
                "nfse_nacional/cancelamento.html",
                configuracoes=configuracoes,
                chave_acesso=chave_acesso,
            )
        
        try:
            # Importar função de transmissão de evento
            from src.services.nfse_nacional import transmitireventocancelamento
            
            # Transmitir evento de cancelamento
            resultado = transmitireventocancelamento(
                chave_nfse=chave_acesso,
                cnpj_prestador=empresa.cnpj,
                codigo_motivo=codigo_motivo,
                descricao_motivo=descricao_motivo,
                configuracao=configuracao,
            )
            
            if resultado.get("sucesso"):
                # Encontrar a emissão pela chave de acesso e excluir o lançamento
                emissao = NfseNacionalEmissao.query.filter_by(
                    empresa_id=empresa_id,
                    chave_nfse=chave_acesso
                ).first()
                
                if emissao and emissao.lancamento:
                    lancamento = emissao.lancamento
                    db.session.delete(lancamento)
                    emissao.lancamento = None
                    logging.info(f"Lançamento financeiro {lancamento.id} excluído ao cancelar NFS-e pela chave {chave_acesso}")
                    db.session.commit()
                
                flash("Cancelamento realizado com sucesso.", "success")
                return render_template(
                    "nfse_nacional/cancelamento.html",
                    configuracoes=configuracoes,
                    chave_acesso=chave_acesso,
                    resultado=resultado,
                )
            else:
                flash(f"Erro no cancelamento: {resultado.get('mensagem')}", "danger")
                return render_template(
                    "nfse_nacional/cancelamento.html",
                    configuracoes=configuracoes,
                    chave_acesso=chave_acesso,
                    resultado=resultado,
                )
                
        except Exception as exc:
            logging.error(f"Erro ao cancelar NFS-e: {exc}")
            flash(f"Erro ao cancelar NFS-e: {exc}", "danger")
            return render_template(
                "nfse_nacional/cancelamento.html",
                configuracoes=configuracoes,
                chave_acesso=chave_acesso,
            )
    
    return render_template(
        "nfse_nacional/cancelamento.html",
        configuracoes=configuracoes,
        chave_acesso="",
    )


@nfse_nacional_bp.route("/emissoes/<int:emissao_id>/cancelar", methods=["POST"])
@login_required
def cancelar_emissao(emissao_id):
    """
    Rota para cancelamento de NFS-e (evento e101101).
    """
    empresa_id = tenant_id()
    empresa = Empresa.query.get_or_404(empresa_id)
    
    emissao = scoped_get_or_404(NfseNacionalEmissao, emissao_id)
    
    # Validar se a emissão pode ser cancelada
    if emissao.situacao_fiscal != "AUTORIZADA":
        if request.is_json:
            return jsonify({"error": "Apenas NFS-e autorizadas podem ser canceladas."}), 400
        flash("Apenas NFS-e autorizadas podem ser canceladas.", "danger")
        return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=emissao_id))
    
    # Validar se a emissão já está cancelada
    if emissao.situacao_fiscal == "CANCELADA":
        if request.is_json:
            return jsonify({"error": "Esta NFS-e já está cancelada."}), 400
        flash("Esta NFS-e já está cancelada.", "warning")
        return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=emissao_id))
    
    # Validar se tem chave de acesso
    if not emissao.chave_nfse or len(emissao.chave_nfse) != 50:
        if request.is_json:
            return jsonify({"error": "Chave de acesso da NFS-e não disponível."}), 400
        flash("Chave de acesso da NFS-e não disponível.", "danger")
        return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=emissao_id))
    
    # Obter dados do formulário
    data = request.get_json(silent=True) if request.is_json else request.form
    codigo_motivo = data.get("codigo_motivo", "1")
    descricao_motivo = data.get("descricao_motivo", "Erro na emissão")
    
    # Obter configuração do ambiente da emissão
    ambiente = emissao.ambiente or "homologacao"
    configuracao = NfseNacionalConfiguracao.query.filter_by(
        empresa_id=empresa_id,
        ambiente=ambiente
    ).first()
    
    if not configuracao:
        if request.is_json:
            return jsonify({"error": "Configuração não encontrada para o ambiente da emissão."}), 400
        flash("Configuração não encontrada para o ambiente da emissão.", "danger")
        return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=emissao_id))
    
    try:
        # Importar função de transmissão de evento
        from src.services.nfse_nacional import transmitireventocancelamento
        
        # Transmitir evento de cancelamento
        resultado = transmitireventocancelamento(
            chave_nfse=emissao.chave_nfse,
            cnpj_prestador=empresa.cnpj,
            codigo_motivo=codigo_motivo,
            descricao_motivo=descricao_motivo,
            configuracao=configuracao,
        )
        
        if resultado.get("sucesso"):
            # Atualizar status da emissão
            emissao.situacao_fiscal = "CANCELADA"
            emissao.status_processamento = "CANCELADA"
            emissao.protocolo_cancelamento = resultado.get("protocolo")
            emissao.motivo_cancelamento = descricao_motivo
            emissao.cancelado_em = datetime.utcnow()
            emissao.cancelado_por_id = current_user.id
            
            # Salvar payload de retorno do cancelamento
            emissao.payload_cancelamento = json.dumps(resultado.get("payload_retorno"), ensure_ascii=False, default=str)
            
            # Excluir lançamento financeiro associado, se existir
            if emissao.lancamento:
                lancamento = emissao.lancamento
                # Excluir o lançamento
                db.session.delete(lancamento)
                emissao.lancamento = None
                logging.info(f"Lançamento financeiro {lancamento.id} excluído ao cancelar NFS-e {emissao.id}")
            
            db.session.commit()
            
            if request.is_json:
                return jsonify(_json_safe({
                    "sucesso": True,
                    "mensagem": "NFS-e cancelada com sucesso.",
                    "protocolo": resultado.get("protocolo"),
                    "situacao_fiscal": "CANCELADA",
                })), 200
            
            flash("NFS-e cancelada com sucesso.", "success")
            return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=emissao_id))
        else:
            # Falha no cancelamento
            if request.is_json:
                return jsonify(_json_safe({
                    "sucesso": False,
                    "error": resultado.get("mensagem"),
                    "errors": resultado.get("errors"),
                })), 400
            
            flash(f"Erro ao cancelar NFS-e: {resultado.get('mensagem')}", "danger")
            return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=emissao_id))
            
    except Exception as exc:
        db.session.rollback()
        logging.error(f"Erro ao cancelar NFS-e: {exc}")
        
        if request.is_json:
            return jsonify({"error": f"Erro ao cancelar NFS-e: {exc}"}), 500
        
        flash(f"Erro ao cancelar NFS-e: {exc}", "danger")
        return redirect(url_for("nfse_nacional.emissao_detalhe", emissao_id=emissao_id))


@nfse_nacional_bp.route("/consultar", methods=["GET", "POST"])
@login_required
def nfse_consultar():
    """
    Rota para consulta de NFS-e pela chave de acesso.
    """
    empresa_id = tenant_id()
    empresa = Empresa.query.get_or_404(empresa_id)
    
    # Obter configurações disponíveis
    configuracoes = NfseNacionalConfiguracao.query.filter_by(
        empresa_id=empresa_id
    ).all()
    
    if request.method == "POST":
        chave_acesso = request.form.get("chave_acesso", "").strip()
        ambiente = request.form.get("ambiente", "homologacao")
        
        if not chave_acesso:
            flash("Informe a chave de acesso da NFS-e.", "danger")
            return render_template(
                "nfse_nacional/consultar.html",
                configuracoes=configuracoes,
                chave_acesso=chave_acesso,
            )
        
        # Obter configuração do ambiente selecionado
        configuracao = NfseNacionalConfiguracao.query.filter_by(
            empresa_id=empresa_id,
            ambiente=ambiente
        ).first()
        
        if not configuracao:
            flash(f"Configuração não encontrada para o ambiente: {ambiente}", "danger")
            return render_template(
                "nfse_nacional/consultar.html",
                configuracoes=configuracoes,
                chave_acesso=chave_acesso,
            )
        
        try:
            # Consultar NFS-e na API
            resultado = consultar_nfse(
                chave_acesso=chave_acesso,
                configuracao=configuracao,
            )
            
            if resultado.get("sucesso"):
                flash("NFS-e encontrada com sucesso.", "success")
                return render_template(
                    "nfse_nacional/consultar.html",
                    configuracoes=configuracoes,
                    chave_acesso=chave_acesso,
                    resultado=resultado,
                )
            else:
                flash(f"Erro na consulta: {resultado.get('mensagem')}", "danger")
                return render_template(
                    "nfse_nacional/consultar.html",
                    configuracoes=configuracoes,
                    chave_acesso=chave_acesso,
                    resultado=resultado,
                )
                
        except Exception as exc:
            logging.error(f"Erro ao consultar NFS-e: {exc}")
            flash(f"Erro ao consultar NFS-e: {exc}", "danger")
            return render_template(
                "nfse_nacional/consultar.html",
                configuracoes=configuracoes,
                chave_acesso=chave_acesso,
            )
    
    return render_template(
        "nfse_nacional/consultar.html",
        configuracoes=configuracoes,
        chave_acesso="",
    )


@nfse_nacional_bp.route("/listagem", methods=["GET"])
@login_required
def listagem():
    """
    Rota para listagem de NFS-e emitidas.
    """
    empresa_id = tenant_id()
    
    # Filtros
    status = request.args.get("status", "")
    situacao = request.args.get("situacao", "")
    busca = request.args.get("busca", "").strip()
    
    # Query base - apenas NFS-e autorizadas fiscalmente ou com número
    query = NfseNacionalEmissao.query.filter_by(empresa_id=empresa_id).filter(
        db.or_(
            NfseNacionalEmissao.situacao_fiscal == 'AUTORIZADA',
            NfseNacionalEmissao.numero_nfse.isnot(None)
        )
    )
    
    # Aplicar filtros adicionais se fornecidos
    if status:
        query = query.filter(NfseNacionalEmissao.status_processamento == status)
    
    if situacao:
        query = query.filter(NfseNacionalEmissao.situacao_fiscal == situacao)
    
    if busca:
        # Buscar por número da nota, chave ou nome do tomador
        query = query.join(Entidade).filter(
            db.or_(
                NfseNacionalEmissao.numero_nfse.like(f"%{busca}%"),
                NfseNacionalEmissao.chave_nfse.like(f"%{busca}%"),
                Entidade.nome.like(f"%{busca}%")
            )
        )
    
    # Ordenar por data de criação (mais recente primeiro)
    query = query.order_by(NfseNacionalEmissao.criado_em.desc())
    
    # Paginação
    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    emissoes = pagination.items
    
    return render_template(
        "nfse_nacional/listagem.html",
        emissoes=emissoes,
        pagination=pagination,
        status=status,
        situacao=situacao,
        busca=busca,
    )


@nfse_nacional_bp.route("/listagem/<int:id>/visualizar", methods=["GET"])
@login_required
def visualizar(id):
    """
    Rota para visualizar detalhes de uma NFS-e emitida.
    """
    emissao = scoped_get_or_404(NfseNacionalEmissao, id)
    
    return render_template(
        "nfse_nacional/visualizar.html",
        emissao=emissao,
    )


@nfse_nacional_bp.route("/listagem/<int:id>/enviar-email", methods=["POST"])
@login_required
def enviar_email(id):
    """
    Rota para enviar NFS-e por email para o cliente.
    """
    emissao = scoped_get_or_404(NfseNacionalEmissao, id)
    
    email_cliente = request.form.get("email_cliente", "").strip()
    mensagem = request.form.get("mensagem", "").strip()
    
    if not email_cliente:
        flash("Informe o email do cliente.", "danger")
        return redirect(url_for("nfse_nacional.visualizar", id=id))
    
    # TODO: Implementar envio de email
    # Por enquanto, apenas simular
    flash(f"Email enviado para {email_cliente} (funcionalidade a ser implementada).", "success")
    
    return redirect(url_for("nfse_nacional.listagem"))


@nfse_nacional_bp.route("/cancelamento-substituicao", methods=["GET", "POST"])
@login_required
def nfse_cancelamento_substituicao():
    """
    Rota para cancelamento de NFS-e por substituição (e105102).
    """
    empresa_id = tenant_id()
    empresa = Empresa.query.get_or_404(empresa_id)
    
    # Obter configurações disponíveis
    configuracoes = NfseNacionalConfiguracao.query.filter_by(
        empresa_id=empresa_id
    ).all()
    
    if request.method == "POST":
        chave_nfse = request.form.get("chave_nfse", "").strip()
        chave_substituta = request.form.get("chave_substituta", "").strip()
        codigo_motivo = request.form.get("codigo_motivo", "1").strip()
        descricao_motivo = request.form.get("descricao_motivo", "").strip()
        ambiente = request.form.get("ambiente", "homologacao")
        
        if not chave_nfse:
            flash("Informe a chave de acesso da NFS-e a ser cancelada.", "danger")
            return render_template(
                "nfse_nacional/cancelamento_substituicao.html",
                configuracoes=configuracoes,
                chave_nfse=chave_nfse,
                chave_substituta=chave_substituta,
                descricao_motivo=descricao_motivo,
            )
        
        if not chave_substituta:
            flash("Informe a chave de acesso da NFS-e substituta.", "danger")
            return render_template(
                "nfse_nacional/cancelamento_substituicao.html",
                configuracoes=configuracoes,
                chave_nfse=chave_nfse,
                chave_substituta=chave_substituta,
                descricao_motivo=descricao_motivo,
            )
        
        # Obter configuração do ambiente selecionado
        configuracao = NfseNacionalConfiguracao.query.filter_by(
            empresa_id=empresa_id,
            ambiente=ambiente
        ).first()
        
        if not configuracao:
            flash(f"Configuração não encontrada para o ambiente: {ambiente}", "danger")
            return render_template(
                "nfse_nacional/cancelamento_substituicao.html",
                configuracoes=configuracoes,
                chave_nfse=chave_nfse,
                chave_substituta=chave_substituta,
                descricao_motivo=descricao_motivo,
            )
        
        try:
            # Transmitir cancelamento por substituição
            resultado = transmitireventocancelamentosubstituicao(
                chave_nfse=chave_nfse,
                codigo_motivo=codigo_motivo,
                descricao_motivo=descricao_motivo,
                chave_substituta=chave_substituta,
                configuracao=configuracao,
            )
            
            if resultado.get("sucesso"):
                flash("Cancelamento por substituição realizado com sucesso.", "success")
                return render_template(
                    "nfse_nacional/cancelamento_substituicao.html",
                    configuracoes=configuracoes,
                    chave_nfse=chave_nfse,
                    chave_substituta=chave_substituta,
                    descricao_motivo=descricao_motivo,
                    resultado=resultado,
                )
            else:
                flash(f"Erro no cancelamento: {resultado.get('mensagem')}", "danger")
                return render_template(
                    "nfse_nacional/cancelamento_substituicao.html",
                    configuracoes=configuracoes,
                    chave_nfse=chave_nfse,
                    chave_substituta=chave_substituta,
                    descricao_motivo=descricao_motivo,
                    resultado=resultado,
                )
                
        except Exception as exc:
            logging.error(f"Erro ao cancelar por substituição: {exc}")
            flash(f"Erro ao cancelar por substituição: {exc}", "danger")
            return render_template(
                "nfse_nacional/cancelamento_substituicao.html",
                configuracoes=configuracoes,
                chave_nfse=chave_nfse,
                chave_substituta=chave_substituta,
                descricao_motivo=descricao_motivo,
            )
    
    return render_template(
        "nfse_nacional/cancelamento_substituicao.html",
        configuracoes=configuracoes,
        chave_nfse="",
        chave_substituta="",
        descricao_motivo="",
    )


@nfse_nacional_bp.route("/consultar/imprimir", methods=["POST"])
@login_required
def nfse_consultar_imprimir():
    """
    Rota para impressão do DANFSe a partir do XML da consulta.
    """
    xml_nfse = request.form.get("xml_nfse")
    chave_acesso = request.form.get("chave_acesso")
    
    if not xml_nfse:
        flash("XML da NFS-e não fornecido.", "danger")
        return redirect(url_for("nfse_nacional.nfse_consultar"))
    
    try:
        import xml.etree.ElementTree as ET
        
        # Parsear XML para extrair dados
        root = ET.fromstring(xml_nfse)
        ns = {"nfse": "http://www.sped.fazenda.gov.br/nfse"}
        
        # Extrair dados necessários para o DANFSe
        numero_nfse = root.findtext(".//nfse:nNFSe", namespaces=ns) or ""
        cod_verificacao = root.findtext(".//nfse:cNFSe", namespaces=ns) or ""
        data_emissao = root.findtext(".//nfse:dhEmi", namespaces=ns) or ""
        valor_servico = root.findtext(".//nfse:vServ", namespaces=ns) or "0.00"
        valor_iss = root.findtext(".//nfse:vISS", namespaces=ns) or "0.00"
        valor_deducoes = root.findtext(".//nfse:vDed", namespaces=ns) or "0.00"
        valor_base_calculo = root.findtext(".//nfse:vBC", namespaces=ns) or "0.00"
        aliquota_iss = root.findtext(".//nfse:aliqISS", namespaces=ns) or "0.00"
        
        # Dados do prestador
        prestador = root.find(".//nfse:prest", namespaces=ns)
        if prestador is not None:
            cnpj_prestador = prestador.findtext("nfse:CNPJ", namespaces=ns) or ""
            nome_prestador = prestador.findtext("nfse:xNome", namespaces=ns) or ""
            im_prestador = prestador.findtext("nfse:IM", namespaces=ns) or ""
            end_prestador = prestador.find("nfse:endPrest", namespaces=ns)
            if end_prestador is not None:
                endereco_prestador = end_prestador.findtext("nfse:xLgr", namespaces=ns) or ""
                numero_prestador = end_prestador.findtext("nfse:nro", namespaces=ns) or ""
                bairro_prestador = end_prestador.findtext("nfse:xBairro", namespaces=ns) or ""
                cidade_prestador = end_prestador.findtext("nfse:xMun", namespaces=ns) or ""
                uf_prestador = end_prestador.findtext("nfse:UF", namespaces=ns) or ""
                cep_prestador = end_prestador.findtext("nfse:CEP", namespaces=ns) or ""
        else:
            cnpj_prestador = ""
            nome_prestador = ""
            im_prestador = ""
            endereco_prestador = ""
            numero_prestador = ""
            bairro_prestador = ""
            cidade_prestador = ""
            uf_prestador = ""
            cep_prestador = ""
        
        # Dados do tomador
        tomador = root.find(".//nfse:tom", namespaces=ns)
        if tomador is not None:
            cnpj_tomador = tomador.findtext("nfse:CNPJ", namespaces=ns) or ""
            cpf_tomador = tomador.findtext("nfse:CPF", namespaces=ns) or ""
            nome_tomador = tomador.findtext("nfse:xNome", namespaces=ns) or ""
            end_tomador = tomador.find("nfse:endTom", namespaces=ns)
            if end_tomador is not None:
                endereco_tomador = end_tomador.findtext("nfse:xLgr", namespaces=ns) or ""
                numero_tomador = end_tomador.findtext("nfse:nro", namespaces=ns) or ""
                bairro_tomador = end_tomador.findtext("nfse:xBairro", namespaces=ns) or ""
                cidade_tomador = end_tomador.findtext("nfse:xMun", namespaces=ns) or ""
                uf_tomador = end_tomador.findtext("nfse:UF", namespaces=ns) or ""
                cep_tomador = end_tomador.findtext("nfse:CEP", namespaces=ns) or ""
        else:
            cnpj_tomador = ""
            cpf_tomador = ""
            nome_tomador = ""
            endereco_tomador = ""
            numero_tomador = ""
            bairro_tomador = ""
            cidade_tomador = ""
            uf_tomador = ""
            cep_tomador = ""
        
        # Dados do serviço
        servico = root.find(".//nfse:serv", namespaces=ns)
        if servico is not None:
            descricao_servico = servico.findtext("nfse:xDesc", namespaces=ns) or ""
            codigo_tributacao_nacional = servico.findtext("nfse:cTribNac", namespaces=ns) or ""
            codigo_tributacao_municipal = servico.findtext("nfse:cTribMun", namespaces=ns) or ""
        else:
            descricao_servico = ""
            codigo_tributacao_nacional = ""
            codigo_tributacao_municipal = ""
        
        # Construir URL do QRCode
        if chave_acesso and len(chave_acesso) == 50:
            qrcode_url = f"https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave={chave_acesso}"
        else:
            qrcode_url = ""
        
        # Preparar payload para o template
        payload_retorno = {
            "numero_nfse": numero_nfse,
            "cod_verificacao": cod_verificacao,
            "data_emissao": data_emissao,
            "valor_servico": valor_servico,
            "valor_iss": valor_iss,
            "valor_deducoes": valor_deducoes,
            "valor_base_calculo": valor_base_calculo,
            "aliquota_iss": aliquota_iss,
            "cnpj_prestador": cnpj_prestador,
            "nome_prestador": nome_prestador,
            "im_prestador": im_prestador,
            "endereco_prestador": endereco_prestador,
            "numero_prestador": numero_prestador,
            "bairro_prestador": bairro_prestador,
            "cidade_prestador": cidade_prestador,
            "uf_prestador": uf_prestador,
            "cep_prestador": cep_prestador,
            "cnpj_tomador": cnpj_tomador,
            "cpf_tomador": cpf_tomador,
            "nome_tomador": nome_tomador,
            "endereco_tomador": endereco_tomador,
            "numero_tomador": numero_tomador,
            "bairro_tomador": bairro_tomador,
            "cidade_tomador": cidade_tomador,
            "uf_tomador": uf_tomador,
            "cep_tomador": cep_tomador,
            "descricao_servico": descricao_servico,
            "codigo_tributacao_nacional": codigo_tributacao_nacional,
            "codigo_tributacao_municipal": codigo_tributacao_municipal,
            "chave_acesso": chave_acesso or "",
        }
        
        return render_template(
            "nfse_nacional/danfs_print.html",
            payload_retorno=payload_retorno,
            qrcode_url=qrcode_url,
        )
        
    except Exception as exc:
        logging.error(f"Erro ao imprimir DANFSe da consulta: {exc}")
        flash(f"Erro ao imprimir DANFSe: {exc}", "danger")
        return redirect(url_for("nfse_nacional.nfse_consultar"))