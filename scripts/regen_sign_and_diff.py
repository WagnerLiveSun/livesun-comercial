import os
import sys
from pathlib import Path
from lxml import etree

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import create_app
from src.services.nfse_nacional import validate_and_sign

if len(sys.argv) != 2:
    print('Uso: python regen_sign_and_diff.py <original_signed_xml>')
    sys.exit(2)

orig_path = Path(sys.argv[1])
if not orig_path.exists():
    print('Arquivo original não encontrado:', orig_path)
    sys.exit(2)

orig = orig_path.read_text(encoding='utf-8')
parser = etree.XMLParser(remove_blank_text=True)
root = etree.fromstring(orig.encode('utf-8'), parser)

# remove existing Signature elements (any namespace)
for sig in root.xpath('//*[local-name()="Signature"]'):
    parent = sig.getparent()
    if parent is not None:
        parent.remove(sig)

unsigned_xml = etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=False).decode('utf-8')

# Use Flask app context so certificate settings (PFX + senha) are resolved from DB
app = create_app()
with app.app_context():
    # empresa_id and ambiente should match the original transmission; use empresa_id=1
    result = validate_and_sign(unsigned_xml, kind='dps', empresa_id=1, ambiente='producao')
    signed = result.get('signed_xml')

if not signed:
    print('Signing failed or did not return signed XML. Result:', result)
    sys.exit(1)

# save signed to temp
from tempfile import gettempdir

td = gettempdir()
out_path = Path(td) / ('regenerated_signed.xml')
out_path.write_bytes(signed.encode('utf-8'))
print('Signed written to', out_path)

# diff
import difflib
orig_lines = orig.splitlines(keepends=True)
new_lines = signed.splitlines(keepends=True)

diff = list(difflib.unified_diff(orig_lines, new_lines, fromfile=str(orig_path), tofile=str(out_path)))
if not diff:
    print('No differences: regenerated signature matches original exactly')
    sys.exit(0)

print(''.join(diff[:4000]))
print('\n--- Diff lines:', len(diff), ' (showing first 4000 chars) ---')

sys.exit(0)
