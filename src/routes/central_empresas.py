"""Rotas somente de leitura para preparar a virada antes da ativação."""
from flask import request, abort
from src.routes.central_integracao import central_bp, authenticate
from src.services.central_empresas import companies


@central_bp.get('/central/empresas')
def existing_companies():
    authenticate(request.full_path.rstrip('?').encode(), allow_inactive=True)
    cursor = request.args.get('apos', default=0, type=int)
    if cursor is None or not 0 <= cursor <= 2147483647:
        abort(422)
    rows, next_cursor = companies(cursor)
    return {'produto': 'COMERCIAL', 'empresas': rows, 'proximo': next_cursor}


@central_bp.get('/central/empresas/<int:identifier>')
def existing_company(identifier):
    authenticate(request.path.encode(), allow_inactive=True)
    if not 1 <= identifier <= 2147483647:
        abort(422)
    rows, _ = companies(identifier=identifier)
    if not rows:
        abort(404)
    return {'produto': 'COMERCIAL', 'empresa': rows[0]}