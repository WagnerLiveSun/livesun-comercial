from datetime import date, datetime, timedelta
from src.app import create_app
from src.models import AssinaturaEmpresa
from src.services.assinatura import ServicoAssinatura

app = create_app()
with app.app_context():
    a = AssinaturaEmpresa(empresa_id=999999, status='trial',
                          data_vencimento=date(2020, 1, 1),
                          data_limite_carencia=date(2020, 1, 8), carencia_dias=7)
    a.bonus_liberado = True
    a.bonus_tipo = 'trial'
    a.bonus_dias = 30
    a.bonus_concedido_em = datetime.utcnow()
    ServicoAssinatura.recalcular_status_por_carencia(a)
    print('trial dentro do prazo > - _teste_recalc_tmp.py:16', a.status, '|', a.bloqueio_nivel, '|', a.motivo_status)

    a.bonus_concedido_em = datetime.utcnow() - timedelta(days=40)
    ServicoAssinatura.recalcular_status_por_carencia(a)
    print('trial expirado > - _teste_recalc_tmp.py:20', a.status, '|', a.bloqueio_nivel, '|', a.motivo_status)

    a.bonus_tipo = 'ilimitado'
    ServicoAssinatura.recalcular_status_por_carencia(a)
    print('ilimitado > - _teste_recalc_tmp.py:24', a.status, '|', a.bloqueio_nivel, '|', a.motivo_status)
