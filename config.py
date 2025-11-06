import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-super-secreta-para-flask-2024'
    
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/ticket_system'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)