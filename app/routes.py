from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User, Cliente, Entregador, Pedido, ItemPedido
import matplotlib.pyplot as plt
import concurrent.futures
import io
import base64
from promisio import promisify

import threading

@promisify
def gerar_grafico(datas, tempos_medios):
    # Gerar o gráfico
    plt.plot(datas, tempos_medios, color='red')
    plt.xlabel('Data')
    plt.ylabel('Tempo Médio (minutos)')
    plt.title('Gráfico de Tempo Médio de Entrega de Pedidos')
    fig = plt.gcf()
    # Converter o gráfico para base64
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png')
    buffer.seek(0)       
    fig.savefig('static/grafico.png', format='png')


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/')
@app.route('/index')
@login_required
def index():  

    tempos_medios = [10, 20, 15, 25, 30]
    datas = ['10/01', '11/01', '12/01', '13/01', '14/01']  
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]    
        
   
        
    # Exibir o gráfico na rota "/"
    return render_template('index.html', title='Home', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/clientes/')
def clientes():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)


@app.route('/cliente/novo/', methods=['GET', 'POST'])
def novo_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        telefone = request.form['telefone']
        cliente = Cliente(nome=nome, endereco=endereco, telefone=telefone)
        db.session.add(cliente)
        db.session.commit()
        return redirect(url_for('clientes'))
    return render_template('novo_cliente.html')


@app.route('/cliente/delete/<id>', methods=['GET', 'POST'])
def delete_cliente(id):
    if request.method == 'POST':
        cliente_id = id
        cliente = Cliente.query.get(cliente_id)
        if cliente:
            db.session.delete(cliente)
            db.session.commit()
            flash('Cliente excluído com sucesso!')
            return redirect(url_for('clientes'))
        else:
            flash('Cliente não encontrado!')
            return redirect(url_for('clientes'))
    else:
        cliente_id = request.args.get('cliente_id')
        cliente = Cliente.query.get(cliente_id)
    if cliente:
        return render_template('delete_cliente.html', cliente=cliente)
    else:
        flash('Cliente não encontrado!')
        return redirect(url_for('clientes'))


@app.route('/pedidos/')
def listar_pedidos():
    pedidos = Pedido.query.all()
    return render_template('listar_pedidos.html', pedidos=pedidos)


@app.route('/pedido/adicionar/', methods=['GET', 'POST'])
def adicionar_pedido():
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        entregador_id = request.form['entregador_id']
        endereco_entrega = request.form['endereco_entrega']
        data_entrega = datetime.strptime(
            request.form['data_entrega'], '%Y-%m-%dT%H:%M')

        pedido = Pedido(cliente_id=cliente_id, entregador_id=entregador_id,
                        endereco_entrega=endereco_entrega, data_entrega=data_entrega)

        db.session.add(pedido)
        db.session.commit()
        flash('Pedido adicionado com sucesso!')
        return redirect(url_for('listar_pedidos'))

    clientes = Cliente.query.all()
    entregadores = Entregador.query.all()
    return render_template('adicionar_pedido.html', clientes=clientes, entregadores=entregadores)


@app.route('/pedido/editar/', methods=['GET', 'POST'])
def editar_pedido():
    if request.method == 'POST':
        pedido_id = request.form['pedido_id']
        cliente_id = request.form['cliente_id']
        entregador_id = request.form['entregador_id']
        endereco_entrega = request.form['endereco_entrega']
        data_entrega = request.form['data_entrega']
        status = request.form['status']

        pedido = Pedido.query.get(pedido_id)
        pedido.cliente_id = cliente_id
        pedido.entregador_id = entregador_id
        pedido.endereco_entrega = endereco_entrega
        pedido.data_entrega = data_entrega
        pedido.status = status

        db.session.commit()
        flash('Pedido editado com sucesso!')
        return redirect(url_for('listar_pedidos'))
    else:
        pedido_id = request.args.get('pedido_id')
        pedido = Pedido.query.get(pedido_id)
        clientes = Cliente.query.all()
        entregadores = Entregador.query.all()
        return render_template('editar_pedido.html', pedido=pedido, clientes=clientes, entregadores=entregadores)


@app.route('/pedido/excluir/', methods=['GET', 'POST'])
def excluir_pedido():
    if request.method == 'POST':
        pedido_id = request.form['pedido_id']

        pedido = Pedido.query.get(pedido_id)
        db.session.delete(pedido)
        db.session.commit()
        flash('Pedido excluído com sucesso!')
        return redirect(url_for('listar_pedidos'))
    else:
        pedido_id = request.args.get('pedido_id')
        pedido = Pedido.query.get(pedido_id)
        return render_template('excluir_pedido.html', pedido=pedido)


@app.route('/entregadores/')
def listar_entregadores():
    entregadores = Entregador.query.all()
    return render_template('listar_entregadores.html', entregadores=entregadores)


@app.route('/entregadores/add/', methods=['GET', 'POST'])
def adicionar_entregador():
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        disponibilidade = request.form['disponibilidade'] == 'True'

        entregador = Entregador(
            nome=nome, telefone=telefone, disponibilidade=disponibilidade)
        db.session.add(entregador)
        db.session.commit()

        return redirect(url_for('listar_entregadores'))

    return render_template('adicionar_entregador.html')


@app.route('/entregadores/edit/<int:id>/', methods=['GET', 'POST'])
def editar_entregador(id):
    entregador = Entregador.query.get(id)

    if request.method == 'POST':
        entregador.nome = request.form['nome']
        entregador.telefone = request.form['telefone']
        entregador.disponibilidade = request.form['disponibilidade'] == 'True'

        db.session.commit()

        return redirect(url_for('listar_entregadores'))

    return render_template('editar_entregador.html', entregador=entregador)


@app.route('/entregadores/delete/<int:id>/ss', methods=['GET', 'POST'])
def deletar_entregador(id):
    entregador = Entregador.query.get(id)

    if request.method == 'POST':
        try:
            db.session.delete(entregador)
            db.session.commit()
        except:
            db.session.rollback()
            return 'Erro ao deletar entregador'

        return redirect(url_for('listar_entregadores'))

    return render_template('deletar_entregador.html', entregador=entregador)


