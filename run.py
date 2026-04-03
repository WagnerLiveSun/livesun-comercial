# LiveSun Controller
# Sistema de Gestão Financeira

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
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    print(f'\n{"="*70}')
    print(f'  LiveSun Controller - Sistema de Gestão Financeira')
    print(f'  URL: http://localhost:{port}')
    print(f'  Login padrão: admin / admin123')
    print(f'{"="*70}\n')
    
    app.run(host=host, port=port, debug=debug)
