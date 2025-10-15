import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from datetime import timedelta
import pymysql
from extensions import db, bcrypt, jwt
import os

# ------------------------------
# INICIALIZAÇÃO DO FLASK E CONFIGURAÇÕES
# ------------------------------
app = Flask(__name__) 

# Hack para o SQLAlchemy aceitar o driver pymysql
pymysql.install_as_MySQLdb()

# Configuração do MySQL com SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:bardopastel@localhost/foodback_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração JWT
app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# ------------------------------
# INICIALIZAÇÃO DAS EXTENSÕES COM O APP
# ------------------------------
db.init_app(app)
jwt.init_app(app)
bcrypt.init_app(app)


# ------------------------------
# FUNÇÕES AUXILIARES JWT
# ------------------------------
@jwt.user_identity_loader
def user_identity_lookup(user_data):
    """Define qual informação do usuário será armazenada no token JWT."""
    return user_data

# ------------------------------
# IMPORTAÇÃO DOS MODELS E BLUEPRINTS
# ------------------------------

from models import Admin, Empresa, ONG, Doacao 
from auth import auth_bp 
from doacao import doacao_bp, solicitacao_bp  

# ------------------------------
# REGISTRO DOS BLUEPRINTS
# ------------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(doacao_bp)       # <-- Adicionado aqui
app.register_blueprint(solicitacao_bp)  # <-- Adicionado aqui


# ------------------------------
# Rotas Principais (Home, Protegida, Admin, etc)
# ------------------------------
@app.route('/')
def home():
    return render_template('login.html') 

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected_route():
    current_user = get_jwt_identity()
    return jsonify({
        "msg": f"Acesso garantido para o usuário ID: {current_user['id']}, Tipo: {current_user['tipo']}"
    })

# Rota de aprovação de usuário (Admin)
@app.route('/api/admin/approve', methods=['POST'])
@jwt_required()
def approve_user():
    current_user = get_jwt_identity()
    if current_user["tipo"] != "admin":
        return jsonify({"msg": "Acesso negado. Somente Administradores."}), 403

    data = request.json
    user_id = data.get("user_id")
    user_type = data.get("user_type")

    if user_type == 'empresa':
        user = Empresa.query.get(user_id)
    elif user_type == 'ong':
        user = ONG.query.get(user_id)
    else:
        return jsonify({"msg": "Tipo de usuário para aprovação inválido"}), 400

    if not user:
        return jsonify({"msg": f"{user_type.capitalize()} não encontrada"}), 404

    user.is_approved = True
    db.session.commit()

    return jsonify({"msg": f"{user_type.capitalize()} ID {user_id} aprovada com sucesso"})

# ------------------------------
# MAIN
# ------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco MySQL
    app.run(debug=True)
