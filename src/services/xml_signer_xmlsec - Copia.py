from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import xmlsec
import base64
import tempfile
import os


def _load_pfx(pfx_path: str, password: str):
    with open(pfx_path, "rb") as f:
        data = f.read()
    priv_key, cert, add_certs = load_key_and_certificates(data, password.encode() if password else None)
    if priv_key is None or cert is None:
        raise ValueError("PFX does not contain a private key and certificate")
    return priv_key, cert, add_certs


def sign_xml_enveloped(xml_string: str, pfx_path: str, pfx_password: str, reference_uri: str | None = None) -> str:
    """Sign an XML document using SHA1 (required by SEFIN) with xmlsec library."""
    priv_key, cert, add_certs = _load_pfx(pfx_path, pfx_password)
    
    # Create temporary files for xmlsec
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as xml_file:
        xml_file.write(xml_string)
        xml_path = xml_file.name
    
    try:
        # Create temporary files for key and cert
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pem', delete=False) as key_file:
            key_pem = priv_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption(),
            )
            key_file.write(key_pem)
            key_path = key_file.name
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pem', delete=False) as cert_file:
            cert_pem = cert.public_bytes(Encoding.PEM)
            cert_file.write(cert_pem)
            cert_path = cert_file.name
        
        # Load XML
        root = xmlsec.parse_file(xml_path)
        
        # Create signature template
        sign = xmlsec.template.create(
            root,
            xmlsec.Transform.EXCL_C14N,
            xmlsec.Transform.RSA_SHA1,
            ns="ds"
        )
        
        # Add KeyInfo
        key_info = xmlsec.template.ensure_key_info(sign)
        x509_data = xmlsec.template.add_x509_data(key_info)
        xmlsec.template.x509_data_add_certificate(x509_data)
        
        # Create signing context
        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_file(key_path, xmlsec.KeyFormat.PEM)
        
        # Load certificate
        ctx.key.load_cert_from_file(cert_path, xmlsec.KeyFormat.PEM)
        
        # Sign the XML
        ctx.sign(sign)
        
        # Get signed XML
        signed_xml = xmlsec.tree_to_string(root)
        
        # Remove namespace prefixes if present
        signed_xml = signed_xml.replace('<ds:', '<').replace('</ds:', '</')
        signed_xml = signed_xml.replace(' xmlns:ds=', ' xmlns=')
        
        # Ensure correct namespace
        if 'xmlns="http://www.w3.org/2000/09/xmldsig#"' not in signed_xml:
            signed_xml = signed_xml.replace(
                '<Signature',
                '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#"',
                1
            )
        
        return signed_xml
        
    finally:
        # Clean up temporary files
        for path in [xml_path, key_path, cert_path]:
            try:
                os.unlink(path)
            except:
                pass
