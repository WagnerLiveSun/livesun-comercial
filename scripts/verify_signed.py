from signxml import XMLVerifier
from lxml import etree
import sys

def verify(path):
    parser = etree.XMLParser(remove_blank_text=True)
    xml = etree.parse(path, parser)
    try:
        res = XMLVerifier().verify(xml)
        print('Signature verified. Signed info digest algorithm:', res)
    except Exception as e:
        print('Verification failed:', type(e).__name__, str(e))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: verify_signed.py signed_file.xml')
    else:
        verify(sys.argv[1])
