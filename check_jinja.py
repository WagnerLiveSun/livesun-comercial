import datetime
import jinja2

stub = "<!DOCTYPE html><html><head><title>{% block title %}Teste{% endblock %}</title></head><body>{% block content %}{% endblock %}</body></html>"

with open('d:/App_LiveSun/LiveSun_Comercial_X/check_jinja/layout.html', 'w', encoding='utf-8') as f:
    f.write(stub)

loader = jinja2.ChoiceLoader([jinja2.FileSystemLoader('d:/App_LiveSun/LiveSun_Comercial_X/check_jinja'), jinja2.FileSystemLoader('d:/App_LiveSun/LiveSun_Comercial_X/src/templates')])
env = jinja2.Environment(loader=loader)
url_for = lambda *a, **k: '/backoffice/comercial/'
env.globals['url_for'] = url_for
env.globals['csrf_token'] = lambda: 'stub-csrf-token'
t = env.get_template('admin/comercial_panel.html')

rows = [
    {'empresa_nome': 'Ativa', 'empresa_id': 1, 'plano': 'Premium', 'status': 'ativa', 'vigencia': datetime.date(2026, 1, 1), 'users_ativos': 5, 'users_total': 10, 'volume_dados': 10, 'atraso_qtd': 0, 'atraso_valor': 0, 'bonus_liberado': False, 'dias_restantes_exclusao': 0, 'data_exclusao': None, 'modulos': {}},
    {'empresa_nome': 'Trial', 'empresa_id': 2, 'plano': 'Premium', 'status': 'ativa', 'vigencia': datetime.date(2026, 2, 1), 'users_ativos': 1, 'users_total': 3, 'volume_dados': 50, 'atraso_qtd': 0, 'atraso_valor': 0, 'bonus_liberado': True, 'bonus_tipo': 'trial', 'bonus_dias': 7, 'bonus_concedido_em': datetime.datetime(2026, 1, 1, 10, 30), 'bonus_fim': datetime.datetime(2026, 1, 8, 10, 30), 'dias_restantes_exclusao': 30, 'data_exclusao': None, 'modulos': {}},
    {'empresa_nome': 'Excluida', 'empresa_id': 3, 'plano': 'Basic', 'status': 'excluida', 'vigencia': datetime.date(2026, 3, 1), 'users_ativos': 0, 'users_total': 2, 'volume_dados': 5, 'atraso_qtd': 0, 'atraso_valor': 0, 'bonus_liberado': False, 'dias_restantes_exclusao': 0, 'data_exclusao': datetime.datetime(2026, 8, 1), 'modulos': {}},
]
resumo = {'clientes_ativos': 1, 'clientes_suspensos': 0, 'clientes_cancelados': 0, 'inadimplentes': 0, 'valor_em_atraso': 0}
try:
    out = t.render(rows=rows, resumo=resumo, eventos=[], filtros={}, ofertas=[], planos_disponiveis=[], module_labels={}, retencao_dias=60, to_brl=lambda v: 'R$ 0.00')
    print('TEMPLATE_RENDER_OK', len(out))
except Exception as e:
    print('FAILED', type(e).__name__, e)

