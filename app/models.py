from datetime import datetime
from hashlib import md5
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)



class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)
    endereco = db.Column(db.String(120), nullable=False)
    telefone =  db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<Cliente %r>' % self.nome

class Entregador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)
    telefone =  db.Column(db.String(20), nullable=False)
    disponibilidade = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return '<Entregador %r>' % self.nome

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    entregador_id = db.Column(db.Integer, db.ForeignKey('entregador.id'), nullable=False)
    endereco_entrega = db.Column(db.String(120), nullable=False)
    data_entrega = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pendente', nullable=False)
  
    cliente = db.relationship('Cliente', backref=db.backref('pedidos', lazy=True))
    entregador = db.relationship('Entregador', backref=db.backref('pedidos', lazy=True))

    def __repr__(self):
        return '<Pedido %r>' % self.id

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)

    pedido = db.relationship('Pedido', backref=db.backref('itens', lazy=True))

    def __repr__(self):
        return '<ItemPedido %r>' % self.id

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefone =  db.Column(db.String(20), nullable=False)
    senha = db.Column(db.String(60), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    def __repr__(self):
     return '<Usuario %r>' % self.nome
