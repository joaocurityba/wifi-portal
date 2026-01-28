#!/usr/bin/env python3
"""
Portal Cautivo Flask Simplificado - Wi-Fi Público Municipal
Versão sem dependências externas complexas
"""

import os
import csv
import smtplib
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, render_template, redirect, url_for, flash, session

# Configuração da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = 'portal-cautivo-municipal'
app.config['CSV_FILE'] = 'data/access_log.csv'

def sanitize_input(text):
    """Sanitiza input para prevenir XSS"""
    if text:
        return str(text).strip().replace('<', '<').replace('>', '>')
    return ''

def validate_phone(phone):
    """Valida formato básico de telefone"""
    if not phone:
        return False
    clean_phone = ''.join(c for c in phone if c.isdigit())
    return len(clean_phone) >= 8 and len(clean_phone) <= 15

def validate_email(email):
    """Valida formato de email"""
    if not email:
        return False
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_birth_date(birth_date):
    """Valida data de nascimento (mínimo 13 anos)"""
    if not birth_date:
        return False
    try:
        from datetime import datetime, date
        birth = datetime.strptime(birth_date, '%Y-%m-%d').date()
        today = date.today()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age >= 13 and birth <= today
    except ValueError:
        return False

# Funções de gerenciamento de usuários
def get_users_file():
    """Retorna o caminho do arquivo de usuários"""
    return 'data/users.csv'

def create_default_user():
    """Cria usuário admin padrão se não existir"""
    users_file = get_users_file()
    os.makedirs(os.path.dirname(users_file), exist_ok=True)
    
    if not os.path.exists(users_file):
        with open(users_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['username', 'password_hash', 'email', 'created_at', 'reset_token', 'reset_expires']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Cria usuário admin padrão
            default_user = {
                'username': 'admin',
                'password_hash': generate_password_hash('admin123'),
                'email': 'admin@prefeitura.com',
                'created_at': datetime.now().isoformat(),
                'reset_token': '',
                'reset_expires': ''
            }
            writer.writerow(default_user)

def get_user(username):
    """Obtém usuário pelo username"""
    users_file = get_users_file()
    if not os.path.exists(users_file):
        return None
    
    with open(users_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username:
                return row
    return None

def verify_password(username, password):
    """Verifica senha do usuário"""
    user = get_user(username)
    if user and check_password_hash(user['password_hash'], password):
        return True
    return False

def update_reset_token(username, token, expires):
    """Atualiza token de recuperação de senha"""
    users_file = get_users_file()
    users = []
    
    with open(users_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username:
                row['reset_token'] = token
                row['reset_expires'] = expires.isoformat()
            users.append(row)
    
    with open(users_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['username', 'password_hash', 'email', 'created_at', 'reset_token', 'reset_expires']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

def reset_password(username, new_password):
    """Redefine senha do usuário"""
    users_file = get_users_file()
    users = []
    
    with open(users_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username:
                row['password_hash'] = generate_password_hash(new_password)
                row['reset_token'] = ''
                row['reset_expires'] = ''
            users.append(row)
    
    with open(users_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['username', 'password_hash', 'email', 'created_at', 'reset_token', 'reset_expires']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

def validate_reset_token(username, token):
    """Valida token de recuperação de senha"""
    user = get_user(username)
    if not user:
        return False
    
    if user['reset_token'] != token:
        return False
    
    if user['reset_expires']:
        expires = datetime.fromisoformat(user['reset_expires'])
        if datetime.now() > expires:
            return False
    
    return True

# Funções de edição de perfil
def update_user(username, data):
    """Atualiza dados do usuário (exceto senha)"""
    users_file = get_users_file()
    users = []
    
    with open(users_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username:
                row.update(data)
            users.append(row)
    
    with open(users_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['username', 'password_hash', 'email', 'created_at', 'reset_token', 'reset_expires']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

def change_password(username, old_password, new_password):
    """Altera senha do usuário com validação da senha atual"""
    user = get_user(username)
    if not user:
        return False, "Usuário não encontrado"
    
    # Verifica se a senha atual está correta
    if not check_password_hash(user['password_hash'], old_password):
        return False, "Senha atual incorreta"
    
    # Valida nova senha
    if not new_password or len(new_password) < 6:
        return False, "A nova senha deve ter pelo menos 6 caracteres"
    
    # Atualiza senha
    update_user(username, {'password_hash': generate_password_hash(new_password)})
    return True, "Senha alterada com sucesso"

def validate_current_password(username, password):
    """Valida se a senha atual está correta"""
    return verify_password(username, password)

def send_reset_email(email, username, token):
    """Envia email de recuperação de senha (simulação)"""
    # Em produção, configure SMTP real aqui
    reset_url = f"http://localhost:5000/admin/reset/{token}"
    print(f"Email para {email}:")
    print(f"Olá {username},")
    print(f"Para redefinir sua senha, acesse: {reset_url}")
    print(f"Este link expira em 1 hora.")
    print("---")
    return True

def log_access(data):
    """Registra acesso no arquivo CSV"""
    os.makedirs(os.path.dirname(app.config['CSV_FILE']), exist_ok=True)
    
    file_exists = os.path.isfile(app.config['CSV_FILE'])
    
    with open(app.config['CSV_FILE'], 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['nome', 'telefone', 'ip', 'mac', 'user_agent', 'data', 'hora', 'email', 'data_nascimento']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(data)

# Rotas de autenticação admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login do painel admin"""
    create_default_user()  # Cria usuário padrão se não existir
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if verify_password(username, password):
            session['admin_logged_in'] = True
            session['username'] = username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout do painel admin"""
    session.pop('admin_logged_in', None)
    session.pop('username', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Solicitação de recuperação de senha"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        # Procura usuário pelo email
        users_file = get_users_file()
        if os.path.exists(users_file):
            with open(users_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['email'] == email:
                        # Gera token de recuperação
                        token = secrets.token_urlsafe(32)
                        expires = datetime.now() + timedelta(hours=1)
                        
                        update_reset_token(row['username'], token, expires)
                        send_reset_email(email, row['username'], token)
                        
                        flash('Instruções de recuperação enviadas para seu email.', 'success')
                        return redirect(url_for('admin_login'))
        
        # Mensagem genérica para não revelar se o email existe
        flash('Se o email estiver cadastrado, instruções foram enviadas.', 'info')
    
    return render_template('reset_password.html')

@app.route('/admin/reset/<token>', methods=['GET', 'POST'])
def reset_password_form(token):
    """Formulário de redefinição de senha"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not validate_reset_token(username, token):
            flash('Token inválido ou expirado.', 'error')
            return redirect(url_for('reset_password_request'))
        
        if not new_password or len(new_password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('reset_form.html', token=token, username=username)
        
        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return render_template('reset_form.html', token=token, username=username)
        
        reset_password(username, new_password)
        flash('Senha redefinida com sucesso!', 'success')
        return redirect(url_for('admin_login'))
    
    # Verifica se o token é válido para exibir o formulário
    users_file = get_users_file()
    username = None
    if os.path.exists(users_file):
        with open(users_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['reset_token'] == token:
                    username = row['username']
                    break
    
    if not username or not validate_reset_token(username, token):
        flash('Token inválido ou expirado.', 'error')
        return redirect(url_for('reset_password_request'))
    
    return render_template('reset_form.html', token=token, username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota principal do portal cativo"""
    
    # Captura parâmetros do MikroTik (GET ou POST)
    ip = sanitize_input(request.args.get('ip', '')) or sanitize_input(request.form.get('ip', ''))
    mac = sanitize_input(request.args.get('mac', '')) or sanitize_input(request.form.get('mac', ''))
    link_orig = sanitize_input(request.args.get('link-orig', '')) or sanitize_input(request.form.get('link-orig', ''))
    
    if request.method == 'POST':
        nome = sanitize_input(request.form.get('nome', ''))
        email = sanitize_input(request.form.get('email', ''))
        data_nascimento = sanitize_input(request.form.get('data_nascimento', ''))
        telefone = sanitize_input(request.form.get('telefone', ''))
        termos = request.form.get('termos', '')

        errors = []

        if not nome:
            errors.append('Por favor, informe seu nome completo.')

        if not email:
            errors.append('Por favor, informe seu email.')
        elif not validate_email(email):
            errors.append('Por favor, informe um email válido.')

        if not data_nascimento:
            errors.append('Por favor, informe sua data de nascimento.')
        elif not validate_birth_date(data_nascimento):
            errors.append('É necessário ter pelo menos 13 anos para utilizar o serviço.')

        if not telefone:
            errors.append('Por favor, informe seu telefone celular.')
        elif not validate_phone(telefone):
            errors.append('Por favor, informe um telefone válido.')

        if not termos:
            errors.append('É necessário aceitar os Termos de Uso para continuar.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('login.html', 
                                 ip=ip, mac=mac, link_orig=link_orig,
                                 nome=nome, email=email, data_nascimento=data_nascimento, telefone=telefone)
        
        user_agent = request.headers.get('User-Agent', 'Desconhecido')
        now = datetime.now()
        data = now.strftime('%Y-%m-%d')
        hora = now.strftime('%H:%M:%S')
        
        access_data = {
            'nome': nome,
            'telefone': telefone,
            'ip': ip,
            'mac': mac,
            'user_agent': user_agent,
            'data': data,
            'hora': hora,
            'email': email,
            'data_nascimento': data_nascimento
        }
        
        try:
            log_access(access_data)
        except Exception as e:
            flash('Erro ao registrar acesso. Por favor, tente novamente.', 'error')
            return render_template('login.html', 
                                 ip=ip, mac=mac, link_orig=link_orig,
                                 nome=nome, telefone=telefone)
        
        redirect_url = link_orig if link_orig else 'https://www.google.com'
        return redirect(redirect_url)
    
    return render_template('login.html', ip=ip, mac=mac, link_orig=link_orig)

@app.route('/termos')
def termos():
    """Página de termos de uso"""
    return render_template('termos.html')

@app.route('/')
def index():
    """Redireciona para a página de login"""
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    """Página de administração"""
    # Verifica se o usuário está logado
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if not os.path.exists(app.config['CSV_FILE']):
        return "Nenhum registro encontrado."
    
    registros = []
    try:
        with open(app.config['CSV_FILE'], 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            registros = list(reader)
    except Exception as e:
        return f"Erro ao ler registros: {str(e)}"
    
    return render_template('admin.html', registros=registros)

@app.route('/admin/profile', methods=['GET', 'POST'])
def admin_profile():
    """Página de edição de perfil do administrador"""
    # Verifica se o usuário está logado
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    username = session['username']
    user = get_user(username)
    
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        # Dados do formulário
        email = sanitize_input(request.form.get('email', ''))
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        
        # Valida email
        if not email:
            errors.append('Por favor, informe o email.')
        elif not validate_email(email):
            errors.append('Por favor, informe um email válido.')
        
        # Valida senha atual (obrigatória para qualquer alteração)
        if not current_password:
            errors.append('Por favor, informe sua senha atual.')
        elif not validate_current_password(username, current_password):
            errors.append('Senha atual incorreta.')
        
        # Se houver nova senha, valida
        if new_password:
            if len(new_password) < 6:
                errors.append('A nova senha deve ter pelo menos 6 caracteres.')
            elif new_password != confirm_password:
                errors.append('As senhas não coincidem.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin_profile.html', user=user)
        
        # Atualiza email
        if email != user['email']:
            update_user(username, {'email': email})
            flash('Email atualizado com sucesso!', 'success')
        
        # Atualiza senha se houver nova senha
        if new_password:
            success, message = change_password(username, current_password, new_password)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
                return render_template('admin_profile.html', user=user)
        
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('admin_profile'))
    
    return render_template('admin_profile.html', user=user)

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)