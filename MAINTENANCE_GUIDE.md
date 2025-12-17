# System Maintenance Guide

Complete gids voor het onderhoud van het Content Creator systeem.

## Inhoudsopgave

- [Daily Maintenance](#daily-maintenance)
- [Weekly Maintenance](#weekly-maintenance)
- [Monthly Maintenance](#monthly-maintenance)
- [Quarterly Maintenance](#quarterly-maintenance)
- [Emergency Procedures](#emergency-procedures)
- [Health Checks](#health-checks)
- [Backup & Recovery](#backup--recovery)
- [Monitoring Alerts](#monitoring-alerts)

## Daily Maintenance

### Morning Checks (5-10 minuten)

**1. System Health Check**
```bash
# Check if all services zijn running
docker-compose ps

# Check application logs voor errors
docker-compose logs --tail=100 app | grep -i error

# Check recent agent activity
docker-compose exec app python -c "
from src.database.connection import get_db
from src.database.models import AgentLog
from datetime import datetime, timedelta, timezone

with get_db() as db:
    recent = db.query(AgentLog)\
        .filter(AgentLog.timestamp > datetime.now(tz=timezone.utc) - timedelta(hours=24))\
        .count()
    print(f'Agent executions last 24h: {recent}')
"
```

**2. Content Review**
```bash
# Check published content from yesterday
docker-compose exec app python -c "
from src.database.connection import get_db
from src.database.models import PublishedContent
from datetime import datetime, timedelta, timezone

with get_db() as db:
    yesterday = db.query(PublishedContent)\
        .filter(PublishedContent.created_at > datetime.now(tz=timezone.utc) - timedelta(days=1))\
        .count()
    print(f'Content published yesterday: {yesterday}')
"
```

**3. API Rate Limit Check**
```bash
# Check remaining API calls
# (Implementation varies per API)
# Twitter: Check via API headers
# Anthropic: Check dashboard
# Stripe: Check dashboard
```

**4. Error Log Review**
```bash
# Check for any critical errors
docker-compose logs --tail=1000 app | grep -i "critical\|fatal\|exception"

# Count errors per hour
docker-compose logs --since=24h app | grep -i error | wc -l
```

### Evening Checks (5 minuten)

**1. Verify Daily Backup**
```bash
# Check if backup ran successfully
ls -lh /path/to/backups/contentcreator_$(date +%Y%m%d)*.sql

# Verify backup size (should be >1MB)
```

**2. Review Engagement Metrics**
```bash
docker-compose exec app python -c "
from src.utils.metrics_collector import MetricsCollector

mc = MetricsCollector()
metrics = mc.get_daily_summary()
print(f'Tweets: {metrics.get(\"tweets\", 0)}')
print(f'Engagement: {metrics.get(\"engagement\", 0)}')
print(f'New subscribers: {metrics.get(\"subscribers\", 0)}')
"
```

**3. Check Disk Space**
```bash
# Check available disk space
df -h | grep -E "/$|/var|/data"

# Alert if <20% free
```

## Weekly Maintenance

### Sunday Morning Routine (30-45 minuten)

**1. Full System Health Audit**

```bash
#!/bin/bash
# weekly_health_check.sh

echo "=== Weekly System Health Check ==="
echo "Date: $(date)"

# Check uptime
echo -e "\n1. System Uptime:"
uptime

# Check memory usage
echo -e "\n2. Memory Usage:"
free -h

# Check disk usage
echo -e "\n3. Disk Usage:"
df -h

# Check Docker containers
echo -e "\n4. Docker Containers:"
docker-compose ps

# Check database size
echo -e "\n5. Database Size:"
docker-compose exec db psql -U contentcreator -c "\l+"

# Check largest tables
echo -e "\n6. Largest Tables:"
docker-compose exec db psql -U contentcreator -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;"

# Check error count
echo -e "\n7. Errors Last Week:"
docker-compose logs --since=168h app | grep -i error | wc -l

# Check API health
echo -e "\n8. API Health:"
curl -s http://localhost:8000/health || echo "Health endpoint not available"
```

**2. Database Maintenance**

```bash
# Connect to database
docker-compose exec db psql -U contentcreator

-- Run these commands
VACUUM ANALYZE;
REINDEX DATABASE contentcreator;

-- Check for bloat
SELECT 
    schemaname, 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                   pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

**3. Performance Review**

```bash
# Analyze slow queries
docker-compose exec db psql -U contentcreator -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"

# Check agent performance
python scripts/analyze_agent_performance.py --last-week
```

**4. Content Analytics**

```bash
# Generate weekly report
python scripts/weekly_report.py

# Review:
# - Total content published
# - Average engagement rate
# - Top performing content
# - Conversion metrics
# - A/B test results
```

**5. Security Checks**

```bash
# Check for failed login attempts (if applicable)
docker-compose logs app | grep -i "failed\|unauthorized"

# Check SSL certificate expiry
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com 2>/dev/null | openssl x509 -noout -dates

# Check for outdated packages
pip list --outdated
```

## Monthly Maintenance

### First Sunday of Month (1-2 uur)

**1. Full Backup Verification**

```bash
# Test backup restore to separate database
createdb contentcreator_test
pg_restore -d contentcreator_test /path/to/backup.sql

# Verify data integrity
psql contentcreator_test -c "SELECT COUNT(*) FROM published_content;"

# Delete test database
dropdb contentcreator_test
```

**2. Dependency Updates**

```bash
# Check for security updates
pip-audit

# Update dependencies
pip list --outdated > outdated_packages.txt

# Review and update one by one
pip install --upgrade <package>

# Run full test suite
pytest tests/

# If tests pass, update requirements.txt
pip freeze > requirements.txt
```

**3. Database Optimization**

```bash
# Analyze query patterns
docker-compose exec db psql -U contentcreator -c "
SELECT 
    queryid,
    query,
    calls,
    total_time/1000 as total_seconds,
    mean_time/1000 as mean_seconds,
    rows
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_time DESC
LIMIT 20;"

# Add indexes if needed
# See PERFORMANCE_GUIDE.md
```

**4. Log Rotation & Cleanup**

```bash
# Clean old logs (keep last 90 days)
find /var/log/contentcreator -name "*.log" -mtime +90 -delete

# Clean old backups (keep last 60 days)
find /backups -name "*.sql" -mtime +60 -delete

# Clean Docker logs
docker system prune -a --volumes --filter "until=720h"
```

**5. Cost Analysis**

```bash
# Calculate monthly costs
python scripts/cost_analysis.py

# Review:
# - API usage costs (Anthropic, Twitter, etc.)
# - Infrastructure costs (server, database)
# - Total cost per content piece
# - ROI analysis
```

**6. Content Strategy Review**

- Review A/B test results
- Analyze content performance trends
- Update content personality if needed
- Review and adjust posting schedule
- Analyze competitor content
- Plan next month's content themes

## Quarterly Maintenance

### First Week of Quarter (Half day)

**1. Full System Audit**

- Review all agents' performance
- Analyze system bottlenecks
- Check for technical debt
- Review architecture decisions
- Plan major improvements

**2. Security Audit**

```bash
# Run security scanner
bandit -r src/ -ll

# Check dependencies for vulnerabilities
pip-audit

# Review access logs
# Check API key rotation schedule
# Review user permissions
```

**3. Disaster Recovery Test**

```bash
# Full disaster recovery simulation
# 1. Stop all services
docker-compose down

# 2. Restore from backup
# 3. Verify all data intact
# 4. Test all functionality
# 5. Document time to recover
```

**4. Performance Benchmarking**

```bash
# Run performance tests
pytest tests/test_performance.py --benchmark-only

# Compare to previous quarter
# Identify performance degradations
# Plan optimizations
```

**5. Capacity Planning**

- Analyze growth trends
- Project infrastructure needs
- Plan scaling strategy
- Budget for next quarter

## Emergency Procedures

### System Down

```bash
# 1. Check service status
docker-compose ps

# 2. Check logs
docker-compose logs --tail=100

# 3. Restart services
docker-compose restart

# 4. If still down, full reset
docker-compose down
docker-compose up -d

# 5. Verify database connection
docker-compose exec app python -c "from src.database.connection import get_db; get_db()"
```

### Database Corruption

```bash
# 1. Stop application
docker-compose stop app

# 2. Create backup of current state
pg_dump -U contentcreator > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Attempt repair
docker-compose exec db psql -U contentcreator -c "REINDEX DATABASE contentcreator;"

# 4. If repair fails, restore from latest backup
# 5. Verify data integrity
# 6. Resume operations
```

### API Rate Limit Exceeded

```bash
# 1. Check which API is rate limited
docker-compose logs app | grep -i "rate limit"

# 2. Pause relevant agent
# Edit .env: ENABLE_MARKET_SCANNER=false

# 3. Wait for rate limit reset
# 4. Re-enable agent gradually
```

### Out of Disk Space

```bash
# 1. Free immediate space
docker system prune -a --volumes

# 2. Remove old backups
find /backups -name "*.sql" -mtime +30 -delete

# 3. Clear logs
truncate -s 0 /var/log/contentcreator/*.log

# 4. Add monitoring alert for disk space
```

## Health Checks

### Automated Health Check Script

```python
#!/usr/bin/env python3
# scripts/health_check.py

import sys
from datetime import datetime, timedelta, timezone
from src.database.connection import get_db
from src.database.models import AgentLog, PublishedContent

def health_check():
    """Comprehensive health check"""
    issues = []
    
    with get_db() as db:
        # Check recent agent activity
        last_24h = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        recent_logs = db.query(AgentLog)\
            .filter(AgentLog.timestamp > last_24h)\
            .count()
        
        if recent_logs == 0:
            issues.append("No agent activity in last 24 hours")
        
        # Check content publishing
        recent_content = db.query(PublishedContent)\
            .filter(PublishedContent.created_at > last_24h)\
            .count()
        
        if recent_content == 0:
            issues.append("No content published in last 24 hours")
        
        # Check errors
        error_logs = db.query(AgentLog)\
            .filter(AgentLog.timestamp > last_24h)\
            .filter(AgentLog.status == 'error')\
            .count()
        
        if error_logs > 10:
            issues.append(f"High error count: {error_logs} in last 24h")
    
    # Return status
    if issues:
        print("UNHEALTHY:", "; ".join(issues))
        return 1
    else:
        print("HEALTHY")
        return 0

if __name__ == "__main__":
    sys.exit(health_check())
```

**Run via cron**:
```bash
# Every hour
0 * * * * /path/to/health_check.py || /path/to/alert.sh
```

## Backup & Recovery

### Automated Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/contentcreator_$DATE.sql"

# Create backup
docker-compose exec -T db pg_dump -U contentcreator > "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Verify backup
if [ -f "$BACKUP_FILE.gz" ]; then
    echo "Backup successful: $BACKUP_FILE.gz"
    
    # Upload to S3 (optional)
    # aws s3 cp "$BACKUP_FILE.gz" s3://my-backups/contentcreator/
    
    # Clean old backups (keep last 30 days)
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
else
    echo "Backup failed!" >&2
    exit 1
fi
```

**Schedule via cron**:
```bash
# Daily at 2 AM
0 2 * * * /path/to/backup.sh
```

### Recovery Procedure

```bash
# 1. Stop application
docker-compose stop app

# 2. Restore database
gunzip -c /backups/contentcreator_YYYYMMDD_HHMMSS.sql.gz | \
    docker-compose exec -T db psql -U contentcreator

# 3. Verify restoration
docker-compose exec db psql -U contentcreator -c "SELECT COUNT(*) FROM published_content;"

# 4. Restart application
docker-compose start app

# 5. Verify system health
python scripts/health_check.py
```

## Monitoring Alerts

### Critical Alerts (Immediate Action)

- System down
- Database connection failed
- Disk space <10%
- Memory usage >90%
- Error rate >10/hour

### Warning Alerts (Check within 1 hour)

- Disk space <20%
- Memory usage >80%
- Error rate >5/hour
- No content published in 6 hours
- API rate limit approaching

### Info Alerts (Check within 24 hours)

- High engagement content detected
- A/B test results significant
- New subscriber milestone reached

## Maintenance Schedule Summary

| Frequency | Duration | Tasks |
|-----------|----------|-------|
| Daily | 15 min | Health checks, content review, logs |
| Weekly | 45 min | DB maintenance, performance review, security |
| Monthly | 2 hours | Full backup test, updates, optimization |
| Quarterly | 4 hours | Full audit, DR test, planning |

## Resources

- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) - Initial deployment
- [PERFORMANCE_GUIDE.md](./PERFORMANCE_GUIDE.md) - Optimization tips
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Development guide

---

**Last Updated**: 2025-12-16
**Version**: 1.0
**Maintained By**: Operations Team
