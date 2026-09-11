import pymysql
from src.access_control import PERMISSION_CATALOG

KEYS = [item['key'] for item in PERMISSION_CATALOG]
print('chaves do catalogo: - _seed_perms_tmp.py:5', len(KEYS))

conn = pymysql.connect(host='195.35.61.111', user='u951548013_LS_Comercial',
                       password='quemsabe123!A', database='u951548013_LS_Comercial')
cur = conn.cursor()
cur.execute('SELECT id FROM empresas')
empresas = [r[0] for r in cur.fetchall()]
print('empresas: - _seed_perms_tmp.py:12', empresas)

inseridos = 0
for eid in empresas:
    for key in KEYS:
        cur.execute(
            "SELECT id FROM role_permissions WHERE empresa_id=%s AND role='operator' AND permission_key=%s",
            (eid, key))
        if cur.fetchone():
            continue
        cur.execute(
            "INSERT INTO role_permissions (empresa_id, role, permission_key, allowed) "
            "VALUES (%s, 'operator', %s, 1)", (eid, key))
        inseridos += 1
conn.commit()
print('permissoes operator inseridas: - _seed_perms_tmp.py:27', inseridos)

cur.execute("SELECT empresa_id, role, COUNT(*) FROM role_permissions GROUP BY empresa_id, role")
for r in cur.fetchall():
    print(r)
conn.close()
