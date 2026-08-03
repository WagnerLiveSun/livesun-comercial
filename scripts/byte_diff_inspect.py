import sys
from pathlib import Path

def hexdump(b):
    return ' '.join(f'{x:02x}' for x in b)

def show_context(a, i, ctx=40):
    start = max(0, i-ctx)
    end = min(len(a), i+ctx)
    return a[start:end]

def main():
    if len(sys.argv) < 3:
        print('usage: byte_diff_inspect.py file1 file2')
        return
    f1 = Path(sys.argv[1])
    f2 = Path(sys.argv[2])
    b1 = f1.read_bytes()
    b2 = f2.read_bytes()
    L = min(len(b1), len(b2))
    diffs = []
    for i in range(L):
        if b1[i] != b2[i]:
            diffs.append(i)
            if len(diffs) >= 20:
                break
    print('len1', len(b1), 'len2', len(b2), 'first_diffs_count', len(diffs))
    for idx in diffs[:10]:
        c1 = show_context(b1, idx)
        c2 = show_context(b2, idx)
        print('\n--- diff at byte', idx)
        print('file1 repr:', repr(c1))
        print('file1 hex :', hexdump(c1))
        print('file2 repr:', repr(c2))
        print('file2 hex :', hexdump(c2))

    # show any trailing bytes
    if len(b1) != len(b2):
        print('\nlength mismatch; trailing bytes:')
        if len(b1) > len(b2):
            print('extra in file1:', hexdump(b1[len(b2):len(b2)+80]))
        else:
            print('extra in file2:', hexdump(b2[len(b1):len(b1)+80]))

if __name__ == '__main__':
    main()
