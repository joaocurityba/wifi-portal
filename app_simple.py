#!/usr/bin/env python3
"""
Portal Cativo Flask - Wi-Fi Público Municipal
Versão com segurança avançada e criptografia
"""

import os
import smtplib
import secrets
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_migrate import Migrate
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv('.env.local.dev')
# Importa modelos SQLAlchemy
from app.models import db, User, AccessLog

# Importa módulos de segurança
from app.security import security_manager, require_admin, rate_limit_admin, generate_csrf_token, validate_csrf_token, require_csrf_token
from app.data_manager import data_manager

# Importa utilitários
from app.utils import ensure_directory

# Configuração de logging avançado
ensure_directory('logs', mode=0o750)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuração da aplicação
app = Flask(__name__)

# Configurações a partir de variáveis de ambiente
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_urlsafe(64))
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://portal_user:portal_password_2026@localhost:5432/wifi_portal')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
app.config['MAX_LOGIN_ATTEMPTS'] = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
app.config['SESSION_TIMEOUT'] = int(os.getenv('SESSION_TIMEOUT', '1800'))
app.config['ALLOWED_HOSTS'] = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Inicializa extensões
db.init_app(app)
migrate = Migrate(app, db)

# Inicializa gerenciadores de segurança
security_manager.init_app(app)
data_manager.init_app(app)

# Configura encriptação nos modelos
from app.models import set_encryption_cipher
set_encryption_cipher(security_manager.cipher_suite)

def sanitize_input(text):
    """Sanitiza input para prevenir XSS"""
    if text:
        return str(text).strip().replace('<', '<').replace('>', '>')
    return ''

def validate_email(email):
    """Valida formato de email"""
    if not email:
        return False
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

# Funções de gerenciamento de usuários
def create_default_user():
    """Cria usuário admin padrão se não existir"""
    with app.app_context():
        # Verifica se já existe algum usuário
        if User.query.count() == 0:
            default_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                email='admin@prefeitura.com',
                created_at=datetime.utcnow()
            )
            db.session.add(default_user)
            db.session.commit()
            logger.info("Default admin user created")

def get_user(username):
    """Obtém usuário pelo username"""
    return User.query.filter_by(username=username).first()

def verify_password(username, password):
    """Verifica senha do usuário"""
    user = get_user(username)
    if user and check_password_hash(user.password_hash, password):
        return True
    return False

def update_reset_token(username, token, expires):
    """Atualiza token de recuperação de senha"""
    user = User.query.filter_by(username=username).first()
    if user:
        user.reset_token = token
        user.reset_expires = expires
        db.session.commit()
        return True
    return False

def reset_password(username, new_password):
    """Redefine senha do usuário"""
    user = User.query.filter_by(username=username).first()
    if user:
        user.password_hash = generate_password_hash(new_password)
        user.reset_token = None
        user.reset_expires = None
        db.session.commit()
        return True
    return False

def validate_reset_token(username, token):
    """Valida token de recuperação de senha"""
    user = get_user(username)
    if not user:
        return False
    
    if user.reset_token != token:
        return False
    
    if user.reset_expires:
        if datetime.utcnow() > user.reset_expires:
            return False
    
    return True

# Funções de edição de perfil
def update_user(username, data):
    """Atualiza dados do usuário (exceto senha)"""
    user = User.query.filter_by(username=username).first()
    if user:
        if 'email' in data:
            user.email = data['email']
        db.session.commit()
        return True
    return False

def change_password(username, old_password, new_password):
    """Altera senha do usuário com validação da senha atual"""
    user = get_user(username)
    if not user:
        return False, "Usuário não encontrado"
    
    # Verifica se a senha atual está correta
    if not check_password_hash(user.password_hash, old_password):
        return False, "Senha atual incorreta"
    
    # Valida nova senha
    if not new_password or len(new_password) < 6:
        return False, "A nova senha deve ter pelo menos 6 caracteres"
    
    # Atualiza senha
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return True, "Senha alterada com sucesso"

def validate_current_password(username, password):
    """Valida se a senha atual está correta"""
    return verify_password(username, password)

def send_reset_email(email, username, token):
    """Envia email de recuperação de senha"""
    try:
        smtp_server = os.getenv('SMTP_SERVER') or os.getenv('MAIL_SERVER') or 'smtp.gmail.com'
        smtp_port = int(os.getenv('SMTP_PORT') or os.getenv('MAIL_PORT') or '587')
        smtp_username = os.getenv('SMTP_USERNAME') or os.getenv('SMTP_USER') or os.getenv('MAIL_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD') or os.getenv('MAIL_PASSWORD')
        use_tls = (os.getenv('SMTP_USE_TLS') or os.getenv('MAIL_USE_TLS') or 'True').lower() == 'true'
        from_email = (
            os.getenv('FROM_EMAIL')
            or os.getenv('SMTP_FROM')
            or os.getenv('MAIL_DEFAULT_SENDER')
            or smtp_username
        )
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
    csrf_token = generate_csrf_token()
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        # Procura usuário pelo email usando SQLAlchemy
        user = User.query.filter_by(email=email).first()
        if user:
            # Gera token de recuperação
            token = secrets.token_urlsafe(32)
            expires = datetime.utcnow() + timedelta(hours=1)
            
            user.reset_token = token
            user.reset_expires = expires
            db.session.commit()
            
            send_reset_email(email, user.username, token)
            
            flash('Instruções de recuperação enviadas para seu email.', 'success')
            return redirect(url_for('admin_login'))
        
        # Mensagem genérica para não revelar se o email existe
        flash('Se o email estiver cadastrado, instruções foram enviadas.', 'info')
    
    return render_template('reset_password.html', csrf_token=csrf_token)

@app.route('/admin/reset/<token>', methods=['GET', 'POST'])
@require_csrf_token
def reset_password_form(token):
    """Formulário de redefinição de senha"""
    # Busca usuário pelo token usando SQLAlchemy
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_expires or user.reset_expires < datetime.utcnow():
        flash('Token inválido ou expirado.', 'error')
        return redirect(url_for('reset_password_request'))
    csrf_token = generate_csrf_token()
    
    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not new_password or len(new_password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('reset_form.html', token=token, username=user.username, csrf_token=csrf_token)
        
        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return render_template('reset_form.html', token=token, username=user.username, csrf_token=csrf_token)
        
        # Atualiza senha e limpa token
        user.password_hash = generate_password_hash(new_password)
        user.reset_token = None
        user.reset_expires = None
        db.session.commit()
        
        flash('Senha redefinida com sucesso!', 'success')
        return redirect(url_for('admin_login'))
    
    return render_template('reset_form.html', token=token, username=user.username, csrf_token=csrf_token)

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

        if not termos:
            errors.append('É necessário aceitar os Termos de Uso para continuar.')

        # Validação anti-bot (verifica se o formulário foi preenchido rapidamente)
        if len(nome) > 0 and len(email) > 0:
            # Verifica se os campos não são preenchidos com valores padrão
            if nome.lower() in ['test', 'teste', 'admin', 'user'] or \
               email.lower() in ['test@test.com', 'admin@admin.com']:
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
                                 nome=nome, email=email)
        
        user_agent = request.headers.get('User-Agent', 'Desconhecido')
        now = datetime.now()
        data = now.strftime('%Y-%m-%d')
        hora = now.strftime('%H:%M:%S')
        
        access_data = {
            'nome': nome,
            'ip': ip,
            'mac': mac,
            'user_agent': user_agent,
            'data': data,
            'hora': hora,
            'email': email
        }
        
        try:
            # Registra no banco de dados PostgreSQL com criptografia
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
                                 nome=nome, email=email)
        
        redirect_url = 'https://www.patydoalferes.rj.gov.br'
        return redirect(redirect_url)
    
    csrf_token = generate_csrf_token()
    return render_template('login.html', ip=ip, mac=mac, link_orig=link_orig, csrf_token=csrf_token)

@app.route('/healthz')
def health_check():
    """Health check endpoint para monitoramento"""
    return {'status': 'healthy', 'service': 'wifi-portal'}, 200

@app.route('/termos')
def termos():
    """Página de termos de uso"""
    return render_template('termos.html')

@app.route('/politica-privacidade')
def politica_privacidade():
    """Página de política de privacidade"""
    return render_template('politica_privacidade.html')

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
    csrf_token = generate_csrf_token()
    
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
            return render_template('admin_profile.html', user=user.to_dict(), csrf_token=csrf_token)
        
        # Atualiza email
        if email != user.email:
            update_user(username, {'email': email})
            flash('Email atualizado com sucesso!', 'success')
        
        # Atualiza senha se houver nova senha
        if new_password:
            success, message = change_password(username, current_password, new_password)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
                return render_template('admin_profile.html', user=user.to_dict(), csrf_token=csrf_token)
        
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('admin_profile'))
    
    return render_template('admin_profile.html', user=user.to_dict(), csrf_token=csrf_token)

if __name__ == '__main__':
    with app.app_context():
        # Cria tabelas se não existirem
        db.create_all()
        # Cria usuário admin padrão
        create_default_user()
    
    ensure_directory('logs', mode=0o750)
    ensure_directory('uploads', mode=0o750)
    app.run(host='0.0.0.0', debug=False)