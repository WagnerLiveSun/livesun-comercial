import os
import time
import base64
import gzip
import tempfile
from pathlib import Path
from src.app import create_app
from src.services.nfse_nacional import transmitir_emissao, build_idempotency_hash


def build_payload():
    ndps_unico = str(int(time.time()) % 1000000)
    payload = {
        "ambiente": "producao",
        "numero_interno": "REPRO-ASSINATURA-001",
        "numero_dps": ndps_unico,
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
    payload["hash_idempotencia"] = build_idempotency_hash(payload)
    return payload


def main():
    app = create_app()
    with app.app_context():
        payload = build_payload()
        result = transmitir_emissao(payload, configuracao=None)
        print("HTTP:", result.get("http_status"))
        print("STATUS:", result.get("status"))
        print("SUCESSO:", result.get("sucesso"))
        print("MENSAGEM:", result.get("mensagem"))
        payload_retorno = result.get("payload_retorno") or {}
        print("REQUEST_URL:", payload_retorno.get("request_url"))
        response_body = payload_retorno.get("response_body")
        if isinstance(response_body, dict):
            print("RESPONSE_BODY:", response_body)
        else:
            print("RESPONSE_BODY_TYPE:", type(response_body).__name__)

        # Diagnostics: compare XML actually sent (gzip+b64 payload) with signed debug file
        try:
            request_body = payload_retorno.get("request_body") or {}
            b64 = request_body.get("dpsXmlGZipB64")
            if b64:
                sent_xml = gzip.decompress(base64.b64decode(b64)).decode("utf-8")
                sent_path = Path(tempfile.gettempdir()) / "sent_xml_from_payload.xml"
                sent_path.write_bytes(sent_xml.encode("utf-8"))
                debug_candidates = sorted(
                    Path(tempfile.gettempdir()).glob("signed_dps_debug_*.xml"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                print("SENT_XML_PATH:", str(sent_path))
                if debug_candidates:
                    debug_path = debug_candidates[0]
                    print("DEBUG_XML_PATH:", str(debug_path))
                    debug_xml = debug_path.read_text(encoding="utf-8")
                    print("SENT_EQ_DEBUG:", sent_xml == debug_xml)
                    print("SENT_LEN:", len(sent_xml), "DEBUG_LEN:", len(debug_xml))
                else:
                    print("DEBUG_XML_NOT_FOUND")
        except Exception as exc:
            print("DIAG_ERROR:", str(exc))


if __name__ == "__main__":
    main()
