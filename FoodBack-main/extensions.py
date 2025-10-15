from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

# Inicialização das Extensões (Instâncias Globais)
db = SQLAlchemy() 
bcrypt = Bcrypt() 
jwt = JWTManager() 