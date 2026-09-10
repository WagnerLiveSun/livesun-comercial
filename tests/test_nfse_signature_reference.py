import unittest
from unittest.mock import patch

from src.services.nfse_nacional import validateandsignxml


class NfseSignatureReferenceTestCase(unittest.TestCase):
    def test_validateandsignxml_uses_infdps_reference_uri(self):
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">'
            '<infDPS Id="DPS12345678901234567890123456789012345678901234">'
            '<tpAmb>1</tpAmb>'
            '</infDPS>'
            '</DPS>'
        )

        with patch('src.services.nfse_nacional.run_xsd_validation', return_value=(True, [])), \
             patch('src.services.nfse_nacional.resolve_certificate_settings', return_value=('cert.pfx', 'senha')), \
             patch('src.services.nfse_nacional.sign_xml_enveloped', return_value='<signed/>') as mock_sign:

            result = validateandsignxml(xml, kind='dps', empresa_id=1, ambiente='homologacao')

        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], None)
        self.assertEqual(result['signedxml'], '<signed/>')
        mock_sign.assert_called_once()
        self.assertEqual(
            mock_sign.call_args.kwargs['reference_uri'],
            '#DPS12345678901234567890123456789012345678901234'
        )


if __name__ == '__main__':
    unittest.main()