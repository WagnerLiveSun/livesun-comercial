import sys
from pathlib import Path
import difflib

if len(sys.argv) != 3:
    print("Uso: python diff_signed_vs_sent.py <signed_path> <expected_path>")
    sys.exit(2)

signed = Path(sys.argv[1])
expected = Path(sys.argv[2])

if not signed.exists():
    print(f"Arquivo assinado não encontrado: {signed}")
    sys.exit(2)
if not expected.exists():
    print(f"Arquivo esperado não encontrado: {expected}")
    sys.exit(2)

s_lines = signed.read_text(encoding='utf-8').splitlines(keepends=True)
e_lines = expected.read_text(encoding='utf-8').splitlines(keepends=True)

diff = list(difflib.unified_diff(e_lines, s_lines, fromfile=str(expected), tofile=str(signed), lineterm=''))

if not diff:
    print('Files are identical')
    sys.exit(0)

print(''.join(diff))
print('\n--- Summary ---')
print(f'{len(diff)} diff lines')

# heuristics: show first 40 diff lines only to avoid huge output
if len(diff) > 200:
    print('\n[Diff truncated - too large]')

sys.exit(0)
