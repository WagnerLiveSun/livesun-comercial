import logging
import requests
import tempfile
from src.services.nfse_nacional import _resolve_certificate_settings, _prepare_mtls_from_pfx, get_base_emissao, _candidate_emission_urls
from src.app import create_app
import os
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager


class SSLContextAdapter(HTTPAdapter):
    def __init__(self, ssl_context, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_context=self.ssl_context, **pool_kwargs)


def try_request_with_tuple(url, cert_tuple):
    try:
        r = requests.post(url, json={'ping': '1'}, timeout=20, cert=cert_tuple, verify=True)
        return r.status_code, r.text[:1000]
    except Exception as e:
        return 'error', str(e)


def try_request_with_combined(url, combined_path):
    try:
        r = requests.post(url, json={'ping': '1'}, timeout=20, cert=combined_path, verify=True)
        return r.status_code, r.text[:1000]
    except Exception as e:
        return 'error', str(e)


def try_request_with_sslcontext(url, certfile, keyfile):
    try:
        ctx = ssl.create_default_context()
        ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
        s = requests.Session()
        s.mount('https://', SSLContextAdapter(ctx))
        r = s.post(url, json={'ping': '1'}, timeout=20, verify=True)
        return r.status_code, r.text[:1000]
    except Exception as e:
        return 'error', str(e)


def try_request_with_tls12(url, certfile, keyfile):
    try:
        # Force TLSv1.2
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.load_default_certs()
        ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
        s = requests.Session()
        s.mount('https://', SSLContextAdapter(ctx))
        r = s.post(url, json={'ping': '1'}, timeout=20, verify=True)
        return r.status_code, r.text[:1000]
    except Exception as e:
        return 'error', str(e)


def main():
    app = create_app()
    with app.app_context():
        # resolve pfx for empresa_id=1 in homologacao
        pfx_path, pfx_pass = _resolve_certificate_settings(empresa_id=1, ambiente='homologacao')
        print('resolved pfx:', pfx_path, 'pass_present:', pfx_pass is not None)
        cert_pem_path, key_pem_path, temp_paths = _prepare_mtls_from_pfx(pfx_path, pfx_pass)
        print('cert_pem_path, key_pem_path:', cert_pem_path, key_pem_path)

        base = get_base_emissao(ambiente='homologacao')
        urls = _candidate_emission_urls(base)
        target = urls[0]
        print('target url:', target)

        # try tuple
        print('\n-- try cert tuple (cert, key)')
        res = try_request_with_tuple(target, (cert_pem_path, key_pem_path))
        print(res)

        # write combined file
        combined = tempfile.NamedTemporaryFile('wb', delete=False, suffix='.pem')
        combined.write(open(cert_pem_path, 'rb').read())
        combined.write(b'\n')
        combined.write(open(key_pem_path, 'rb').read())
        combined.close()
        print('\n-- try combined file path')
        res2 = try_request_with_combined(target, combined.name)
        print(res2)

        print('\n-- try SSLContext adapter')
        res3 = try_request_with_sslcontext(target, cert_pem_path, key_pem_path)
        print(res3)


if __name__ == '__main__':
    main()
