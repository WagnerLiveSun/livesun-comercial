from unittest.mock import patch
from xml.etree import ElementTree as ET
import unittest

from src.services.nfse_nacional import builddpsxml


class NfseMunicipiosTestCase(unittest.TestCase):
    def test_prestador_tomador_e_local_de_prestacao_sao_independentes(self):
        payload = {
            "codigo_municipio": "3106200",
            "empresa_cnpj": "12345678000199",
            "empresa_endereco_rua": "Rua do Prestador",
            "empresa_endereco_numero": "10",
            "empresa_endereco_bairro": "Centro",
            "empresa_endereco_cep": "30100000",
            "ambiente": "homologacao",
            "versao_layout": "1.00",
            "tomador_documento": "98765432000100",
            "tomador_nome": "Tomador Teste",
            "tomador_codigo_municipio_ibge": "3304557",
            "tomador_endereco_cep": "20000000",
            "tomador_endereco_rua": "Rua do Tomador",
            "tomador_endereco_numero": "20",
            "tomador_endereco_bairro": "Centro",
            "servico_local_prestacao": "tomador",
            "codigo_servico": "010101",
            "servico_codigo_nacional": "010101",
            "cNBS": "118064000",
            "descricao_servico": "Servico especifico da emissao",
            "valor_servico": "100.00",
            "numero_interno": "TESTE-MUNICIPIOS",
            "serie": "1",
            "numero_nfse_sugerido": "1",
            "op_simp_nac": "3",
        }

        with patch("src.services.nfse_nacional.validate_catalog_references"):
            xml = builddpsxml(payload)

        root = ET.fromstring(xml)
        namespace = {"nfse": "http://www.sped.fazenda.gov.br/nfse"}

        self.assertEqual(root.findtext(".//nfse:cLocEmi", namespaces=namespace), "3106200")
        self.assertEqual(
            root.findtext(".//nfse:cLocPrestacao", namespaces=namespace),
            "3304557",
        )
        self.assertEqual(
            root.findtext(".//nfse:toma/nfse:end/nfse:endNac/nfse:cMun", namespaces=namespace),
            "3304557",
        )
        self.assertEqual(
            root.findtext(".//nfse:cServ/nfse:xDescServ", namespaces=namespace),
            "Servico especifico da emissao",
        )
        self.assertEqual(
            root.findtext(".//nfse:cServ/nfse:cNBS", namespaces=namespace),
            "118064000",
        )


if __name__ == "__main__":
    unittest.main()
