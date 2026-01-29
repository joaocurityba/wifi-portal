#!/bin/bash
# Portal Cautivo - Deployment and Pre-Flight Checklist
# Use this before deploying to production on Ubuntu server
# Usage: bash deploy/checklist.sh

set -e

echo "========================================="
echo "Portal Cautivo - Deployment Checklist"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    return 1
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check 1: Python version
echo "[1/15] Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$PYTHON_VERSION >= 3.9" | bc -l) )); then
        check_pass "Python 3.9+ found (${PYTHON_VERSION})"
    else
        check_fail "Python 3.9+ required (found ${PYTHON_VERSION})"
    fi
else
    check_fail "Python3 not found"
fi

# Check 2: Virtual environment
echo ""
echo "[2/15] Checking virtual environment..."
if [ -d "/var/www/wifi-portal/.venv" ]; then
    check_pass "Virtual environment found at /var/www/wifi-portal/.venv"
else
    check_fail "Virtual environment not found at /var/www/wifi-portal/.venv"
fi

# Check 3: Requirements installed
echo ""
echo "[3/15] Checking if requirements are installed..."
if /var/www/wifi-portal/.venv/bin/pip list | grep -q "gunicorn"; then
    check_pass "Gunicorn installed"
else
    check_fail "Gunicorn not installed"
fi

# Check 4: .env.local exists
echo ""
echo "[4/15] Checking .env.local configuration..."
if [ -f "/var/www/wifi-portal/.env.local" ]; then
    check_pass ".env.local file exists"
    if grep -q "SECRET_KEY=" "/var/www/wifi-portal/.env.local"; then
        check_pass "SECRET_KEY is set"
    else
        check_fail "SECRET_KEY not found in .env.local"
    fi
else
    check_fail ".env.local not found (copy from .env.template)"
fi

# Check 5: Directory permissions
echo ""
echo "[5/15] Checking directory permissions..."
if [ -d "/var/www/wifi-portal/data" ]; then
    PERMS=$(stat -c '%a' /var/www/wifi-portal/data)
    if [ "$PERMS" = "750" ] || [ "$PERMS" = "755" ]; then
        check_pass "data/ has appropriate permissions ($PERMS)"
    else
        check_warn "data/ permissions are $PERMS (recommend 750)"
    fi
else
    check_fail "data/ directory not found"
fi

# Check 6: Log directory
echo ""
echo "[6/15] Checking logs directory..."
if [ -d "/var/www/wifi-portal/logs" ]; then
    check_pass "logs/ directory exists"
else
    check_fail "logs/ directory not found (will be created by app)"
fi

# Check 7: Static files
echo ""
echo "[7/15] Checking static files..."
if [ -d "/var/www/wifi-portal/static" ]; then
    check_pass "static/ directory exists"
else
    check_fail "static/ directory not found"
fi

# Check 8: Nginx installed
echo ""
echo "[8/15] Checking Nginx installation..."
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1)
    check_pass "Nginx installed (${NGINX_VERSION})"
else
    check_warn "Nginx not installed (required for production)"
fi

# Check 9: Systemd service
echo ""
echo "[9/15] Checking systemd service..."
if [ -f "/etc/systemd/system/portal-cautivo.service" ]; then
    check_pass "Systemd service file exists"
    if systemctl is-enabled portal-cautivo &>/dev/null; then
        check_pass "Service is enabled"
    else
        check_warn "Service is not enabled (run: sudo systemctl enable portal-cautivo)"
    fi
else
    check_warn "Systemd service not installed (copy deploy/portal.service to /etc/systemd/system/)"
fi

# Check 10: SSL certificate
echo ""
echo "[10/15] Checking SSL certificate..."
if [ -f "/etc/letsencrypt/live/seu-dominio.com/fullchain.pem" ]; then
    check_pass "SSL certificate found"
else
    check_warn "Let's Encrypt certificate not found (run: sudo certbot certonly --standalone -d seu-dominio.com)"
fi

# Check 11: Firewall
echo ""
echo "[11/15] Checking firewall rules..."
if sudo ufw status | grep -q "Status: active"; then
    check_pass "UFW firewall is active"
    if sudo ufw status | grep -q "443/tcp"; then
        check_pass "Port 443 (HTTPS) is open"
    else
        check_warn "Port 443 may not be open (run: sudo ufw allow 443/tcp)"
    fi
else
    check_warn "UFW firewall appears inactive"
fi

# Check 12: Logrotate
echo ""
echo "[12/15] Checking logrotate configuration..."
if [ -f "/etc/logrotate.d/wifi-portal" ]; then
    check_pass "Logrotate configuration installed"
else
    check_warn "Logrotate not configured (copy deploy/logrotate.conf to /etc/logrotate.d/wifi-portal)"
fi

# Check 13: CSRF protection
echo ""
echo "[13/15] Checking CSRF protection in templates..."
if grep -q "csrf_token" /var/www/wifi-portal/templates/*.html 2>/dev/null; then
    check_pass "CSRF tokens found in templates"
else
    check_warn "CSRF tokens may not be present in all forms"
fi

# Check 14: Database/data integrity
echo ""
echo "[14/15] Checking data file integrity..."
if [ -f "/var/www/wifi-portal/data/users.csv" ]; then
    LINES=$(wc -l < /var/www/wifi-portal/data/users.csv)
    check_pass "users.csv exists ($LINES lines)"
else
    check_fail "users.csv not found"
fi

# Check 15: Application test
echo ""
echo "[15/15] Testing application import..."
if /var/www/wifi-portal/.venv/bin/python -c "from wsgi import app; print('OK')" 2>/dev/null; then
    check_pass "Application imports successfully"
else
    check_fail "Application import failed"
fi

# Summary
echo ""
echo "========================================="
echo "Pre-flight checklist complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Review warnings above"
echo "2. Start the service: sudo systemctl start portal-cautivo"
echo "3. Check status: sudo systemctl status portal-cautivo"
echo "4. View logs: sudo journalctl -u portal-cautivo -f"
echo "5. Test URL: https://seu-dominio.com/login"
echo ""
