import sys
from pathlib import Path
from lxml import etree

if len(sys.argv) != 3:
    print('Uso: python compare_signature.py <file1> <file2>')
    sys.exit(2)

f1 = Path(sys.argv[1])
f2 = Path(sys.argv[2])

for p in (f1, f2):
    if not p.exists():
        print('Arquivo não encontrado:', p)
        sys.exit(2)

parser = etree.XMLParser(remove_blank_text=True)

def extract_signature(path):
    root = etree.fromstring(path.read_bytes(), parser)
    sigs = root.xpath('//*[local-name()="Signature"]')
    if not sigs:
        return None
    sig = sigs[0]
    # canonicalize Signature element
    c14n = etree.tostring(sig, method='c14n', exclusive=True, with_comments=True)
    return c14n

c1 = extract_signature(f1)
c2 = extract_signature(f2)

if c1 is None or c2 is None:
    print('Uma das entradas não tem Signature')
    sys.exit(2)

# write to temp files
from tempfile import gettempdir
td = gettempdir()
path1 = Path(td) / 'sig1.c14n'
path2 = Path(td) / 'sig2.c14n'
path1.write_bytes(c1)
path2.write_bytes(c2)

print('Canonicalized signatures written to:', path1, path2)

# show simple diff
import difflib
s1 = c1.decode('utf-8', errors='replace').splitlines(keepends=True)
s2 = c2.decode('utf-8', errors='replace').splitlines(keepends=True)
fromfile = str(f1)
tofile = str(f2)
for line in difflib.unified_diff(s1, s2, fromfile=fromfile, tofile=tofile, lineterm=''):
    print(line)

sys.exit(0)
