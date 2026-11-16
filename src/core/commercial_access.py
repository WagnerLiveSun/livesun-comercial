"""Apresentação de restrições comerciais; não altera autorização ou cobrança."""
from flask import jsonify, render_template, request
from werkzeug.exceptions import Forbidden


class CommercialAccessError(Forbidden):
    def __init__(self, description, code=403):
        super().__init__(description=description)
        self.code = code


def register_commercial_access_errors(app):
    @app.errorhandler(CommercialAccessError)
    def commercial_access_error(error):
        if request.accept_mimetypes.best == 'application/json':
            response = jsonify(error='acesso_comercial_indisponivel', message=error.description)
        else:
            response = app.make_response(render_template('errors/commercial_access.html',
                access_restricted=True, temporary=error.code == 503, message=error.description))
        response.status_code = error.code
        response.headers['Cache-Control'] = 'no-store'
        if error.code == 503:
            response.headers['Retry-After'] = '60'
        return response