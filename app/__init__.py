from flask import Flask
from flask_login import LoginManager
from config import Config

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    from app.models import db
    db.init_app(app)
    
    login_manager.init_app(app)
    
    from app.routes import main_bp
    from app.auth import auth_bp
    from app.api.routes import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))
    
    return app