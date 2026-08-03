from src.app import create_app

# Ajuste: cria a app e executa a simulação dentro do app_context
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Importa e executa o main do script de simulação
        from scripts.emitir_nfs_simulado import main
        main()
