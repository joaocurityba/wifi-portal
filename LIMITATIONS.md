# ⚠️ Limitações e Considerações

Documento que descreve as limitações atuais do Portal Cativo, restrições técnicas e roadmap de melhorias futuras.

---

## 📋 Índice

1. [Limitações Arquiteturais](#limitações-arquiteturais)
2. [Limitações de Armazenamento](#limitações-de-armazenamento)
3. [Limitações de Escalabilidade](#limitações-de-escalabilidade)
4. [Limitações de Segurança](#limitações-de-segurança)
5. [Limitações de Features](#limitações-de-features)
6. [Limitações de Infraestrutura](#limitações-de-infraestrutura)
7. [Limitações de Integração](#limitações-de-integração)
8. [Considerações de Performance](#considerações-de-performance)
9. [Roadmap de Melhorias](#roadmap-de-melhorias)
10. [Migração Futura](#migração-futura)

---

## 🏗️ Limitações Arquiteturais

### **Armazenamento em CSV**

**❌ Limitação Atual:**
- Dados armazenados em arquivos CSV simples
- Não suporta transações ACID
- Leitura/escrita pode ser lenta com muitos registros
- Risco de corrupção em caso de falha
- Busca sequencial (O(n))

**Impacto:**
- Máximo recomendado: **10.000 registros** por arquivo
- Performance degrada com volume alto
- Concorrência limitada

**Workaround Temporário:**
```python
# Rotação automática de logs (em data_manager.py)
# Quando access_log.csv > 5MB, criar novo arquivo
if os.path.getsize('access_log.csv') > 5_000_000:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.rename('access_log.csv', f'access_log_{timestamp}.csv')
```

**Solução Futura:**
- Migrar para PostgreSQL ou MySQL
- Ver [Migração para Banco de Dados](#roadmap-de-melhorias)

---

### **Monolito Flask**

**❌ Limitação Atual:**
- Aplicação monolítica em arquivo único (`app_simple.py`)
- Difícil manutenção e escalabilidade
- Testes unitários complexos

**Impacto:**
- Escalabilidade horizontal limitada
- Acoplamento alto entre componentes

**Solução Futura:**
- Refatorar para arquitetura modular
- Separar em blueprints Flask
- Considerar microserviços

---

## 💾 Limitações de Armazenamento

### **Dados de Usuários (users.csv)**

**Formato Atual:**
```csv
username,password_hash,role,created_at
admin,$pbkdf2-sha256$...,admin,2024-01-15
```

**Limitações:**

| Aspecto | Limitação | Impacto |
|---------|-----------|---------|
| **Capacidade** | ~1.000 usuários | Performance degrada após isso |
| **Busca** | Linear O(n) | Lento para muitos usuários |
| **Concorrência** | Lock de arquivo | Múltiplos writes podem falhar |
| **Backup** | Manual ou cron | Sem backup automático OLTP |
| **Auditoria** | Limitada | Sem histórico de alterações |

---

### **Logs de Acesso (access_log.csv)**

**Formato Atual:**
```csv
timestamp,username,ip_address,mac_address,device_type,success
2024-01-15 10:30:00,user123,192.168.1.100,AA:BB:CC:DD:EE:FF,mobile,true
```

**Limitações:**

| Aspecto | Limitação | Impacto |
|---------|-----------|---------|
| **Tamanho** | Cresce indefinidamente | Disco pode encher |
| **Rotação** | Manual | Requer intervenção |
| **Análise** | Ferramentas externas | Sem dashboard integrado |
| **Compressão** | Não implementada | Usa mais espaço |

**Mitigação:**

```bash
# Cron para rotação semanal
0 0 * * 0 find /var/www/wifi-portal/data -name "access_log_*.csv" -mtime +30 -delete
```

---

### **Logs Encriptados (access_log_encrypted.json)**

**❌ Limitação Atual:**
- JSON não é eficiente para grandes volumes
- Sem índices para busca rápida
- Desencriptação completa necessária para leitura

**Impacto:**
- Lento para buscar registros específicos
- Alto uso de CPU para desencriptar

**Solução Futura:**
- Encriptação a nível de coluna em banco SQL
- Usar AES-GCM com chunking

---

## 📈 Limitações de Escalabilidade

### **Concorrência de Usuários**

**Capacidade Atual:**

| Configuração | Usuários Simultâneos | Requisições/s |
|--------------|---------------------|---------------|
| **Dev (1 worker)** | ~50 | ~100 |
| **Prod (4 workers)** | ~200 | ~400 |
| **Prod (8 workers)** | ~400 | ~800 |

**Gargalos:**

1. **Gunicorn Workers:**
   - Limitado pelo número de cores da CPU
   - Fórmula: `workers = (2 × CPU) + 1`
   - Servidor de 4 cores = máximo 9 workers

2. **Redis:**
   - Single-threaded por natureza
   - ~100k ops/s em hardware comum
   - Não é gargalo na configuração atual

3. **I/O de Disco (CSV):**
   - Maior gargalo em alta concorrência
   - Locks impedem escrita paralela

**Teste de Carga:**

```bash
# Instalar Apache Bench
sudo apt install apache2-utils -y

# Testar login (100 requisições, 10 concorrentes)
ab -n 100 -c 10 -p login.txt -T "application/x-www-form-urlencoded" https://wifi.prefeitura.com.br/login

# Resultado esperado atual:
# Requests per second: ~100 [#/sec]
# Time per request: 100 [ms] (mean)
# Failed requests: 0
```

---

### **Escalabilidade Horizontal**

**❌ Limitação Atual:**
- CSV compartilhado não funciona com múltiplos containers
- Sessões Flask são in-memory (não distribuídas)

**Não Funciona:**
```yaml
# ❌ Isso NÃO vai funcionar
services:
  app:
    deploy:
      replicas: 3  # Múltiplas instâncias vão corromper CSV
```

**Solução Futura:**
- Migrar para banco de dados centralizado
- Redis para sessões distribuídas
- Load balancer com sticky sessions

---

## 🔒 Limitações de Segurança

### **Autenticação**

**Implementado:**
- ✅ PBKDF2 para hash de senhas
- ✅ Rate limiting (100 req/min)
- ✅ CSRF protection
- ✅ Session timeout

**Não Implementado:**

| Feature | Status | Prioridade |
|---------|--------|-----------|
| **2FA/MFA** | ❌ Não | Alta |
| **OAuth2/OIDC** | ❌ Não | Média |
| **Biometria** | ❌ Não | Baixa |
| **Passwordless** | ❌ Não | Média |
| **Captcha** | ❌ Não | Alta |
| **Account Lockout** | ⚠️ Parcial | Alta |

**Impacto:**
- Vulnerável a brute force sofisticado
- Sem integração com AD/LDAP corporativo

---

### **Criptografia**

**Implementado:**
- ✅ Fernet para dados sensíveis
- ✅ SSL/TLS em produção

**Limitações:**

1. **Chave Única:**
   - Uma SECRET_KEY para tudo
   - Rotação de chave requer reencriptação manual

2. **Sem HSM:**
   - Chaves armazenadas em .env
   - Não usa Hardware Security Module

3. **Algoritmo:**
   - Fernet (AES-128-CBC + HMAC)
   - Mais seguro seria AES-256-GCM

**Solução Futura:**
```python
# KMS (Key Management Service)
from aws_encryption_sdk import encrypt, decrypt
from aws_encryption_sdk.key_providers.kms import KMSMasterKeyProvider

# Rotação automática de chaves
```

---

### **GDPR / LGPD**

**Parcialmente Conforme:**

| Requisito | Status | Observação |
|-----------|--------|------------|
| **Consentimento** | ⚠️ Parcial | Aceite de termos implementado |
| **Direito ao Esquecimento** | ❌ Não | Sem funcionalidade de deletar dados |
| **Portabilidade** | ⚠️ Parcial | Pode exportar CSV manualmente |
| **Minimização de Dados** | ✅ Sim | Coleta apenas essencial |
| **Anonimização** | ❌ Não | Logs não são anonimizados |
| **Auditoria** | ⚠️ Parcial | Logs de acesso mas sem trilha completa |

**Ações Necessárias:**
1. Implementar funcionalidade de deletar conta
2. Anonimizar IPs após 90 dias
3. Relatório de dados pessoais do usuário
4. Trilha de auditoria completa

---

## 🚀 Limitações de Features

### **Dashboard Admin**

**Implementado:**
- ✅ Ver logs de acesso
- ✅ Gerenciar usuários (limitado)

**Não Implementado:**

| Feature | Status | Dificuldade |
|---------|--------|-------------|
| **Estatísticas em Tempo Real** | ❌ | Média |
| **Gráficos de Uso** | ❌ | Média |
| **Exportação de Relatórios** | ❌ | Baixa |
| **Notificações** | ❌ | Alta |
| **Gerenciamento de Dispositivos** | ❌ | Alta |
| **Blacklist/Whitelist** | ❌ | Média |
| **Configuração via UI** | ❌ | Alta |

---

### **Portal do Usuário**

**Implementado:**
- ✅ Login
- ✅ Termos de uso

**Não Implementado:**

| Feature | Status | Impacto |
|---------|--------|---------|
| **Perfil do Usuário** | ❌ | Médio |
| **Histórico de Sessões** | ❌ | Baixo |
| **Autoatendimento (Reset Senha)** | ❌ | Alto |
| **Multi-idioma** | ❌ | Médio |
| **Modo Escuro** | ❌ | Baixo |
| **PWA (App Móvel)** | ❌ | Médio |

---

### **Integrações**

**MikroTik:**
- ✅ Redirect funciona
- ⚠️ API integration limitada
- ❌ Sem gestão de bandwidth
- ❌ Sem controle de quota

**Social Login:**
- ❌ Google
- ❌ Facebook
- ❌ Microsoft

**Sistemas Externos:**
- ❌ Active Directory
- ❌ RADIUS
- ❌ LDAP

---

## 🖥️ Limitações de Infraestrutura

### **Docker Compose (Não é Kubernetes)**

**Limitações:**

| Aspecto | Docker Compose | Kubernetes |
|---------|---------------|-----------|
| **Auto-scaling** | ❌ Não | ✅ Sim |
| **Auto-healing** | ⚠️ Limitado (restart) | ✅ Sim |
| **Rolling Updates** | ❌ Não | ✅ Sim |
| **Service Discovery** | ⚠️ DNS interno | ✅ Completo |
| **Load Balancing** | ❌ Não (precisa nginx) | ✅ Sim |
| **Multi-node** | ❌ Não (single host) | ✅ Sim |

**Impacto:**
- Limitado a um único servidor
- Downtime durante deploys
- Sem failover automático

**Migração Futura:**
- Helm chart para Kubernetes
- Ver [Roadmap](#roadmap-de-melhorias)

---

### **Observabilidade**

**Implementado:**
- ✅ Logs básicos
- ✅ Health checks

**Não Implementado:**

| Feature | Status | Impacto |
|---------|--------|---------|
| **Métricas (Prometheus)** | ❌ | Alto |
| **Traces (Jaeger)** | ❌ | Médio |
| **APM (New Relic/Datadog)** | ❌ | Médio |
| **Alertas** | ❌ | Alto |
| **Dashboards (Grafana)** | ❌ | Alto |

**Workaround:**
```bash
# Verificação manual de logs
docker-compose -f docker-compose.prod.yml logs -f | grep ERROR
```

---

## 🔌 Limitações de Integração

### **API REST**

**❌ Não Existe API Pública**

Não há endpoints para:
- Criar usuários via API
- Consultar logs programaticamente
- Integrar com sistemas externos
- Webhooks

**Solução Futura:**
```python
# API REST com FastAPI
@app.get("/api/v1/users")
async def list_users(token: str = Depends(oauth2_scheme)):
    """Lista usuários (requer autenticação)."""
    pass

@app.post("/api/v1/auth")
async def authenticate(credentials: OAuth2PasswordRequestForm):
    """Autentica e retorna JWT."""
    pass
```

---

### **Webhooks**

**❌ Não Implementado**

Não há como notificar sistemas externos sobre:
- Novos logins
- Falhas de autenticação
- Sessões expiradas

**Use Case:**
```python
# Notificar sistema de billing quando usuário se conecta
def on_user_login(user_id, ip_address):
    webhook_url = "https://billing.prefeitura.com.br/webhook"
    requests.post(webhook_url, json={
        "event": "user.login",
        "user_id": user_id,
        "ip": ip_address
    })
```

---

## ⚡ Considerações de Performance

### **Benchmarks Atuais**

**Hardware de Teste:**
- CPU: 4 cores @ 2.5GHz
- RAM: 8GB
- Disco: SSD

**Resultados:**

| Endpoint | Latência (p50) | Latência (p95) | Throughput |
|----------|---------------|---------------|------------|
| `/login` | 50ms | 100ms | 200 req/s |
| `/admin` | 80ms | 150ms | 150 req/s |
| `/healthz` | 5ms | 10ms | 2000 req/s |

**Gargalos Identificados:**

1. **I/O de CSV:** ~30ms por leitura
2. **Bcrypt/PBKDF2:** ~20ms por hash
3. **Redis:** <1ms (não é gargalo)

---

### **Otimizações Aplicadas**

✅ Gzip compression no Nginx  
✅ Static file caching  
✅ Redis para rate limiting  
✅ Connection pooling  

---

### **Otimizações Pendentes**

❌ Caching de queries frequentes  
❌ CDN para assets  
❌ Lazy loading de dados  
❌ Database indexes  
❌ Query optimization  

---

## 🗺️ Roadmap de Melhorias

### **v2.0 - Banco de Dados** (Q2 2024)

**Objetivo:** Migrar de CSV para PostgreSQL

- [ ] Schema design
- [ ] Migration scripts
- [ ] ORM (SQLAlchemy)
- [ ] Testes de migração
- [ ] Documentação de migração
- [ ] Rollback plan

**Benefícios:**
- ✅ Transações ACID
- ✅ Busca rápida com índices
- ✅ Concorrência real
- ✅ Integridade referencial
- ✅ Backup confiável

---

### **v2.1 - API REST** (Q3 2024)

**Objetivo:** Criar API pública para integrações

- [ ] FastAPI endpoints
- [ ] JWT authentication
- [ ] OpenAPI documentation
- [ ] Rate limiting por API key
- [ ] SDK Python/JavaScript

**Endpoints Planejados:**

```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{id}
DELETE /api/v1/users/{id}
GET    /api/v1/logs
GET    /api/v1/stats
```

---

### **v2.2 - Dashboard Avançado** (Q4 2024)

**Objetivo:** Dashboard com estatísticas em tempo real

- [ ] Gráficos interativos (Chart.js)
- [ ] Filtros avançados
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Notificações em tempo real (WebSocket)
- [ ] Multi-idioma (i18n)

---

### **v3.0 - Kubernetes** (Q1 2025)

**Objetivo:** Suporte a alta disponibilidade

- [ ] Helm charts
- [ ] Horizontal Pod Autoscaling
- [ ] StatefulSet para Redis
- [ ] Ingress controller
- [ ] Cert-manager para SSL
- [ ] Prometheus + Grafana

**Arquitetura:**

```
                      ┌─────────────┐
                      │   Ingress   │
                      └──────┬──────┘
                             │
                ┌────────────┴────────────┐
                │                         │
         ┌──────▼──────┐           ┌─────▼──────┐
         │ Nginx (3x)  │           │ App (5x)   │
         └─────────────┘           └────────────┘
                                         │
                                   ┌─────▼──────┐
                                   │ PostgreSQL │
                                   │  (HA)      │
                                   └────────────┘
```

---

### **v3.1 - Autenticação Avançada** (Q2 2025)

- [ ] 2FA/MFA (TOTP)
- [ ] OAuth2 (Google, Microsoft)
- [ ] SAML2 (SSO corporativo)
- [ ] Passwordless (magic links)
- [ ] Biometria (WebAuthn)

---

### **v4.0 - Microserviços** (Q3 2025)

**Objetivo:** Separar em serviços independentes

```
┌─────────────────┐
│  Auth Service   │  → PostgreSQL
├─────────────────┤
│  User Service   │  → PostgreSQL
├─────────────────┤
│  Log Service    │  → TimescaleDB
├─────────────────┤
│ Analytics Svc   │  → ClickHouse
└─────────────────┘
```

---

## 🔄 Migração Futura

### **CSV → PostgreSQL**

**Estratégia de Migração:**

```bash
# 1. Exportar CSV para SQL
python scripts/migrate_csv_to_sql.py

# 2. Verificar dados
python scripts/verify_migration.py

# 3. Backup
pg_dump portal_db > backup.sql

# 4. Switch gradual (Blue-Green Deployment)
# - Manter CSV por 30 dias
# - Escrita dupla (CSV + SQL)
# - Validar consistência
# - Remover CSV

# 5. Rollback se necessário
psql portal_db < backup.sql
```

**Downtime Estimado:** < 5 minutos

---

### **Docker Compose → Kubernetes**

**Plano de Migração:**

1. **Preparação:**
   - Criar Helm charts
   - Testes em cluster de staging
   - Documentar processo

2. **Migração:**
   - Provisionar cluster K8s
   - Deploy com Helm
   - Migrar DNS
   - Validar

3. **Rollback:**
   - Reverter DNS
   - Voltar para Docker Compose

**Downtime Estimado:** < 15 minutos

---

## 📊 Comparação: Agora vs Futuro

| Aspecto | Atual (v1.0) | Futuro (v4.0) |
|---------|-------------|--------------|
| **Storage** | CSV | PostgreSQL + TimescaleDB |
| **Concorrência** | ~400 users | ~10.000+ users |
| **Autenticação** | Username/Password | 2FA + OAuth2 + SSO |
| **API** | ❌ Não | ✅ REST + GraphQL |
| **Escalabilidade** | Vertical | Horizontal (K8s) |
| **Observabilidade** | Logs básicos | Prometheus + Grafana + APM |
| **Infraestrutura** | Docker Compose | Kubernetes |
| **Deploy** | Manual | CI/CD (GitOps) |

---

## 🎯 Contribuir com Melhorias

Quer ajudar a resolver essas limitações?

1. Escolha uma issue do [Roadmap](https://github.com/seu-repo/wifi-portal/projects/1)
2. Comente na issue
3. Faça fork e crie branch
4. Implemente e teste
5. Abra Pull Request

Ver [CONTRIBUTING.md](CONTRIBUTING-NEW.md) para detalhes.

---

## ⚖️ Trade-offs Conscientes

Algumas "limitações" são decisões de design:

### **Simplicidade vs Complexidade**

**Decisão:** Manter CSV inicialmente
**Razão:** 
- Facilita deploy inicial
- Não requer DBA
- Backup simples (copiar arquivo)
- Suficiente para <5.000 usuários

### **Features vs Manutenibilidade**

**Decisão:** Monolito simples
**Razão:**
- Mais fácil de entender
- Menos overhead operacional
- Time pequeno

---

<p align="center">
  <strong>Esta é uma lista viva - será atualizada conforme o projeto evolui.</strong>
</p>
