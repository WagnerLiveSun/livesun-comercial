import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app import create_app
from src.services.nfse_nacional import build_dps_xml, validate_and_sign

app = create_app()
with app.app_context():
    payload = {
        'ambiente': 'producao',
        'empresa_id': 1,
        'empresa_nome': 'Empresa Teste',
        'empresa_cnpj': '12345678000199',
        'empresa_endereco_rua': 'Rua Teste',
        'empresa_endereco_numero': '123',
        'empresa_endereco_bairro': 'Centro',
        'empresa_endereco_cep': '01310-100',
        'codigo_municipio': '3550308',
        'tomador_nome': 'Cliente Teste',
        'tomador_documento': '98765432100',
        'servico_codigo_nacional': '100101',
        'servico_nbs': '10101',
        'servico_descricao': 'Agenciamento, corretagem ou intermediação de câmbio',
        'valor_servico': '100.00'
    }
    
    xml = build_dps_xml(payload)
    print('=== XML DPS ===')
    print(xml[:1000])
    print()
    
    # Verificar onde está o atributo Id
    if 'Id=' in xml:
        print('Atributo Id encontrado no XML')
        # Extrair o valor do Id
        import re
        id_match = re.search(r'Id="([^"]+)"', xml)
        if id_match:
            print(f'Valor do Id: {id_match.group(1)}')
    else:
        print('Atributo Id NÃO encontrado no XML')
    print()
    
    res = validate_and_sign(xml, kind='dps', empresa_id=1, ambiente='producao')
    print(f'Valid: {res.get("valid")}')
    print(f'Signed: {res.get("signed_xml") is not None}')
    
    if res.get('errors'):
        print(f'Errors: {res.get("errors")}')
    
    if res.get('signed_xml'):
        print('=== Signed XML (preview) ===')
        signed = res.get('signed_xml')
        print(signed[:2000])
        # Verificar se contém Signature
        if 'Signature' in signed:
            print('\n✓ Assinatura encontrada no XML')
            # Verificar prefixos de namespace
            if 'ds:' in signed:
                print('✗ Prefixo ds: encontrado (deve ser removido)')
            else:
                print('✓ Prefixo ds: não encontrado (correto)')
        else:
            print('\n✗ Assinatura NÃO encontrada no XML')
