Resumo do trabalho — Correções de assinatura SEFIN (NFS-e)
=====================================================

Objetivo
--------
- Corrigir rejeições SEFIN (E0714 / E1229 / E0237) e produzir o XML DPS assinado exatamente como foi enviado.
- Deixar claro o que foi alterado e onde outro agente pode continuar (próximo passo: fallback para xmlsec).

O que foi feito
---------------
- Ajustes no signer para forçar algoritmos e canonicalização exigidos pela SEFIN:
  - `SignatureMethod`: `rsa-sha1`
  - `DigestMethod`: `sha1`
  - Canonicalization: `http://www.w3.org/2001/10/xml-exc-c14n#WithComments`
- Extração do `Id` de `infDPS` e uso como `reference_uri="#DPS..."`.
- Normalização do namespace da tag `<Signature>` e formatação de `<X509Certificate>` (remover espaços e quebrar em 64 caracteres) para obter reproducibilidade byte-a-byte.
- Dump de artefatos de debug em binário para preservar LFs: `signed_dps_debug_<Id>.xml`, `tmp_debug_cert_<Id>.pem`, `tmp_debug_key_<Id>.pem` (diretório temporário do sistema).
- Scripts de inspeção e reprodução adicionados para regenerar assinaturas e comparar com o XML real enviado.

Arquivos alterados / relevantes
------------------------------
- Handler de assinatura (principal): [src/services/xml_signer.py](src/services/xml_signer.py)
- Fluxo de validação / envio: [src/services/nfse_nacional.py](src/services/nfse_nacional.py)
- Scripts de investigação / execução:
  - [scripts/regen_sign_and_diff.py](scripts/regen_sign_and_diff.py)
  - [scripts/emitir_nfs_producao_repro.py](scripts/emitir_nfs_producao_repro.py)
  - [scripts/test_signature_variants.py](scripts/test_signature_variants.py)
  - [scripts/test_mtls_send.py](scripts/test_mtls_send.py)
  - [scripts/verify_signed.py](scripts/verify_signed.py)

Onde olhar / artefatos gerados
------------------------------
- Arquivos de debug (temp dir): `signed_dps_debug_<Id>.xml`, `tmp_debug_cert_<Id>.pem`, `tmp_debug_key_<Id>.pem`.
- Arquivo extraído do tráfego que usamos como referência: `tmp_extracted_sent_request.xml` (local no repo/tmp ou tmp do sistema — procurar por este nome nos testes).

Como reproduzir localmente
-------------------------
1) Ative o ambiente virtual e rode o script de regeneração/diff (assume `.venv`):

```powershell
Set-Location 'D:\App_LiveSun\LiveSun_Comercial'
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe scripts\regen_sign_and_diff.py
```

2) Para tentar um envio de produção de teste (cuidado: evita spam — execute apenas 1 vez):

```powershell
Set-Location 'D:\App_LiveSun\LiveSun_Comercial'
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe scripts\emitir_nfs_producao_repro.py
```

Checks úteis antes de implementar xmlsec
-------------------------------------
- Verificar se o binding Python `xmlsec` está disponível:

```powershell
python -c "import xmlsec; print(xmlsec.__version__)"
```

- Verificar se o binário `xmlsec1` está no PATH (Windows):

```powershell
where xmlsec1
```

Próximos passos sugeridos (para o próximo agente)
-------------------------------------------------
1) Implementar fallback para `xmlsec` em `src/services/xml_signer.py`:
   - Preferir binding Python `xmlsec` se disponível (melhor compatibilidade com xmlsec1).
   - Se não houver binding, chamar `xmlsec1` via subprocess com arquivos temporários (entrada XML, key PEM, cert PEM) e capturar saída assinada.
   - Garantir que os algoritmos e c14n usados sejam equivalentes aos atuais (`rsa-sha1`, `sha1`, `Exclusive C14N WithComments`).
2) Testar apenas 1 envio em produção por tentativa e validar resposta JSON (não repetir automaticamente).
3) Se E0714 persistir, coletar (a) XML enviado (arquivo de payload salvo em `emitir_nfs_producao_repro.py`), (b) assinatura canônica do `SignedInfo`, (c) certificado apresentado e cadeia, e abrir com logs para a SEFIN.

Notas importantes
---------------
- Muitos erros observados são provocados por proxies/front-ends (IIS/ARR/WAF) que retornam 403/503 HTML — cuidado ao interpretar respostas não-JSON.
- A reprodução byte-a-byte já foi alcançada localmente para ao menos um DPS usando o signer atual; ainda assim a SEFIN retornou E0714 em produção em várias tentativas.
- Limitação de créditos: testar `xmlsec` binding é mais barato (apenas pip install) do que tentar serviços externos; use o binding local primeiro.

Contato/Contexto
----------------
Se precisar, o próximo agente deve revisar os scripts em `scripts/` e os logs de testes (terminal history). O ponto de entrada para reproduzir é o `scripts/regen_sign_and_diff.py`.

----
Gerado em 2026-06-01 por agente automático (resumo para continuidade).
