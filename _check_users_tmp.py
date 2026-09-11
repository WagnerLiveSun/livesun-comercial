import pymysql

for label, cfg in [
    ('ORIGEM LOCAL', dict(host='localhost', user='controller_owner',
                          password='Controller@2026!', database='comercial')),
    ('DESTINO', dict(host='195.35.61.111', user='u951548013_LS_Comercial',
                     password='quemsabe123!A', database='u951548013_LS_Comercial')),
]:
    conn = pymysql.connect(**cfg)
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, role, is_admin, empresa_id, is_active FROM users")
    print('', label)
    for r in cur.fetchall():
        print(r)
    conn.close()
