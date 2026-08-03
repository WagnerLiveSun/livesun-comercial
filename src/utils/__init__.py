# LiveSun Comercial - Utilitários

from flask import url_for
from flask_login import current_user


def get_empresa_logo(empresa=None):
    """
    Retorna o caminho do logo da empresa.
    Se não houver logo configurado, retorna o logo padrão.
    """
    if empresa is None and current_user.is_authenticated:
        empresa = current_user.empresa
    
    if empresa and empresa.logo_caminho:
        return empresa.logo_caminho
    
    # Logo padrão
    return url_for('static', filename='images/logo.png')
