"""
Serviço de integração com API do Brevo para envio de emails transacionais.
"""
import os
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
            'to': [{'email': to_email}],
            'templateId': int(self.reset_password_template_id),
            'params': {
                'username': username,
                'reset_code': reset_code,
                'app_name': 'LiveSun Comercial',
                'current_year': str(datetime.now().year)
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
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Erro na requisição ao Brevo: {e}')
            return False


# Instância global do serviço
brevo_service = BrevoService()
