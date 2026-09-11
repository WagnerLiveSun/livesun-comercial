"""Ponto de restauracao: dump SQL das tres bases + manifest."""
import subprocess
from datetime import datetime

DUMP = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
STAMP = datetime.now().strftime('%Y%m%d_%H%M')

BASES = [
    ('local_comercial', dict(host='localhost', port=3306, user='controller_owner',
                             password='Controller@2026!', database='comercial')),
    ('hostinger_destino', dict(host='195.35.61.111', port=3306, user='u951548013_LS_Comercial',
                               password='quemsabe123!A', database='u951548013_LS_Comercial')),
    ('hostinger_origem_gfinanceiro', dict(host='195.35.61.111', port=3306, user='u951548013_gfinanceiro',
                                          password='quemsabe123!A', database='u951548013_gfinanceiro')),
]

for nome, cfg in BASES:
    saida = f"backups/ponto_restauracao_{nome}_{STAMP}.sql"
    cmd = [
        DUMP,
        f"--host={cfg['host']}", f"--port={cfg['port']}",
        f"--user={cfg['user']}", f"--password={cfg['password']}",
        '--single-transaction', '--routines', '--triggers', '--events',
        '--default-character-set=utf8mb4',
        cfg['database'],
    ]
    print(f'Dumping {nome} > {saida} - _ponto_restauracao_tmp.py:27')
    with open(saida, 'w', encoding='utf-8') as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print('ERRO: - _ponto_restauracao_tmp.py:31', r.stderr[:500])
    else:
        import os
        size = os.path.getsize(saida)
        print(f'OK ({size:,} bytes) - _ponto_restauracao_tmp.py:35')

with open('backups/ponto_restauracao_LEIA-ME.txt', 'w', encoding='utf-8') as f:
    f.write(f"""PONTO DE RESTAURACAO - {datetime.now().strftime('%d/%m/%Y %H:%M')}
=========================================================
Arquivos:
  ponto_restauracao_local_comercial_{STAMP}.sql          -> banco local 'comercial'
  ponto_restauracao_hostinger_destino_{STAMP}.sql        -> banco Hostinger 'u951548013_LS_Comercial' (destino atual do sistema)
  ponto_restauracao_hostinger_origem_gfinanceiro_{STAMP}.sql -> banco Hostinger 'u951548013_gfinanceiro' (origem da migracao)

Estado do codigo: commit 2fb1bc5 (tag: ponto-restauracao-{STAMP})

RESTAURAR (exemplo):
  mysql -h HOST -u USER -p NOMEDOBANCO < arquivo.sql

Observacoes:
  - Dump com --single-transaction (consistente, InnoDB), rotinas, triggers e eventos.
  - Guarde esses arquivos em local seguro (fora da maquina, de preferencia).
""")

print('ponto de restauracao concluido')
