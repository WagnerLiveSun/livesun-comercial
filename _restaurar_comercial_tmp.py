import pymysql

origem = pymysql.connect(host='localhost', user='controller_owner',
                         password='Controller@2026!', database='comercial')
destino = pymysql.connect(host='195.35.61.111', user='u951548013_LS_Comercial',
                          password='quemsabe123!A', database='u951548013_LS_Comercial')

co = origem.cursor()
cd = destino.cursor()

co.execute("SELECT * FROM users WHERE username='comercial'")
cols = [d[0] for d in co.description]
row = co.fetchone()
dados = dict(zip(cols, row))
print('Usuario encontrado na origem: - _restaurar_comercial_tmp.py:15', {k: dados[k] for k in ('id', 'username', 'email', 'role', 'is_admin', 'empresa_id')})

cd.execute("SELECT id FROM users WHERE username='comercial'")
if cd.fetchone():
    print('Usuario comercial JA existe no destino  nada feito - _restaurar_comercial_tmp.py:19')
else:
    # inserir sem o id (novo id no destino), mantendo hash de senha e demais campos
    insert_cols = [c for c in cols if c != 'id']
    placeholders = ', '.join(['%s'] * len(insert_cols))
    cd.execute(
        f"INSERT INTO users ({', '.join(insert_cols)}) VALUES ({placeholders})",
        [dados[c] for c in insert_cols],
    )
    destino.commit()
    print('Usuario comercial inserido no destino com id: - _restaurar_comercial_tmp.py:29', cd.lastrowid)

cd.execute("SELECT id, username, email, role, is_admin, empresa_id FROM users")
for r in cd.fetchall():
    print(r)
origem.close()
destino.close()
