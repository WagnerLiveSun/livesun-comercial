"""Script auxiliar: gera DPS, valida com XSDs oficiais e assina com PFX (se configurado).

Uso:
  python scripts/validate_and_sign_nfse.py

Configure via variáveis de ambiente:
  NFS_SCHEMA_XSD  -> caminho para NFSe_v1.00.xsd ou DPS_v1.00.xsd
  NFS_PFX_PATH    -> caminho para .pfx/.p12
  NFS_PFX_PASS    -> senha do pfx
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app import create_app
from src.services.nfse_nacional import build_dps_xml, build_idempotency_hash, validate_and_sign


def example_payload():
    payload = {
        "ambiente": "homologacao",
        "numero_interno": "TEST-0001",
        "empresa_id": 1,
        "empresa_nome": "Empresa de Teste LTDA",
        "empresa_cnpj": "12345678000199",
        "empresa_endereco_rua": "Rua Teste",
        "empresa_endereco_numero": "123",
        "empresa_endereco_bairro": "Centro",
        "empresa_endereco_cep": "01310-100",
        "inscricao_municipal": "123456",
        "codigo_municipio": "3550308",
        "regime_tributario": "NORMAL",
        "tomador_id": 1,
        "tomador_nome": "Cliente Teste",
        "tomador_documento": "98765432100",
        "tomador_tipo": "PF",
        "servico_id": 1,
        "servico_codigo_interno": "SVC-001",
        "servico_codigo_nacional": "100101",
        "servico_nbs": "10101",
        "servico_descricao": "Agenciamento, corretagem ou intermediação de câmbio",
        "valor_servico": "100.00",
        "valor_deducoes": "0.00",
        "valor_iss": "2.00",
    }
    payload["hash_idempotencia"] = build_idempotency_hash(payload)
    return payload


def main():
    app = create_app()
    with app.app_context():
        payload = example_payload()
        dps_xml = build_dps_xml(payload)
        print('--- DPS (preview) ---')
        print(dps_xml[:2000])

        res = validate_and_sign(dps_xml, kind='dps')
        print('\nValidation result:', res.get('valid'))
        if res.get('errors'):
            print('Errors:')
            for e in res.get('errors'):
                print(' -', e)

        if res.get('signed_xml'):
            print('\nSigned XML preview:')
            print(res.get('signed_xml')[:2000])
            with open('nfse_signed_preview.xml', 'w', encoding='utf-8') as f:
                f.write(res.get('signed_xml'))
            print('\nSigned XML saved to nfse_signed_preview.xml')


if __name__ == '__main__':
    main()
