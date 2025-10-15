import os
import sys
from getpass import getpass

# Ajuste do caminho: Adiciona o diretório pai (onde estão app.py, models.py) ao PATH
# Isso garante que as importações abaixo funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Importa as instâncias necessárias do app.py e os modelos
    from app import app, db, bcrypt
    from models import Admin
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Verifique se as dependências (flask, flask_sqlalchemy, etc.) estão instaladas e se app.py/models.py estão no diretório correto.")
    sys.exit(1)


def seed_admin():
    """Cria um usuário Administrador inicial no banco de dados."""
    
    # Executa a operação dentro do contexto da aplicação Flask
    with app.app_context():
        print("--- Criador de Administrador Inicial ---")
        
        # 1. Verifica se já existe algum administrador
        if Admin.query.first():
            print("Um administrador já existe no banco de dados. Operação cancelada.")
            return

        print("Nenhum administrador encontrado. Criando novo usuário admin...")

        # 2. Solicita as credenciais do novo admin
        # NOTA: O 'getpass' oculta a senha digitada no terminal
        nome = input("Nome do Administrador: ")
        email = input("Email (será usado para login): ")
        
        # Loop para garantir que as senhas coincidam
        while True:
            senha1 = getpass("Senha: ")
            senha2 = getpass("Confirme a Senha: ")
            if senha1 == senha2:
                break
            print("As senhas não coincidem. Tente novamente.")
            
        # 3. Hash da senha
        hashed_password = bcrypt.generate_password_hash(senha1).decode('utf-8')

        # 4. Cria e salva o objeto Admin
        try:
            admin_user = Admin(
                nome=nome,
                email=email,
                senha=hashed_password
            )
            
            db.session.add(admin_user)
            db.session.commit()
            print("\n✅ Sucesso! Usuário Administrador criado e salvo no banco de dados.")
            print(f"Nome: {nome}, Email: {email}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao criar o usuário administrador: {e}")


if __name__ == '__main__':
    seed_admin()