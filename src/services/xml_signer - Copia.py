# -*- coding: utf-8 -*-

import os
import re
import tempfile

from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from lxml import etree
from signxml import XMLSigner
from signxml.algorithms import SignatureConstructionMethod

XMLDSIG_NS = "http://www.w3.org/2000/09/xmldsig#"
NFSE_NS = "http://www.sped.fazenda.gov.br/nfse"


def _load_pfx(pfx_path: str, password: str | None):
    with open(pfx_path, "rb") as f:
        data = f.read()

    priv_key, cert, add_certs = load_key_and_certificates(
        data,
        password.encode("utf-8") if password else None,
    )

    if priv_key is None or cert is None:
        raise ValueError("PFX does not contain a private key and certificate")

    return priv_key, cert, list(add_certs or [])


def _retag_namespace(node, namespace_uri: str):
    local_name = etree.QName(node).localname
    node.tag = f"{{{namespace_uri}}}{local_name}"


def _normalizar_namespace_signature(xml_str: str) -> str:
    parser = etree.XMLParser(remove_blank_text=True, resolve_entities=False, no_network=True)
    root = etree.fromstring(xml_str.encode("utf-8"), parser)

    signature_nodes = root.xpath('//*[local-name()="Signature"]')
    if not signature_nodes:
        return xml_str

    sig = signature_nodes[0]

    ds_local_names = {
        "Signature",
        "SignedInfo",
        "CanonicalizationMethod",
        "SignatureMethod",
        "Reference",
        "Transforms",
        "Transform",
        "DigestMethod",
        "DigestValue",
        "SignatureValue",
        "KeyInfo",
        "X509Data",
        "X509Certificate",
        "X509IssuerSerial",
        "X509IssuerName",
        "X509SerialNumber",
    }

    for node in sig.iter():
        local_name = etree.QName(node).localname
        if local_name in ds_local_names:
            _retag_namespace(node, XMLDSIG_NS)

    root_local = etree.QName(root).localname
    new_root = etree.Element(
        f"{{{NFSE_NS}}}{root_local}",
        nsmap={None: NFSE_NS, "ds": XMLDSIG_NS},
    )

    for key, value in root.attrib.items():
        new_root.set(key, value)

    for child in list(root):
        new_root.append(child)

    return etree.tostring(
        new_root,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=False,
    ).decode("utf-8")


def sign_xml_enveloped(
    xml_string: str,
    pfx_path: str,
    pfx_password: str | None,
    reference_uri: str | None = None,
) -> str:
    priv_key, cert, add_certs = _load_pfx(pfx_path, pfx_password)

    parser = etree.XMLParser(
        remove_blank_text=True,
        resolve_entities=False,
        no_network=True,
    )
    root = etree.fromstring(xml_string.encode("utf-8"), parser)

    infdps_node = root.xpath('//*[local-name()="infDPS"][@Id]')
    if not infdps_node:
        raise ValueError("infDPS element with Id attribute not found")

    infdps_id = infdps_node[0].get("Id")
    if not infdps_id:
        raise ValueError("infDPS element does not have Id attribute")

    signer = XMLSigner(
        method=SignatureConstructionMethod.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
    )

    leaf_only = os.environ.get("NFS_SIGN_LEAF_ONLY", "0").strip() == "1"
    cert_chain = [cert] if leaf_only else ([cert] + add_certs)

    signed_root = signer.sign(
        root,
        key=priv_key,
        cert=cert_chain,
        reference_uri=reference_uri or f"#{infdps_id}",
        id_attribute="Id",
    )

    signed_xml = etree.tostring(
        signed_root,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=False,
    ).decode("utf-8")

    signed_xml = _normalizar_namespace_signature(signed_xml)

    def _wrap_x509(match):
        inner = match.group(2)
        cleaned = re.sub(r"\s+", "", inner)
        wrapped = "\n".join(
            cleaned[i:i + 64] for i in range(0, len(cleaned), 64)
        )
        return f"{match.group(1)}{wrapped}\n{match.group(3)}"

    if os.environ.get("NFS_SIGN_WRAP_X509", "1").strip() != "0":
        signed_xml = re.sub(
            r"(<ds:X509Certificate>)(.*?)(</ds:X509Certificate>)",
            _wrap_x509,
            signed_xml,
            flags=re.S,
        )

    try:
        td = tempfile.gettempdir()
        debug_signed_path = os.path.join(td, f"signed_dps_debug_{infdps_id}.xml")
        with open(debug_signed_path, "wb") as f:
            f.write(signed_xml.encode("utf-8"))

        cert_pem = cert.public_bytes(Encoding.PEM)
        key_pem = priv_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.PKCS8,
            NoEncryption(),
        )

        cert_path = os.path.join(td, f"tmp_debug_cert_{infdps_id}.pem")
        key_path = os.path.join(td, f"tmp_debug_key_{infdps_id}.pem")

        with open(cert_path, "wb") as f:
            f.write(cert_pem)

        with open(key_path, "wb") as f:
            f.write(key_pem)
    except Exception:
        pass

    return signed_xml