import io

path = r"d:\App_LiveSun\LiveSun_Comercial_X\src\routes\nfse_nacional.py"
with io.open(path, "r", encoding="utf-8") as f:
    text = f.read()

start_marker = "def emissao_imprimir_danfs(emissao_id: int):"
end_marker = 'return render_template("nfse_nacional/danfs_print.html", emissao=emissao, empresa=empresa, qr_code_url=qr_code_url)'

si = text.index(start_marker)
ei = text.index(end_marker, si) + len(end_marker)

new_fn = (
    "def emissao_imprimir_danfs(emissao_id: int):\n"
    "    emissao = scoped_get_or_404(NfseNacionalEmissao, emissao_id)\n"
    "    empresa, qr_img_url = _preparar_danfs(emissao)\n"
    "    chave = emissao.chave_nfse\n"
    "    return render_template(\n"
    "        \"nfse_nacional/danfs_print.html\",\n"
    "        emissao=emissao,\n"
    "        empresa=empresa,\n"
    "        qr_code_url=chave,\n"
    "        qr_img_url=qr_img_url,\n"
    "    )"
)

new_text = text[:si] + new_fn + text[ei:]
with io.open(path, "w", encoding="utf-8") as f:
    f.write(new_text)

print("REPLACED_OK - _refactor_imprimir_tmp.py:31", len(text), len(new_text))