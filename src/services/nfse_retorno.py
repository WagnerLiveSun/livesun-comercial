"""Leitura local do retorno fiscal. Não transmite nem consulta documentos."""

import base64
import gzip
import json
import logging
import zlib
from xml.etree import ElementTree as ET


def decodificar_xml_nfse(valor):
    """Aceita XML autorizado puro, base64 ou gzip/base64; nunca aceita DPS."""
    if not isinstance(valor, str) or not valor.strip():
        return ""
    texto = valor.strip()
    try:
        if not texto.startswith("<"):
            bruto = base64.b64decode(texto, validate=True)
            if bruto[:2] == b"\x1f\x8b":
                bruto = gzip.decompress(bruto)
            texto = bruto.decode("utf-8-sig").strip()
        raiz = ET.fromstring(texto)
        if raiz.tag.rsplit("}", 1)[-1] != "NFSe":
            return ""
        if not any(n.tag.rsplit("}", 1)[-1] == "infNFSe" for n in raiz.iter()):
            return ""
        return texto
    except (ValueError, OSError, EOFError, zlib.error, ET.ParseError):
        return ""


def ler_retorno_nfse(payload=None, xml_nfse=None):
    """Normaliza identificadores, dando precedência ao XML autorizado."""
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (ValueError, TypeError):
            payload = {}
    payload = payload if isinstance(payload, dict) else {}
    corpo = payload.get("response_body")
    fontes = [corpo, payload] if isinstance(corpo, dict) else [payload]
    candidatos = [xml_nfse]
    for fonte in fontes:
        candidatos.extend(fonte.get(k) for k in ("xml_nfse", "nfseXmlGZipB64", "nfseXml", "xml"))
    xml = next((texto for candidato in candidatos
                if (texto := decodificar_xml_nfse(candidato))), "")

    def primeiro(*nomes):
        for fonte in fontes:
            for nome in nomes:
                valor = fonte.get(nome)
                if isinstance(valor, (str, int)) and str(valor).strip():
                    return str(valor).strip()
        return ""

    dados = {
        "xml_nfse": xml,
        "numero_nfse": primeiro("numero_nfse", "nNFSe"),
        "codigo_verificacao": primeiro("codigo_verificacao", "codigoVerificacao", "cNFSe"),
        "chave_nfse": primeiro("chave_nfse", "chaveAcesso", "chave"),
    }
    if xml:
        raiz = ET.fromstring(xml)
        inf = next(n for n in raiz.iter() if n.tag.rsplit("}", 1)[-1] == "infNFSe")

        def texto(*nomes):
            return next(((n.text or "").strip() for n in inf.iter()
                         if n.tag.rsplit("}", 1)[-1] in nomes and (n.text or "").strip()), "")

        for campo, nomes in (
            ("numero_nfse", ("nNFSe",)),
            ("codigo_verificacao", ("cNFSe", "codigoVerificacao")),
            ("chave_nfse", ("chaveAcesso", "chave")),
        ):
            valor = texto(*nomes)
            if valor:
                if dados[campo] and dados[campo] != valor:
                    logging.warning("Divergência em %s do retorno NFS-e; prevalece o XML autorizado.", campo)
                dados[campo] = valor
        identificador = inf.get("Id", "")
        if not dados["chave_nfse"] and identificador.startswith("NFS"):
            chave = identificador[3:]
            if len(chave) == 50 and chave.isdigit():
                dados["chave_nfse"] = chave
    return dados


def atualizar_identificadores_nfse(emissao, payload=None, xml_nfse=None):
    """Atualiza somente dados recuperados; transação fica a cargo do chamador."""
    dados = ler_retorno_nfse(
        payload if payload is not None else emissao.payload_retorno,
        xml_nfse if xml_nfse is not None else emissao.xml_nfse,
    )
    alterou = False
    for campo, valor in dados.items():
        if valor and getattr(emissao, campo, None) != valor:
            setattr(emissao, campo, valor)
            alterou = True
    return alterou