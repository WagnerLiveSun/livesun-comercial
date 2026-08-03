# LiveSun Comercial
# Sistema de Gestão Comercial e Financeira

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.app import create_app

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration from environment or use defaults
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('SERVER_PORT', 5000))
    # Force debug mode for development with auto-reload
    debug = True
    
    print(f'\n{"="*70}')
    print(f'  LiveSun Comercial - Sistema de Gestão Comercial e Financeira')
    print(f'  URL: http://localhost:{port}')
    print(f'  Login padrão: admin / admin123')
    print(f'  Modo DEBUG ativado (auto-reload habilitado)')
    print(f'{"="*70}\n')
    
    # Use reloader with extra files to watch
    app.run(host=host, port=port, debug=debug, use_reloader=True, extra_files=['src/routes/comercial_operacional.py'])
