from datetime import datetime
from flask import Flask, g, json, make_response, redirect, render_template, request, url_for, flash
from flask_mysqldb import MySQL
from hashlib import sha1

from functions.geral import calcular_idade, datetime_para_string, gerar_senha, remove_prefixo

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
    print('\n\n\n cookie:', cookie ,'\n\n\n')
    if cookie:
        # Se o cookie existe, Converte o valor dele de JSON para dicionário
        g.appuser = json.loads(cookie)
    else:
        # Se o cookie não existe, a variável do ususário está vazia
        g.appuser = ''
    




@app.route('/')
def home():
    if g.appuser == '':
        return redirect(url_for('login'))


    sql = '''
        SELECT id, title, content, status, date
        FROM notes
        WHERE status != 'off' AND user = %s
        ORDER BY id DESC;
    '''
    cur = mysql.connection.cursor()
    cur.execute(sql, (g.appuser['id'],))
    notes = cur.fetchall()
    cur.close()



    return render_template('home.html', notes=notes, usuario=g.appuser)

@app.route('/new', methods=['GET', 'POST'])
def new_note():
    if g.appuser == '':
        return redirect(url_for('login'))

    if request.method == 'POST':
        form = dict(request.form)
        sql = '''
            INSERT INTO notes (title, content, user)
            VALUES (%s, %s, %s)  
        '''
        cur = mysql.connection.cursor()
        cur.execute(sql, (form['title'], form['content'], g.appuser['id']))
        mysql.connection.commit()
        cur.close()

        flash('Nota adicionada com sucesso!', 'success')
        return redirect(url_for('home'))

    return render_template('new_note.html', usuario=g.appuser)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    if g.appuser == '':
        return redirect(url_for('login'))
    
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

    return render_template('edit_note.html', note=note , usuario=g.appuser)

@app.route('/delete/<int:id>')
def delete_note(id):
    if g.appuser == '':
        return redirect(url_for('login'))
    
    sql = '''
        UPDATE notes
        SET status = 'off'  -- Muda o status da nota para 'off' em vez de deletá-la
        WHERE id = %s
    '''
    cur = mysql.connection.cursor()
    cur.execute(sql, [id])
    mysql.connection.commit()
    cur.close()

    flash('Nota deletada com sucesso!', 'success')
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])  # Rota para login de usuário
def login():
    # Se o usuário está logado, redireciona para a página de perfil
    if g.appuser != '':
        return redirect(url_for('perfil'))

    erro = False

    # Se o formulário foi enviado
    if request.method == 'POST':

        # Pega os dados preenchidos no formulário
        form = dict(request.form)

        # Teste mesa
        # print('\n\n\n FORM:', form, '\n\n\n')

         # Pesquisa se os dados existem no banco de dados → g.appuser
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

@app.route('/perfil')
def perfil():

    # Se o usuário não está logado redireciona para a página de login
    if g.appuser == '':
        return redirect(url_for('login'))

    # Calcula idade do usuário
    g.appuser['idade'] = calcular_idade(g.appuser['nascimento'])

    # Obtém a quantidade de trecos ativos do usuário
    sql = "SELECT count(id) AS total FROM notes WHERE user = %s AND status = 'on'"
    cur = mysql.connection.cursor()
    cur.execute(sql, (g.appuser['id'],))
    row = cur.fetchone()
    cur.close()

    # Teste de mesa
    # print('\n\n\n DB', row, '\n\n\n')

    # Adiciona a quantidade ao perfil
    g.appuser['total'] = row['total']

    # Dados, variáveis e valores a serem passados para o template HTML
    pagina = {
        'usuario': g.appuser,
    }

    # Renderiza o template HTML, passaod valores para ele
    return render_template('perfil.html', **pagina)

@app.route('/cadastro', methods=['GET', 'POST'])  # Cadastro de usuário
def cadastro():

    jatem = ''
    success = False

    # Se o usuário está logado redireciona para a página de perfil
    if g.appuser != '':
        return redirect(url_for('perfil'))

    if request.method == 'POST':

        form = dict(request.form)

        # Verifica se usuário já está cadastrado, pelo e-mail
        sql = "SELECT u_id, u_status FROM usuario WHERE u_email = %s AND u_status != 'del'"
        cur = mysql.connection.cursor()
        cur.execute(sql, (form['email'],))
        rows = cur.fetchall()
        cur.close()

        # print('\n\n\n LEN:', len(rows), '\n\n\n')

        if len(rows) > 0:
            # Se já está cadastrado
            if rows[0]['u_status'] == 'off':
                jatem = 'Este e-mail já está cadastrado para um usuário inativo. Entre em contato para saber mais.'
            else:
                jatem = 'Este e-mail já está cadastrado. Tente fazer login ou solicitar uma nova senha.'
        else:
            # Se não está cadastrado, inclui os dados do form no banco de dados
            sql = "INSERT INTO usuario (u_nome, u_nascimento, u_email, u_senha) VALUES (%s, %s, %s, SHA1(%s))"
            cur = mysql.connection.cursor()
            cur.execute(
                sql, (
                    form['nome'],
                    form['nascimento'],
                    form['email'],
                    form['senha'],
                )
            )
            mysql.connection.commit()
            cur.close()

            success = True

    # Dados, variáveis e valores a serem passados para o template HTML
    pagina = {
        'jatem': jatem,
        'success': success,
    }

    return render_template('cadastro.html', **pagina)

@app.route('/logout')
def logout():

    # Se o usuário não está logado redireciona para a página de login
    if g.appuser == '':
        return redirect(url_for('login'))

    # Página de destino após logout
    resposta = make_response(redirect(url_for('login')))

    # Apaga o cookie do usuário
    resposta.set_cookie(
        key='user',  # Nome do cookie
        value='',  # Apara o valor do cookie
        max_age=0  # A validade do cookie é ZERO
    )

    # Redireciona para login
    return resposta

@app.route('/apagausuario')
def apagausuario():
    # Apaga um usuário do sistema
    # Também apaga todos os seus "trecos"

    # Se o usuário não está logado redireciona para a página de login
    if g.appuser == '':
        return redirect(url_for('login'))

    # Configura o status do usuário para 'del' no banco de dados
    sql = "UPDATE usuario SET u_status = 'del' WHERE u_id = %s"
    cur = mysql.connection.cursor()
    cur.execute(sql, (g.appuser['id'],))
    mysql.connection.commit()
    cur.close()

    # Configura o status dos itens do usuário para 'del' no banco de dados
    sql = "UPDATE notes SET status = 'del' WHERE user = %s"
    cur = mysql.connection.cursor()
    cur.execute(sql, (g.appuser['id'],))
    mysql.connection.commit()
    cur.close()

    # Página de destino de logout
    resposta = make_response(redirect(url_for('login')))

    # apaga o cookie do usuário
    resposta.set_cookie(
        key='user',  # Nome do cookie
        value='',  # Apara o valor do cookie
        max_age=0  # A validade do cookie é ZERO
    )

    # Redireciona para login
    return resposta

@app.route('/editaperfil', methods=['GET', 'POST'])
def editaperfil():
    # Se o usuário não está logado, redireciona para a página de login
    if g.appuser == '':
        return redirect(url_for('login'))

    if request.method == 'POST':
        form = dict(request.form)

        # Atualiza os dados do usuário no banco de dados
        sql = '''
            UPDATE usuario
            SET u_nome = %s,
                u_nascimento = %s,
                u_email = %s
            WHERE u_id = %s
        '''
        cur = mysql.connection.cursor()
        cur.execute(sql, (
            form['nome'],
            form['nascimento'],
            form['email'],
            g.appuser['id'],
        ))
        mysql.connection.commit()

        # Verifica se a senha atual foi fornecida e se a nova senha é válida
        if form['senha_atual'] and form['nova_senha']:
            sql = '''
                SELECT u_senha FROM usuario WHERE u_id = %s
            '''
            cur.execute(sql, (g.appuser['id'],))
            usuario = cur.fetchone()

            # Verifica se a senha atual está correta
            if usuario and usuario['u_senha'] == sha1(form['senha_atual'].encode()).hexdigest():
                # Atualiza a senha
                sql = '''
                    UPDATE usuario SET u_senha = SHA1(%s) WHERE u_id = %s
                '''
                cur.execute(sql, (form['nova_senha'], g.appuser['id']))
                mysql.connection.commit()
                flash('Senha alterada com sucesso!', 'success')
            else:
                flash('A senha atual está incorreta.', 'danger')

        cur.close()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('logout'))

    # Recebe dados do usuário
    sql = '''
        SELECT * FROM usuario
        WHERE u_id = %s
            AND u_status = 'on'    
    '''
    cur = mysql.connection.cursor()
    cur.execute(sql, (g.appuser['id'],))
    user_data = cur.fetchone()
    cur.close()

    # Dados, variáveis e valores a serem passados para o template HTML
    pagina = {
        'usuario': g.appuser,
        'form': user_data
    }
    return render_template('editaperfil.html', **pagina)

@app.route('/novasenha', methods=['GET', 'POST'])  # Pedido de senha de usuário
def novasenha():

    novasenha = ''
    erro = False

    # Se o usuário está logado, redireciona para a página de perfil
    if g.appuser != '':
        return redirect(url_for('perfil'))

    # Se o formulário foi enviado
    if request.method == 'POST':

        # Obtém dados preenchidos
        form = dict(request.form)


        # Pesquisa pelo email e nascimento informados, no banco de dados
        sql = '''
            SELECT u_id
            FROM usuario
            WHERE u_email = %s
                AND u_nascimento = %s
                AND u_status = 'on'
        '''
        cur = mysql.connection.cursor()
        cur.execute(sql, (form['email'], form['nascimento'],))
        row = cur.fetchone()
        cur.close()

        # Teste de mesa
        # print('\n\n\n DB:', row, '\n\n\n')

        # Se o usuário não existe
        if row == None:
            # Exibe mensagem no frontend
            erro = True
        else:
            # Gera uma nova senha
            novasenha = gerar_senha()

            # Salva a nova senha no banco de dados
            sql = "UPDATE usuario SET u_senha = SHA1(%s) WHERE u_id = %s"
            cur = mysql.connection.cursor()
            cur.execute(sql, (novasenha, row['u_id'],))
            mysql.connection.commit()
            cur.close()

    # Dados, variáveis e valores a serem passados para o template HTML
    pagina = {
        'erro': erro,
        'novasenha': novasenha,
    }

    return render_template('novasenha.html', **pagina)

@app.route('/termos')
def termos():
    if g.appuser == '':
        return redirect(url_for('login'))
    
    return render_template('termos.html', usuario=g.appuser)

@app.route('/privacidade')
def privacidade():
    if g.appuser == '':
        return redirect(url_for('login'))
    return render_template('privacidade.html', usuario=g.appuser)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)