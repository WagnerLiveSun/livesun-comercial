import os
import time
import requests
from lxml import etree
from signxml import XMLSigner
from signxml.algorithms import SignatureConstructionMethod

from src.app import create_app
from src.services.nfse_nacional import (
    builddpsxml,
    buildidempotencyhash,
    resolvecertificatesettings,
    preparemtlsfrompfx,
    buildemissaojsonpayload,
    getbaseemissao,
    candidateemissionurls,
)
from src.services.xml_signer import sign_xml_enveloped, _load_pfx, _normalizar_namespace_signature


def payload_base(numero_dps: str):
    payload = {
        "ambiente": "producao",
        "numero_interno": f"REPRO-VAR-{numero_dps}",
        "numero_dps": numero_dps,
        "empresa_id": 1,
        "empresa_nome": "LIVESUN LTDA",
        "empresa_cnpj": "27907386000176",
        "inscricao_municipal": "1057760-8",
        "empresa_endereco_rua": "RUA TESTE",
        "empresa_endereco_numero": "100",
        "empresa_endereco_bairro": "CENTRO",
        "empresa_endereco_cep": "20000000",
        "codigo_municipio": "3304557",
        "regime_tributario": "NORMAL",
        "tomador_nome": "Wagner",
        "tomador_documento": "00941812766",
        "servico_codigo_nacional": "170202",
        "servico_nbs": "118064000",
        "servico_descricao": "Prestação de serviços de apoio administrativo no esclarecimento de dúvidas operacionais, parametrização de rotinas internas e suporte ao usuário no fluxo de processos de sistemas de escritório.",
        "valor_servico": "2.00",
        "valor_deducoes": "0.00",
        "valor_iss": "0.00",
        "tpRetISSQN": "1",
        "tribISSQN": "1",
    }
    payload["hash_idempotencia"] = buildidempotencyhash({**payload, "nonce": time.time_ns()})
    return payload


def sign_raw(xml_string: str, pfx_path: str, pfx_password: str, leaf_only: bool, normalize: bool, wrap64: bool):
    priv_key, cert, add_certs = _load_pfx(pfx_path, pfx_password)
    parser = etree.XMLParser(remove_blank_text=True, resolve_entities=False, no_network=True)
    root = etree.fromstring(xml_string.encode("utf-8"), parser)
    inf = root.xpath('//*[local-name()="infDPS"][@Id]')[0]
    inf_id = inf.get("Id")

    signer = XMLSigner(
        method=SignatureConstructionMethod.enveloped,
        signature_algorithm='rsa-sha1',
        digest_algorithm='sha1',
        c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#WithComments',
    )
    certs = [cert] if leaf_only else ([cert] + add_certs)
    signed_root = signer.sign(
        root,
        key=priv_key,
        cert=certs,
        reference_uri=f'#{inf_id}',
        id_attribute='Id',
    )
    signed_xml = etree.tostring(signed_root, encoding='utf-8', xml_declaration=True, pretty_print=False).decode('utf-8')

    if normalize:
        signed_xml = _normalizar_namespace_signature(signed_xml)

    if wrap64:
        import re
        def _wrap_x509(match):
            inner = match.group(2)
            cleaned = re.sub(r'\s+', '', inner)
            wrapped = '\n'.join([cleaned[i:i+64] for i in range(0, len(cleaned), 64)])
            return f"{match.group(1)}{wrapped}\n{match.group(3)}"
        signed_xml = re.sub(r'(<X509Certificate>)(.*?)(</X509Certificate>)', _wrap_x509, signed_xml, flags=re.S)

    return signed_xml


def send_signed_xml(signed_xml: str, idempotency: str):
    pfx_path, pfx_pass = resolvecertificatesettings(empresa_id=1, ambiente='producao')
    cert_path, key_path, temp_paths = preparemtlsfrompfx(pfx_path, pfx_pass)
    try:
        base = getbaseemissao(ambiente='producao')
        url = candidateemissionurls(base)[0]
        body = buildemissaojsonpayload({}, signed_xml)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/xml, application/json, text/xml, text/plain',
            'X-Idempotency-Key': idempotency,
            'X-NFSe-Layout-Version': '1.0',
        }
        resp = requests.post(url, json=body, headers=headers, timeout=30, cert=(cert_path, key_path), verify=True)
        return resp.status_code, resp.text
    finally:
        for p in temp_paths:
            try:
                os.remove(p)
            except Exception:
                pass


def main():
    app = create_app()
    with app.app_context():
        pfx_path, pfx_pass = resolvecertificatesettings(empresa_id=1, ambiente='producao')

        variants = [
            ("current", lambda xml: sign_xml_enveloped(xml, pfx_path, pfx_pass)),
            ("raw_fullchain", lambda xml: sign_raw(xml, pfx_path, pfx_pass, leaf_only=False, normalize=False, wrap64=False)),
            ("raw_leaf", lambda xml: sign_raw(xml, pfx_path, pfx_pass, leaf_only=True, normalize=False, wrap64=False)),
            ("normalized_nowrap", lambda xml: sign_raw(xml, pfx_path, pfx_pass, leaf_only=False, normalize=True, wrap64=False)),
        ]

        seed = int(time.time()) % 1000000
        for idx, (name, signer_fn) in enumerate(variants, start=1):
            numero_dps = str(seed + idx)
            payload = payload_base(numero_dps)
            unsigned = builddpsxml(payload)
            signed = signer_fn(unsigned)
            status, text = send_signed_xml(signed, payload["hash_idempotencia"] + f"-{name}")
            print(f"[{name}] status={status}")
            print(text[:600])
            print("-" * 80)


if __name__ == '__main__':
    main()
