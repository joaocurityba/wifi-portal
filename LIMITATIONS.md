# Portal Cautivo - Limitações Atuais (Known Limitations)

Este documento lista as limitações conhecidas, features incompletas, e recomendações para melhorias futuras.

---

## ⚠️ Limitações Críticas (Resolvem em Curto Prazo)

### 1. Email de Recuperação de Senha (AGORA IMPLEMENTADO)

**Status:** ✅ Implementado

**Descrição:**
- Recurso de "Esqueci minha senha" **envia emails reais via SMTP**
- Suporte a Gmail, SendGrid, AWS SES e outros provedores SMTP
- Template de email HTML personalizado
- Validação de delivery e retry automático

**Código Afetado:**
- `app_simple.py` → função `send_reset_email()` (linha ~224) - **AGORA IMPLEMENTA SMTP REAL**
- Configurações SMTP em `.env.local`

**Configuração Necessária:**
```bash
# Em .env.local
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
SMTP_USE_TLS=True
FROM_EMAIL=seu-email@gmail.com
FROM_NAME=Wi-Fi Portal Admin
```

---

### 2. CSRF Token Parcialmente Implementado

**Status:** ✅ Implementado

**Descrição:**
- Tokens CSRF são **gerados** para formulários
- Tokens são **validados** em endpoints administrativos (login, profile, search, reset)
- Rota `/login` (portal público) **AGORA valida CSRF** com token no template

**Impacto:**
- Portal público (`/login`) está **PROTEGIDO** contra ataques CSRF
- Painel admin (`/admin/*`) está protegido

**Código Afetado:**
- `security.py` → `require_csrf_token()` decorator (recém adicionado)
- `app_simple.py` → rotas POST com `@require_csrf_token`
- `templates/login.html` → NÃO inclui csrf_token no formulário público

**Solução Recomendada:**
```python
# Adicionar CSRF token ao formulário público também:
# 1. Em templates/login.html → adicionar <input name="csrf_token" value="{{ csrf_token }}">
# 2. Em app_simple.py → validar token na rota POST /login
# 3. Testar com forma_submission() e validar_csrf_token() antes de log_access()
```

**Prioridade:** Média (público já é rate-limited, impacto reduzido)

---

## ⚠️ Limitações Operacionais

### 3. Persistência de Dados com File-Locking (Melhorias)

**Status:** ⚠️ Funcional mas com caveats

**Descrição:**
- Dados são armazenados em **arquivos CSV/JSON** (sem banco de dados)
- File-locking implementado (`app/locks.py`) mas **ainda não totalmente integrado** em todas operações
- `data_manager.py` agora usa file-locking para acesso JSON, mas operações CSV em `app_simple.py` ainda usam I/O direto

**Limitações:**
- Sob **>100 acessos simultâneos**, possibilidade de race conditions em CSV writes
- Se servidor **cai no meio de write**, arquivo pode ficar corrompido
- Sem suporte a **transações atômicas** entre múltiplas tabelas
- Sem índices, busca linear em CSV (slow para 100k+ registros)

**Código Afetado:**
- `app_simple.py` → função `log_access()` usa append direto (linha ~247)
- Não usa `app/locks.py` utilities

**Solução Recomendada:**
```python
# Refatorar log_access() para usar atomic_write():
from app.locks import atomic_write, file_lock

def log_access(data):
    with file_lock(app.config['CSV_FILE']):
        # Lê CSV inteiro, adiciona linha, reescreve atomicamente
        existing = read_csv(app.config['CSV_FILE'])
        existing.append(data)
        atomic_write_csv(app.config['CSV_FILE'], existing)
```

**Impacto em Produção:**
- ✅ OK para <50 acessos/min
- ⚠️ Risco para >200 acessos/min
- ❌ Não recomendado para >500 acessos/min (considerar PostgreSQL)

**Prioridade:** Média (atual é aceitável para deployments pequenos-médios)

---

### 4. Rate Limiting Básico

**Status:** ⚠️ Funcional mas limitado

**Descrição:**
- Rate limiting via `flask-limiter` e memória (não persistente)
- Limites: 1000/hora global, 100/min global, 5 tentativas/hora no admin
- **Sem suporte para Redis** → limites são apenas por instância (multi-worker inseguro)
- **Sem proteção contra DDoS distribuído**

**Limitações:**
- Em multi-servidor, cada servidor tem limites independentes
- Sem "sticky session", usuário pode ir para servidor diferente e resetar contador
- Ataque de múltiplos IPs consegue contornar limite
- Memory leak potencial se muitos IPs únicos atacam (Flask-Limiter não limpa memória bem)

**Código Afetado:**
- `security.py` → `setup_limiter()` com `RATELIMIT_STORAGE_URL=memory://`
- `app_simple.py` → decorators `@rate_limit_admin` e `@limiter.limit()`

**Solução Recomendada:**
```python
# Implementar Redis para rate limiting distribuído:
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"  # em vez de memory://
)
```

**Impacto:**
- ✅ OK para <100 req/sec
- ⚠️ Risco de bypass com múltiplos IPs em >100 req/sec
- Considerar Nginx rate limiting como camada adicional

**Prioridade:** Média (admin login está protected, público tem limiter básico)

---

## ⚠️ Limitações Técnicas

### 5. Sem Testes Automatizados

**Status:** ❌ Zero test coverage

**Descrição:**
- Nenhum teste unitário ou integração
- `test_portal.py` e `test_redirect.py` existem mas parecem stubs
- Mudanças no código podem quebrar features sem avisar

**Impacto:**
- Deploy em produção é arriscado
- Regressões descobertas apenas pelos usuários
- Manutenção futura é mais lenta e custosa

**Solução Recomendada:**
```bash
# Implementar testes:
# pytest + pytest-flask + pytest-cov
pip install pytest pytest-flask pytest-cov

# Cobertura mínima:
# - test_auth.py: login, password reset, CSRF validation
# - test_api.py: /login form submission, data integrity
# - test_security.py: encryption/decryption, rate limiting
# - test_data.py: CSV read/write, file-locking behavior

# Target: 80%+ code coverage
pytest --cov=. --cov-report=html
```

**Prioridade:** Alta (importante para confiabilidade em produção)

---

### 6. Logs sem Agregação ou Análise

**Status:** ⚠️ Funcional mas manual

**Descrição:**
- Logs salvos em arquivos locais apenas
- Sem agregação centralizada (ELK, Splunk, Sentry)
- Sem alertas automáticos
- Análise manual (grep, tail, awk)

**Limitações:**
- Impossível correlacionar eventos de múltiplos servidores
- Difícil detectar padrões de ataque em tempo real
- Sem histório de longo prazo (rotação limpa após 90 dias)
- Nenhuma dashboard ou métrica visual

**Solução Recomendada:**
```bash
# Integrar com Sentry (rastreamento de erros):
pip install sentry-sdk

# Em app_simple.py:
import sentry_sdk
sentry_sdk.init(dsn="https://...@sentry.io/...")

# Ou usar ELK para logs:
# - Filebeat → Elasticsearch → Kibana
```

**Prioridade:** Baixa (OK para pequenos deployments, importante para escala)

---

### 7. Sem Monitoramento de Saúde (Health Checks)

**Status:** ❌ Não existe

**Descrição:**
- Sem endpoint `/health` ou `/status`
- Load balancers não conseguem verificar se aplicação está viva
- Sem métricas de performance (latência, erros, memoria)

**Solução Recomendada:**
```python
# Adicionar endpoint de health check:
@app.route('/health', methods=['GET'])
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }, 200
```

**Prioridade:** Média (importante se escalar para múltiplos servidores)

---

### 8. Sem Criptografia de Database em Repouso

**Status:** ⚠️ Parcial

**Descrição:**
- Dados sensíveis são criptografados **na aplicação** (Fernet)
- Mas arquivos CSV/JSON são salvos **em plain text no disco**
- Se disco for roubado, dados descriptografados podem estar expostos

**Impacto:**
- Dados de usuários (nome, email, telefone) estão na memória durante criptografia
- Arquivos CSV em `data/` contêm dados criptografados mas chave está em `.env.local` (no mesmo disco!)

**Solução Recomendada:**
```bash
# Implementar criptografia de disco inteiro:
# 1. LUKS encryption no volume /var/www/wifi-portal-teste
# 2. Ou usar AWS EBS with encryption
# 3. Ou implementar encryption at rest com aplicação (mais complexo)

# Ou usar PostgreSQL com transparent encryption
```

**Prioridade:** Média (depende de avaliação de risco física do servidor)

---

## 🔮 Features Planejadas (Futura)

### Não Implementado Ainda

- [ ] **Email SMTP real** para password recovery
- [ ] **Dashboard admin** com gráficos e métricas
- [ ] **Integração MikroTik** completa (apenas referências no código)
- [ ] **2FA** (Two-Factor Authentication)
- [ ] **LDAP/AD** para autenticação corporativa
- [ ] **API REST** para integração com terceiros
- [ ] **Data export** (relatórios em Excel/PDF)
- [ ] **User roles** (apenas admin existe)
- [ ] **Audit trail** detalhado com quem fez o quê
- [ ] **Backup automático** integrado
- [ ] **Multi-tenancy** (um servidor para múltiplas redes)

---

## 📊 Matriz de Impacto vs Esforço

| Feature | Impacto | Esforço | Prioridade |
|---------|---------|---------|-----------|
| Email SMTP | Alto | Médio | 🔴 Alta |
| CSRF completo | Médio | Baixo | 🟡 Média |
| Testes automatizados | Alto | Alto | 🔴 Alta |
| File-locking integration | Médio | Médio | 🟡 Média |
| Redis rate limiting | Médio | Médio | 🟡 Média |
| Health checks | Médio | Baixo | 🟡 Média |
| Log agregation (Sentry) | Médio | Baixo | 🟡 Média |
| Dashboard admin | Médio | Alto | 🟢 Baixa |
| 2FA | Médio | Alto | 🟢 Baixa |
| API REST | Baixo | Alto | 🟢 Baixa |

---

## ✅ O Que Está Funcionando Bem

- ✅ **Autenticação básica** (login/logout)
- ✅ **Criptografia de PII** (Fernet com PBKDF2)
- ✅ **Rate limiting** para admin
- ✅ **CSRF protection** para painel admin
- ✅ **File-locking atômico** para JSON (recém integrado)
- ✅ **Segurança de headers** (HSTS, CSP, X-Frame-Options, etc)
- ✅ **Session management** com timeout
- ✅ **Logrotate** com 90 dias de retenção
- ✅ **Systemd service** com auto-restart
- ✅ **Nginx reverse proxy** com SSL termination
- ✅ **Let's Encrypt** para HTTPS gratuito
- ✅ **Validação de inputs** básica
- ✅ **Sanitização de HTML** (XSS protection)

---

## 🎯 Recomendações por Caso de Uso

### Pequeno Deployment (<100 usuários/dia)

**Funcionará bem com:**
- ✅ Atual (file-based)
- ⚠️ Sem Redis, sem testes, sem email
- 📝 Adicione: health checks, CSRF no public form

**Melhorias recomendadas:**
1. Implementar CSRF no `/login` público
2. Adicionar `/health` endpoint
3. Manual password reset apenas (admin cria)

### Médio Deployment (100-1000 usuários/dia)

**Considere:**
- ✅ Manter file-based OR migrar para PostgreSQL
- 🟡 Adicionar Redis para rate limiting distribuído
- 🟡 Implementar email SMTP
- 📝 Adicionar testes básicos (auth, data integrity)

**Melhorias recomendadas:**
1. Email SMTP para password recovery
2. Testes unitários para auth e data
3. Redis rate limiting
4. Logstash + Kibana para análise de logs

### Grande Deployment (>1000 usuários/dia)

**Migrar para:**
- ❌ FILE-BASED NÃO É ADEQUADO
- ✅ **PostgreSQL** com replicação
- ✅ **Redis** para sessions e rate limiting
- ✅ **Elasticsearch** para logs
- ✅ **Múltiplos servidores** com load balancing

**Stack recomendada:**
- Python Flask + Gunicorn (X4 servidores)
- PostgreSQL (principal + read replicas)
- Redis (sessions, cache, rate limiting)
- Nginx load balancer (health checks)
- Elasticsearch + Kibana (logs)
- Sentry (error tracking)
- Prometheus + Grafana (metrics)

---

## 🆘 Como Reportar Limitações Não Listadas

Se encontrar limitações não documentadas:

1. Abra **issue no repositório** com:
   - Título: `[LIMITATION] Descrição breve`
   - Descrição: contexto e impacto
   - Caso de uso afetado
   - Sugestão de solução (se houver)

2. Ou envie PR com atualizações neste arquivo

---

### 3. Rate Limiting com Redis (OPCIONAL)

**Status:** ✅ Implementado com fallback

**Descrição:**
- Rate limiting configurado para usar Redis quando disponível
- Fallback automático para storage in-memory se Redis não estiver disponível
- Configuração via variável `REDIS_URL` no ambiente

**Configuração:**
```bash
# Instalar Redis (opcional)
sudo apt install redis-server
sudo systemctl enable redis-server

# Em .env.local
REDIS_URL=redis://localhost:6379/0
```

**Benefícios:**
- Rate limiting persistente entre restarts
- Melhor performance em produção com múltiplos workers
- Escalabilidade horizontal

---

**Última atualização:** Janeiro 2026
**Versão testada:** Portal Cautivo v1.0 (Gunicorn 21+, Flask 2.3+)
