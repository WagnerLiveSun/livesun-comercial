import pymysql

# Conexão direta com MySQL - ajuste conforme seu ambiente
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='123456',
    database='livesun_comercial'
)

try:
    with connection.cursor() as cursor:
        # Verificar se a coluna já existe
        cursor.execute("SHOW COLUMNS FROM empresas LIKE 'atividade_contratos'")
        result = cursor.fetchone()
        
        if result:
            print("Coluna atividade_contratos já existe.")
        else:
            print("Adicionando coluna atividade_contratos...")
            cursor.execute("ALTER TABLE empresas ADD COLUMN atividade_contratos BOOLEAN DEFAULT FALSE AFTER atividade_locacao")
            connection.commit()
            print("Coluna adicionada com sucesso!")
            
finally:
    connection.close()
