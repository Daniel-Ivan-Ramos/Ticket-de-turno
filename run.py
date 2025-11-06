import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask...")
    print("📊 Sistema de Gestión de Turnos")
    print("🌐 Disponible en: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)