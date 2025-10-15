from extensions import db
from datetime import datetime
from sqlalchemy.sql import func # Importa 'func' para usar funções do banco (como data/hora automáticas)

# =========================================================
# CLASSES DE USUÁRIO (Admin, Empresa, ONG)
# =========================================================

class Admin(db.Model):
    __tablename__ = 'admin'
    id_admin = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    nome = db.Column(db.String(255))
    
    def get_id(self):
        return self.id_admin

class Empresa(db.Model):
    __tablename__ = 'empresa'
    id_empresa = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(20), unique=True, nullable=True)
    nome_empresa = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(50))
    endereco = db.Column(db.String(255))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow) 
    is_approved = db.Column(db.Boolean, default=False) 

    # O relacionamento é definido na classe Doacao/Solicitacao
    
    def get_id(self):
        return self.id_empresa

class ONG(db.Model):
    __tablename__ = 'ong'
    id_ong = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(20), unique=True, nullable=True)
    nome_ong = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(50))
    endereco = db.Column(db.String(255))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False) 

    # O relacionamento é definido na classe Doacao/Solicitacao
    
    def get_id(self):
        return self.id_ong

# =========================================================
# CLASSE DE DOAÇÃO
# =========================================================

class Doacao(db.Model):
    __tablename__ = 'doacao'
    id_doacao = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    tipo_alimento = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.String(50), nullable=False)
    data_validade = db.Column(db.Date) # Melhor usar data de validade para alimentos
    
    # status: disponivel -> reservado (por ONG) -> concluida
    status = db.Column(db.String(50), default='disponivel') 
    
    data_criacao = db.Column(db.DateTime(timezone=True), server_default=func.now())
    data_atualizacao = db.Column(db.DateTime(timezone=True), onupdate=func.now()) # Novo campo

    # Chave Estrangeira para a Empresa (quem doou)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id_empresa'), nullable=False)
    # Relacionamento: Empresa que criou a doação
    empresa = db.relationship('Empresa', backref='doacoes', foreign_keys=[id_empresa])
    
    # Chave Estrangeira para a ONG que reservou/recebeu (Pode ser NULL)
    id_ong_recebedora = db.Column(db.Integer, db.ForeignKey('ong.id_ong'), nullable=True)
    # Relacionamento: ONG que recebe/reservou a doação
    ong_recebedora = db.relationship('ONG', backref='doacoes_recebidas', foreign_keys=[id_ong_recebedora])
    
    # Chave Estrangeira para a Solicitação (Opcional: qual solicitação esta doação está atendendo)
    id_solicitacao = db.Column(db.Integer, db.ForeignKey('solicitacao.id_solicitacao'), nullable=True)
    solicitacao_atendida = db.relationship('Solicitacao', backref='doacao_atendimento', foreign_keys=[id_solicitacao])

    def to_dict(self):
        return {
            'id_doacao': self.id_doacao,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'tipo_alimento': self.tipo_alimento,
            'quantidade': self.quantidade,
            'data_validade': self.data_validade.isoformat() if self.data_validade else None,
            'status': self.status,
            'id_empresa': self.id_empresa,
            'id_ong_recebedora': self.id_ong_recebedora,
            'id_solicitacao': self.id_solicitacao,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
        }


# =========================================================
# CLASSE DE SOLICITAÇÃO (Criada por ONG)
# =========================================================

class Solicitacao(db.Model):
    __tablename__ = 'solicitacao'
    id_solicitacao = db.Column(db.Integer, primary_key=True)
    
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    item_necessario = db.Column(db.String(100), nullable=False)
    quantidade_necessaria = db.Column(db.String(50), nullable=False)
    data_limite = db.Column(db.Date) # Data limite para receber
    status = db.Column(db.String(50), default='aberta') # aberta, atendida, cancelada
    
    data_criacao = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    # Chave Estrangeira para a ONG (quem solicitou)
    id_ong = db.Column(db.Integer, db.ForeignKey('ong.id_ong'), nullable=False)
    # Relacionamento: ONG que criou a solicitação
    ong = db.relationship('ONG', backref='solicitacoes', foreign_keys=[id_ong])

    def to_dict(self):
        return {
            'id_solicitacao': self.id_solicitacao,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'item_necessario': self.item_necessario,
            'quantidade_necessaria': self.quantidade_necessaria,
            'data_limite': self.data_limite.isoformat() if self.data_limite else None,
            'status': self.status,
            'id_ong': self.id_ong,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
        }