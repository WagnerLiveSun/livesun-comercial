# Teste do código alternativo nfse_nacional
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# nfse_nacional.py — BLOCO 1/4
import json
import logging
import requests
from datetime import datetime

try:
    from requests_pkcs12 import post as pkcs12_post, get as pkcs12_get
    PKCS12_DISPONIVEL = True
except ImportError:
    PKCS12_DISPONIVEL = False
    print("requests-pkcs12 não instalado. Execute: pip install requests-pkcs12")

logger = logging.getLogger(__name__)

# ── Configuração de ambiente ───────────────────────────────────────────────────
AMBIENTES = {
    "producao": {
        "url_base": "https://sefin.nfse.gov.br/SefinNacional",
        "tipo_ambiente": 1,
    },
    "homologacao": {
        "url_base": "https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional",
        "tipo_ambiente": 2,
    },
}

MODO_ENVIO    = os.getenv("NFS_MODO_ENVIO", "json").lower()      # "json" ou "xml"
DEBUG_CERT    = os.getenv("NFS_DEBUG_CERT", "0") == "1"
AMBIENTE_PADRAO = os.getenv("NFS_AMBIENTE", "homologacao")


def _resolver_ambiente(ambiente: str | None) -> dict:
    ambiente = (ambiente or AMBIENTE_PADRAO).lower()
    if ambiente not in AMBIENTES:
        raise ValueError(f"Ambiente inválido: {ambiente!r}. Use 'producao' ou 'homologacao'.")
    return {**AMBIENTES[ambiente], "nome": ambiente}


def _resolver_pfx(empresa_id: int, ambiente: str) -> tuple[str, str]:
    """Resolve o caminho e senha do PFX para a empresa/ambiente."""
    # Usa o mesmo caminho que o sistema atual
    base_dir = "uploads/nfse_certificados"
    sufixo   = "producao" if ambiente == "producao" else "homologacao"
    
    pfx_path = os.path.join(base_dir, str(empresa_id), sufixo)
    
    # Encontra o arquivo .pfx no diretório
    if os.path.isdir(pfx_path):
        for file in os.listdir(pfx_path):
            if file.endswith('.pfx'):
                pfx_path = os.path.join(pfx_path, file)
                break
        else:
            raise FileNotFoundError(f"Nenhum arquivo .pfx encontrado em {pfx_path}")
    else:
        raise FileNotFoundError(f"Diretório não encontrado: {pfx_path}")
    
    # Usa a senha padrão do sistema
    pfx_senha = ""  # O sistema atual usa senha vazia ou resolve de outra forma

    if DEBUG_CERT:
        logger.debug(f"[CERT] empresa_id={empresa_id} ambiente={ambiente} pfx_path={pfx_path!r}")

    if not os.path.isfile(pfx_path):
        raise FileNotFoundError(f"Certificado PFX não encontrado: {pfx_path!r}")

    return pfx_path, pfx_senha


# nfse_nacional.py — BLOCO 2/4
def _fazer_requisicao(method: str, url: str, pfx_path: str, pfx_senha: str,
                       headers: dict, body=None, timeout: int = 30) -> requests.Response:
    """Executa requisição mTLS via requests-pkcs12."""
    if not PKCS12_DISPONIVEL:
        raise RuntimeError(
            "requests-pkcs12 não instalado. Execute: pip install requests-pkcs12"
        )

    kwargs = dict(
        url=url,
        headers=headers,
        pkcs12_filename=pfx_path,
        pkcs12_password=pfx_senha,
        timeout=timeout,
        verify=True,
    )

    if body is not None:
        kwargs["data"] = body

    if DEBUG_CERT:
        logger.debug(f"[mTLS] {method.upper()} {url}")
        logger.debug(f"[mTLS] pfx_path={pfx_path!r}")
        logger.debug(f"[mTLS] headers={headers}")

    method = method.upper()
    if method == "POST":
        resp = pkcs12_post(**kwargs)
    elif method == "GET":
        resp = pkcs12_get(**kwargs)
    else:
        raise ValueError(f"Método HTTP não suportado: {method}")

    return resp


def _montar_payload_json(xml_assinado: str) -> str:
    """Monta o envelope JSON exigido pela Sefin Nacional."""
    return json.dumps({"dps_xml": xml_assinado}, ensure_ascii=False)


def _log_retorno(resp: requests.Response, operacao: str) -> dict:
    """Formata o retorno da API para debug e retorno ao ERP."""
    try:
        corpo = resp.json()
    except Exception:
        corpo = resp.text

    retorno = {
        "operacao": operacao,
        "status_http": resp.status_code,
        "url": resp.url,
        "payload_retorno": corpo,
        "headers_resposta": dict(resp.headers),
    }

    if resp.status_code >= 400:
        logger.warning(f"[NFS-e] {operacao} — HTTP {resp.status_code}: {corpo}")
    else:
        logger.info(f"[NFS-e] {operacao} — HTTP {resp.status_code} OK")

    return retorno


# nfse_nacional.py — BLOCO 3/4
def transmitir_emissao(
    xml_assinado: str,
    empresa_id: int,
    ambiente: str | None = None,
    timeout: int = 30,
) -> dict:
    """
    Transmite a DPS assinada para a Sefin Nacional via POST /nfse.

    Args:
        xml_assinado : XML da DPS já assinado com ICP-Brasil.
        empresa_id   : ID da empresa no ERP (para resolver certificado).
        ambiente     : 'producao' ou 'homologacao'. Padrão: NFS_AMBIENTE env.
        timeout      : Timeout HTTP em segundos.

    Returns:
        dict com status_http, payload_retorno, url, etc.
    """
    amb      = _resolver_ambiente(ambiente)
    pfx_path, pfx_senha = _resolver_pfx(empresa_id, amb["nome"])

    url_base = amb["url_base"].rstrip("/")
    url      = f"{url_base}/nfse"

    if MODO_ENVIO == "json":
        payload  = _montar_payload_json(xml_assinado)
        headers  = {
            "Content-Type": "application/json",
            "Accept":       "application/json",
        }
    else:
        payload  = xml_assinado.encode("utf-8")
        headers  = {
            "Content-Type": "application/xml; charset=UTF-8",
            "Accept":       "application/xml",
        }

    if DEBUG_CERT:
        logger.debug(f"[transmitir_emissao] url={url!r} modo={MODO_ENVIO} ambiente={amb['nome']}")
        logger.debug(f"[transmitir_emissao] payload (primeiros 500 chars): {payload[:500]}")

    resp = _fazer_requisicao("POST", url, pfx_path, pfx_senha, headers, payload, timeout)
    return _log_retorno(resp, "transmitir_emissao")


def main():
    """Teste básico das funções alternativas."""
    print("=== Teste do código alternativo nfse_nacional ===")
    
    # Teste 1: Resolução de ambiente
    try:
        amb = _resolver_ambiente("homologacao")
        print(f"✓ Ambiente resolvido: {amb}")
    except Exception as e:
        print(f"✗ Erro ao resolver ambiente: {e}")
    
    # Teste 2: Resolução de PFX
    try:
        pfx_path, pfx_senha = _resolver_pfx(1, "producao")
        print(f"✓ PFX resolvido: {pfx_path}")
        print(f"  Senha preenchida: {bool(pfx_senha)}")
    except Exception as e:
        print(f"✗ Erro ao resolver PFX: {e}")
    
    # Teste 3: Verificar se requests-pkcs12 está disponível
    print(f"✓ requests-pkcs12 disponível: {PKCS12_DISPONIVEL}")
    
    print("\n=== Teste concluído ===")


if __name__ == "__main__":
    main()
