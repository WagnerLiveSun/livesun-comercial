import pymysql

SQLS = [
    "ALTER TABLE assinatura_empresa ADD COLUMN bonus_tipo VARCHAR(20) NULL",
    "ALTER TABLE assinatura_empresa ADD COLUMN bonus_dias INT NULL",
]

BASES = [
    ('LOCAL', dict(host='localhost', port=3306, user='controller_owner',
                   password='Controller@2026!', database='comercial')),
    ('HOSTINGER', dict(host='195.35.61.111', port=3306, user='u951548013_LS_Comercial',
                       password='quemsabe123!A', database='u951548013_LS_Comercial')),
]

for label, cfg in BASES:
    print(f'{label} - _aplicar_032_tmp.py:16')
    try:
        conn = pymysql.connect(**cfg)
        cur = conn.cursor()
        for sql in SQLS:
            try:
                cur.execute(sql)
                print('OK: - _aplicar_032_tmp.py:23', sql[:60])
            except Exception as e:
                if 'Duplicate' in str(e):
                    print('ja existe: - _aplicar_032_tmp.py:26', sql[:60])
                else:
                    print('ERRO: - _aplicar_032_tmp.py:28', e)
        conn.commit()
        conn.close()
    except Exception as e:
        print('FALHA conexao: - _aplicar_032_tmp.py:32', e)
