import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.models import db, Usuario, Municipio, Ticket

app = create_app()

def test_database():
    with app.app_context():
        try:
            print("🧪 Probando conexión a la base de datos...")
            
            db.engine.connect()
            print("✅ Conexión a MySQL exitosa")
            
            usuarios_count = Usuario.query.count()
            municipios_count = Municipio.query.count()
            tickets_count = Ticket.query.count()
            
            print(f"📊 Estadísticas de la base de datos:")
            print(f"   👥 Usuarios: {usuarios_count}")
            print(f"   🏙️  Municipios: {municipios_count}")
            print(f"   🎫 Tickets: {tickets_count}")
            
            municipios = Municipio.query.all()
            print(f"\n🏘️  Municipios disponibles:")
            for mun in municipios:
                print(f"   - {mun.nombre} ({mun.codigo})")
                
        except Exception as e:
            print(f"❌ Error en la prueba: {e}")

if __name__ == '__main__':
    test_database()