import pandas as pd
import sys
import os
import sqlalchemy

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# Adicionar o diretório config ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config import config

def get_db_engine():
    """Cria engine de conexão com o banco usando configuração do app"""
    cfg = config['default']
    engine = sqlalchemy.create_engine(cfg.SQLALCHEMY_DATABASE_URI)
    return engine

def import_cnae_from_csv():
    """Importa dados de CNAE do arquivo CSV"""
    csv_file = r"D:\App_LiveSun\LiveSun_Comercial_X\cnae_subclasses.csv"
    
    try:
        # Ler o arquivo CSV
        df = pd.read_csv(csv_file)
        
        print(f"Total de linhas no CSV: {len(df)}")
        
        return df
    except Exception as e:
        print(f"Erro ao ler arquivo CSV: {e}")
        return None

def insert_cnae_to_db(df):
    """Insere dados de CNAE no banco de dados usando SQLAlchemy"""
    engine = get_db_engine()
    
    try:
        # Deletar dados existentes
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("DELETE FROM nfse_cnae_referencia"))
            conn.commit()
        
        print("Tabela limpa com sucesso!")
        
        # Inserir novos dados
        count = 0
        for _, row in df.iterrows():
            codigo = str(row['subclasse']).strip()
            denominacao = str(row['denominacao']).strip()
            
            if codigo and codigo != 'nan':
                secao = str(row['secao']).strip() if pd.notna(row['secao']) and str(row['secao']).strip() != 'nan' else None
                divisao = str(row['divisao']).strip() if pd.notna(row['divisao']) and str(row['divisao']).strip() != 'nan' else None
                grupo = str(row['grupo']).strip() if pd.notna(row['grupo']) and str(row['grupo']).strip() != 'nan' else None
                classe = str(row['classe']).strip() if pd.notna(row['classe']) and str(row['classe']).strip() != 'nan' else None
                
                insert_sql = sqlalchemy.text("""
                    INSERT INTO nfse_cnae_referencia 
                    (codigo, denominacao, secao, divisao, grupo, classe, subclasse, ativo)
                    VALUES (:codigo, :denominacao, :secao, :divisao, :grupo, :classe, :subclasse, 1)
                """)
                
                with engine.connect() as conn:
                    conn.execute(insert_sql, {
                        'codigo': codigo,
                        'denominacao': denominacao,
                        'secao': secao,
                        'divisao': divisao,
                        'grupo': grupo,
                        'classe': classe,
                        'subclasse': codigo
                    })
                    conn.commit()
                
                count += 1
                
                if count % 100 == 0:
                    print(f"Processados: {count}")
        
        print(f"\nTotal de CNAE inseridos: {count}")
        return True
        
    except Exception as e:
        print(f"Erro ao inserir dados: {e}")
        return False

if __name__ == "__main__":
    df = import_cnae_from_csv()
    if df is not None:
        if insert_cnae_to_db(df):
            print("\nImportação concluída com sucesso!")
