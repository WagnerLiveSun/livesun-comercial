# Teste da assinatura com xmlsec
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.xml_signer_xmlsec import sign_xml_enveloped
from src.services.nfse_nacional import build_dps_xml

def main():
    print("=== Teste de assinatura com xmlsec ===")
    
    # Usar XML de teste simples
    xml_string = '''<?xml version="1.0" encoding="UTF-8"?>
<DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">
  <infDPS Id="DPS355030821234567800019900001000000000000068">
    <tpAmb>1</tpAmb>
    <dhEmi>2026-05-29T23:00:00-03:00</dhEmi>
    <verAplic>LiveSun/1.0</verAplic>
    <serie>00001</serie>
    <nDPS>68</nDPS>
    <dCompet>2026-05-29</dCompet>
    <tpEmit>1</tpEmit>
    <cLocEmi>3550308</cLocEmi>
    <prest>
      <CNPJ>12345678000199</CNPJ>
      <regTrib>
        <opSimpNac>1</opSimpNac>
        <regEspTrib>0</regEspTrib>
      </regTrib>
    </prest>
    <toma>
      <CPF>98765432100</CPF>
      <xNome>Cliente Teste</xNome>
    </toma>
    <serv>
      <locPrest>
        <cLocPrestacao>3550308</cLocPrestacao>
      </locPrest>
      <cServ>
        <cTribNac>100101</cTribNac>
        <xDescServ>Agenciamento, corretagem ou intermediação de câmbio</xDescServ>
        <cNBS>000010101</cNBS>
      </cServ>
    </serv>
    <valores>
      <vServPrest>
        <vServ>100.00</vServ>
      </vServPrest>
      <trib>
        <tribMun>
          <tribISSQN>1</tribISSQN>
          <tpRetISSQN>2</tpRetISSQN>
        </tribMun>
        <totTrib>
          <indTotTrib>0</indTotTrib>
        </totTrib>
      </trib>
    </valores>
  </infDPS>
</DPS>'''
    
    print(f"✓ XML DPS gerado")
    
    # Assinar com xmlsec
    try:
        pfx_path = r"D:\App_LiveSun\LiveSun_Comercial\uploads\nfse_certificados\1\producao\27907386000176_up-leg-certificate_20260526192434.pfx"
        pfx_password = ""
        
        signed_xml = sign_xml_enveloped(xml_string, pfx_path, pfx_password)
        print(f"✓ XML assinado com xmlsec")
        
        # Verificar se tem assinatura
        if '<Signature' in signed_xml:
            print(f"✓ Assinatura encontrada no XML")
        else:
            print(f"✗ Assinatura não encontrada no XML")
        
        # Verificar prefixos
        if 'ds:' in signed_xml:
            print(f"✗ Prefixo ds: encontrado (deve ser removido)")
        else:
            print(f"✓ Prefixo ds: não encontrado (correto)")
        
        # Verificar namespace
        if 'xmlns="http://www.w3.org/2000/09/xmldsig#"' in signed_xml:
            print(f"✓ Namespace correto encontrado")
        else:
            print(f"✗ Namespace incorreto")
        
        # Mostrar preview
        print("\n=== Signed XML (preview) ===")
        print(signed_xml[:2000])
        
    except Exception as e:
        print(f"✗ Erro ao assinar XML: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
