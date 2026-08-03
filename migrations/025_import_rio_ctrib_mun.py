import os
import sys
from sqlalchemy import create_engine, text

# Ler configuração do banco de dados das variáveis de ambiente
db_user = os.environ.get('DB_USER', 'root')
db_password = os.environ.get('DB_PASSWORD', '')
db_host = os.environ.get('DB_HOST', 'localhost')
db_name = os.environ.get('DB_NAME', 'livesun_comercial_x')

db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(db_url)

print(f'Using DB: {db_name}')

# Ler arquivo de serviços
with open('Anexos/TabelaServicos.txt', 'r', encoding='latin1') as f:
    lines = f.readlines()

# Processar linhas
inserts = []
for line in lines[1:]:  # Pular cabeçalho
    line = line.strip()
    if not line:
        continue
    
    # Separar código e descrição (formato: "01.01.01\tDescrição")
    parts = line.split('\t')
    if len(parts) >= 2:
        codigo = parts[0].strip()
        descricao = parts[1].strip()
        
        if codigo and descricao:
            # Escapar aspas
            descricao = descricao.replace("'", "''")
            inserts.append(f"('3304557', 'RJ', 'Rio de Janeiro', '{codigo}', '{descricao}', TRUE, NULL, 'TabelaServicos_RJ', TRUE, NOW(), NOW())")

# Gerar SQL
sql = f"""
INSERT INTO nfse_ctrib_mun_referencia (
    codigo_ibge,
    uf_sigla,
    nome_municipio,
    codigo_tributacao_municipal,
    descricao,
    exige_ctribmun,
    data_inicio_vigencia,
    origem_catalogo,
    ativo,
    criado_em,
    atualizado_em
) VALUES
{', '.join(inserts)}
ON DUPLICATE KEY UPDATE 
    descricao = VALUES(descricao),
    exige_ctribmun = VALUES(exige_ctribmun),
    atualizado_em = NOW();
"""

print(f'Importando {len(inserts)} registros para o Rio de Janeiro...')
try:
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)
    print(f'Migration 025 applied successfully - {len(inserts)} registros importados')
except Exception as e:
    print('Migration failed:', e)
    sys.exit(1)
