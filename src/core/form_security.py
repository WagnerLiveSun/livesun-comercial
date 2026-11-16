"""Mensagens de formulário sem desativar CSRF nem repetir operações sensíveis."""
from flask import render_template
from flask_wtf.csrf import CSRFError


def register_form_errors(app):
    @app.errorhandler(CSRFError)
    def csrf_error(error):
        app.logger.warning('Formulário rejeitado pela validação CSRF.')
        response = app.make_response((render_template('errors/csrf.html'), 400))
        response.headers['Cache-Control'] = 'no-store'
        return response