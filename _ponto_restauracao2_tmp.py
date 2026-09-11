import subprocess
from datetime import datetime

DUMP = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
STAMP = datetime.now().strftime('%Y%m%d_%H%M')

BASES = [
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
        '--column-statistics=0',
        '--single-transaction', '--routines', '--triggers', '--events',
        '--default-character-set=utf8mb4',
        cfg['database'],
    ]
    print(f'Dumping {nome} > {saida} - _ponto_restauracao2_tmp.py:25')
    with open(saida, 'w', encoding='utf-8') as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print('ERRO: - _ponto_restauracao2_tmp.py:29', r.stderr[:300])
    else:
        import os
        print(f'OK ({os.path.getsize(saida):,} bytes) - _ponto_restauracao2_tmp.py:32')

# atualiza LEIA-ME com os novos nomes
import glob
arquivos = sorted(glob.glob('backups/ponto_restauracao_*.sql'))
with open('backups/ponto_restauracao_LEIA-ME.txt', 'w', encoding='utf-8') as f:
    f.write(f"PONTO DE RESTAURACAO - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    f.write('=' * 60 + '\nArquivos:\n')
    for a in arquivos:
        f.write(f'  {a}\n')
    f.write("""
RESTAURAR (exemplo):
  mysql -h HOST -u USER -p NOMEDOBANCO < arquivo.sql

Codigos:
  local_comercial        -> banco local 'comercial'
  hostinger_destino      -> 'u951548013_LS_Comercial' (destino atual do sistema)
  hostinger_origem_gfinanceiro -> 'u951548013_gfinanceiro' (origem da migracao)

Estado do codigo: commit 2fb1bc5 (tag ponto-restauracao no Git)
""")
print('concluido')
