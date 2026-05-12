# Procfile para Railway
# Define como iniciar a aplicação

web: gunicorn -w 4 -b 0.0.0.0:$PORT "src.app:create_app()" --timeout 120
