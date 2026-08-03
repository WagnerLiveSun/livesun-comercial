from sqlalchemy import create_engine, text
from config.config import Config
import sys
import os

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

print("=== Migrações NFS-e cTribMun (MySQL) ===\n")

# 1. Criar tabela nfse_ctrib_mun_referencia
print("1. Criando tabela nfse_ctrib_mun_referencia...")
sql_023 = open('migrations/023_create_nfse_ctrib_mun_referencia.sql', 'r', encoding='utf-8').read()
try:
    with engine.begin() as conn:
        conn.exec_driver_sql(sql_023)
    print("   ✓ Tabela criada com sucesso")
except Exception as e:
    print(f"   ✗ Erro ao criar tabela: {e}")
    # Continuar mesmo se der erro (pode já existir)

# 2. Aumentar tamanho da coluna codigo_tributacao_municipal
print("\n2. Aumentando tamanho da coluna codigo_tributacao_municipal...")
sql_026 = open('migrations/026_alter_nfse_ctrib_mun_codigo_length.sql', 'r', encoding='utf-8').read()
try:
    with engine.begin() as conn:
        conn.exec_driver_sql(sql_026)
    print("   ✓ Coluna alterada com sucesso")
except Exception as e:
    print(f"   ✗ Erro ao alterar coluna: {e}")
    # Continuar mesmo se der erro (pode já ter sido alterada)

# 3. Importar dados de Belo Horizonte
print("\n3. Importando dados de CTISS_BH para Belo Horizonte...")
sql_024 = open('migrations/024_migrate_ctiss_bh_to_nfse_ctrib_mun.sql', 'r', encoding='utf-8').read()
try:
    with engine.begin() as conn:
        result = conn.exec_driver_sql(sql_024)
        print(f"   ✓ Dados de BH importados com sucesso")
except Exception as e:
    print(f"   ✗ Erro ao importar dados de BH: {e}")
    sys.exit(1)

# 4. Importar dados do Rio de Janeiro
print("\n4. Importando dados do Rio de Janeiro...")
with open('Anexos/TabelaServicos.txt', 'r', encoding='utf-8') as f:
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
sql_025 = f"""
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

try:
    with engine.begin() as conn:
        conn.exec_driver_sql(sql_025)
    print(f"   ✓ {len(inserts)} registros do Rio importados com sucesso")
except Exception as e:
    print(f"   ✗ Erro ao importar dados do Rio: {e}")
    sys.exit(1)

print("\n=== Todas as migrações concluídas com sucesso ===")
