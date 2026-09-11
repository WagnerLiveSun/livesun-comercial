"""
Serviço de integração com API do Brevo para envio de emails transacionais.
"""
import os
import base64
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BrevoService:
    """Serviço para envio de emails via API do Brevo."""
    
    def __init__(self):
        self.api_key = os.getenv('BREVO_API_KEY')
        self.base_url = 'https://api.brevo.com/v3'
        self.reset_password_template_id = os.getenv('BREVO_RESET_PASSWORD_TEMPLATE_ID', '1')
    
    def send_reset_password_email(self, to_email, username, reset_code):
        """
        Envia email de recuperação de senha.
        
        Args:
            to_email (str): Email do destinatário
            username (str): Nome do usuário
            reset_code (str): Código de recuperação (6 dígitos)
        
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        if not self.api_key:
            logger.error('BREVO_API_KEY não configurada')
            return False
        
        logger.info(f'Enviando email para {to_email} com código {reset_code}')
        logger.info(f'Template ID: {self.reset_password_template_id}')
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'api-key': self.api_key
        }
        
        payload = {
            'to': [
                {
                    'email': to_email,
                    'name': username
                }
            ],
            'templateId': int(self.reset_password_template_id),
            'params': {
                'username': username,
                'app_name': 'LiveSun Comercial',
                'reset_code': reset_code,
                'current_year': datetime.now().year
            },
            'sender': {
                'name': 'LiveSun Comercial',
                'email': 'noreply@livesun.com.br'
            }
        }
        
        try:
            logger.info(f'Payload: {payload}')
            response = requests.post(
                f'{self.base_url}/smtp/email',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f'Response status: {response.status_code}')
            logger.info(f'Response body: {response.text}')
            
            if response.status_code == 201:
                logger.info(f'Email de recuperação enviado para {to_email}')
                return True
            else:
                logger.error(f'Erro ao enviar email: {response.status_code} - {response.text}')
                logger.error(f'Headers: {response.headers}')
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Erro na requisição ao Brevo: {e}')
            logger.error(f'Tipo de erro: {type(e).__name__}')
            return False
        except Exception as e:
            logger.error(f'Erro inesperado ao enviar email: {e}')
            logger.error(f'Tipo de erro: {type(e).__name__}')
            return False


    def send_transactional_email(self, to_email, to_name, subject, html_content, attachment=None):
        """
        Envia um email transacional via API do Brevo com conteúdo HTML
        e adjunto opcional (por exemplo, o PDF do DANFSe).

        Args:
            to_email (str): Email do destinatário.
            to_name (str): Nome do destinatário.
            subject (str): Assunto do email.
            html_content (str): Corpo do email em HTML.
            attachment (dict, opcional): {
                'name': 'nome_do_arquivo.pdf',
                'content': bytes,           # bytes do arquivo
                'content_type': 'application/pdf'
            }

        Returns:
            bool: True se enviado com sucesso, False caso contrário.
        """
        if not self.api_key:
            logger.error('BREVO_API_KEY não configurada')
            return False

        logger.info(f'Enviando email transacional (NFS-e) para {to_email}')

        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'api-key': self.api_key
        }

        payload = {
            'to': [
                {
                    'email': to_email,
                    'name': to_name or to_email
                }
            ],
            'sender': {
                'name': 'LiveSun Comercial',
                'email': 'noreply@livesun.com.br'
            },
            'subject': subject,
            'htmlContent': html_content
        }

        if attachment and attachment.get('content'):
            # Brevo espera o adjunto em base64 no campo 'content'.
            adjunto_bytes = attachment.get('content')
            if hasattr(adjunto_bytes, 'read'):
                adjunto_bytes = adjunto_bytes.read()
            payload['attachment'] = [
                {
                    'name': attachment.get('name') or 'adjunto.pdf',
                    'content': base64.b64encode(adjunto_bytes).decode('ascii')
                }
            ]

        try:
            response = requests.post(
                f'{self.base_url}/smtp/email',
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 201:
                logger.info(f'Email transacional enviado para {to_email}')
                return True
            else:
                logger.error(f'Erro ao enviar email transacional: {response.status_code} - {response.text}')
                logger.error(f'Headers: {response.headers}')
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f'Erro na requisição ao Brevo (transacional): {e}')
            logger.error(f'Tipo de erro: {type(e).__name__}')
            return False
        except Exception as e:
            logger.error(f'Erro inesperado ao enviar email transacional: {e}')
            logger.error(f'Tipo de erro: {type(e).__name__}')
            return False


# Instância global do serviço
brevo_service = BrevoService()
