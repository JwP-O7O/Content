# Performance Optimization Guide

Gids voor het optimaliseren van de performance van het Content Creator systeem.

## Inhoudsopgave

- [Performance Baselines](#performance-baselines)
- [Database Optimization](#database-optimization)
- [API Optimization](#api-optimization)
- [Memory Optimization](#memory-optimization)
- [Caching Strategies](#caching-strategies)
- [Async Optimization](#async-optimization)
- [Monitoring & Profiling](#monitoring--profiling)
- [Scaling Strategies](#scaling-strategies)

## Performance Baselines

### Current Performance Metrics

Based op testing met mock data:

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Agent execution time | 2-5s | <3s | ⚠️ |
| Database query time | 50-200ms | <100ms | ⚠️ |
| API call time | 500-2000ms | <1000ms | ⚠️ |
| Memory usage | 200-400MB | <300MB | ⚠️ |
| Content generation | 10-15s | <10s | ⚠️ |

### Performance Goals

**Short-term (1 month)**:
- [ ] Reduce avg agent execution to <3s
- [ ] Optimize database queries to <100ms
- [ ] Implement caching layer (Redis)
- [ ] Reduce memory footprint to <300MB

**Long-term (3 months)**:
- [ ] Handle 1000+ content items/day
- [ ] Support 10K+ active users
- [ ] 99.9% uptime
- [ ] <500ms API response times

## Database Optimization

### 1. Index Optimization

**Current Indexes** (zie `src/database/models.py`):
- ✅ `published_content.created_at`
- ✅ `insights.created_at`
- ✅ `user_interactions.user_id`

**Add These Indexes**:

```python
# In src/database/models.py

# Voor frequent queries
Index('idx_content_status_date', 'status', 'created_at')
Index('idx_user_engagement', 'user_id', 'created_at')
Index('idx_insights_confidence', 'confidence', 'created_at')
Index('idx_abtest_status', 'test_id', 'status')
```

**Implementation**:
```bash
# Create migration
alembic revision --autogenerate -m "Add performance indexes"

# Apply migration
alembic upgrade head
```

### 2. Query Optimization

**Problem**: N+1 queries in agent loops

**Solution**: Use eager loading

```python
# Before (N+1 problem)
insights = db.query(Insight).filter(...).all()
for insight in insights:
    content = insight.content_plans  # Extra query per insight!

# After (eager loading)
from sqlalchemy.orm import joinedload

insights = db.query(Insight)\
    .options(joinedload(Insight.content_plans))\
    .filter(...)\
    .all()
```

**Apply to these areas**:
- [ ] `ContentStrategistAgent` - insight → content_plan relationships
- [ ] `ConversionAgent` - user → interactions relationships
- [ ] `PerformanceAnalyticsAgent` - content → metrics relationships

### 3. Connection Pooling

**Current**: Default SQLAlchemy settings
**Target**: Optimized pool voor production

```python
# In src/database/connection.py

from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # Connections in pool
    max_overflow=20,        # Extra connections when needed
    pool_pre_ping=True,     # Verify connections before use
    pool_recycle=3600,      # Recycle connections every hour
    echo=False              # Disable SQL logging in production
)
```

### 4. Database Maintenance

**Weekly Tasks**:
```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Reindex for fragmentation
REINDEX DATABASE contentcreator;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Automated via cron**:
```bash
# Add to crontab
0 2 * * 0 /path/to/scripts/db_maintenance.sh
```

## API Optimization

### 1. Rate Limit Management

**Current**: Sequential API calls
**Problem**: Slow when hitting multiple APIs

**Solution**: Batch requests met async

```python
# Before
market_data = exchange_api.get_ticker("BTC/USDT")
news = news_api.get_latest()
sentiment = twitter_api.get_sentiment()

# After (parallel)
async def fetch_all_data():
    market_task = asyncio.create_task(exchange_api.get_ticker_async("BTC/USDT"))
    news_task = asyncio.create_task(news_api.get_latest_async())
    sentiment_task = asyncio.create_task(twitter_api.get_sentiment_async())
    
    return await asyncio.gather(market_task, news_task, sentiment_task)

market_data, news, sentiment = await fetch_all_data()
```

### 2. Request Retry Strategy

**Exponential backoff voor API failures**:

```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
async def fetch_with_retry(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 3. Response Compression

**Enable gzip for API responses**:

```python
# In API integration files
headers = {
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': 'ContentCreator/1.0'
}
```

## Memory Optimization

### 1. Memory Profiling

**Install memory profiler**:
```bash
pip install memory-profiler
```

**Profile specific functions**:
```python
from memory_profiler import profile

@profile
def expensive_function():
    # Your code here
    pass
```

**Run profiling**:
```bash
python -m memory_profiler src/agents/analysis_agent.py
```

### 2. Generator Usage

**Problem**: Loading large datasets into memory

**Solution**: Use generators

```python
# Before (loads all into memory)
def get_all_insights(db):
    return db.query(Insight).all()

# After (yields one at a time)
def get_all_insights(db):
    for insight in db.query(Insight).yield_per(100):
        yield insight
```

### 3. Context Managers

**Ensure resources are freed**:

```python
# Database sessions
with get_db() as db:
    # Use db
    pass
# Auto-closed here

# Files
with open('file.txt', 'r') as f:
    data = f.read()
# Auto-closed here
```

### 4. Memory Limits

**Set limits in Docker**:

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

## Caching Strategies

### 1. Redis Integration

**Install Redis**:
```bash
docker-compose up redis  # If using docker-compose
```

**Add to requirements.txt**:
```
redis==5.0.0
aioredis==2.0.1
```

**Implementation**:

```python
# src/utils/cache.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def cache(expiry=3600):
    """Cache decorator with expiry in seconds"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(
                cache_key,
                expiry,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator
```

**Usage**:
```python
@cache(expiry=300)  # 5 minutes
async def get_market_data(symbol):
    # Expensive API call
    return await exchange_api.get_ticker(symbol)
```

### 2. Cache Warming

**Pre-populate common queries**:

```python
async def warm_cache():
    """Run at startup to pre-populate cache"""
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    
    tasks = [get_market_data(symbol) for symbol in symbols]
    await asyncio.gather(*tasks)
```

### 3. Cache Invalidation

**Invalidate on updates**:

```python
def invalidate_cache(pattern):
    """Clear cache keys matching pattern"""
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)

# After publishing content
invalidate_cache("get_published_content:*")
```

## Async Optimization

### 1. Async Everywhere

**Convert blocking operations**:

```python
# Before (blocking)
def fetch_news():
    response = requests.get(url)  # Blocks!
    return response.json()

# After (async)
async def fetch_news():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 2. Concurrent Agent Execution

**Run independent agents in parallel**:

```python
async def run_phase1_parallel():
    """Run Phase 1 agents concurrently"""
    scanner_task = asyncio.create_task(market_scanner.run())
    news_task = asyncio.create_task(news_scanner.run())
    
    results = await asyncio.gather(
        scanner_task,
        news_task,
        return_exceptions=True
    )
    
    return results
```

### 3. Semaphore for Rate Limiting

**Control concurrent API calls**:

```python
# Limit to 5 concurrent API calls
semaphore = asyncio.Semaphore(5)

async def rate_limited_api_call(url):
    async with semaphore:
        return await fetch_url(url)
```

## Monitoring & Profiling

### 1. Application Profiling

**cProfile voor CPU profiling**:

```bash
python -m cProfile -o profile.stats main.py

# Analyze results
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

### 2. Performance Metrics Collection

**Track key metrics**:

```python
# src/utils/metrics_collector.py (enhance existing)

import time
from functools import wraps

def track_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            
            # Log performance
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            
            # Store metric
            metrics_collector.record_execution_time(
                func.__name__,
                duration
            )
            
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    
    return wrapper
```

### 3. Real-time Monitoring

**Prometheus metrics** (optional):

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
api_calls = Counter('api_calls_total', 'Total API calls', ['endpoint'])
response_time = Histogram('response_time_seconds', 'Response time')

# Use in code
@response_time.time()
async def fetch_data():
    api_calls.labels(endpoint='twitter').inc()
    # ... fetch logic
```

## Scaling Strategies

### 1. Horizontal Scaling

**Multiple agent instances**:

```yaml
# docker-compose.yml
services:
  agent_worker_1:
    build: .
    environment:
      - WORKER_ID=1
  
  agent_worker_2:
    build: .
    environment:
      - WORKER_ID=2
```

**Task queue (Celery)**:

```python
from celery import Celery

app = Celery('contentcreator')

@app.task
def process_insight(insight_id):
    # Process in background
    pass

# Enqueue task
process_insight.delay(123)
```

### 2. Vertical Scaling

**Resource allocation**:

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### 3. Load Balancing

**Nginx reverse proxy**:

```nginx
upstream contentcreator {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    location / {
        proxy_pass http://contentcreator;
    }
}
```

## Quick Wins Checklist

Eenvoudige optimalisaties met grote impact:

- [ ] Add database indexes voor frequent queries
- [ ] Implement connection pooling
- [ ] Add Redis caching voor API calls
- [ ] Convert blocking I/O to async
- [ ] Enable query result caching
- [ ] Add response compression
- [ ] Implement retry logic met exponential backoff
- [ ] Use generators voor large datasets
- [ ] Profile and optimize top 5 slowest functions
- [ ] Set proper resource limits in Docker

## Performance Testing

**Load testing met Locust**:

```python
# locustfile.py
from locust import HttpUser, task, between

class ContentCreatorUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_insights(self):
        self.client.get("/api/insights")
    
    @task(3)  # 3x more frequent
    def get_content(self):
        self.client.get("/api/content")
```

**Run load test**:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

## Resources

- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Python Async Best Practices](https://docs.python.org/3/library/asyncio.html)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/faq/performance.html)

---

**Last Updated**: 2025-12-16
**Version**: 1.0
**Performance Target**: <3s agent execution, <100ms DB queries, <1s API calls
