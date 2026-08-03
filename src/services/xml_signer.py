# -*- coding: utf-8 -*-

import os
import re
import tempfile
import base64
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from lxml import etree

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


class SHA1XMLSigner:
    """Subclass of XMLSigner that allows SHA1 by bypassing the weak digest check."""
    pass


def _canonicalize_xml(element):
    """Canonicalize XML using EXCL_C14N"""
    return etree.tostring(
        element,
        method="c14n",
        exclusive=True,
        with_comments=False
    )


def _calculate_digest(data):
    """Calculate SHA1 digest"""
    return base64.b64encode(hashlib.sha1(data).digest()).decode("utf-8")


def sign_xml_enveloped(
    xml_string: str,
    pfx_path: str,
    pfx_password: str | None,
    reference_uri: str | None = None,
) -> str:
    """Assina um documento XML usando SHA1 (exigido pela SEFIN) com implementação manual."""
    priv_key, cert, add_certs = _load_pfx(pfx_path, pfx_password)

    parser = etree.XMLParser(
        remove_blank_text=True,
        resolve_entities=False,
        no_network=True,
    )
    root = etree.fromstring(xml_string.encode("utf-8"), parser)

    # Verificar se é evento (infPedReg) ou emissão (infDPS)
    infpedreg_node = root.xpath('//*[local-name()="infPedReg"][@Id]')
    infdps_node = root.xpath('//*[local-name()="infDPS"][@Id]')
    
    if infpedreg_node:
        # É um evento de cancelamento
        target_node = infpedreg_node[0]
        target_id = infpedreg_node[0].get("Id")
        if not target_id:
            raise ValueError("infPedReg element does not have Id attribute")
    elif infdps_node:
        # É uma emissão de NFS-e
        target_node = infdps_node[0]
        target_id = infdps_node[0].get("Id")
        if not target_id:
            raise ValueError("infDPS element does not have Id attribute")
    else:
        raise ValueError("Neither infPedReg nor infDPS element with Id attribute found")

    # Canonicalize target element
    target_canonical = _canonicalize_xml(target_node)
    
    # Calculate digest
    digest_value = _calculate_digest(target_canonical)
    
    # Create signature element
    signature = etree.Element(f"{{{XMLDSIG_NS}}}Signature", nsmap={None: XMLDSIG_NS})
    
    # SignedInfo
    signed_info = etree.SubElement(signature, f"{{{XMLDSIG_NS}}}SignedInfo")
    
    # CanonicalizationMethod
    canonicalization_method = etree.SubElement(signed_info, f"{{{XMLDSIG_NS}}}CanonicalizationMethod")
    canonicalization_method.set("Algorithm", "http://www.w3.org/2001/10/xml-exc-c14n#")
    
    # SignatureMethod
    signature_method = etree.SubElement(signed_info, f"{{{XMLDSIG_NS}}}SignatureMethod")
    signature_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1")
    
    # Reference
    reference = etree.SubElement(signed_info, f"{{{XMLDSIG_NS}}}Reference")
    reference.set("URI", f"#{target_id}")
    
    # Transforms
    transforms = etree.SubElement(reference, f"{{{XMLDSIG_NS}}}Transforms")
    transform = etree.SubElement(transforms, f"{{{XMLDSIG_NS}}}Transform")
    transform.set("Algorithm", "http://www.w3.org/2001/10/xml-exc-c14n#")
    
    # DigestMethod
    digest_method = etree.SubElement(reference, f"{{{XMLDSIG_NS}}}DigestMethod")
    digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")
    
    # DigestValue
    digest_value_elem = etree.SubElement(reference, f"{{{XMLDSIG_NS}}}DigestValue")
    digest_value_elem.text = digest_value
    
    # Canonicalize SignedInfo
    signed_info_canonical = _canonicalize_xml(signed_info)
    
    # Sign the canonicalized SignedInfo
    signature_value = priv_key.sign(
        signed_info_canonical,
        padding.PKCS1v15(),
        hashes.SHA1()
    )
    signature_value_b64 = base64.b64encode(signature_value).decode("utf-8")
    
    # SignatureValue
    signature_value_elem = etree.SubElement(signature, f"{{{XMLDSIG_NS}}}SignatureValue")
    signature_value_elem.text = signature_value_b64
    
    # KeyInfo
    key_info = etree.SubElement(signature, f"{{{XMLDSIG_NS}}}KeyInfo")
    x509_data = etree.SubElement(key_info, f"{{{XMLDSIG_NS}}}X509Data")
    x509_certificate = etree.SubElement(x509_data, f"{{{XMLDSIG_NS}}}X509Certificate")
    
    # Get certificate in DER format
    cert_der = cert.public_bytes(Encoding.DER)
    cert_b64 = base64.b64encode(cert_der).decode("utf-8")
    
    # Wrap certificate at 64 characters
    cert_wrapped = "\n".join([cert_b64[i:i+64] for i in range(0, len(cert_b64), 64)])
    x509_certificate.text = cert_wrapped
    
    # Insert signature as child of root element (pedRegEvento or DPS), after the target element
    if infpedreg_node:
        # Para evento, inserir após infPedReg dentro do elemento pedRegEvento
        pedreg_node = root.xpath('//*[local-name()="pedRegEvento"]')
        if pedreg_node:
            pedreg_node[0].insert(1, signature)
        else:
            root.insert(1, signature)
    else:
        # Para DPS, inserir após infDPS
        root.insert(1, signature)
    
    # Get signed XML
    signed_xml = etree.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=False,
    ).decode("utf-8")
    
    # Remove namespace prefixes if present
    signed_xml = signed_xml.replace('<ds:', '<').replace('</ds:', '</')
    signed_xml = signed_xml.replace(' xmlns:ds=', ' xmlns=')

    return signed_xml