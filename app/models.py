from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import qrcode
from io import BytesIO
import base64

db = SQLAlchemy()

class Municipio(db.Model):
    __tablename__ = 'municipios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    codigo = db.Column(db.String(10), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True)
    
    tickets = db.relationship('Ticket', backref='municipio', lazy=True)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    curp = db.Column(db.String(18), nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(100), nullable=False)
    apellido_materno = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    municipio_id = db.Column(db.Integer, db.ForeignKey('municipios.id'), nullable=False)
    numero_turno = db.Column(db.Integer, nullable=False)
    estatus = db.Column(db.Enum('Pendiente', 'Resuelto'), default='Pendiente')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('municipio_id', 'numero_turno', name='uq_municipio_turno'),
    )
    
    def generar_qr_base64(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"CURP:{self.curp}|TURNO:{self.numero_turno}|MUN:{self.municipio_id}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()