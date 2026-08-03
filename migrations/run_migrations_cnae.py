import subprocess
import sys
import os

def run_sql_file(sql_file):
    """Executa um arquivo SQL usando o MySQL"""
    mysql_path = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
    
    if not os.path.exists(mysql_path):
        print(f"MySQL não encontrado em: {mysql_path}")
        # Tentar encontrar no PATH
        mysql_path = "mysql"
    
    command = f'"{mysql_path}" -u root -p123456 livesun < "{sql_file}"'
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Arquivo {sql_file} executado com sucesso!")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"Erro ao executar {sql_file}:")
            print(result.stderr)
    except Exception as e:
        print(f"Erro ao executar comando: {e}")

if __name__ == "__main__":
    # Executar migração 027 (criar tabela)
    print("Executando migração 027...")
    run_sql_file(r"D:\App_LiveSun\LiveSun_Comercial_X\migrations\027_create_cnae_table.sql")
    
    # Executar migração 028 (importar dados)
    print("\nExecutando migração 028...")
    run_sql_file(r"D:\App_LiveSun\LiveSun_Comercial_X\migrations\028_import_cnae_data.sql")
    
    print("\nMigrações concluídas!")
