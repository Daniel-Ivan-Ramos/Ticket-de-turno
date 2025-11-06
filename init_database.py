import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.models import db, Usuario, Municipio
from werkzeug.security import generate_password_hash

def init_database():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Inicializando base de datos...")
            
            db.create_all()
            print("✅ Tablas creadas exitosamente")
            
            admin = Usuario.query.filter_by(username='admin').first()
            if not admin:
                admin_user = Usuario(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    email='admin@sistema.com',
                    es_admin=True
                )
                db.session.add(admin_user)
                print("✅ Usuario administrador creado")
            else:
                print("⚠️  Usuario admin ya existe")
            
            if Municipio.query.count() == 0:
                municipios = [
                    Municipio(nombre='Aguascalientes', codigo='AGS'),
                    Municipio(nombre='Jesús María', codigo='JEM'),
                    Municipio(nombre='Calvillo', codigo='CAL'),
                    Municipio(nombre='Asientos', codigo='ASI'),
                    Municipio(nombre='Rincón de Romos', codigo='RIN')
                ]
                db.session.add_all(municipios)
                print("✅ Municipios de ejemplo creados")
            else:
                print(f"⚠️  Ya existen {Municipio.query.count()} municipios")
            
            db.session.commit()
            print("🎉 Base de datos inicializada correctamente!")
            print("\n📋 CREDENCIALES DE ACCESO:")
            print("   🌐 URL: http://localhost:5000")
            print("   👤 Usuario: admin")
            print("   🔑 Contraseña: admin123")
            
        except Exception as e:
            print(f"❌ Error durante la inicialización: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_database()