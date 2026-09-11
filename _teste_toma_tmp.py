import sys, re
sys.stdout.reconfigure(encoding="utf-8")
from src.app import app

with app.app_context():
    from src.models import NfseNacionalEmissao
    e = NfseNacionalEmissao.query.filter(NfseNacionalEmissao.numero_nfse == "83").order_by(NfseNacionalEmissao.id.desc()).first()
    if e is None:
        e = NfseNacionalEmissao.query.get(83)
    print("emissao id:", e.id, "| numero:", e.numero_nfse, "| ambiente:", e.ambiente)
    xml = e.xml_dps or ""
    m = re.search(r"<toma>.*?</toma>", xml, re.S)
    print("BLOCO TOMA:", m.group(0) if m else "AUSENTE")
    print("tomador_id:", e.tomador_id)
    t = e.tomador
    if t:
        for f in ("nome", "cnpj_cpf", "inscricao_municipal", "endereco_logradouro", "endereco_numero",
                  "endereco_bairro", "endereco_cep", "codigo_municipio_ibge", "email", "telefone"):
            print(" ", f, "=", getattr(t, f, "<n/a>"))
