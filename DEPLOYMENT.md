# Deployment Guide - Content Creator System

Complete deployment checklist voor het Content Creator autonomous AI agent systeem.

## Pre-Deployment Checklist

### 1. System Requirements

- [ ] Python 3.9+ geïnstalleerd
- [ ] PostgreSQL 12+ database beschikbaar
- [ ] Minimum 2GB RAM beschikbaar
- [ ] Minimum 10GB disk space
- [ ] Stable internet connectie
- [ ] Linux/Unix environment (Ubuntu 20.04+ recommended)

### 2. API Keys & Credentials

#### Required (Phase 1 - Core):
- [ ] Anthropic API key (Claude)
- [ ] Twitter/X API credentials (API key, secret, access tokens, bearer token)
- [ ] Telegram Bot token
- [ ] PostgreSQL database URL

#### Optional (Phase 2 - Audience Building):
- [ ] Binance API key (voor market data)
- [ ] Additional news API keys

#### Required voor Phase 3 (Monetization):
- [ ] Stripe API key (live mode)
- [ ] Stripe webhook secret
- [ ] Stripe price IDs (Basic, Premium, VIP)
- [ ] Discord bot token
- [ ] Discord guild (server) ID

## Installation Steps

### 1. Clone en Setup

```bash
# Clone het project
cd /opt
git clone <repository-url> content-creator
cd content-creator

# Maak virtual environment
python3 -m venv venv
source venv/bin/activate

# Installeer dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Maak PostgreSQL database
sudo -u postgres psql
CREATE DATABASE content_creator;
CREATE USER content_creator_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE content_creator TO content_creator_user;
\q

# Test database connectie
psql -h localhost -U content_creator_user -d content_creator
```

### 3. Environment Configuration

```bash
# Kopieer .env template
cp .env.example .env

# Edit .env met je credentials
nano .env
```

Minimale `.env` configuratie:

```env
# Database
DATABASE_URL=postgresql://content_creator_user:strong_password_here@localhost:5432/content_creator

# LLM
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Social Media (Phase 1)
TWITTER_API_KEY=xxxxx
TWITTER_API_SECRET=xxxxx
TWITTER_ACCESS_TOKEN=xxxxx
TWITTER_ACCESS_TOKEN_SECRET=xxxxx
TWITTER_BEARER_TOKEN=xxxxx

TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHANNEL_ID=@your_channel

# Monetization (Phase 3)
STRIPE_API_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_PRICE_ID_BASIC=price_xxxxx
STRIPE_PRICE_ID_PREMIUM=price_xxxxx
STRIPE_PRICE_ID_VIP=price_xxxxx

DISCORD_BOT_TOKEN=xxxxx
DISCORD_GUILD_ID=xxxxx

# Configuration
HUMAN_IN_THE_LOOP=false
CONTENT_PERSONALITY=hyper-analytical
CONVERSION_MIN_ENGAGEMENT_SCORE=60
LOG_LEVEL=INFO
```

### 4. Initialize Database

```bash
# Initialiseer database tabellen
python init_db.py

# Verify database schema
python verify_system.py
```

### 5. System Verification

```bash
# Run complete system verification
python verify_system.py

# Expected output: All checks should pass
# Warnings voor Phase 3 zijn OK als je alleen Phase 1-2 wilt draaien
```

## Production Deployment Options

### Option 1: Systemd Service (Recommended)

Maak een systemd service voor 24/7 operatie:

```bash
# Maak service file
sudo nano /etc/systemd/system/content-creator.service
```

Inhoud:

```ini
[Unit]
Description=Content Creator AI Agent System
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/content-creator
Environment="PATH=/opt/content-creator/venv/bin"
ExecStart=/opt/content-creator/venv/bin/python main.py --scheduled
Restart=always
RestartSec=10
StandardOutput=append:/var/log/content-creator/output.log
StandardError=append:/var/log/content-creator/error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Maak log directory
sudo mkdir -p /var/log/content-creator
sudo chown www-data:www-data /var/log/content-creator

# Enable en start service
sudo systemctl daemon-reload
sudo systemctl enable content-creator
sudo systemctl start content-creator

# Check status
sudo systemctl status content-creator

# View logs
sudo journalctl -u content-creator -f
```

### Option 2: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run
CMD ["python", "main.py", "--scheduled"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: content_creator
      POSTGRES_USER: content_creator_user
      POSTGRES_PASSWORD: strong_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  content-creator:
    build: .
    depends_on:
      - postgres
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped

volumes:
  postgres_data:
```

```bash
# Deploy met Docker
docker-compose up -d

# View logs
docker-compose logs -f content-creator
```

### Option 3: Supervisor (Alternative)

```bash
# Install supervisor
sudo apt-get install supervisor

# Maak config
sudo nano /etc/supervisor/conf.d/content-creator.conf
```

```ini
[program:content-creator]
command=/opt/content-creator/venv/bin/python main.py --scheduled
directory=/opt/content-creator
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/content-creator/error.log
stdout_logfile=/var/log/content-creator/output.log
```

```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start content-creator
```

## Monitoring & Maintenance

### 1. Log Monitoring

```bash
# Real-time logs
tail -f logs/content_creator_*.log

# Search logs
grep "ERROR" logs/*.log
grep "Pipeline Complete" logs/*.log

# Database logs
sudo -u postgres tail -f /var/log/postgresql/postgresql-15-main.log
```

### 2. Database Maintenance

```bash
# Backup database (daily recommended)
pg_dump -h localhost -U content_creator_user content_creator > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h localhost -U content_creator_user content_creator < backup_20250101.sql

# Vacuum database (weekly)
psql -h localhost -U content_creator_user -d content_creator -c "VACUUM ANALYZE;"
```

### 3. Health Checks

```bash
# Manual health check via API (add to main.py)
curl http://localhost:8000/health

# Or check via Python
python -c "
from src.orchestrator import AgentOrchestrator
import asyncio
orch = AgentOrchestrator()
health = asyncio.run(orch.get_system_health())
print(f'Health Score: {health[\"health_score\"]}/100')
"
```

### 4. Performance Monitoring

Monitor deze metrics:
- CPU usage (should be < 50% average)
- Memory usage (should be < 1.5GB)
- Database size
- API rate limit usage
- Error rates in logs

```bash
# CPU/Memory monitoring
top -p $(pgrep -f "python main.py")

# Database size
psql -U content_creator_user -d content_creator -c "
SELECT pg_size_pretty(pg_database_size('content_creator'));
"

# Disk space
df -h
```

## Scaling & Optimization

### For High Volume (1000+ posts/day):

1. **Database Optimization**:
```sql
-- Add indexes voor performance
CREATE INDEX idx_published_content_date ON published_content(published_at);
CREATE INDEX idx_insights_confidence ON insights(confidence);
CREATE INDEX idx_user_interactions_user ON user_interactions(user_id);
CREATE INDEX idx_ab_tests_status ON ab_tests(status);
```

2. **Multiple Workers**:
Draai meerdere instances voor verschillende fasen:
- Instance 1: Phase 1-2 (content creation)
- Instance 2: Phase 3 (monetization)
- Instance 3: Phase 4 (optimization)

3. **Caching Layer**:
Add Redis voor caching van API responses en metrics.

4. **Queue System**:
Implement Celery voor async task processing.

## Security Hardening

### 1. Environment Security

```bash
# Secure .env file
chmod 600 .env
chown www-data:www-data .env

# Secure database credentials
sudo -u postgres psql -c "ALTER USER content_creator_user WITH PASSWORD 'new_strong_password';"
```

### 2. API Rate Limiting

Check API usage regularly:
- Anthropic: Monitor token usage
- Twitter: Max 300 requests per 15 min
- Stripe: Follow webhook best practices

### 3. Database Security

```sql
-- Restrict database access
REVOKE ALL ON DATABASE content_creator FROM PUBLIC;
GRANT CONNECT ON DATABASE content_creator TO content_creator_user;

-- Enable SSL for remote connections
-- In postgresql.conf:
-- ssl = on
-- ssl_cert_file = '/path/to/server.crt'
-- ssl_key_file = '/path/to/server.key'
```

## Troubleshooting

### Common Issues:

**1. Database Connection Errors**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -h localhost -U content_creator_user -d content_creator

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

**2. API Rate Limit Errors**
```bash
# Check current rate limits in scheduler
# Reduce frequencies in src/scheduler.py if needed

# For Twitter, increase intervals:
# market_scan: every 30min → 60min
# engagement: every 1h → 2h
```

**3. High Memory Usage**
```bash
# Check memory
free -h

# Restart service
sudo systemctl restart content-creator

# Consider reducing concurrent operations in orchestrator
```

**4. Logs Growing Too Large**
```bash
# Setup log rotation
sudo nano /etc/logrotate.d/content-creator
```

```
/var/log/content-creator/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload content-creator > /dev/null 2>&1 || true
    endscript
}
```

## Phase-by-Phase Deployment

Je kunt het systeem gefaseerd deployen:

### Start with Phase 1 (Foundation):
```bash
# In .env:
# Comment out Phase 3 credentials

# Run scheduler with Phase 1
python main.py --scheduled
# Choose option: 1
```

### Add Phase 2 (Audience Building):
```bash
# No new credentials needed
# Run scheduler with Phase 2
python main.py --scheduled
# Choose option: 2
```

### Add Phase 3 (Monetization):
```bash
# Add Stripe & Discord credentials to .env
# Run scheduler with Phase 3
python main.py --scheduled
# Choose option: 3
```

### Add Phase 4 (Self-Optimization):
```bash
# No new credentials needed
# System automatically optimizes!
python main.py --scheduled
# Choose option: 4
```

## Backup Strategy

### Automated Backups:

```bash
# Maak backup script
nano /opt/content-creator/scripts/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/content-creator"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U content_creator_user content_creator > "$BACKUP_DIR/db_$DATE.sql"

# Config backup
cp /opt/content-creator/.env "$BACKUP_DIR/env_$DATE"

# Logs backup
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" /opt/content-creator/logs/

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
chmod +x /opt/content-creator/scripts/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /opt/content-creator/scripts/backup.sh >> /var/log/content-creator/backup.log 2>&1
```

## Post-Deployment Verification

After deployment, verify:

1. **System is running**:
```bash
sudo systemctl status content-creator
```

2. **Content is being generated**:
```bash
# Check recent content in database
psql -U content_creator_user -d content_creator -c "
SELECT COUNT(*) FROM published_content WHERE published_at > NOW() - INTERVAL '24 hours';
"
```

3. **No errors in logs**:
```bash
grep -i "error" logs/content_creator_$(date +%Y-%m-%d).log | tail -20
```

4. **Health score is good**:
```python
# Via interactive menu option 16
# Or via Python script
```

5. **All agents are running**:
```bash
# Check agent_logs table
psql -U content_creator_user -d content_creator -c "
SELECT agent_name, COUNT(*) as runs, MAX(timestamp) as last_run
FROM agent_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY agent_name
ORDER BY last_run DESC;
"
```

## Support & Monitoring URLs

Setup monitoring endpoints (optional):
- Health check: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`
- Status dashboard: `http://localhost:8000/dashboard`

## Rollback Procedure

If deployment fails:

```bash
# Stop service
sudo systemctl stop content-creator

# Restore database from backup
psql -U content_creator_user -d content_creator < /opt/backups/content-creator/db_YYYYMMDD.sql

# Restore config
cp /opt/backups/content-creator/env_YYYYMMDD /opt/content-creator/.env

# Restart with previous version
git checkout <previous-commit>
sudo systemctl start content-creator
```

---

**Deployment Complete!**

Het systeem draait nu 24/7 en optimaliseert zichzelf automatisch via Phase 4 feedback loops.

Monitor de eerste 48 uur extra goed en check:
- Logs voor errors
- System health score
- Content quality
- API usage
- Database performance
