import sys
from pathlib import Path
from lxml import etree
import hashlib

if len(sys.argv) != 2:
    print('Uso: python inspect_cert_chain.py <file>')
    sys.exit(2)

p = Path(sys.argv[1])
if not p.exists():
    print('Arquivo não encontrado:', p)
    sys.exit(2)

root = etree.fromstring(p.read_bytes())
certs = root.xpath('//*[local-name()="X509Certificate"]/text()')
print('Found', len(certs), 'cert blocks in', p)
for i,c in enumerate(certs,1):
    cleaned = ''.join(c.split())
    h = hashlib.sha1(cleaned.encode('utf-8')).hexdigest()
    print(f'{i}: {h} len={len(cleaned)} start={cleaned[:16]}')
