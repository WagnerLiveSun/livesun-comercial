"""Aplica a migration 031 (bonus de assinatura) nas bases local e Hostinger."""

import pymysql

SQLS = [
    "ALTER TABLE assinatura_empresa ADD COLUMN bonus_liberado TINYINT(1) NOT NULL DEFAULT 0",
    "ALTER TABLE assinatura_empresa ADD COLUMN bonus_motivo VARCHAR(255) NULL",
    "ALTER TABLE assinatura_empresa ADD COLUMN bonus_concedido_em DATETIME NULL",
    "CREATE INDEX idx_assinatura_bonus_liberado ON assinatura_empresa (bonus_liberado)",
]

BASES = [
    ('LOCAL', dict(host='localhost', port=3306, user='controller_owner',
                   password='Controller@2026!', database='comercial')),
    ('HOSTINGER', dict(host='195.35.61.111', port=3306, user='u951548013_LS_Comercial',
                       password='quemsabe123!A', database='u951548013_LS_Comercial')),
]

for label, cfg in BASES:
    print(f'{label} - _aplicar_031_tmp.py:20')
    try:
        conn = pymysql.connect(**cfg)
        cur = conn.cursor()
        for sql in SQLS:
            try:
                cur.execute(sql)
                print('OK: - _aplicar_031_tmp.py:27', sql[:60])
            except pymysql.err.OperationalError as e:
                if 'Duplicate column' in str(e) or 'Duplicate key name' in str(e):
                    print('ja existe: - _aplicar_031_tmp.py:30', sql[:60])
                else:
                    print('ERRO: - _aplicar_031_tmp.py:32', e)
            except pymysql.err.MySQLError as e:
                if 'Duplicate' in str(e):
                    print('ja existe: - _aplicar_031_tmp.py:35', sql[:60])
                else:
                    print('ERRO: - _aplicar_031_tmp.py:37', e)
        conn.commit()
        conn.close()
        print('concluido - _aplicar_031_tmp.py:40')
    except Exception as e:
        print('FALHA conexao: - _aplicar_031_tmp.py:42', e)
