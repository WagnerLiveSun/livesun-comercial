"""Script de exemplo: gera DPS, valida XSD (opcional), assina (opcional) e emite em modo simulado.

Uso:
 python scripts/emitir_nfs_simulado.py

Opções: editar as variáveis `SCHEMA_XSD`, `PFX_PATH` e `PFX_PASS` abaixo para testar validação e assinatura.
"""
import os
from src.services.nfse_nacional import build_dps_xml, transmitir_emissao
from src.services.nfse_nacional import build_idempotency_hash

SCHEMA_XSD = os.environ.get("NFS_SCHEMA_XSD")  # caminho para XSD (opcional)
PFX_PATH = os.environ.get("NFS_PFX_PATH")  # caminho para pfx (opcional)
PFX_PASS = os.environ.get("NFS_PFX_PASS")  # senha do pfx (opcional)


def example_payload():
    payload = {
        "ambiente": "homologacao",
        "numero_interno": "TEST-0001",
        "empresa_id": 1,
        "empresa_nome": "Empresa de Teste LTDA",
        "empresa_cnpj": "12345678000199",
        "inscricao_municipal": "123456",
        "empresa_endereco_rua": "Rua Teste",
        "empresa_endereco_numero": "100",
        "empresa_endereco_bairro": "Centro",
        "empresa_endereco_cep": "01001000",
        "codigo_municipio": "3550308",
        "regime_tributario": "NORMAL",
        "tomador_id": 1,
        "tomador_nome": "Cliente Teste",
        "tomador_documento": "98765432100",
        "tomador_tipo": "PF",
        "servico_id": 1,
        "servico_codigo_interno": "SVC-001",
        "servico_codigo_nacional": "10101",
        "servico_nbs": "1234",
        "servico_descricao": "Serviço de teste",
        "valor_servico": "100.00",
        "valor_deducoes": "0.00",
        "valor_iss": "2.00",
    }
    payload["hash_idempotencia"] = build_idempotency_hash(payload)
    return payload


def main():
    payload = example_payload()
    dps_xml = build_dps_xml(payload)

    print("--- DPS (sem assinatura) ---")
    print(dps_xml[:2000])

    # validação XSD (se informado)
    if SCHEMA_XSD:
        from src.services.nfse_validation import validate_xml

        ok, errors = validate_xml(dps_xml, SCHEMA_XSD)
        print(f"XSD validation: {ok}")
        if errors:
            print("Errors:")
            for e in errors:
                print(" -", e)

    # assinatura (se informado)
    signed_xml = dps_xml
    if PFX_PATH and PFX_PASS is not None:
        from src.services.xml_signer import sign_xml_enveloped

        signed_xml = sign_xml_enveloped(dps_xml, PFX_PATH, PFX_PASS)
        print("--- DPS assinado (preview) ---")
        print(signed_xml[:2000])

    # emitir (modo simulado quando configuracao is None)
    resultado = transmitir_emissao(payload, configuracao=None)
    print("--- Resultado de emissão (simulado) ---")
    print(resultado)


if __name__ == "__main__":
    main()
