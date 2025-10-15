from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db  
from models import Doacao, Empresa, ONG, Solicitacao
from datetime import datetime

# ------------------------------
# Criação dos Blueprints de Doação e Solicitação
# ------------------------------
doacao_bp = Blueprint('doacao', __name__, url_prefix='/api/doacoes')
solicitacao_bp = Blueprint('solicitacao', __name__, url_prefix='/api/solicitacoes')

# ------------------------------
# Funções Auxiliares de Segurança
# ------------------------------
def get_user_type():
    """Retorna o tipo do usuário logado (admin, empresa, ong)."""
    current_user = get_jwt_identity()
    return current_user.get("tipo")

def get_user_id():
    """Retorna o ID do usuário logado."""
    current_user = get_jwt_identity()
    return current_user.get("id")

def doacao_to_dict(doacao):
    """Converte um objeto Doacao em um dicionário JSON."""
    empresa_nome = Empresa.query.get(doacao.id_empresa).nome_empresa if doacao.id_empresa else None

    return {
        "id_doacao": doacao.id_doacao,
        "titulo": doacao.titulo,
        "descricao": doacao.descricao,
        "tipo_alimento": doacao.tipo_alimento,
        "quantidade": doacao.quantidade,
        "data_disponibilidade": doacao.data_disponibilidade.isoformat() if doacao.data_disponibilidade else None,
        "status": doacao.status,
        "data_criacao": doacao.data_criacao.isoformat(),
        "id_empresa": doacao.id_empresa,
        "empresa": empresa_nome,
        "id_solicitacao_vinculada": doacao.id_solicitacao,
        "id_ong_recebedora": doacao.id_ong_recebedora
    }

# ------------------------------
# ROTAS DE DOAÇÃO (Empresa)
# ------------------------------
@doacao_bp.route('/', methods=['POST'])
@jwt_required()
def criar_doacao():
    """Endpoint para Empresas criarem uma nova Doação."""
    if get_user_type() != 'empresa':
        return jsonify({"msg": "Acesso negado. Apenas Empresas podem criar doações."}), 403

    data = request.json
    empresa = Empresa.query.get(get_user_id())

    # Garante que a empresa está aprovada
    if not empresa.is_approved:
        return jsonify({"msg": "Sua conta de Empresa precisa ser aprovada pelo Admin para criar doações."}), 403

    try:
        data_disp = datetime.strptime(data.get("data_disponibilidade"), '%Y-%m-%d').date()
    except:
        return jsonify({"msg": "Formato de data inválido. Use YYYY-MM-DD."}), 400

    nova_doacao = Doacao(
        titulo=data.get("titulo"),
        descricao=data.get("descricao"),
        tipo_alimento=data.get("tipo_alimento"),
        quantidade=data.get("quantidade"),
        data_disponibilidade=data_disp,
        id_empresa=get_user_id()
    )

    db.session.add(nova_doacao)
    db.session.commit()
    return jsonify({"msg": "Doação criada com sucesso!", "doacao": doacao_to_dict(nova_doacao)}), 201


@doacao_bp.route('/minhas', methods=['GET'])
@jwt_required()
def listar_minhas_doacoes():
    """Endpoint para Empresas listarem suas próprias Doações."""
    if get_user_type() != 'empresa':
        return jsonify({"msg": "Acesso negado. Apenas Empresas podem listar suas doações."}), 403

    doacoes = Doacao.query.filter_by(id_empresa=get_user_id()).all()
    return jsonify([doacao_to_dict(d) for d in doacoes])


@doacao_bp.route('/<int:doacao_id>', methods=['PUT'])
@jwt_required()
def atualizar_doacao(doacao_id):
    """Endpoint para Empresas atualizarem suas Doações."""
    if get_user_type() != 'empresa':
        return jsonify({"msg": "Acesso negado."}), 403

    doacao = Doacao.query.get(doacao_id)

    if not doacao or doacao.id_empresa != get_user_id():
        return jsonify({"msg": "Doação não encontrada ou acesso negado."}), 404

    if doacao.status != 'disponivel':
        return jsonify({"msg": "Não é possível alterar uma doação que não está 'disponivel'."}), 403

    data = request.json
    doacao.titulo = data.get("titulo", doacao.titulo)
    doacao.descricao = data.get("descricao", doacao.descricao)
    doacao.tipo_alimento = data.get("tipo_alimento", doacao.tipo_alimento)
    doacao.quantidade = data.get("quantidade", doacao.quantidade)

    if "data_disponibilidade" in data:
        try:
            doacao.data_disponibilidade = datetime.strptime(data["data_disponibilidade"], '%Y-%m-%d').date()
        except:
            return jsonify({"msg": "Formato de data inválido. Use YYYY-MM-DD."}), 400

    db.session.commit()
    return jsonify({"msg": "Doação atualizada com sucesso!", "doacao": doacao_to_dict(doacao)})


@doacao_bp.route('/<int:doacao_id>', methods=['DELETE'])
@jwt_required()
def deletar_doacao(doacao_id):
    """Endpoint para Empresas deletarem suas Doações (se estiverem 'disponivel')."""
    if get_user_type() != 'empresa':
        return jsonify({"msg": "Acesso negado."}), 403

    doacao = Doacao.query.get(doacao_id)

    if not doacao or doacao.id_empresa != get_user_id():
        return jsonify({"msg": "Doação não encontrada ou acesso negado."}), 404

    if doacao.status != 'disponivel':
        return jsonify({"msg": "Não é possível deletar uma doação que já foi solicitada ou concluída."}), 403

    db.session.delete(doacao)
    db.session.commit()
    return jsonify({"msg": "Doação deletada com sucesso!"}), 200

# ------------------------------
# ROTAS DE VISUALIZAÇÃO (ONG)
# ------------------------------
@doacao_bp.route('/disponiveis', methods=['GET'])
@jwt_required()
def listar_doacoes_disponiveis():
    """Endpoint para ONGs visualizarem todas as Doações disponíveis."""
    user_type = get_user_type()
    if user_type not in ['ong', 'admin']:
        return jsonify({"msg": "Acesso negado. Apenas ONGs e Admin podem visualizar."}), 403

    if user_type == 'ong':
        ong = ONG.query.get(get_user_id())
        if not ong.is_approved:
            return jsonify({"msg": "Sua conta de ONG precisa ser aprovada pelo Admin para visualizar doações."}), 403

    doacoes = Doacao.query.filter_by(status='disponivel').order_by(Doacao.data_criacao.desc()).all()
    return jsonify([doacao_to_dict(d) for d in doacoes])

# ------------------------------
# ROTAS DE SOLICITAÇÃO (ONG)
# ------------------------------
@solicitacao_bp.route('/<int:doacao_id>', methods=['POST'])
@jwt_required()
def solicitar_doacao(doacao_id):
    """Endpoint para ONGs solicitarem uma doação disponível."""
    if get_user_type() != 'ong':
        return jsonify({"msg": "Acesso negado. Apenas ONGs podem solicitar doações."}), 403

    ong_id = get_user_id()
    ong = ONG.query.get(ong_id)

    if not ong.is_approved:
        return jsonify({"msg": "Sua conta de ONG precisa ser aprovada pelo Admin para solicitar doações."}), 403

    doacao = Doacao.query.get(doacao_id)

    if not doacao:
        return jsonify({"msg": "Doação não encontrada."}), 404

    if doacao.status != 'disponivel':
        return jsonify({"msg": "Esta doação não está mais disponível para solicitação."}), 403

    solicitacao_existente = Solicitacao.query.filter_by(
        id_doacao=doacao_id,
        id_ong=ong_id,
        status_solicitacao='pendente'
    ).first()

    if solicitacao_existente:
        return jsonify({"msg": "Você já possui uma solicitação pendente para esta doação."}), 400

    nova_solicitacao = Solicitacao(
        id_doacao=doacao_id,
        id_ong=ong_id,
        status_solicitacao='pendente'
    )
    db.session.add(nova_solicitacao)
    db.session.flush()  # Obtém o ID da nova_solicitacao

    doacao.status = 'solicitada'
    doacao.id_solicitacao = nova_solicitacao.id_solicitacao
    doacao.id_ong_recebedora = ong_id

    db.session.commit()

    return jsonify({
        "msg": f"Solicitação enviada com sucesso para a Doação ID {doacao_id}.",
        "solicitacao_id": nova_solicitacao.id_solicitacao
    }), 201
