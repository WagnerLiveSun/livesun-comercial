import pymysql

conn = pymysql.connect(host='195.35.61.111', user='u951548013_LS_Comercial',
                       password='quemsabe123!A', database='u951548013_LS_Comercial')
cur = conn.cursor()
cur.execute("UPDATE users SET role='admin' WHERE is_admin=1 AND (role IS NULL OR role='')")
print('admins corrigidos: - _fix_roles_tmp.py:7', cur.rowcount)
cur.execute("UPDATE users SET role='operator' WHERE (is_admin=0 OR is_admin IS NULL) AND (role IS NULL OR role='')")
print('operadores corrigidos: - _fix_roles_tmp.py:9', cur.rowcount)
conn.commit()
cur.execute("SELECT id, username, role, is_admin, empresa_id FROM users")
for r in cur.fetchall():
    print(r)
conn.close()
