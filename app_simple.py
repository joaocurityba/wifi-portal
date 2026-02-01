#!/usr/bin/env python3
"""
Portal Cautivo Flask - Wi-Fi Público Municipal
Versão com segurança avançada e criptografia
"""

import os
import csv
import smtplib
import secrets
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, render_template, redirect, url_for, flash, session
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv('.env.local')

# Importa módulos de segurança
from app.security import security_manager, require_admin, rate_limit_admin, generate_csrf_token, validate_csrf_token, require_csrf_token
from app.data_manager import data_manager

# Configuração de logging avançado
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuração da aplicação
app = Flask(__name__)

# Configurações a partir de variáveis de ambiente
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_urlsafe(64))
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
app.config['CSV_FILE'] = os.getenv('CSV_FILE', 'data/access_log.csv')
app.config['MAX_LOGIN_ATTEMPTS'] = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
app.config['SESSION_TIMEOUT'] = int(os.getenv('SESSION_TIMEOUT', '1800'))
app.config['ALLOWED_HOSTS'] = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Inicializa gerenciadores de segurança
security_manager.init_app(app)
data_manager.init_app(app)

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
                'created_at': datetime.now().isoformat()
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
            users.append(row)
    
    with open(users_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['username', 'password_hash', 'email', 'created_at']
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
    """Envia email de recuperação de senha"""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        use_tls = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
        from_email = os.getenv('FROM_EMAIL', smtp_username)
        from_name = os.getenv('FROM_NAME', 'Wi-Fi Portal Admin')

        if not smtp_username or not smtp_password:
            logger.error("SMTP credentials not configured")
            return False

        reset_url = f"{request.host_url.rstrip('/')}/admin/reset/{token}"

        msg = smtplib.SMTP(smtp_server, smtp_port)
        msg.ehlo()

        if use_tls:
            msg.starttls()
            msg.ehlo()

        msg.login(smtp_username, smtp_password)

        subject = "Recuperação de Senha - Portal Wi-Fi"
        body = f"""Olá {username},

Você solicitou a recuperação de senha para o painel administrativo do Portal Wi-Fi.

Para redefinir sua senha, acesse o link abaixo:
{reset_url}

Este link expira em 1 hora.

Se você não solicitou esta recuperação, ignore este email.

Atenciosamente,
{from_name}
"""

        message = f"From: {from_name} <{from_email}>\n"
        message += f"To: {email}\n"
        message += f"Subject: {subject}\n\n"
        message += body

        msg.sendmail(from_email, email, message.encode('utf-8'))
        msg.quit()

        logger.info(f"Reset email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")
        return False

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
@rate_limit_admin
@require_csrf_token
def admin_login():
    """Login do painel admin com rate limiting"""
    create_default_user()  # Cria usuário padrão se não existir
    
    if request.method == 'POST':
        username = security_manager.sanitize_input_advanced(request.form.get('username', '').strip())
        password = request.form.get('password', '')
        
        # Validação de força da senha para login (se for senha fraca, alerta)
        if len(password) < 8:
            security_manager.log_security_event('weak_password_attempt', {
                'username': username,
                'password_length': len(password)
            })
        
        if verify_password(username, password):
            session['admin_logged_in'] = True
            session['username'] = username
            session.permanent = True
            app.permanent_session_lifetime = timedelta(seconds=app.config['SESSION_TIMEOUT'])
            
            security_manager.log_security_event('admin_login_success', {
                'username': username
            })
            
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin'))
        else:
            security_manager.log_security_event('admin_login_failed', {
                'username': username,
                'ip': request.remote_addr
            })
            flash('Usuário ou senha incorretos.', 'error')
    
    # Gera token CSRF para o formulário
    csrf_token = generate_csrf_token()
    return render_template('admin_login.html', csrf_token=csrf_token)

@app.route('/admin/logout')
def admin_logout():
    """Logout do painel admin"""
    session.pop('admin_logged_in', None)
    session.pop('username', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/reset-password', methods=['GET', 'POST'])
@require_csrf_token
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
@require_csrf_token
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
@security_manager.limiter.limit("20 per minute")
@require_csrf_token
def login():
    """Rota principal do portal cativo com criptografia"""
    
    # Captura parâmetros do MikroTik (GET ou POST)
    ip = security_manager.sanitize_input_advanced(request.args.get('ip', '')) or security_manager.sanitize_input_advanced(request.form.get('ip', ''))
    mac = security_manager.sanitize_input_advanced(request.args.get('mac', '')) or security_manager.sanitize_input_advanced(request.form.get('mac', ''))
    link_orig = security_manager.sanitize_input_advanced(request.args.get('link-orig', '')) or security_manager.sanitize_input_advanced(request.form.get('link-orig', ''))
    
    if request.method == 'POST':
        nome = security_manager.sanitize_input_advanced(request.form.get('nome', ''))
        email = security_manager.sanitize_input_advanced(request.form.get('email', ''))
        data_nascimento = security_manager.sanitize_input_advanced(request.form.get('data_nascimento', ''))
        telefone = security_manager.sanitize_input_advanced(request.form.get('telefone', ''))
        termos = request.form.get('termos', '')

        errors = []

        if not nome:
            errors.append('Por favor, informe seu nome completo.')
        elif len(nome) < 3:
            errors.append('O nome deve ter pelo menos 3 caracteres.')

        if not email:
            errors.append('Por favor, informe seu email.')
        elif not validate_email(email):
            errors.append('Por favor, informe um email válido.')
        elif len(email) > 100:
            errors.append('O email deve ter no máximo 100 caracteres.')

        if not data_nascimento:
            errors.append('Por favor, informe sua data de nascimento.')
        elif not validate_birth_date(data_nascimento):
            errors.append('É necessário ter pelo menos 13 anos para utilizar o serviço.')

        if not telefone:
            errors.append('Por favor, informe seu telefone celular.')
        elif not validate_phone(telefone):
            errors.append('Por favor, informe um telefone válido.')
        elif len(telefone) > 20:
            errors.append('O telefone deve ter no máximo 20 caracteres.')

        if not termos:
            errors.append('É necessário aceitar os Termos de Uso para continuar.')

        # Validação anti-bot (verifica se o formulário foi preenchido rapidamente)
        if len(nome) > 0 and len(email) > 0 and len(telefone) > 0:
            # Verifica se os campos não são preenchidos com valores padrão
            if nome.lower() in ['test', 'teste', 'admin', 'user'] or \
               email.lower() in ['test@test.com', 'admin@admin.com'] or \
               telefone in ['123456789', '987654321', '111111111']:
                security_manager.log_security_event('suspicious_form_submission', {
                    'ip': ip,
                    'user_agent': request.headers.get('User-Agent', 'Unknown')
                })
                errors.append('Por favor, informe dados válidos.')

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
            # Registra no CSV tradicional (para compatibilidade)
            log_access(access_data)
            
            # Registra no sistema criptografado
            data_manager.log_access_encrypted(access_data)
            
            security_manager.log_security_event('access_registered', {
                'ip': ip,
                'mac': mac,
                'user_agent': user_agent[:100]  # Limita tamanho
            })
            
        except Exception as e:
            logger.error(f"Erro ao registrar acesso: {e}")
            flash('Erro ao registrar acesso. Por favor, tente novamente.', 'error')
            return render_template('login.html', 
                                 ip=ip, mac=mac, link_orig=link_orig,
                                 nome=nome, telefone=telefone)
        
        redirect_url = 'https://www.patydoalferes.rj.gov.br'
        return redirect(redirect_url)
    
    csrf_token = generate_csrf_token()
    return render_template('login.html', ip=ip, mac=mac, link_orig=link_orig, csrf_token=csrf_token)

@app.route('/termos')
def termos():
    """Página de termos de uso"""
    return render_template('termos.html')

@app.route('/')
def index():
    """Redireciona para a página de login"""
    return redirect(url_for('login'))

@app.route('/admin')
@require_admin
def admin():
    """Página de administração com criptografia"""
    try:
        # Obtém logs criptografados
        encrypted_logs = data_manager.get_access_logs(limit=1000)
        
        # Obtém estatísticas
        stats = data_manager.get_user_stats()
        
        return render_template('admin.html', 
                             registros=encrypted_logs, 
                             stats=stats,
                             total_registros=len(encrypted_logs))
    except Exception as e:
        logger.error(f"Erro ao carregar painel admin: {e}")
        return f"Erro ao carregar painel administrativo: {str(e)}", 500

@app.route('/admin/stats')
@require_admin
def admin_stats():
    """Página de estatísticas detalhadas"""
    try:
        stats = data_manager.get_user_stats()
        return render_template('admin_stats.html', stats=stats)
    except Exception as e:
        logger.error(f"Erro ao carregar estatísticas: {e}")
        return f"Erro ao carregar estatísticas: {str(e)}", 500

@app.route('/admin/search', methods=['GET', 'POST'])
@require_admin
@require_csrf_token
def admin_search():
    """Busca em logs de acesso"""
    if request.method == 'POST':
        search_term = security_manager.sanitize_input_advanced(request.form.get('search_term', ''))
        search_field = request.form.get('search_field', 'nome')
        
        if search_term:
            results = data_manager.search_access_logs(search_term, search_field)
            return render_template('admin_search.html', 
                                 results=results, 
                                 search_term=search_term,
                                 search_field=search_field)
    
    return render_template('admin_search.html', results=[], search_term='', search_field='nome')

@app.route('/admin/profile', methods=['GET', 'POST'])
@require_csrf_token
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
    app.run(host='0.0.0.0', debug=False)