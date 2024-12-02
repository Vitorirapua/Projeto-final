from datetime import datetime
from flask import Flask, g, json, make_response, redirect, render_template, request, url_for, flash
from flask_mysqldb import MySQL

from functions.geral import datetime_para_string, remove_prefixo

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Necessário para usar flash messages

# Configurações de acesso ao MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Adicione sua senha se houver
app.config['MYSQL_DB'] = 'notepad_db'  # Nome do banco de dados
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_USE_UNICODE'] = True
app.config['MYSQL_CHARSET'] = 'utf8mb4'

mysql = MySQL(app)

@app.before_request
def before_request():
    cur = mysql.connection.cursor()
    cur.execute("SET NAMES utf8mb4")
    cur.execute("SET character_set_connection=utf8mb4")
    cur.execute("SET character_set_client=utf8mb4")
    cur.execute("SET character_set_results=utf8mb4")
    cur.execute("SET lc_time_names = 'pt_BR'")
    cur.close()

    cookie = request.cookies.get('user')

    if cookie:
        # Se o cookie existe, Converte o valor dele de JSON para dicionário
        g.user = json.loads(cookie)
    else:
        # Se o cookie não existe, a variável do ususário está vazia
        g.user = ''
        
@app.route('/')
def home():
    sql = '''
        SELECT id, title, content, status, date
        FROM notes
        WHERE status != 'off'  -- Exibe apenas notas com status 'on'
        ORDER BY id DESC;
    '''
    cur = mysql.connection.cursor()
    cur.execute(sql)
    notes = cur.fetchall()
    cur.close()

    return render_template('home.html', notes=notes)

@app.route('/new', methods=['GET', 'POST'])
def new_note():
    if request.method == 'POST':
        form = dict(request.form)
        sql = '''
            INSERT INTO notes (title, content, user)
            VALUES (%s, %s, %s)  
        '''
        cur = mysql.connection.cursor()
        cur.execute(sql, (form['title'], form['content'], g.user['id']))
        mysql.connection.commit()
        cur.close()

        flash('Nota adicionada com sucesso!', 'success')
        return redirect(url_for('home'))

    return render_template('new_note.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    if request.method == 'POST':
        form = dict(request.form)
        sql = '''
            UPDATE notes
            SET title = %s, content = %s
            WHERE id = %s
        '''
        cur = mysql.connection.cursor()
        cur.execute(sql, (form['title'], form['content'], id))
        mysql.connection.commit()
        cur.close()

        flash('Nota atualizada com sucesso!', 'success')
        return redirect(url_for('home'))

    sql = '''
        SELECT id, title, content, date
        FROM notes
        WHERE id = %s
    '''
    cur = mysql.connection.cursor()
    cur.execute(sql, (id,))
    note = cur.fetchone()
    cur.close()

    return render_template('edit_note.html', note=note)

@app.route('/delete/<int:id>')
def delete_note(id):
    sql = '''
        UPDATE notes
        SET status = 'off'  -- Muda o status da nota para 'off' em vez de deletá-la
        WHERE id = %s
    '''
    cur = mysql.connection.cursor()
    cur.execute(sql, (id,))
    mysql.connection.commit()
    cur.close()

    flash('Nota deletada com sucesso!', 'success')
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])  # Rota para login de usuário
def login():
    # Se o usuário está logado, redireciona para a página de perfil
    if g.user != '':
        return redirect(url_for('perfil'))

    erro = False

    # Se o formulário foi enviado
    if request.method == 'POST':

        # Pega os dados preenchidos no formulário
        form = dict(request.form)

        # Teste mesa
        # print('\n\n\n FORM:', form, '\n\n\n')

         # Pesquisa se os dados existem no banco de dados → usuario
        sql = '''
            SELECT *,
                -- Gera uma versão das datas em pt-BR para salvar no cookie
                DATE_FORMAT(u_data, '%%d/%%m/%%Y às %%H:%%m') AS u_databr,
                DATE_FORMAT(u_nascimento, '%%d/%%m/%%Y') AS u_nascimentobr
            FROM usuario
            WHERE u_email = %s
                AND u_senha = SHA1(%s)
                AND u_status = 'on'
            '''
        cur = mysql.connection.cursor()
        cur.execute(sql, (form['email'], form['senha'],))
        user = cur.fetchone()
        cur.close()


        # Teste mesa
        print('\n\n\n DB:', user, '\n\n\n')

        if user == None:
            # Se o usuário não foi encontrado
            erro = True
        else:
            # Se achou o usuário, apaga a senha do usuário
            del user['u_senha']

            # Extrai o primeiro nome do usuário
            user['u_pnome'] = user['u_nome'].split()[0]

            # Formata as datas para usar no JSON
            user = datetime_para_string(user)

            # Remove o prefixo das chaves do dicionário
            cookie_valor = remove_prefixo(user)

            # Converte os dados em JSON (texto) para gravar no cookie,
            # porque cookies só aceitam dados na forma texto
            cookie_json = json.dumps(cookie_valor)

            # Teste de mesa
            # print('\n\n\n JSON:', cookie_json, '\n\n\n')

            # Prepara a página de destino → index
            resposta = make_response(redirect(url_for('home')))

            # Cria o cookie
            resposta.set_cookie(
                key='user',  # Nome do cookie
                value=cookie_json,  # Valor a ser gravado no cookie
                max_age=60 * 60 * 24 * 365  # Validade do cookie em segundos
            )

            # Redireciona para a página de destino → index
            return resposta

    # Dados, variáveis e valores a serem passados para o template HTML
    pagina = {
        'titulo': 'Login',
        'erro': erro
    }

    return render_template('login.html', **pagina)

if __name__ == '__main__':
    app.run(debug=True)