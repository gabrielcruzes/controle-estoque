from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'l0r#l3!9p67aqm@!n(ko5@3&^ri29-o4z=j5-x9i+wr17=pomc'
SENHA_CORRETA = "soeusei123"

# ==============================================
# FUNÇÕES AUXILIARES
# ==============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logado' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    conn = sqlite3.connect('estoque.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL
        )''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )''')

# ==============================================
# ROTAS DE AUTENTICAÇÃO
# ==============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form.get('senha')
        if senha == SENHA_CORRETA:
            session['logado'] = True
            return redirect(url_for('index'))
        flash('Senha incorreta!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))

# ==============================================
# ROTAS PRINCIPAIS
# ==============================================

@app.route('/')
@login_required
def index():
    with get_db_connection() as conn:
        produtos = conn.execute('SELECT * FROM produtos ORDER BY nome ASC').fetchall()
        total_estoque = conn.execute('SELECT SUM(quantidade) FROM produtos').fetchone()[0] or 0
    return render_template('index.html', produtos=produtos, total_estoque=total_estoque)

@app.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar():
    if request.method == 'POST':
        nome = request.form['nome']
        quantidade = int(request.form['quantidade'])
        
        with get_db_connection() as conn:
            conn.execute('INSERT INTO produtos (nome, quantidade) VALUES (?, ?)', (nome, quantidade))
            conn.commit()
        return redirect(url_for('index'))
    return render_template('cadastrar.html')

@app.route('/movimentar', methods=['GET', 'POST'])
@login_required
def movimentar():
    if request.method == 'POST':
        produto_id = int(request.form['produto_id'])
        quantidade = int(request.form['quantidade'])
        tipo = request.form['tipo']
        data_movimentacao = request.form['data_movimentacao'] or datetime.now().strftime('%Y-%m-%dT%H:%M')
        
        try:
            data_formatada = datetime.strptime(data_movimentacao, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Formato de data/hora inválido!', 'danger')
            return redirect(url_for('movimentar'))
        
        with get_db_connection() as conn:
            # Atualizar estoque
            operacao = '+' if tipo == 'entrada' else '-'
            conn.execute(f'UPDATE produtos SET quantidade = quantidade {operacao} ? WHERE id = ?',
                        (quantidade, produto_id))
            
            # Registrar movimentação
            conn.execute('''
                INSERT INTO movimentacoes (produto_id, quantidade, tipo, data)
                VALUES (?, ?, ?, ?)
            ''', (produto_id, quantidade, tipo, data_formatada))
            
            conn.commit()
        return redirect(url_for('index'))
    
    with get_db_connection() as conn:
        produtos = conn.execute('SELECT * FROM produtos ORDER BY nome ASC').fetchall()
    return render_template('movimentar.html', produtos=produtos, datetime_now=datetime.now().strftime('%Y-%m-%dT%H:%M'))

@app.route('/produtos')
@login_required
def listar_produtos():
    with get_db_connection() as conn:
        produtos = conn.execute('SELECT * FROM produtos ORDER BY nome ASC').fetchall()
    return render_template('produtos.html', produtos=produtos)

@app.route('/deletar_produto/<int:id>')
@login_required
def deletar_produto(id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM movimentacoes WHERE produto_id = ?', (id,))
        conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
        conn.commit()
    return redirect(url_for('listar_produtos'))

@app.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    if request.method == 'POST':
        novo_nome = request.form['nome']
        nova_quantidade = int(request.form['quantidade'])
        
        with get_db_connection() as conn:
            conn.execute('UPDATE produtos SET nome = ?, quantidade = ? WHERE id = ?',
                        (novo_nome, nova_quantidade, id))
            conn.commit()
        return redirect(url_for('listar_produtos'))
    
    with get_db_connection() as conn:
        produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
    return render_template('editar_produto.html', produto=produto)

@app.route('/historico')
@login_required
def historico():
    with get_db_connection() as conn:
        movimentacoes = conn.execute('''
            SELECT m.id, p.nome, m.quantidade, m.tipo, m.data
            FROM movimentacoes m
            JOIN produtos p ON m.produto_id = p.id
            ORDER BY m.data DESC
        ''').fetchall()
    return render_template('historico.html', movimentacoes=movimentacoes)

# ==============================================
# INICIALIZAÇÃO
# ==============================================

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)