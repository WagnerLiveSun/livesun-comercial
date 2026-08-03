from __future__ import annotations

import base64
import gzip
import hashlib
import json as _json
import logging
import os
import tempfile
import unicodedata
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from lxml import etree
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import QName

from src.services.nfse_validation import validate_xml
from src.services.xml_signer import sign_xml_enveloped

BASE_DISTRIBUICAO_HOMOLOGACAO = "https://adn.producaorestrita.nfse.gov.br"
BASE_DISTRIBUICAO_PRODUCAO = "https://adn.nfse.gov.br"
BASE_EMISSAO_HOMOLOGACAO = "https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional"
BASE_EMISSAO_PRODUCAO = "https://sefin.nfse.gov.br/SefinNacional"

BRASILIA_TZ = timezone(timedelta(hours=-3))
NS_NFSE = "http://www.sped.fazenda.gov.br/nfse"
NS_DS = "http://www.w3.org/2000/09/xmldsig#"

logger = logging.getLogger(__name__)


def limpar_texto_xml(texto) -> str:
    if not texto:
        return ""
    texto_normalizado = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto_normalizado if not unicodedata.combining(c)).strip()


def default_output_dir() -> str:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.environ.get("NFS_XML_OUT_DIR") or os.path.join(repo_root, "dist", "data", "XML")


def ensure_output_dir() -> str:
    out = default_output_dir()
    os.makedirs(out, exist_ok=True)
    return out


def save_xml(xml_string: str, prefix: str) -> str:
    out = ensure_output_dir()
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_prefix = "".join(ch for ch in prefix if ch.isalnum() or ch in ("_", "-"))[:64]
    filename = f"{safe_prefix}_{ts}.xml"
    path = os.path.join(out, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_string)
    return path


def only_digits(value) -> str:
    if value is None:
        return ""
    return "".join(ch for ch in str(value) if ch.isdigit())


def decimal(value, default: Decimal = Decimal("0.00")) -> Decimal:
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return default


def date_(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def first_non_empty(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def normalize_text(value) -> str:
    text = unicodedata.normalize("NFKD", str(value) if value is not None else "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.strip().casefold()


def require_fields(payload: dict, fields: list[tuple[str, tuple[str, ...]]], scope: str) -> dict[str, str]:
    values: dict[str, str] = {}
    missing: list[str] = []

    for label, keys in fields:
        value = first_non_empty(payload, *keys)
        if not value:
            missing.append(label)
        else:
            values[label] = value

    if missing:
        raise ValueError(f"{scope}: preencha os campos obrigatorios: {', '.join(missing)}.")

    return values


def generate_internal_number(empresa_id: int) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:8].upper()
    return f"NFSE-{empresa_id}-{stamp}-{suffix}"


def generateinternalnumber(empresa_id: int) -> str:
    return generate_internal_number(empresa_id)


def buildidempotencyhash(payload: dict) -> str:
    normalized = _json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def ambiente_homologacao(ambiente: str | None) -> bool:
    text = str(ambiente or "").strip().lower()
    return text.startswith("h") or text in {
        "2",
        "homologacao",
        "homologação",
        "prodrestrita",
        "producaorestrita",
        "produção restrita",
    }


def normalize_sefin_emissao_base(url: str, ambiente: str | None = None) -> str:
    normalized = (url or "").strip().rstrip("/")
    lowered = normalized.lower()

    if not normalized:
        return BASE_EMISSAO_HOMOLOGACAO if ambiente_homologacao(ambiente) else BASE_EMISSAO_PRODUCAO

    if "sefin.nfse.gov.br" in lowered and "sefinnacional" not in lowered and "api/sefinnacional" not in lowered:
        return BASE_EMISSAO_PRODUCAO

    if "sefin.producaorestrita.nfse.gov.br" in lowered and "sefinnacional" not in lowered and "api/sefinnacional" not in lowered:
        return BASE_EMISSAO_HOMOLOGACAO

    return normalized


def get_base_emissao(configuracao=None, ambiente: str | None = None) -> str:
    explicit = (
        os.environ.get("NFS_BASE_EMISSAO")
        or getattr(configuracao, "endpoint_emissao", None)
        or getattr(configuracao, "endpoint_base_emissao", None)
        or getattr(configuracao, "endpoint_base", None)
        or ""
    ).strip().rstrip("/")

    if explicit:
        return normalize_sefin_emissao_base(explicit, ambiente=ambiente)

    return BASE_EMISSAO_HOMOLOGACAO if ambiente_homologacao(ambiente) else BASE_EMISSAO_PRODUCAO


def get_base_distribuicao(configuracao=None, ambiente: str | None = None) -> str:
    explicit = (
        os.environ.get("NFS_BASE_DISTRIBUICAO")
        or getattr(configuracao, "endpoint_distribuicao", None)
        or getattr(configuracao, "endpoint_base_distribuicao", None)
        or getattr(configuracao, "endpoint_base", None)
        or ""
    ).strip().rstrip("/")

    if explicit:
        return explicit

    return BASE_DISTRIBUICAO_HOMOLOGACAO if ambiente_homologacao(ambiente) else BASE_DISTRIBUICAO_PRODUCAO


def endpoint_looks_like_distribuicao(url: str) -> bool:
    lowered = (url or "").lower()
    return "adn." in lowered or "contribuintes" in lowered


def candidate_emission_urls(base_emissao: str) -> list[str]:
    base = (base_emissao or "").strip().rstrip("/")
    candidates: list[str] = []

    if not base:
        return candidates

    for suffix in ("/nfse", "", "/API/SefinNacional/nfse", "/API/SefinNacional"):
        candidate = f"{base}{suffix}".rstrip("/")
        if candidate not in candidates:
            candidates.append(candidate)

    return candidates


def resolve_municipio_codigo_ibge(
    codigo: str | None = None,
    cidade: str | None = None,
    uf: str | None = None,
) -> str:
    codigo_digits = only_digits(codigo)
    if len(codigo_digits) == 7:
        return codigo_digits

    cidade_norm = normalize_text(cidade)
    uf_norm = str(uf or "").strip().upper()
    if not cidade_norm:
        return ""

    try:
        from src.models import NfseMunicipioReferencia
    except Exception:
        return ""

    query = NfseMunicipioReferencia.query.filter_by(ativo=True)
    if uf_norm:
        query = query.filter(NfseMunicipioReferencia.uf_sigla == uf_norm)

    for municipio in query.all():
        if normalize_text(municipio.nome_municipio) == cidade_norm:
            return str(municipio.codigo_ibge)

    return ""


def validate_catalog_references(payload: dict) -> None:
    codigo_municipio = only_digits(payload.get("codigo_municipio") or payload.get("codigo_municipio_ibge") or "")
    if codigo_municipio:
        try:
            from src.models import NfseMunicipioReferencia
            municipio = NfseMunicipioReferencia.query.filter_by(
                codigo_ibge=codigo_municipio,
                ativo=True,
            ).first()
            if not municipio:
                raise ValueError(f"Codigo de municipio invalido ou nao importado: {codigo_municipio}.")
        except ImportError:
            pass

    codigo_nbs = only_digits(payload.get("servico_nbs") or payload.get("nbs") or "")
    if codigo_nbs:
        try:
            from src.models import NfseNbsReferencia
            nbs = NfseNbsReferencia.query.filter_by(codigo_nbs=codigo_nbs, ativo=True).first()
            if not nbs:
                logging.warning("Codigo NBS nao encontrado no catalogo: %s", codigo_nbs)
        except ImportError:
            pass


def resolve_servico_codigo_nacional(payload: dict) -> str:
    explicit = only_digits(
        payload.get("servico_codigo_nacional")
        or payload.get("cTribNac")
        or payload.get("servico_codigo")
        or payload.get("servicocodigonacional")
        or ""
    )
    if explicit:
        return explicit.zfill(6)

    raise ValueError("Codigo de servico nacional invalido ou nao encontrado no catalogo oficial.")


def resolve_ndps_sequence(payload: dict) -> str:
    suggested = str(
        payload.get("numero_nfse_sugerido")
        or payload.get("nDPS")
        or payload.get("numero_dps")
        or payload.get("numeronfsesugerido")
        or ""
    ).strip()

    if suggested.isdigit():
        return suggested.lstrip("0") or "1"

    empresa_id = payload.get("empresa_id") or payload.get("empresaid")
    ambiente = str(payload.get("ambiente") or "").strip().lower()

    if empresa_id:
        try:
            from src.models import NfseNacionalEmissao
            query = NfseNacionalEmissao.query.filter_by(empresa_id=empresa_id)
            if ambiente:
                query = query.filter(NfseNacionalEmissao.ambiente == ambiente)
            ultimo = query.order_by(NfseNacionalEmissao.id.desc()).first()
            if ultimo and getattr(ultimo, "id", None):
                return str(int(ultimo.id))
        except Exception:
            pass

    return "1"


def resolve_certificate_settings(
    empresa_id: int | None = None,
    ambiente: str | None = None,
) -> tuple[str | None, str | None]:
    pfx_path = None
    pfx_pass = None

    if empresa_id is None:
        return None, None

    try:
        from src.models import NfseNacionalCertificado

        ambiente_text = (ambiente or "").strip().lower()
        ambiente_q = "homologacao" if ambiente_homologacao(ambiente_text) else "producao"

        query = NfseNacionalCertificado.query.filter_by(empresa_id=empresa_id, ativo=True)
        if ambiente_q:
            query = query.filter(NfseNacionalCertificado.ambiente == ambiente_q)

        cert = query.order_by(NfseNacionalCertificado.validade_em.desc()).first()
        if cert:
            if getattr(cert, "caminho_arquivo", None):
                pfx_path = cert.caminho_arquivo.strip() or None
            if getattr(cert, "senha", None) is not None:
                pfx_pass = cert.senha.strip() if isinstance(cert.senha, str) else cert.senha
    except Exception:
        pass

    return pfx_path, pfx_pass


def resolvecertificatesettings(
    empresa_id: int | None = None,
    ambiente: str | None = None,
) -> tuple[str | None, str | None]:
    return resolve_certificate_settings(empresa_id=empresa_id, ambiente=ambiente)


def prepare_mtls_from_pfx(pfx_path: str, pfx_password: str | None) -> tuple[str, str, list[str]]:
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
    from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates

    with open(pfx_path, "rb") as handle:
        data = handle.read()

    private_key, cert, additional_certs = load_key_and_certificates(
        data,
        pfx_password.encode("utf-8") if pfx_password else None,
    )

    if private_key is None or cert is None:
        raise ValueError("PFX sem chave privada ou certificado.")

    now = datetime.utcnow()
    cert_not_before = getattr(cert, "not_valid_before", None)
    cert_not_after = getattr(cert, "not_valid_after", None)

    if cert_not_before and cert_not_before > now:
        raise ValueError(f"Certificado nao valido ainda. Valido a partir de {cert_not_before}")
    if cert_not_after and cert_not_after < now:
        raise ValueError(f"Certificado expirado. Expirou em {cert_not_after}")

    key_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )

    cert_pem = cert.public_bytes(Encoding.PEM)
    if additional_certs:
        for ca in additional_certs:
            cert_pem += ca.public_bytes(Encoding.PEM)

    temp_paths: list[str] = []

    cert_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pem")
    cert_file.write(cert_pem)
    cert_file.close()
    temp_paths.append(cert_file.name)

    key_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pem")
    key_file.write(key_pem)
    key_file.close()
    temp_paths.append(key_file.name)

    return cert_file.name, key_file.name, temp_paths


def preparemtlsfrompfx(pfx_path: str, pfx_password: str | None) -> tuple[str, str, list[str]]:
    return prepare_mtls_from_pfx(pfx_path, pfx_password)


def response_payload(response) -> dict:
    try:
        content_type = response.headers.get("content-type", "").lower()
        if "json" in content_type:
            return response.json()
    except Exception:
        pass

    return {
        "raw": response.text,
        "headers": dict(getattr(response, "headers", {}) or {}),
        "status_code": getattr(response, "status_code", None),
    }


def default_xsd_dir() -> str:
    env = os.environ.get("NFS_XSD_DIR")
    if env:
        return env
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(repo_root, "NFS_XSD_DIR")


def resolve_xsd_path(kind: str = "dps") -> str:
    xsd_dir = default_xsd_dir()
    kind_l = (kind or "").strip().lower()

    candidates_map = {
        "dps": [
            "DPS_v1.00.xsd",
            "dps_v1.00.xsd",
            "Dps_v1.00.xsd",
            "DPS.xsd",
            "dps.xsd",
        ],
        "nfse": [
            "NFSe_v1.00.xsd",
            "nfse_v1.00.xsd",
            "Nfse_v1.00.xsd",
            "NFSe.xsd",
            "nfse.xsd",
        ],
        "evento": [
            "evento_v1.00.xsd",
            "pedRegEvento_v1.00.xsd",
        ],
    }

    candidates = candidates_map.get(kind_l, []) + [
        f"{kind}.xsd",
        f"{kind.upper()}.xsd",
        f"{kind.lower()}.xsd",
    ]

    for name in candidates:
        path = os.path.join(xsd_dir, name)
        if os.path.isfile(path):
            return path

    try:
        for entry in os.listdir(xsd_dir):
            lower = entry.lower()
            if kind_l in lower and lower.endswith(".xsd"):
                return os.path.join(xsd_dir, entry)
    except Exception:
        pass

    raise FileNotFoundError(f"Nao foi encontrado XSD para '{kind}' em: {xsd_dir}")


def jsonsafe(obj: Any):
    if isinstance(obj, Decimal):
        return format(obj, "0.2f")
    if isinstance(obj, dict):
        return {k: jsonsafe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonsafe(v) for v in obj]
    return obj


def run_xsd_validation(xml_string: str, kind: str = "dps") -> tuple[bool, list[str]]:
    try:
        xsd_path = resolve_xsd_path(kind)
    except Exception as exc:
        return False, [f"XSD resolve error: {exc}"]

    try:
        result = validate_xml(xml_string, xsd_path)
    except Exception as exc:
        return False, [f"XSD validation error: {exc}"]

    if isinstance(result, bool):
        return result, ([] if result else ["Falha de validacao XSD sem detalhes."])

    if isinstance(result, tuple):
        valid = bool(result[0])
        msgs = result[1] if len(result) > 1 else []
        if msgs is None:
            msgs = []
        if not isinstance(msgs, list):
            msgs = [str(msgs)]
        return valid, [str(x) for x in msgs]

    if isinstance(result, dict):
        valid = bool(result.get("valid", True))
        msgs = result.get("errors") or result.get("mensagens") or []
        if not isinstance(msgs, list):
            msgs = [str(msgs)]
        return valid, [str(x) for x in msgs]

    return True, []


def builddpsxml(payload: dict) -> str:
    ET.register_namespace("", NS_NFSE)
    ET.register_namespace("ds", NS_DS)

    validate_catalog_references(payload)

    def q(tag: str) -> str:
        return QName(NS_NFSE, tag)

    prestador = require_fields(
        payload,
        [
            ("codigo_municipio", ("codigo_municipio", "codigo_municipio_ibge", "empresacodigomunicipioibge")),
            ("CNPJ", ("empresa_cnpj", "cnpj", "prestador_cnpj", "empresacnpj")),
            ("Rua", ("empresa_endereco_rua", "endereco_rua", "rua", "logradouro", "empresaenderecorua")),
            ("Numero", ("empresa_endereco_numero", "endereco_numero", "numero", "nro", "empresaendereconumero")),
            ("Bairro", ("empresa_endereco_bairro", "endereco_bairro", "bairro", "empresaenderecobairro")),
            ("CEP", ("empresa_endereco_cep", "endereco_cep", "cep", "empresaenderecocep")),
        ],
        "Prestador",
    )

    root = ET.Element(q("DPS"), versao="1.00")

    codigo_mun = only_digits(prestador["codigo_municipio"])
    cmun7 = codigo_mun.zfill(7)[-7:]
    
    # Debug: mostrar código do município emissor
    logging.info(f"[DEBUG] Código município emissor: {codigo_mun} (cmun7: {cmun7})")
    
    # Tentar buscar nome do município para debug
    try:
        from src.models import NfseMunicipioReferencia
        municipio_ref = NfseMunicipioReferencia.query.filter_by(
            codigo_ibge=codigo_mun,
            ativo=True
        ).first()
        if municipio_ref:
            logging.info(f"[DEBUG] Nome município emissor: {municipio_ref.nome_municipio} - {municipio_ref.uf_sigla}")
        else:
            logging.info(f"[DEBUG] Município não encontrado na tabela de referência")
    except Exception as e:
        logging.info(f"[DEBUG] Erro ao buscar nome do município: {e}")

    local_prestacao = str(payload.get("servico_local_prestacao") or payload.get("servicolocalprestacao") or "emitente").strip().lower()
    tomador_codigo_municipio = resolve_municipio_codigo_ibge(
        payload.get("tomador_codigo_municipio_ibge") or payload.get("tomadorcodigomunicipioibge"),
        payload.get("tomador_endereco_cidade") or payload.get("tomadorenderecocidade"),
        payload.get("tomador_endereco_uf") or payload.get("tomadorenderecouf"),
    )

    cmun_prestacao = cmun7
    if local_prestacao == "tomador" and tomador_codigo_municipio:
        cmun_prestacao = tomador_codigo_municipio.zfill(7)[-7:]

    cnpj_value = only_digits(prestador["CNPJ"]).zfill(14)[-14:]
    id_insc = cnpj_value
    tipo_insc = 2 if len(id_insc) == 14 else 1
    serie = str(payload.get("serie") or "1")[:5].zfill(5)
    ndps_str = resolve_ndps_sequence(payload)
    if not ndps_str.isdigit():
        ndps_str = "1"

    id_dps = f"DPS{cmun7}{tipo_insc}{id_insc}{serie}{ndps_str.zfill(15)}"

    inf = ET.SubElement(root, q("infDPS"), Id=id_dps)
    ET.SubElement(inf, q("tpAmb")).text = "2" if ambiente_homologacao(payload.get("ambiente")) else "1"
    ET.SubElement(inf, q("dhEmi")).text = (
        datetime.now(BRASILIA_TZ) - timedelta(minutes=1)
    ).replace(microsecond=0).isoformat()
    ET.SubElement(inf, q("verAplic")).text = str(os.environ.get("APP_NAME") or "LiveSun/1.0")
    ET.SubElement(inf, q("serie")).text = serie
    ET.SubElement(inf, q("nDPS")).text = str(int(ndps_str)) if int(ndps_str) > 0 else "1"
    ET.SubElement(inf, q("dCompet")).text = (date_(payload.get("dCompet")) or date.today()).strftime("%Y-%m-%d")
    tp_emit = str(payload.get("tpEmit") or "1")
    ET.SubElement(inf, q("tpEmit")).text = tp_emit
    ET.SubElement(inf, q("cLocEmi")).text = cmun7

    prest = ET.SubElement(inf, q("prest"))
    ET.SubElement(prest, q("CNPJ")).text = cnpj_value

    inscricao_municipal = first_non_empty(payload, "inscricao_municipal", "empresa_inscricao_municipal", "im", "inscricaomunicipal")
    
    # Debug: mostrar inscrição municipal
    logging.info(f"[DEBUG] Inscrição Municipal encontrada: {inscricao_municipal}")
    
    # O município do Rio de Janeiro (3304557) não aceita IM pois não tem informações complementares no CNC
    if inscricao_municipal and codigo_mun != "3304557":
        ET.SubElement(prest, q("IM")).text = inscricao_municipal
        logging.info(f"[DEBUG] Campo IM adicionado ao XML: {inscricao_municipal}")
    else:
        if codigo_mun == "3304557":
            logging.info(f"[DEBUG] Campo IM NÃO adicionado ao XML (município Rio de Janeiro não aceita IM)")
        else:
            logging.info(f"[DEBUG] Campo IM NÃO adicionado ao XML (inscrição municipal não informada)")

    # Endereço do prestador não deve ser informado quando o próprio prestador for o emitente (tpEmit=1)
    if tp_emit != "1":
        end = ET.SubElement(prest, q("end"))
        end_nac = ET.SubElement(end, q("endNac"))
        ET.SubElement(end_nac, q("cMun")).text = cmun7
        ET.SubElement(end_nac, q("CEP")).text = only_digits(prestador["CEP"]).zfill(8)[-8:]
        ET.SubElement(end, q("xLgr")).text = limpar_texto_xml(prestador["Rua"])
        ET.SubElement(end, q("nro")).text = str(prestador["Numero"]).strip()
        ET.SubElement(end, q("xBairro")).text = limpar_texto_xml(prestador["Bairro"])
        logging.info(f"[DEBUG] Endereço do prestador adicionado (tpEmit={tp_emit})")
    else:
        logging.info(f"[DEBUG] Endereço do prestador NÃO adicionado (tpEmit=1 - prestador é emitente)")

    reg = ET.SubElement(prest, q("regTrib"))
    # Buscar do cadastro da empresa: op_simp_nac (1=Não Optante, 2=MEI, 3=ME/EPP)
    op_simp_nac = first_non_empty(payload, "op_simp_nac", "opSimpNac", "empresa_op_simp_nac")
    ET.SubElement(reg, q("opSimpNac")).text = str(op_simp_nac or "3")
    
    # Debug: mostrar opSimpNac
    logging.info(f"[DEBUG] opSimpNac usado: {op_simp_nac or '3'}")
    
    # Quando opSimpNac = 3 (ME/EPP), é obrigatório informar regApTribSN
    if op_simp_nac == "3":
        reg_ap_trib_sn = first_non_empty(payload, "reg_ap_trib_sn", "regApTribSN", "empresa_reg_ap_trib_sn")
        ET.SubElement(reg, q("regApTribSN")).text = str(reg_ap_trib_sn or "1")
        logging.info(f"[DEBUG] regApTribSN adicionado: {reg_ap_trib_sn or '1'}")
    
    ET.SubElement(reg, q("regEspTrib")).text = str(payload.get("regEspTrib") or "0")

    tomador_doc = only_digits(payload.get("tomador_documento") or payload.get("cpf_cnpj_tomador") or payload.get("tomadordocumento") or "")
    tomador_nome = str(payload.get("tomador_nome") or payload.get("razao_social_tomador") or payload.get("tomadornome") or "").strip()

    if tomador_doc or tomador_nome:
        toma = ET.SubElement(inf, q("toma"))
        if len(tomador_doc) == 11:
            ET.SubElement(toma, q("CPF")).text = tomador_doc
        elif tomador_doc:
            ET.SubElement(toma, q("CNPJ")).text = tomador_doc.zfill(14)[-14:]
        if tomador_nome:
            ET.SubElement(toma, q("xNome")).text = limpar_texto_xml(tomador_nome)

    serv = ET.SubElement(inf, q("serv"))
    loc = ET.SubElement(serv, q("locPrest"))
    ET.SubElement(loc, q("cLocPrestacao")).text = cmun_prestacao

    cserv = ET.SubElement(serv, q("cServ"))
    ctribnac_digits = resolve_servico_codigo_nacional(payload)
    ET.SubElement(cserv, q("cTribNac")).text = ctribnac_digits

    ctribmun = only_digits(payload.get("cTribMun") or payload.get("codigo_tributacao_municipal") or "")
    if ctribmun:
        ET.SubElement(cserv, q("cTribMun")).text = ctribmun.zfill(3)[-3:]

    desc = str(payload.get("servico_descricao") or payload.get("descricao") or payload.get("servicodescricao") or "").strip()
    ET.SubElement(cserv, q("xDescServ")).text = limpar_texto_xml(desc)

    nbs_val = only_digits(payload.get("servico_nbs") or payload.get("nbs") or payload.get("serviconbs") or "")
    if nbs_val:
        ET.SubElement(cserv, q("cNBS")).text = nbs_val.zfill(9)[-9:]

    valores = ET.SubElement(inf, q("valores"))
    vservprest = ET.SubElement(valores, q("vServPrest"))
    valor_servico = (
        payload.get("valor_servico")
        or payload.get("valorservico")
        or payload.get("valor_serv")
        or "0"
    )
    ET.SubElement(vservprest, q("vServ")).text = f"{decimal(valor_servico):.2f}"

    trib = ET.SubElement(valores, q("trib"))
    tribmun = ET.SubElement(trib, q("tribMun"))
    ET.SubElement(tribmun, q("tribISSQN")).text = str(payload.get("tribISSQN") or "1")
    ET.SubElement(tribmun, q("tpRetISSQN")).text = str(payload.get("tpRetISSQN") or "1")

    # totTrib é obrigatório pelo XSD
    # Para ME/EPP (opSimpNac = 3), usar pTotTribSN (percentual Simples Nacional)
    # Para outros, usar indTotTrib=0
    tottrib = ET.SubElement(trib, q("totTrib"))
    if op_simp_nac == "3":
        # Para ME/EPP, usa pTotTribSN (percentual do Simples Nacional)
        reg_ap_trib_sn = first_non_empty(payload, "reg_ap_trib_sn", "regApTribSN", "empresa_reg_ap_trib_sn")
        ET.SubElement(tottrib, q("pTotTribSN")).text = str(reg_ap_trib_sn or "6.00")
        logging.info(f"[DEBUG] totTrib adicionado com pTotTribSN={reg_ap_trib_sn or '6.00'} (opSimpNac=3 - ME/EPP)")
    else:
        ET.SubElement(tottrib, q("indTotTrib")).text = "0"
        logging.info(f"[DEBUG] totTrib adicionado com indTotTrib=0 (opSimpNac={op_simp_nac})")

    def limpa_espaco(elem):
        for node in elem.iter():
            if node.text:
                node.text = node.text.strip()
            if node.tail:
                node.tail = node.tail.strip()

    limpa_espaco(root)

    xml_puro_string = ET.tostring(
        root,
        encoding="utf-8",
        method="xml",
        xml_declaration=False,
    ).decode("utf-8")

    save_xml(xml_puro_string, f"dps_{ndps_str}")
    return xml_puro_string


def validateandsignxml(
    xml_string: str,
    kind: str = "dps",
    empresa_id: int | None = None,
    ambiente: str | None = None,
) -> dict:
    valid, errors = run_xsd_validation(xml_string, kind=kind)

    signed_xml = None
    pfx_path, pfx_pass = resolve_certificate_settings(empresa_id=empresa_id, ambiente=ambiente)

    reference_uri = None
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_string.encode("utf-8"), parser)
        infdps_node = root.xpath('//*[local-name()="infDPS"][@Id]')
        if infdps_node:
            infdps_id = infdps_node[0].get("Id")
            if infdps_id:
                reference_uri = f"#{infdps_id}"
    except Exception as exc:
        errors.append(f"Failed to extract infDPS ID: {exc}")
        valid = False

    if valid and pfx_path and pfx_pass is not None:
        try:
            signed_xml = sign_xml_enveloped(
                xml_string,
                pfx_path,
                pfx_pass,
                reference_uri=reference_uri,
            )
            save_xml(signed_xml, "dps_signed")
        except Exception as exc:
            errors.append(f"Signing error: {exc}")
            signed_xml = None
            valid = False
    elif valid and not pfx_path:
        errors.append("Certificado PFX nao localizado para a empresa/ambiente.")
        valid = False

    return {
        "valid": valid,
        "errors": errors or None,
        "signedxml": signed_xml,
    }


def build_emissao_json_payload(payload: dict, dps_xml_assinado: str) -> dict:
    xml_limpo = (dps_xml_assinado or "").strip().lstrip("\ufeff")
    if not xml_limpo:
        raise ValueError("XML DPS assinado esta vazio.")

    xml_bytes = xml_limpo.encode("utf-8")
    xml_gzip = gzip.compress(xml_bytes)
    xml_b64 = base64.b64encode(xml_gzip).decode("ascii")

    return {
        "ambiente": payload.get("ambiente"),
        "referencia": payload.get("hash_idempotencia") or buildidempotencyhash(payload),
        "dpsXmlGZipB64": xml_b64,
    }


def buildemissaojsonpayload(payload: dict, dpsxmlassinado: str) -> dict:
    return build_emissao_json_payload(payload, dpsxmlassinado)


def transmitiremissao(payload: dict, configuracao=None) -> dict:
    import requests

    ambiente = payload.get("ambiente") or getattr(configuracao, "ambiente", None)
    empresa_id = payload.get("empresa_id") or payload.get("empresaid")

    dps_xml = payload.get("xml_dps") or builddpsxml(payload)

    validation = validateandsignxml(
        dps_xml,
        kind="dps",
        empresa_id=empresa_id,
        ambiente=ambiente,
    )

    if not validation.get("valid"):
        logging.error("Falha na validacao antes do envio: %s", validation.get("errors"))
        return {
            "sucesso": False,
            "status": "REJEITADA_VALIDACAO",
            "situacao_fiscal": "REJEITADA",
            "protocolo": None,
            "numero_nfse": None,
            "codigo_verificacao": None,
            "chave_nfse": None,
            "xml_nfse": None,
            "payload_retorno": None,
            "mensagem": "Validacao XSD falhou antes do envio.",
            "errors": validation.get("errors"),
            "httpstatus": 400,
        }

    dps_xml_assinado = validation.get("signedxml")
    request_json_body = build_emissao_json_payload(payload, dps_xml_assinado)

    base_emissao = get_base_emissao(configuracao=configuracao, ambiente=ambiente)
    base_distribuicao = get_base_distribuicao(configuracao=configuracao, ambiente=ambiente)

    emission_candidates = candidate_emission_urls(base_emissao)
    request_url = emission_candidates[0] if emission_candidates else f"{base_emissao}/nfse"

    headers_json = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    cert_paths: list[str] = []

    try:
        pfx_path, pfx_pass = resolve_certificate_settings(empresa_id=empresa_id, ambiente=ambiente)
        cert = None
        if pfx_path:
            cert_pem, key_pem, cert_paths = prepare_mtls_from_pfx(pfx_path, pfx_pass)
            cert = (cert_pem, key_pem)

        response = requests.post(
            request_url,
            json=request_json_body,
            headers=headers_json,
            cert=cert,
            timeout=60,
            verify=os.environ.get("NFS_CA_BUNDLE") or True,
        )

        retorno = response_payload(response)
        mensagem = "Processado com sucesso." if response.ok else str(
            retorno.get("raw") if isinstance(retorno, dict) else retorno
        )

        return {
            "sucesso": response.ok,
            "status": (
                retorno.get("status") if isinstance(retorno, dict) else None
            ) or ("PROCESSADA" if response.ok else "ERRO_API"),
            "situacao_fiscal": (
                retorno.get("situacao_fiscal") if isinstance(retorno, dict) else None
            ) or ("AUTORIZADA" if response.ok else "REJEITADA"),
            "protocolo": retorno.get("protocolo") if isinstance(retorno, dict) else None,
            "numero_nfse": retorno.get("numero_nfse") if isinstance(retorno, dict) else None,
            "codigo_verificacao": retorno.get("codigo_verificacao") if isinstance(retorno, dict) else None,
            "chave_nfse": retorno.get("chaveAcesso") if isinstance(retorno, dict) else None,
            "xml_nfse": response.text if str(response.text or "").lstrip().startswith("<") else None,
            "payload_retorno": {
                "request_url": request_url,
                "request_content_type": headers_json["Content-Type"],
                "request_body": jsonsafe(request_json_body),
                "base_emissao": base_emissao,
                "base_distribuicao": base_distribuicao,
                "response_headers": dict(response.headers),
                "response_body": retorno,
            },
            "mensagem": mensagem,
            "errors": None,
            "httpstatus": response.status_code,
        }

    except requests.exceptions.SSLError as exc:
        return {
            "sucesso": False,
            "status": "ERRO_SSL",
            "situacao_fiscal": "PENDENTE",
            "protocolo": None,
            "numero_nfse": None,
            "codigo_verificacao": None,
            "chave_nfse": None,
            "xml_nfse": None,
            "payload_retorno": {
                "erro": str(exc),
                "request_url": request_url,
            },
            "mensagem": f"Falha SSL no transporte para o endpoint configurado: {exc}",
            "errors": [str(exc)],
            "httpstatus": 495,
        }

    except requests.exceptions.RequestException as exc:
        return {
            "sucesso": False,
            "status": "ERRO_TRANSPORTE",
            "situacao_fiscal": "PENDENTE",
            "protocolo": None,
            "numero_nfse": None,
            "codigo_verificacao": None,
            "chave_nfse": None,
            "xml_nfse": None,
            "payload_retorno": {
                "erro": str(exc),
                "request_url": request_url,
            },
            "mensagem": f"Falha no transporte para o endpoint configurado: {exc}",
            "errors": [str(exc)],
            "httpstatus": 503,
        }

    finally:
        for path in cert_paths:
            try:
                os.remove(path)
            except Exception:
                pass


def validate_ctrib_mun(codigo_ibge: str, ctribmun: str) -> tuple[bool, str]:
    """Valida o código de tributação municipal para o município."""
    if not ctribmun:
        return True, ""  # cTribMun é opcional
    
    try:
        from src.models import NfseCtribMunReferencia
    except ImportError:
        return True, ""  # Se não tiver o modelo, não valida
    
    try:
        ctribmun_ref = NfseCtribMunReferencia.query.filter_by(
            codigo_ibge=codigo_ibge,
            codigo_ctrib=ctribmun,
            ativo=True
        ).first()
        
        if not ctribmun_ref:
            return False, f"Código de tributação municipal {ctribmun} não encontrado para o município {codigo_ibge}"
        
        return True, ""
    except Exception as exc:
        logging.warning(f"Erro ao validar cTribMun: {exc}")
        return True, ""  # Em caso de erro, não bloqueia


# ============================================================================
# FUNÇÕES PARA EVENTO DE CANCELAMENTO DE NFS-e (e101101)
# ============================================================================

def buildeventocancelamentosubstituicao_xml(
    chave_nfse: str,
    codigo_motivo: str,
    descricao_motivo: str,
    chave_substituta: str,
    cnpj_prestador: str,
    versao_aplicativo: str = "LiveSun_v1.00",
    ambiente: str = "2",
) -> str:
    """
    Gera o XML do evento de cancelamento por substituição (e105102).
    
    Args:
        chave_nfse: Chave de acesso da NFS-e a ser cancelada (50 dígitos)
        codigo_motivo: Código do motivo do cancelamento
        descricao_motivo: Descrição do motivo
        chave_substituta: Chave de acesso da NFS-e substituta (50 dígitos)
        cnpj_prestador: CNPJ do prestador (14 dígitos)
        versao_aplicativo: Versão do aplicativo
        ambiente: Ambiente (1=Produção, 2=Homologação)
    
    Returns:
        XML do evento como string
    """
    import xml.etree.ElementTree as ET
    from datetime import datetime, timezone
    
    # Data/hora atual em UTC
    dh_proc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    dh_evento = dh_proc
    
    # ID do evento (59 caracteres): EVT + chave(50) + tipo_evento(6)
    tipo_evento = "105102"
    id_evento = f"EVT{chave_nfse}{tipo_evento}"
    
    # ID do pedido de registro (59 caracteres): PRE + chave(50) + tipo_evento(6)
    id_pedido = f"PRE{chave_nfse}{tipo_evento}"
    
    # Criar XML
    root = ET.Element("evento")
    root.set("xmlns", "http://www.sped.fazenda.gov.br/nfse")
    root.set("versao", "1.00")
    
    inf_evento = ET.SubElement(root, "infEvento")
    inf_evento.set("Id", id_evento)
    
    ET.SubElement(inf_evento, "verAplic").text = versao_aplicativo
    ET.SubElement(inf_evento, "ambGer").text = ambiente
    ET.SubElement(inf_evento, "nSeqEvento").text = "1"
    ET.SubElement(inf_evento, "dhProc").text = dh_proc
    ET.SubElement(inf_evento, "nDFe").text = "0"
    
    ped_reg_evento = ET.SubElement(inf_evento, "pedRegEvento")
    ped_reg_evento.set("versao", "1.00")
    
    inf_ped_reg = ET.SubElement(ped_reg_evento, "infPedReg")
    inf_ped_reg.set("Id", id_pedido)
    
    tp_amb = "1" if ambiente == "1" else "2"
    ET.SubElement(inf_ped_reg, "tpAmb").text = tp_amb
    ET.SubElement(inf_ped_reg, "verAplic").text = versao_aplicativo
    ET.SubElement(inf_ped_reg, "dhEvento").text = dh_evento
    ET.SubElement(inf_ped_reg, "CNPJAutor").text = cnpj_prestador
    ET.SubElement(inf_ped_reg, "chNFSe").text = chave_nfse
    
    # Evento e105102 - Cancelamento por Substituição
    e105102 = ET.SubElement(inf_ped_reg, "e105102")
    ET.SubElement(e105102, "xDesc").text = "Cancelamento de NFS-e por Substituicao"
    ET.SubElement(e105102, "cMotivo").text = codigo_motivo
    if descricao_motivo:
        ET.SubElement(e105102, "xMotivo").text = descricao_motivo
    ET.SubElement(e105102, "chSubstituta").text = chave_substituta
    
    # Placeholder para assinatura
    signature = ET.SubElement(root, "Signature")
    signature.set("xmlns", "http://www.w3.org/2000/09/xmldsig#")
    
    # Limpar espaços em branco
    def limpa_espaco(elem):
        for node in elem.iter():
            if node.text:
                node.text = node.text.strip()
            if node.tail:
                node.tail = node.tail.strip()
    
    limpa_espaco(root)
    
    xml_puro_string = ET.tostring(
        root,
        encoding="utf-8",
        method="xml",
        xml_declaration=False,
    ).decode("utf-8")
    
    save_xml(xml_puro_string, f"evento_cancelamento_substituicao_{chave_nfse}")
    return xml_puro_string


def buildeventocancelamento_xml(
    chave_nfse: str,
    cnpj_prestador: str,
    codigo_motivo: str = "1",
    descricao_motivo: str = "Erro na emissão",
    ambiente: str = "homologacao",
    versao_aplicativo: str = "LiveSun/1.0",
) -> str:
    """
    Gera o XML do evento de cancelamento de NFS-e (e101101).
    
    Args:
        chave_nfse: Chave de acesso da NFS-e a ser cancelada (50 dígitos)
        cnpj_prestador: CNPJ do prestador (14 dígitos)
        codigo_motivo: Código de justificativa do cancelamento (padrão: "1")
        descricao_motivo: Descrição do motivo do cancelamento
        ambiente: Ambiente (homologacao ou producao)
        versao_aplicativo: Versão do aplicativo
    
    Returns:
        XML do evento de cancelamento como string
    """
    ET.register_namespace("", NS_NFSE)
    ET.register_namespace("ds", NS_DS)
    
    def q(tag: str) -> str:
        return QName(NS_NFSE, tag)
    
    # Gerar ID do pedido de registro: PRE + 56 dígitos numéricos = 59 caracteres total
    # Padrão: PRE[0-9]{56} conforme XSD TSIdPedRefEvt
    # Usamos: PRE (3) + Chave de Acesso NFS-e (50) + Tipo do evento (6) = 59 caracteres
    tipo_evento = "101101"  # código numérico do evento (sem o "e")
    id_ped_reg = f"PRE{chave_nfse}{tipo_evento}"
    
    # Log para debug
    logger.error(f"[CANCELAMENTO DEBUG] chave_nfse length: {len(chave_nfse)}, chave_nfse: {chave_nfse}")
    logger.error(f"[CANCELAMENTO DEBUG] id_ped_reg length: {len(id_ped_reg)}, id_ped_reg: {id_ped_reg}")
    
    # Data/hora atual em UTC
    dh_evento = (datetime.now(timezone.utc) - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    dh_proc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    
    # Ambiente
    tp_amb = "2" if ambiente_homologacao(ambiente) else "1"
    
    # CNPJ do autor (prestador)
    cnpj_autor = only_digits(cnpj_prestador).zfill(14)[-14:]
    
    # Criar elemento raiz pedRegEvento
    root = ET.Element(q("pedRegEvento"), versao="1.00")
    
    # infPedReg com atributo Id conforme XSD
    inf_ped_reg = ET.SubElement(root, q("infPedReg"), Id=id_ped_reg)
    
    # tpAmb
    ET.SubElement(inf_ped_reg, q("tpAmb")).text = tp_amb
    
    # verAplic
    ET.SubElement(inf_ped_reg, q("verAplic")).text = versao_aplicativo
    
    # dhEvento (data/hora do evento)
    ET.SubElement(inf_ped_reg, q("dhEvento")).text = dh_evento
    
    # CNPJ do autor
    ET.SubElement(inf_ped_reg, q("CNPJAutor")).text = cnpj_autor
    
    # chNFSe (chave da NFS-e)
    ET.SubElement(inf_ped_reg, q("chNFSe")).text = chave_nfse
    
    # e101101 (evento de cancelamento)
    e101101 = ET.SubElement(inf_ped_reg, q("e101101"))
    
    # xDesc (descrição fixa)
    ET.SubElement(e101101, q("xDesc")).text = "Cancelamento de NFS-e"
    
    # cMotivo (código de justificativa)
    ET.SubElement(e101101, q("cMotivo")).text = codigo_motivo
    
    # xMotivo (descrição do motivo)
    ET.SubElement(e101101, q("xMotivo")).text = limpar_texto_xml(descricao_motivo)
    
    def limpa_espaco(elem):
        for node in elem.iter():
            if node.text:
                node.text = node.text.strip()
            if node.tail:
                node.tail = node.tail.strip()
    
    limpa_espaco(root)
    
    xml_puro_string = ET.tostring(
        root,
        encoding="utf-8",
        method="xml",
        xml_declaration=False,
    ).decode("utf-8")
    
    save_xml(xml_puro_string, f"evento_cancelamento_{chave_nfse}")
    return xml_puro_string


def validateandsignevento_xml(
    xml_string: str,
    empresa_id: int | None = None,
    ambiente: str | None = None,
) -> dict:
    """
    Valida e assina o XML de evento de cancelamento.
    
    Args:
        xml_string: XML do evento como string
        empresa_id: ID da empresa para buscar certificado
        ambiente: Ambiente (homologacao ou producao)
    
    Returns:
        Dict com valid, errors e signedxml
    """
    valid, errors = run_xsd_validation(xml_string, kind="pedRegEvento")
    
    signed_xml = None
    pfx_path, pfx_pass = resolve_certificate_settings(empresa_id=empresa_id, ambiente=ambiente)
    
    reference_uri = None
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_string.encode("utf-8"), parser)
        # Para evento, o ID está em infPedReg
        infpedreg_node = root.xpath('//*[local-name()="infPedReg"][@Id]')
        if infpedreg_node:
            infpedreg_id = infpedreg_node[0].get("Id")
            if infpedreg_id:
                reference_uri = f"#{infpedreg_id}"
    except Exception as exc:
        errors.append(f"Failed to extract infPedReg ID: {exc}")
        valid = False
    
    if valid and pfx_path and pfx_pass is not None:
        try:
            signed_xml = sign_xml_enveloped(
                xml_string,
                pfx_path,
                pfx_pass,
                reference_uri=reference_uri,
            )
            save_xml(signed_xml, "evento_cancelamento_signed")
        except Exception as exc:
            errors.append(f"Signing error: {exc}")
            signed_xml = None
            valid = False
    elif valid and not pfx_path:
        errors.append("Certificado PFX nao localizado para a empresa/ambiente.")
        valid = False
    
    return {
        "valid": valid,
        "errors": errors or None,
        "signedxml": signed_xml,
    }


def build_evento_json_payload(payload: dict, evento_xml_assinado: str) -> dict:
    """
    Constrói o payload JSON para transmissão do evento de cancelamento.
    
    Args:
        payload: Dict com dados do evento
        evento_xml_assinado: XML do evento assinado
    
    Returns:
        Dict com o payload JSON para a API
    """
    xml_limpo = (evento_xml_assinado or "").strip().lstrip("\ufeff")
    if not xml_limpo:
        raise ValueError("XML evento assinado esta vazio.")
    
    # Remover elemento nPedRegEvento se presente (não é aceito pela API)
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_limpo.encode("utf-8"), parser)
    npedreg_nodes = root.xpath('//*[local-name()="nPedRegEvento"]')
    for node in npedreg_nodes:
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)
            logger.info(f"[CANCELAMENTO] Removido elemento nPedRegEvento do XML assinado")
    
    xml_limpo = etree.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
    
    xml_bytes = xml_limpo.encode("utf-8")
    xml_gzip = gzip.compress(xml_bytes)
    xml_b64 = base64.b64encode(xml_gzip).decode("ascii")
    
    return {
        "pedidoRegistroEventoXmlGZipB64": xml_b64,
    }


def transmitireventocancelamentosubstituicao(
    chave_nfse: str,
    codigo_motivo: str,
    descricao_motivo: str,
    chave_substituta: str,
    configuracao=None,
) -> dict:
    """
    Transmite o evento de cancelamento por substituição (e105102) para a API NFS-e Nacional.
    
    Args:
        chave_nfse: Chave de acesso da NFS-e a ser cancelada (50 dígitos)
        codigo_motivo: Código do motivo do cancelamento
        descricao_motivo: Descrição do motivo
        chave_substituta: Chave de acesso da NFS-e substituta (50 dígitos)
        configuracao: Objeto de configuração da empresa
    
    Returns:
        Dict com resultado da transmissão
    """
    ambiente = getattr(configuracao, "ambiente", None) if configuracao else None
    empresa_id = getattr(configuracao, "empresa_id", None) if configuracao else None
    
    # Obter CNPJ do prestador da empresa
    empresa = Empresa.query.get(empresa_id) if empresa_id else None
    cnpj_prestador = empresa.cnpj if empresa else ""
    
    # Validar chaves
    chave_nfse = only_digits(chave_nfse)
    chave_substituta = only_digits(chave_substituta)
    cnpj_prestador = only_digits(cnpj_prestador)
    
    if len(chave_nfse) != 50:
        return {
            "sucesso": False,
            "status": "ERRO_VALIDACAO",
            "mensagem": f"Chave da NFS-e deve ter 50 dígitos. Recebido: {len(chave_nfse)}",
            "httpstatus": 400,
        }
    
    if len(chave_substituta) != 50:
        return {
            "sucesso": False,
            "status": "ERRO_VALIDACAO",
            "mensagem": f"Chave da NFS-e substituta deve ter 50 dígitos. Recebido: {len(chave_substituta)}",
            "httpstatus": 400,
        }
    
    if len(cnpj_prestador) != 14:
        return {
            "sucesso": False,
            "status": "ERRO_VALIDACAO",
            "mensagem": f"CNPJ do prestador deve ter 14 dígitos. Recebido: {len(cnpj_prestador)}",
            "httpstatus": 400,
        }
    
    # Gerar XML do evento
    evento_xml = buildeventocancelamentosubstituicao_xml(
        chave_nfse=chave_nfse,
        codigo_motivo=codigo_motivo,
        descricao_motivo=descricao_motivo,
        chave_substituta=chave_substituta,
        cnpj_prestador=cnpj_prestador,
        ambiente="1" if ambiente == "producao" else "2",
    )
    
    # Validar e assinar XML
    validation = validateandsignevento_xml(
        evento_xml,
        empresa_id=empresa_id,
        ambiente=ambiente,
    )
    
    if not validation.get("valid"):
        logging.error("Falha na validacao do evento antes do envio: %s", validation.get("errors"))
        return {
            "sucesso": False,
            "status": "REJEITADA_VALIDACAO",
            "situacao_fiscal": "REJEITADA",
            "protocolo": None,
            "mensagem": "Validacao XSD falhou antes do envio.",
            "errors": validation.get("errors"),
            "httpstatus": 400,
        }
    
    evento_xml_assinado = validation.get("signedxml")
    
    # Construir payload JSON
    payload = {
        "ambiente": ambiente,
        "chave_nfse": chave_nfse,
        "codigo_motivo": codigo_motivo,
        "descricao_motivo": descricao_motivo,
        "chave_substituta": chave_substituta,
    }
    request_json_body = build_evento_json_payload(payload, evento_xml_assinado)
    
    # Determinar endpoint
    base_emissao = get_base_emissao(configuracao=configuracao, ambiente=ambiente)
    
    # Para eventos, usar endpoint /nfse/{chaveAcesso}/eventos
    request_url = f"{base_emissao}/nfse/{chave_nfse}/eventos"
    
    headers_json = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    cert_paths: list[str] = []
    
    try:
        pfx_path, pfx_pass = resolve_certificate_settings(empresa_id=empresa_id, ambiente=ambiente)
        cert = None
        if pfx_path:
            cert_pem, key_pem, cert_paths = prepare_mtls_from_pfx(pfx_path, pfx_pass)
            cert = (cert_pem, key_pem)
        
        response = requests.post(
            request_url,
            headers=headers_json,
            json=request_json_body,
            cert=cert,
            timeout=60,
            verify=os.environ.get("NFS_CA_BUNDLE") or True,
        )
        
        logging.info(f"Resposta da API (cancelamento substituicao): {response.status_code} - {response.text[:500]}")
        
        if response.ok:
            retorno = response.json()
            return {
                "sucesso": True,
                "status": "AUTORIZADA",
                "situacao_fiscal": "CANCELADA_SUBSTITUICAO",
                "protocolo": retorno.get("protocolo"),
                "mensagem": "Cancelamento por substituição realizado com sucesso.",
                "payload_retorno": retorno,
                "httpstatus": response.status_code,
            }
        else:
            return {
                "sucesso": False,
                "status": "REJEITADA",
                "situacao_fiscal": "REJEITADA",
                "protocolo": None,
                "mensagem": f"Erro na transmissão: {response.status_code} - {response.text}",
                "httpstatus": response.status_code,
            }
        
    except requests.exceptions.SSLError as exc:
        return {
            "sucesso": False,
            "status": "ERRO_SSL",
            "situacao_fiscal": "ERRO",
            "protocolo": None,
            "mensagem": f"Falha SSL no transporte para o endpoint configurado: {exc}",
            "httpstatus": 495,
        }
        
    except requests.exceptions.RequestException as exc:
        return {
            "sucesso": False,
            "status": "ERRO_TRANSPORTE",
            "situacao_fiscal": "ERRO",
            "protocolo": None,
            "mensagem": f"Falha no transporte para o endpoint configurado: {exc}",
            "httpstatus": 503,
        }
        
    finally:
        for path in cert_paths:
            try:
                os.remove(path)
            except Exception:
                pass


def transmitireventocancelamento(
    chave_nfse: str,
    cnpj_prestador: str,
    codigo_motivo: str = "1",
    descricao_motivo: str = "Erro na emissão",
    configuracao=None,
) -> dict:
    """
    Transmite o evento de cancelamento de NFS-e para a API NFS-e Nacional.
    
    Args:
        chave_nfse: Chave de acesso da NFS-e a ser cancelada
        cnpj_prestador: CNPJ do prestador
        codigo_motivo: Código de justificativa do cancelamento
        descricao_motivo: Descrição do motivo do cancelamento
        configuracao: Objeto de configuração da empresa
    
    Returns:
        Dict com resultado da transmissão
    """
    import requests
    
    ambiente = configuracao.ambiente if configuracao else None
    empresa_id = configuracao.empresa_id if configuracao else None
    
    # Gerar XML do evento
    evento_xml = buildeventocancelamento_xml(
        chave_nfse=chave_nfse,
        cnpj_prestador=cnpj_prestador,
        codigo_motivo=codigo_motivo,
        descricao_motivo=descricao_motivo,
        ambiente=ambiente,
    )
    
    # Validar e assinar XML
    validation = validateandsignevento_xml(
        evento_xml,
        empresa_id=empresa_id,
        ambiente=ambiente,
    )
    
    if not validation.get("valid"):
        logging.error("Falha na validacao do evento antes do envio: %s", validation.get("errors"))
        return {
            "sucesso": False,
            "status": "REJEITADA_VALIDACAO",
            "situacao_fiscal": "REJEITADA",
            "protocolo": None,
            "mensagem": "Validacao XSD falhou antes do envio.",
            "errors": validation.get("errors"),
            "httpstatus": 400,
        }
    
    evento_xml_assinado = validation.get("signedxml")
    
    # Construir payload JSON
    payload = {
        "ambiente": ambiente,
        "chave_nfse": chave_nfse,
        "codigo_motivo": codigo_motivo,
        "descricao_motivo": descricao_motivo,
    }
    request_json_body = build_evento_json_payload(payload, evento_xml_assinado)
    
    # Determinar endpoint
    base_emissao = get_base_emissao(configuracao=configuracao, ambiente=ambiente)
    
    # Para eventos, usar endpoint /nfse/{chaveAcesso}/eventos
    request_url = f"{base_emissao}/nfse/{chave_nfse}/eventos"
    
    headers_json = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    cert_paths: list[str] = []
    
    try:
        pfx_path, pfx_pass = resolve_certificate_settings(empresa_id=empresa_id, ambiente=ambiente)
        cert = None
        if pfx_path:
            cert_pem, key_pem, cert_paths = prepare_mtls_from_pfx(pfx_path, pfx_pass)
            cert = (cert_pem, key_pem)
        
        response = requests.post(
            request_url,
            json=request_json_body,
            headers=headers_json,
            cert=cert,
            timeout=60,
            verify=os.environ.get("NFS_CA_BUNDLE") or True,
        )
        
        retorno = response_payload(response)
        
        # Log para debug do evento de cancelamento
        logging.error(f"[CANCELAMENTO DEBUG] URL: {request_url}")
        logging.error(f"[CANCELAMENTO DEBUG] Status: {response.status_code}")
        logging.error(f"[CANCELAMENTO DEBUG] Request Body: {jsonsafe(request_json_body)}")
        logging.error(f"[CANCELAMENTO DEBUG] Response Body: {retorno}")
        
        mensagem = "Processado com sucesso." if response.ok else str(
            retorno.get("raw") if isinstance(retorno, dict) else retorno
        )
        
        return {
            "sucesso": response.ok,
            "status": (
                retorno.get("status") if isinstance(retorno, dict) else None
            ) or ("PROCESSADA" if response.ok else "ERRO_API"),
            "situacao_fiscal": (
                retorno.get("situacao_fiscal") if isinstance(retorno, dict) else None
            ) or ("AUTORIZADA" if response.ok else "REJEITADA"),
            "protocolo": retorno.get("protocolo") if isinstance(retorno, dict) else None,
            "mensagem": mensagem,
            "errors": None,
            "httpstatus": response.status_code,
            "payload_retorno": {
                "request_url": request_url,
                "request_content_type": headers_json["Content-Type"],
                "request_body": jsonsafe(request_json_body),
                "response_headers": dict(response.headers),
                "response_body": retorno,
            },
        }
        
    except requests.exceptions.SSLError as exc:
        return {
            "sucesso": False,
            "status": "ERRO_SSL",
            "situacao_fiscal": "PENDENTE",
            "protocolo": None,
            "mensagem": f"Falha SSL no transporte para o endpoint configurado: {exc}",
            "errors": [str(exc)],
            "httpstatus": 495,
        }
        
    except requests.exceptions.RequestException as exc:
        return {
            "sucesso": False,
            "status": "ERRO_TRANSPORTE",
            "situacao_fiscal": "PENDENTE",
            "protocolo": None,
            "mensagem": f"Falha no transporte para o endpoint configurado: {exc}",
            "errors": [str(exc)],
            "httpstatus": 503,
        }
        
    finally:
        for path in cert_paths:
            try:
                os.remove(path)
            except Exception:
                pass


def consultar_nfse(
    chave_acesso: str,
    configuracao=None,
) -> dict:
    """
    Consulta uma NFS-e pela chave de acesso na API NFS-e Nacional.
    
    Args:
        chave_acesso: Chave de acesso da NFS-e (50 dígitos)
        configuracao: Objeto de configuração da empresa
    
    Returns:
        Dict com resultado da consulta
    """
    import requests
    import xml.etree.ElementTree as ET
    
    ambiente = getattr(configuracao, "ambiente", None) if configuracao else None
    empresa_id = getattr(configuracao, "empresa_id", None) if configuracao else None
    
    # Validar chave de acesso
    chave_acesso = only_digits(chave_acesso)
    if len(chave_acesso) != 50:
        return {
            "sucesso": False,
            "status": "ERRO_VALIDACAO",
            "mensagem": f"Chave de acesso deve ter 50 dígitos. Recebido: {len(chave_acesso)}",
            "xml_nfse": None,
            "httpstatus": 400,
        }
    
    # Determinar endpoint
    base_emissao = get_base_emissao(configuracao=configuracao, ambiente=ambiente)
    request_url = f"{base_emissao}/nfse/{chave_acesso}"
    
    headers_json = {
        "Accept": "application/xml",
    }
    
    cert_paths: list[str] = []
    
    try:
        pfx_path, pfx_pass = resolve_certificate_settings(empresa_id=empresa_id, ambiente=ambiente)
        cert = None
        if pfx_path:
            cert_pem, key_pem, cert_paths = prepare_mtls_from_pfx(pfx_path, pfx_pass)
            cert = (cert_pem, key_pem)
        
        response = requests.get(
            request_url,
            headers=headers_json,
            cert=cert,
            timeout=60,
            verify=os.environ.get("NFS_CA_BUNDLE") or True,
        )
        
        # Verificar se a resposta é XML
        xml_nfse = response.text if str(response.text or "").lstrip().startswith("<") else None
        
        return {
            "sucesso": response.ok,
            "status": "ENCONTRADA" if response.ok else "NAO_ENCONTRADA",
            "mensagem": "NFS-e encontrada com sucesso." if response.ok else f"Erro na consulta: {response.status_code}",
            "xml_nfse": xml_nfse,
            "httpstatus": response.status_code,
            "payload_retorno": {
                "request_url": request_url,
                "response_headers": dict(response.headers),
            },
        }
        
    except requests.exceptions.SSLError as exc:
        return {
            "sucesso": False,
            "status": "ERRO_SSL",
            "mensagem": f"Falha SSL no transporte para o endpoint configurado: {exc}",
            "xml_nfse": None,
            "dados_nfse": {},
            "httpstatus": 495,
        }
        
    except requests.exceptions.RequestException as exc:
        return {
            "sucesso": False,
            "status": "ERRO_TRANSPORTE",
            "mensagem": f"Falha no transporte para o endpoint configurado: {exc}",
            "xml_nfse": None,
            "dados_nfse": {},
            "httpstatus": 503,
        }
        
    finally:
        for path in cert_paths:
            try:
                os.remove(path)
            except Exception:
                pass