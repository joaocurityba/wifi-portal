#!/usr/bin/env python3
"""
Portal Cativo Flask - Wi-Fi Público Municipal
Versão com segurança avançada e criptografia
"""

import os
import json
import smtplib
import secrets
import logging
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_migrate import Migrate
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv('.env.local')
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

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_port=1,
)

UNIFI_SETTINGS_FILE = os.path.join('data', 'unifi_settings.json')
OMADA_SETTINGS_FILE = os.path.join('data', 'omada_settings.json')
PORTAL_CONTEXT_SESSION_KEY = 'portal_context'
PORTAL_CONTEXT_TTL_SECONDS = 1800
DEFAULT_OMADA_AUTH_TIME_UNIT = 'milliseconds'
OMADA_AUTH_TIME_UNITS = {
    'milliseconds': 60 * 1000,
    'microseconds': 60 * 1000 * 1000,
}
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'

def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'sim', 'on'}

def parse_days(value, default, minimum=1, maximum=3650):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, minimum), maximum)

def get_privacy_settings():
    return {
        'controller_name': os.getenv('PRIVACY_CONTROLLER_NAME', 'Prefeitura Municipal de Paty do Alferes'),
        'privacy_contact_email': os.getenv('PRIVACY_CONTACT_EMAIL', ''),
        'privacy_contact_url': os.getenv('PRIVACY_CONTACT_URL', ''),
        'access_log_retention_days': parse_days(os.getenv('ACCESS_LOG_RETENTION_DAYS'), 180, 1, 3650),
        'portal_session_retention_days': parse_days(os.getenv('PORTAL_SESSION_RETENTION_DAYS'), 365, 1, 3650),
        'last_updated': os.getenv('PRIVACY_POLICY_UPDATED_AT', '27/05/2026'),
    }

def build_login_form_action():
    if not env_bool('FORCE_HTTPS_LOGIN_FORM', False):
        return url_for('login')

    public_portal_url = os.getenv('PUBLIC_PORTAL_URL', '').strip().rstrip('/')
    if public_portal_url:
        parsed_url = urlparse(public_portal_url)
        if parsed_url.scheme == 'https' and parsed_url.netloc:
            return f"{public_portal_url}{url_for('login')}"

    host = request.host or ''
    local_hosts = ('localhost', '127.0.0.1', '[::1]')
    if host and not any(host.startswith(local_host) for local_host in local_hosts):
        return url_for('login', _external=True, _scheme='https')

    return url_for('login')

def normalize_omada_auth_time_unit(unit):
    """Normaliza a unidade usada no campo time da API Hotspot Omada."""
    aliases = {
        'ms': 'milliseconds',
        'millisecond': 'milliseconds',
        'milliseconds': 'milliseconds',
        'milissegundo': 'milliseconds',
        'milissegundos': 'milliseconds',
        'us': 'microseconds',
        'microsecond': 'microseconds',
        'microseconds': 'microseconds',
        'microssegundo': 'microseconds',
        'microssegundos': 'microseconds',
    }
    normalized = aliases.get(str(unit or '').strip().lower())
    return normalized if normalized in OMADA_AUTH_TIME_UNITS else DEFAULT_OMADA_AUTH_TIME_UNIT

def get_omada_auth_time_value(minutes, unit=None):
    """Converte minutos para o valor enviado no campo time do Omada."""
    auth_minutes = int(minutes)
    auth_time_unit = normalize_omada_auth_time_unit(unit)
    return auth_minutes * OMADA_AUTH_TIME_UNITS[auth_time_unit], auth_time_unit

def parse_minutes(value, default=0, min_value=0, max_value=14400):
    """Converte e limita valores de tempo em minutos."""
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return default
    if minutes < min_value or minutes > max_value:
        return default
    return minutes

def format_duration_pt(seconds):
    """Formata uma duracao curta para mensagens do portal."""
    try:
        remaining_minutes = max((int(seconds) + 59) // 60, 1)
    except (TypeError, ValueError):
        remaining_minutes = 1

    if remaining_minutes < 60:
        return f"{remaining_minutes} minuto" if remaining_minutes == 1 else f"{remaining_minutes} minutos"

    hours, minutes = divmod(remaining_minutes, 60)
    hour_text = f"{hours} hora" if hours == 1 else f"{hours} horas"
    if not minutes:
        return hour_text
    minute_text = f"{minutes} minuto" if minutes == 1 else f"{minutes} minutos"
    return f"{hour_text} e {minute_text}"

def load_unifi_settings():
    """Carrega configurações do UniFi do arquivo JSON ou variáveis de ambiente"""
    settings = {
        'controller_url': os.getenv('UNIFI_CONTROLLER_URL', ''),
        'username': os.getenv('UNIFI_USERNAME', ''),
        'password': os.getenv('UNIFI_PASSWORD', ''),
        'site': os.getenv('UNIFI_SITE', 'default'),
        'auth_minutes': parse_minutes(os.getenv('GUEST_AUTH_MINUTES', '480'), 480, 1, 14400),
        'cooldown_minutes': parse_minutes(os.getenv('GUEST_COOLDOWN_MINUTES', '0'), 0, 0, 14400),
    }
    if os.path.exists(UNIFI_SETTINGS_FILE):
        try:
            with open(UNIFI_SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
            settings.update({k: v for k, v in saved.items() if v is not None and v != ''})
        except Exception as e:
            logger.error(f"Error loading UniFi settings: {e}")
    settings['auth_minutes'] = parse_minutes(settings.get('auth_minutes'), 480, 1, 14400)
    settings['cooldown_minutes'] = parse_minutes(settings.get('cooldown_minutes'), 0, 0, 14400)
    return settings

def save_unifi_settings(settings):
    """Salva configurações do UniFi no arquivo JSON"""
    ensure_directory('data', mode=0o750)
    try:
        with open(UNIFI_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        os.chmod(UNIFI_SETTINGS_FILE, 0o600)
        return True
    except Exception as e:
        logger.error(f"Error saving UniFi settings: {e}")
        return False

def load_omada_settings():
    """Carrega configuracoes do Omada do arquivo JSON ou variaveis de ambiente"""
    settings = {
        'controller_url': os.getenv('OMADA_CONTROLLER_URL', ''),
        'controller_id': os.getenv('OMADA_CONTROLLER_ID', ''),
        'operator_username': os.getenv('OMADA_OPERATOR_USERNAME', ''),
        'operator_password': os.getenv('OMADA_OPERATOR_PASSWORD', ''),
        'default_site': os.getenv('OMADA_DEFAULT_SITE', 'Default'),
        'auth_minutes': parse_minutes(os.getenv('OMADA_AUTH_MINUTES', os.getenv('GUEST_AUTH_MINUTES', '480')), 480, 1, 14400),
        'cooldown_minutes': parse_minutes(os.getenv('OMADA_COOLDOWN_MINUTES', os.getenv('GUEST_COOLDOWN_MINUTES', '0')), 0, 0, 14400),
        'auth_time_unit': os.getenv('OMADA_AUTH_TIME_UNIT', DEFAULT_OMADA_AUTH_TIME_UNIT),
    }
    if os.path.exists(OMADA_SETTINGS_FILE):
        try:
            with open(OMADA_SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
            settings.update({k: v for k, v in saved.items() if v is not None and v != ''})
        except Exception as e:
            logger.error(f"Error loading Omada settings: {e}")
    settings['auth_minutes'] = parse_minutes(settings.get('auth_minutes'), 480, 1, 14400)
    settings['cooldown_minutes'] = parse_minutes(settings.get('cooldown_minutes'), 0, 0, 14400)
    settings['auth_time_unit'] = normalize_omada_auth_time_unit(settings.get('auth_time_unit'))
    return settings

def save_omada_settings(settings):
    """Salva configuracoes do Omada no arquivo JSON"""
    ensure_directory('data', mode=0o750)
    try:
        with open(OMADA_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        os.chmod(OMADA_SETTINGS_FILE, 0o600)
        return True
    except Exception as e:
        logger.error(f"Error saving Omada settings: {e}")
        return False

def normalize_mac(mac):
    """Normaliza enderecos MAC usados pelos controladores."""
    if not mac:
        return ''
    return str(mac).strip().lower().replace('-', ':').replace('.', ':')

def parse_referer_query():
    """Extrai parametros da URL de origem do captive browser."""
    referer = request.headers.get('Referer', '')
    if not referer:
        return {}
    try:
        return parse_qs(urlparse(referer).query, keep_blank_values=False)
    except Exception:
        return {}

def get_request_value(*names):
    """Busca um parametro em GET ou POST e sanitiza o valor."""
    for name in names:
        value = request.args.get(name, '') or request.form.get(name, '')
        if value:
            return security_manager.sanitize_input_advanced(value)
    return ''

def get_referer_value(*names):
    """Busca um parametro no Referer quando o POST perde campos ocultos."""
    referer_params = parse_referer_query()
    for name in names:
        values = referer_params.get(name) or []
        if values:
            return security_manager.sanitize_input_advanced(values[0])
    return ''

def get_saved_portal_context():
    """Recupera contexto recente salvo na sessao do captive browser."""
    saved = session.get(PORTAL_CONTEXT_SESSION_KEY)
    if not isinstance(saved, dict):
        return {}

    saved_at = saved.get('saved_at')
    try:
        saved_at_dt = datetime.fromisoformat(saved_at)
    except (TypeError, ValueError):
        session.pop(PORTAL_CONTEXT_SESSION_KEY, None)
        return {}

    if datetime.utcnow() - saved_at_dt > timedelta(seconds=PORTAL_CONTEXT_TTL_SECONDS):
        session.pop(PORTAL_CONTEXT_SESSION_KEY, None)
        return {}

    return saved

def get_saved_context_value(saved_context, *names):
    """Busca parametro em contexto de portal previamente salvo."""
    if not saved_context:
        return ''
    for name in names:
        value = saved_context.get(name, '')
        if value:
            return security_manager.sanitize_input_advanced(value)
    return ''

def remember_portal_context(portal_context):
    """Salva parametros validos para recuperar POSTs sem campos ocultos."""
    if not portal_context.get('client_mac'):
        return

    provider = portal_context.get('provider', 'unifi')
    omada_params = portal_context.get('omada') or {}

    saved = {
        'provider': provider,
        'saved_at': datetime.utcnow().isoformat(),
        'id': portal_context.get('client_mac') if provider == 'unifi' else '',
        'ap': portal_context.get('ap_mac') if provider == 'unifi' else '',
        'url': portal_context.get('redirect_url') if provider == 'unifi' else '',
        'ssid': portal_context.get('ssid') if provider == 'unifi' else '',
        't': portal_context.get('timestamp') or '',
        'clientMac': omada_params.get('clientMac') or '',
        'apMac': omada_params.get('apMac') or '',
        'gatewayMac': omada_params.get('gatewayMac') or '',
        'ssidName': omada_params.get('ssidName') or '',
        'radioId': omada_params.get('radioId') or '',
        'site': omada_params.get('site') or '',
        'redirectUrl': omada_params.get('redirectUrl') or '',
        'vid': omada_params.get('vid') or '',
    }
    session[PORTAL_CONTEXT_SESSION_KEY] = saved
    session.modified = True

def log_missing_portal_mac(portal_provider):
    """Registra contexto tecnico quando o formulario chega sem MAC."""
    referer = request.headers.get('Referer', '')
    try:
        referer_path = urlparse(referer).path
    except Exception:
        referer_path = ''

    saved_context = get_saved_portal_context()
    security_manager.log_security_event('portal_client_mac_missing', {
        'method': request.method,
        'path': request.path,
        'portal_provider': portal_provider,
        'query_has_unifi_id': bool(request.args.get('id')),
        'form_has_unifi_id': bool(request.form.get('id')),
        'referer_has_unifi_id': bool(get_referer_value('id')),
        'session_has_unifi_id': bool(saved_context.get('id')),
        'query_has_omada_client_mac': bool(request.args.get('clientMac')),
        'form_has_omada_client_mac': bool(request.form.get('clientMac')),
        'referer_has_omada_client_mac': bool(get_referer_value('clientMac')),
        'session_has_omada_client_mac': bool(saved_context.get('clientMac')),
        'referer_path': referer_path,
        'user_agent': request.headers.get('User-Agent', 'Unknown')[:120],
    })

def build_portal_context():
    """Monta parametros de portal para UniFi e Omada."""
    saved_context = get_saved_portal_context() if request.method == 'POST' else {}

    def portal_value(*names):
        return (
            get_request_value(*names)
            or get_referer_value(*names)
            or get_saved_context_value(saved_context, *names)
        )

    provider_hint = get_request_value('portal_provider') or get_saved_context_value(saved_context, 'provider')

    unifi_client_mac = portal_value('id')
    unifi_ap_mac = portal_value('ap')
    unifi_redirect_url = portal_value('url')
    unifi_ssid = portal_value('ssid')

    omada_client_mac = portal_value('clientMac')
    omada_ap_mac = portal_value('apMac')
    omada_gateway_mac = portal_value('gatewayMac')
    omada_ssid = portal_value('ssidName')
    omada_radio_id = portal_value('radioId')
    omada_site = portal_value('site')
    omada_redirect_url = portal_value('redirectUrl')
    omada_vid = portal_value('vid')

    provider = 'omada' if omada_client_mac or provider_hint == 'omada' else 'unifi'

    portal_context = {
        'provider': provider,
        'client_mac': omada_client_mac or unifi_client_mac,
        'ap_mac': omada_ap_mac or unifi_ap_mac,
        'redirect_url': omada_redirect_url or unifi_redirect_url,
        'ssid': omada_ssid or unifi_ssid,
        'timestamp': get_request_value('t'),
        'omada': {
            'clientMac': omada_client_mac,
            'apMac': omada_ap_mac,
            'gatewayMac': omada_gateway_mac,
            'ssidName': omada_ssid,
            'radioId': omada_radio_id,
            'site': omada_site,
            'redirectUrl': omada_redirect_url,
            'vid': omada_vid,
        }
    }
    remember_portal_context(portal_context)
    return portal_context

def authorize_unifi_guest(client_mac, minutes=480, ap_mac=None):
    """Autoriza dispositivo no UniFi Controller"""
    settings = load_unifi_settings()
    controller_url = settings.get('controller_url', '')
    username = settings.get('username', '')
    password = settings.get('password', '')
    site = settings.get('site', 'default')

    if not controller_url or not username or not password:
        logger.error("UniFi Controller credentials not configured")
        return False

    # Normaliza o MAC address
    client_mac = client_mac.lower().replace('-', ':').replace('.', ':')

    try:
        s = requests.Session()
        s.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'WiFi-Portal/1.0'
        })

        # Tenta login em dois endpoints (versões diferentes do Controller)
        login_payload = {
            'username': username,
            'password': password,
            'remember': True
        }
        login_success = False

        for endpoint in ['/api/auth/login', '/api/login']:
            try:
                login_resp = s.post(
                    f"{controller_url}{endpoint}",
                    json=login_payload,
                    verify=False,
                    allow_redirects=False,
                    timeout=10
                )
                logger.info(f"UniFi login attempt {endpoint}: status {login_resp.status_code}")

                if login_resp.status_code == 200:
                    login_success = True
                    logger.info(f"UniFi login successful via {endpoint}")
                    break
                elif login_resp.status_code in [302, 303, 307]:
                    location = login_resp.headers.get('Location', '')
                    if 'login' not in location.lower():
                        login_success = True
                        break
            except requests.exceptions.RequestException as e:
                logger.warning(f"UniFi login attempt {endpoint} error: {e}")

        if not login_success:
            logger.error("UniFi login failed on all endpoints")
            return False

        # Extrai CSRF token do header da resposta de login (necessário para UniFi OS)
        csrf_token = login_resp.headers.get('X-Csrf-Token', '')
        if csrf_token:
            s.headers.update({'X-CSRF-Token': csrf_token})
            logger.info("CSRF token found in response headers")

        # Autoriza o guest pelo MAC
        payload = {
            'cmd': 'authorize-guest',
            'mac': client_mac,
            'minutes': int(minutes)
        }
        if ap_mac:
            payload['ap_mac'] = ap_mac.lower().replace('-', ':').replace('.', ':')

        # Tenta com e sem prefixo /proxy/network (UniFi OS vs standalone)
        auth_resp = None
        for prefix in ['/proxy/network', '']:
            auth_url = f"{controller_url}{prefix}/api/s/{site}/cmd/stamgr"
            logger.info(f"Trying authorize at: {auth_url}")
            auth_resp = s.post(
                auth_url,
                json=payload,
                verify=False,
                timeout=10
            )
            if auth_resp.status_code == 200:
                break
            logger.warning(f"Authorize attempt {auth_url}: {auth_resp.status_code}")

        # Logout
        for logout_ep in ['/api/auth/logout', '/logout', '/api/logout']:
            try:
                s.post(f"{controller_url}{logout_ep}", verify=False, timeout=5)
                break
            except Exception:
                continue

        if auth_resp.status_code == 200:
            logger.info(f"UniFi guest authorized: {client_mac}")
            return True
        else:
            logger.error(f"UniFi auth failed: {auth_resp.status_code} - {auth_resp.text[:200]}")
            return False

    except Exception as e:
        logger.error(f"UniFi authorization error: {e}")
        return False

def authorize_omada_guest(omada_params, minutes=480):
    """Autoriza dispositivo no Omada Controller via External Portal API."""
    settings = load_omada_settings()
    controller_url = settings.get('controller_url', '').rstrip('/')
    controller_id = settings.get('controller_id', '').strip('/')
    operator_username = settings.get('operator_username', '')
    operator_password = settings.get('operator_password', '')
    default_site = settings.get('default_site', 'Default')
    auth_time_value, auth_time_unit = get_omada_auth_time_value(
        minutes,
        settings.get('auth_time_unit', DEFAULT_OMADA_AUTH_TIME_UNIT)
    )

    if not controller_url or not controller_id or not operator_username or not operator_password:
        logger.error("Omada Controller credentials not configured")
        return False

    client_mac = normalize_mac(omada_params.get('clientMac'))
    ap_mac = normalize_mac(omada_params.get('apMac'))
    gateway_mac = normalize_mac(omada_params.get('gatewayMac'))
    ssid_name = omada_params.get('ssidName', '')
    radio_id = omada_params.get('radioId', '')
    site = omada_params.get('site') or default_site
    vlan_id = omada_params.get('vid', '')

    if not client_mac:
        logger.error("Omada client MAC not received")
        return False

    is_gateway_auth = bool(gateway_mac)
    if is_gateway_auth:
        if not vlan_id:
            logger.error("Omada gateway auth missing VLAN ID")
            return False
    elif not ap_mac or not ssid_name or radio_id == '':
        logger.error("Omada EAP auth missing AP MAC, SSID or radio ID")
        return False

    hotspot_base = f"{controller_url}/{controller_id}/api/v2/hotspot"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'WiFi-Portal/1.0'
    }

    try:
        s = requests.Session()
        login_resp = s.post(
            f"{hotspot_base}/login",
            json={
                'name': operator_username,
                'password': operator_password
            },
            headers=headers,
            verify=False,
            timeout=10
        )

        try:
            login_data = login_resp.json()
        except ValueError:
            logger.error(f"Omada login returned invalid JSON: {login_resp.text[:200]}")
            return False

        if login_resp.status_code != 200 or login_data.get('errorCode') != 0:
            logger.error(f"Omada login failed: {login_resp.status_code} - {login_data}")
            return False

        csrf_token = (login_data.get('result') or {}).get('token')
        if not csrf_token:
            logger.error("Omada login did not return CSRF token")
            return False

        auth_payload = {
            'clientMac': client_mac,
            'site': site,
            'time': auth_time_value,
            'authType': 4
        }
        logger.info(
            f"Omada auth expiration: {int(minutes)} minutes as {auth_time_value} ({auth_time_unit})"
        )

        if is_gateway_auth:
            auth_payload.update({
                'gatewayMac': gateway_mac,
                'vid': vlan_id
            })
        else:
            auth_payload.update({
                'apMac': ap_mac,
                'ssidName': ssid_name,
                'radioId': radio_id
            })

        auth_headers = headers.copy()
        auth_headers['Csrf-Token'] = csrf_token

        auth_resp = s.post(
            f"{hotspot_base}/extPortal/auth",
            json=auth_payload,
            headers=auth_headers,
            verify=False,
            timeout=10
        )

        try:
            auth_data = auth_resp.json()
        except ValueError:
            logger.error(f"Omada auth returned invalid JSON: {auth_resp.text[:200]}")
            return False

        if auth_resp.status_code == 200 and auth_data.get('errorCode') == 0:
            logger.info(f"Omada guest authorized: {client_mac}")
            return True

        logger.error(f"Omada auth failed: {auth_resp.status_code} - {auth_data}")
        return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Omada authorization request error: {e}")
        return False
    except Exception as e:
        logger.error(f"Omada authorization error: {e}")
        return False

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
    
    # Captura parâmetros do UniFi ou Omada Controller (GET ou POST)
    portal_context = build_portal_context()
    portal_provider = portal_context['provider']
    client_mac = portal_context['client_mac']
    ap_mac = portal_context['ap_mac']
    redirect_url = portal_context['redirect_url']
    ssid = portal_context['ssid']
    timestamp = portal_context['timestamp']
    omada_params = portal_context['omada']
    controller_settings = load_omada_settings() if portal_provider == 'omada' else load_unifi_settings()
    controller_site = (
        omada_params.get('site') or controller_settings.get('default_site', 'Default')
        if portal_provider == 'omada'
        else controller_settings.get('site', 'default')
    )
    auth_minutes = parse_minutes(controller_settings.get('auth_minutes'), 480, 1, 14400)
    cooldown_minutes = parse_minutes(controller_settings.get('cooldown_minutes'), 0, 0, 14400)

    def render_login_form(**extra):
        context = {
            'client_mac': client_mac,
            'ap_mac': ap_mac,
            'redirect_url': redirect_url,
            'ssid': ssid,
            'timestamp': timestamp,
            'portal_provider': portal_provider,
            'omada_params': omada_params,
            'form_disabled': False,
            'login_form_action': build_login_form_action(),
            'csrf_token': generate_csrf_token()
        }
        context.update(extra)
        return render_template('login.html', **context)

    if client_mac and cooldown_minutes > 0:
        portal_session_state = data_manager.get_portal_session_state(
            client_mac,
            portal_provider,
            controller_site
        )
        if portal_session_state.get('blocked'):
            remaining = format_duration_pt(portal_session_state.get('remaining_seconds', 0))
            flash(
                f'Para manter o Wi-Fi disponivel a todos, este acesso possui limite de tempo. '
                f'Voce podera solicitar um novo acesso em {remaining}.',
                'info'
            )
            security_manager.log_security_event('portal_cooldown_blocked', {
                'client_mac': client_mac,
                'controller_type': portal_provider,
                'controller_site': controller_site,
                'remaining_seconds': portal_session_state.get('remaining_seconds', 0)
            })
            return render_login_form(
                form_disabled=True,
                cooldown_state=portal_session_state
            )
    
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
                    'client_mac': client_mac,
                    'user_agent': request.headers.get('User-Agent', 'Unknown')
                })
                errors.append('Por favor, informe dados válidos.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_login_form(nome=nome, email=email)
        
        user_agent = request.headers.get('User-Agent', 'Desconhecido')
        now = datetime.now()
        data = now.strftime('%Y-%m-%d')
        hora = now.strftime('%H:%M:%S')
        if not client_mac:
            log_missing_portal_mac(portal_provider)
        
        access_data = {
            'nome': nome,
            'ip': request.remote_addr,
            'mac': client_mac,
            'controller_type': portal_provider,
            'controller_site': controller_site,
            'user_agent': user_agent,
            'data': data,
            'hora': hora,
            'email': email,
            'ap_mac': ap_mac,
            'gateway_mac': omada_params.get('gatewayMac') if portal_provider == 'omada' else None,
            'vlan_id': omada_params.get('vid') if portal_provider == 'omada' else None,
            'ssid': ssid
        }
        
        try:
            # Registra no banco de dados PostgreSQL com criptografia
            data_manager.log_access_encrypted(access_data)
            
            security_manager.log_security_event('access_registered', {
                'client_mac': client_mac,
                'ap_mac': ap_mac,
                'controller_type': portal_provider,
                'ssid': ssid,
                'user_agent': user_agent[:100]  # Limita tamanho
            })
            
        except Exception as e:
            logger.error(f"Erro ao registrar acesso: {e}")
            flash('Erro ao registrar acesso. Por favor, tente novamente.', 'error')
            return render_login_form(nome=nome, email=email)
        
        # Autoriza o dispositivo no controlador de origem
        if client_mac:
            if portal_provider == 'omada':
                auth_result = authorize_omada_guest(omada_params, minutes=auth_minutes)
            else:
                auth_result = authorize_unifi_guest(client_mac, minutes=auth_minutes, ap_mac=ap_mac)
            if not auth_result:
                logger.error(f"Failed to authorize MAC {client_mac} on {portal_provider} controller")
                flash('Não foi possível liberar o acesso à internet. Tente novamente.', 'error')
                return render_login_form(nome=nome, email=email)
            data_manager.register_portal_session(
                mac=client_mac,
                controller_type=portal_provider,
                controller_site=controller_site,
                ssid=ssid,
                auth_minutes=auth_minutes,
                cooldown_minutes=cooldown_minutes
            )
        else:
            logger.warning(f"No client MAC received — cannot authorize on {portal_provider}")
            flash('Dispositivo não identificado. Tente reconectar à rede Wi-Fi.', 'error')
            return render_login_form(nome=nome, email=email)
        
        # Redireciona para a URL original ou site padrão
        final_url = redirect_url or 'https://www.patydoalferes.rj.gov.br'
        return redirect(final_url)
    
    return render_login_form()

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
    return render_template('politica_privacidade.html', **get_privacy_settings())

@app.route('/')
def index():
    """Redireciona para a página de login"""
    return redirect(url_for('login', **request.args))

def run_privacy_cleanup(apply_changes=False):
    settings = get_privacy_settings()
    result = data_manager.cleanup_expired_privacy_records(
        access_log_retention_days=settings['access_log_retention_days'],
        portal_session_retention_days=settings['portal_session_retention_days'],
        apply_changes=apply_changes
    )

    action = 'removidos' if apply_changes else 'encontrados'
    print(f"Registros de acesso {action}: {result.get('access_logs', 0)}")
    print(f"Sessoes do portal {action}: {result.get('portal_sessions', 0)}")
    if result.get('error'):
        raise RuntimeError(result['error'])

@app.cli.command('privacy-cleanup')
def privacy_cleanup_command():
    """Conta dados expirados pela politica de retencao."""
    run_privacy_cleanup(apply_changes=False)

@app.cli.command('privacy-cleanup-apply')
def privacy_cleanup_apply_command():
    """Remove dados expirados pela politica de retencao."""
    run_privacy_cleanup(apply_changes=True)

@app.route('/admin')
@require_admin
def admin():
    """Página de administração com criptografia"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        if per_page not in [25, 50, 100, 200]:
            per_page = 50

        # Obtém logs criptografados paginados
        pagination = data_manager.get_access_logs_page(page=page, per_page=per_page)
        encrypted_logs = pagination['items']
        
        # Obtém estatísticas
        stats = data_manager.get_user_stats()
        
        return render_template('admin.html', 
                             registros=encrypted_logs, 
                             stats=stats,
                             pagination=pagination,
                             total_registros=pagination['total'],
                             per_page=per_page)
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

@app.route('/admin/unifi', methods=['GET', 'POST'])
@require_csrf_token
def admin_unifi_settings():
    """Página de configurações do UniFi Controller"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    settings = load_unifi_settings()
    csrf_token = generate_csrf_token()

    if request.method == 'POST':
        action = request.form.get('action', 'save')

        controller_url = sanitize_input(request.form.get('controller_url', '')).rstrip('/')
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        site = sanitize_input(request.form.get('site', '')) or 'default'
        auth_minutes = request.form.get('auth_minutes', '480')
        cooldown_minutes = request.form.get('cooldown_minutes', '0')

        try:
            auth_minutes = int(auth_minutes)
            if auth_minutes < 1 or auth_minutes > 14400:
                auth_minutes = 480
        except ValueError:
            auth_minutes = 480
        cooldown_minutes = parse_minutes(cooldown_minutes, 0, 0, 14400)

        new_settings = {
            'controller_url': controller_url,
            'username': username,
            'password': password if password else settings.get('password', ''),
            'site': site,
            'auth_minutes': auth_minutes,
            'cooldown_minutes': cooldown_minutes,
        }

        if action == 'test':
            # Testa conexão com o Controller
            if not controller_url or not username or not (password or settings.get('password')):
                flash('Preencha todos os campos de conexão antes de testar.', 'error')
            else:
                try:
                    s = requests.Session()
                    s.headers.update({
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'User-Agent': 'WiFi-Portal/1.0'
                    })
                    test_password = password if password else settings.get('password', '')
                    login_payload = {
                        'username': username,
                        'password': test_password,
                        'remember': True
                    }
                    login_ok = False
                    for endpoint in ['/api/auth/login', '/api/login']:
                        try:
                            resp = s.post(
                                f"{controller_url}{endpoint}",
                                json=login_payload,
                                verify=False,
                                allow_redirects=False,
                                timeout=10
                            )
                            if resp.status_code == 200:
                                login_ok = True
                                break
                            elif resp.status_code in [302, 303, 307]:
                                location = resp.headers.get('Location', '')
                                if 'login' not in location.lower():
                                    login_ok = True
                                    break
                        except requests.exceptions.RequestException:
                            continue
                    # Testa se consegue acessar API (com prefixo UniFi OS)
                    if login_ok:
                        csrf_token_val = resp.headers.get('X-Csrf-Token', '')
                        if csrf_token_val:
                            s.headers.update({'X-CSRF-Token': csrf_token_val})
                        api_ok = False
                        for prefix in ['/proxy/network', '']:
                            try:
                                api_resp = s.get(
                                    f"{controller_url}{prefix}/api/s/{site}/stat/sta",
                                    verify=False, timeout=10
                                )
                                if api_resp.status_code == 200:
                                    api_ok = True
                                    break
                            except Exception:
                                continue
                    for logout_ep in ['/api/auth/logout', '/logout', '/api/logout']:
                        try:
                            s.post(f"{controller_url}{logout_ep}", verify=False, timeout=5)
                            break
                        except Exception:
                            continue
                    if login_ok and api_ok:
                        flash('Conexão com o UniFi Controller realizada com sucesso!', 'success')
                    elif login_ok:
                        flash('Login OK, mas não foi possível acessar a API. Verifique permissões.', 'warning')
                    else:
                        flash('Falha na autenticação. Verifique usuário e senha.', 'error')
                except requests.exceptions.ConnectionError:
                    flash('Não foi possível conectar ao Controller. Verifique o endereço.', 'error')
                except Exception as e:
                    flash(f'Erro ao testar conexão: {str(e)}', 'error')

            settings = new_settings
        else:
            # Salva configurações
            if save_unifi_settings(new_settings):
                flash('Configurações salvas com sucesso!', 'success')
                security_manager.log_security_event('unifi_settings_updated', {
                    'username': session.get('username'),
                    'controller_url': controller_url
                })
                settings = new_settings
            else:
                flash('Erro ao salvar configurações.', 'error')

    display_settings = {
        'controller_url': settings.get('controller_url', ''),
        'username': settings.get('username', ''),
        'site': settings.get('site', 'default'),
        'auth_minutes': settings.get('auth_minutes', 480),
        'cooldown_minutes': settings.get('cooldown_minutes', 0),
        'has_password': bool(settings.get('password')),
    }
    is_configured = bool(settings.get('controller_url') and settings.get('username') and settings.get('password'))

    return render_template('admin_unifi.html',
                         settings=display_settings,
                         is_configured=is_configured,
                         csrf_token=csrf_token)

@app.route('/admin/omada', methods=['GET', 'POST'])
@require_csrf_token
def admin_omada_settings():
    """Página de configurações do Omada Controller"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    settings = load_omada_settings()
    csrf_token = generate_csrf_token()

    if request.method == 'POST':
        action = request.form.get('action', 'save')

        controller_url = sanitize_input(request.form.get('controller_url', '')).rstrip('/')
        controller_id = sanitize_input(request.form.get('controller_id', '')).strip('/')
        operator_username = sanitize_input(request.form.get('operator_username', ''))
        operator_password = request.form.get('operator_password', '')
        default_site = sanitize_input(request.form.get('default_site', '')) or 'Default'
        auth_minutes = request.form.get('auth_minutes', '480')
        cooldown_minutes = request.form.get('cooldown_minutes', '0')
        auth_time_unit = normalize_omada_auth_time_unit(
            request.form.get(
                'auth_time_unit',
                settings.get('auth_time_unit', DEFAULT_OMADA_AUTH_TIME_UNIT)
            )
        )

        try:
            auth_minutes = int(auth_minutes)
            if auth_minutes < 1 or auth_minutes > 14400:
                auth_minutes = 480
        except ValueError:
            auth_minutes = 480
        cooldown_minutes = parse_minutes(cooldown_minutes, 0, 0, 14400)

        new_settings = {
            'controller_url': controller_url,
            'controller_id': controller_id,
            'operator_username': operator_username,
            'operator_password': operator_password if operator_password else settings.get('operator_password', ''),
            'default_site': default_site,
            'auth_minutes': auth_minutes,
            'cooldown_minutes': cooldown_minutes,
            'auth_time_unit': auth_time_unit,
        }

        if action == 'test':
            if not controller_url or not controller_id or not operator_username or not (operator_password or settings.get('operator_password')):
                flash('Preencha todos os campos de conexão antes de testar.', 'error')
            else:
                try:
                    s = requests.Session()
                    s.headers.update({
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'User-Agent': 'WiFi-Portal/1.0'
                    })
                    test_password = operator_password if operator_password else settings.get('operator_password', '')
                    login_resp = s.post(
                        f"{controller_url}/{controller_id}/api/v2/hotspot/login",
                        json={
                            'name': operator_username,
                            'password': test_password
                        },
                        verify=False,
                        timeout=10
                    )

                    try:
                        login_data = login_resp.json()
                    except ValueError:
                        login_data = {}

                    token = (login_data.get('result') or {}).get('token')
                    if login_resp.status_code == 200 and login_data.get('errorCode') == 0 and token:
                        flash('Login na API Hotspot do Omada realizado com sucesso!', 'success')
                    elif login_resp.status_code == 200 and login_data.get('errorCode') == 0:
                        flash('Login OK, mas o Omada não retornou token CSRF. Verifique a versão e permissões do operador.', 'warning')
                    else:
                        flash('Falha na autenticação do Omada. Verifique operador, senha e Controller ID.', 'error')
                except requests.exceptions.ConnectionError:
                    flash('Não foi possível conectar ao Omada Controller. Verifique URL, porta e firewall.', 'error')
                except Exception as e:
                    flash(f'Erro ao testar conexão Omada: {str(e)}', 'error')

            settings = new_settings
        else:
            if save_omada_settings(new_settings):
                flash('Configurações Omada salvas com sucesso!', 'success')
                security_manager.log_security_event('omada_settings_updated', {
                    'username': session.get('username'),
                    'controller_url': controller_url,
                    'auth_time_unit': auth_time_unit
                })
                settings = new_settings
            else:
                flash('Erro ao salvar configurações Omada.', 'error')

    display_auth_minutes = settings.get('auth_minutes', 480)
    display_auth_time_unit = normalize_omada_auth_time_unit(
        settings.get('auth_time_unit', DEFAULT_OMADA_AUTH_TIME_UNIT)
    )
    display_auth_time_value, display_auth_time_unit = get_omada_auth_time_value(
        display_auth_minutes,
        display_auth_time_unit
    )

    display_settings = {
        'controller_url': settings.get('controller_url', ''),
        'controller_id': settings.get('controller_id', ''),
        'operator_username': settings.get('operator_username', ''),
        'default_site': settings.get('default_site', 'Default'),
        'auth_minutes': display_auth_minutes,
        'cooldown_minutes': settings.get('cooldown_minutes', 0),
        'auth_time_unit': display_auth_time_unit,
        'auth_time_value': display_auth_time_value,
        'has_password': bool(settings.get('operator_password')),
    }
    is_configured = bool(
        settings.get('controller_url')
        and settings.get('controller_id')
        and settings.get('operator_username')
        and settings.get('operator_password')
    )

    return render_template('admin_omada.html',
                         settings=display_settings,
                         is_configured=is_configured,
                         csrf_token=csrf_token)

if __name__ == '__main__':
    with app.app_context():
        # Cria tabelas se não existirem
        db.create_all()
        # Cria usuário admin padrão
        create_default_user()
    
    ensure_directory('logs', mode=0o750)
    ensure_directory('uploads', mode=0o750)
    app.run(host='0.0.0.0', debug=False)
