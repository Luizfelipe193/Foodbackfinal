import os
import sys

# Adiciona o diretório raiz do projeto (onde está o app.py) ao caminho de importação do Python.
# Isso resolve o erro 'attempted relative import with no known parent package'.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # A importação agora deve funcionar perfeitamente
    from app import app, db

    with app.app_context():
        # Este comando apaga todas as tabelas e as recria com base nos modelos (models.py)
        db.drop_all()
        db.create_all()
        print("✅ SUCESSO! As tabelas do banco de dados foram criadas (ou já existem).")

except Exception as e:
    print("❌ ERRO FATAL: Falha ao criar as tabelas.")
    print(f"Detalhe do Erro: {e}")
