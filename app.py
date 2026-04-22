import sqlite3
import webbrowser
import threading
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'chave_secreta_ecologica_tcc'
DATABASE = "database.db"
app.jinja_env.cache = {}

def conectar():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Isso permite usar usuario['id_usuario']
    return conn

def init_db():
    conn = conectar()
    cur = conn.cursor()
    # Tabela Usuários (Conforme modelo.sql do TCC)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Tabela Atividades
    cur.execute("""
        CREATE TABLE IF NOT EXISTS atividades (
            id_atividade INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            fator_emissao REAL NOT NULL
        )
    """)
    # Tabela Registros
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registros_carbono (
            id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_atividade INTEGER NOT NULL,
            quantidade REAL NOT NULL,
            emissao_total REAL,
            data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
            FOREIGN KEY (id_atividade) REFERENCES atividades(id_atividade)
        )
    """)
    
    # Inserir dados iniciais se a tabela de atividades estiver vazia
    cur.execute("SELECT COUNT(*) FROM atividades")
    if cur.fetchone()[0] == 0:
        atividades_iniciais = [
            ("Transporte - Carro (km)", 0.21),
            ("Energia elétrica (kWh)", 0.06),
            ("Alimentação - Carne (kg)", 27.0)
        ]
        cur.executemany("INSERT INTO atividades (nome, fator_emissao) VALUES (?, ?)", atividades_iniciais)
    
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        conn = conectar()
        usuario = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        conn.close()

        if usuario and check_password_hash(usuario["senha"], senha):
            session["user_id"] = usuario["id_usuario"] # Agora a chave existe!
            session["usuario_nome"] = usuario["nome"]
            session["usuario_email"] = usuario["email"]
            return redirect(url_for("index"))
        else:
            flash("E-mail ou senha incorretos.")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])
        conn = conectar()
        try:
            conn.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
            conn.commit()
            flash("Cadastro realizado com sucesso! Faça login.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Este e-mail já está cadastrado.")
        finally:
            conn.close()
    return render_template("cadastro.html")

@app.route("/index")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = conectar()
    atividades = conn.execute("SELECT * FROM atividades").fetchall()
    res = conn.execute("SELECT SUM(emissao_total) FROM registros_carbono WHERE id_usuario = ?", (session["user_id"],)).fetchone()
    total_co2 = res[0] if res[0] else 0
    conn.close()
    
    return render_template("index.html", atividades=atividades, total=total_co2)

@app.route("/registrar", methods=["POST"])
def registrar():
    if "user_id" not in session:
        return redirect(url_for("login"))

    id_ativ = request.form["atividade"]
    qtd = float(request.form["quantidade"])
    
    conn = conectar()
    ativ = conn.execute("SELECT fator_emissao FROM atividades WHERE id_atividade = ?", (id_ativ,)).fetchone()
    
    if ativ:
        emissao = qtd * ativ["fator_emissao"]
        conn.execute("""
            INSERT INTO registros_carbono (id_usuario, id_atividade, quantidade, emissao_total)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], id_ativ, qtd, emissao))
        conn.commit()
        flash("Atividade registrada com sucesso!")
    
    conn.close()
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

def abrir_navegador():
    webbrowser.open_new("http://127.0.0.1:5000")


@app.route("/relatorio")
def relatorio():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = conectar()
    registros = conn.execute("""
        SELECT a.nome, r.quantidade, r.emissao_total, r.data_registro
        FROM registros_carbono r
        JOIN atividades a ON r.id_atividade = a.id_atividade
        WHERE r.id_usuario = ?
        ORDER BY r.data_registro DESC
    """, (session["user_id"],)).fetchall()
    conn.close()
    
    return render_template("relatorio.html", registros=registros)

print(app.url_map)

if __name__ == "__main__":
    init_db()
    # threading garante que o navegador abra SEM travar o servidor
    threading.Timer(1.5, abrir_navegador).start()
    app.run(debug=True, use_reloader=False)


