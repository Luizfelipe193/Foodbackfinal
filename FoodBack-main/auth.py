from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
# Importa as extensões do arquivo neutro extensions.py
from extensions import db, bcrypt 
from models import Admin, Empresa, ONG # Importa os modelos

# Criação do Blueprint de Autenticação
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ------------------------------
# Registro de Usuários
# ------------------------------
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    nome = data.get("nome")
    email = data.get("email")
    senha = data.get("senha")
    tipo = data.get("tipo")
    cnpj = data.get("cnpj")

    if tipo not in ["empresa", "ong"]:
        return jsonify({"msg": "Tipo de usuário inválido para registro via API"}), 400

    if not nome or not email or not senha:
          return jsonify({"msg": "Dados obrigatórios (nome, email, senha) faltando."}), 400

    hashed_password = bcrypt.generate_password_hash(senha).decode('utf-8')
    user = None
    
    try:
        if tipo == "empresa":
            # Checa se o email ou CNPJ já existe
            if Empresa.query.filter_by(email=email).first() or Empresa.query.filter_by(cnpj=cnpj).first():
                return jsonify({"msg": "Erro: Email ou CNPJ já está cadastrado como Empresa."}), 400

            user = Empresa(
                nome_empresa=nome,
                email=email,
                senha=hashed_password,
                cnpj=cnpj,
                is_approved=False
            )
        
        elif tipo == "ong":
            # Checa se o email ou CNPJ já existe
            if ONG.query.filter_by(email=email).first() or ONG.query.filter_by(cnpj=cnpj).first():
                return jsonify({"msg": "Erro: Email ou CNPJ já está cadastrado como ONG."}), 400

            user = ONG(
                nome_ong=nome,
                email=email,
                senha=hashed_password,
                cnpj=cnpj,
                is_approved=False
            )
        
        db.session.add(user)
        db.session.commit()
        return jsonify({"msg": f"{tipo.capitalize()} registrado com sucesso. Aguarde aprovação do admin!"}), 201
        
    except Exception as e:
        db.session.rollback()
        # Removido o catch genérico por Duplicate entry, a verificação agora é explícita acima
        return jsonify({"msg": f"Erro interno ao registrar. Detalhe: {e}"}), 500


# ------------------------------
# Login
# ------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    senha = data.get("senha")
    
    if not email or not senha:
        return jsonify({"msg": "Email e senha são obrigatórios."}), 400
        
    user = None
    tipo = None
    
    # 1. Tentar Admin
    admin = Admin.query.filter_by(email=email).first()
    if admin and bcrypt.check_password_hash(admin.senha, senha):
        user = admin
        tipo = "admin"
    
    # 2. Tentar Empresa
    if not user:
        empresa = Empresa.query.filter_by(email=email).first()
        if empresa and bcrypt.check_password_hash(empresa.senha, senha):
            if not empresa.is_approved:
                return jsonify({"msg": "Empresa aguardando aprovação do administrador"}), 403
            user = empresa
            tipo = "empresa"
    
    # 3. Tentar ONG
    if not user:
        ong = ONG.query.filter_by(email=email).first()
        if ong and bcrypt.check_password_hash(ong.senha, senha):
            if not ong.is_approved:
                return jsonify({"msg": "ONG aguardando aprovação do administrador"}), 403
            user = ong
            tipo = "ong"
            
    if user:
        # Cria o token com a ID correta e o tipo de usuário
        access_token = create_access_token(
            identity={"id": user.get_id(), "tipo": tipo}
        )
        return jsonify(access_token=access_token, user_type=tipo) # Retorna user_type para o cliente

    return jsonify({"msg": "Credenciais inválidas"}), 401
