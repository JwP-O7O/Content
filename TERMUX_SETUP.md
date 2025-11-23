# Termux Setup Guide

Special setup instructions voor Content Creator op Termux (Android).

## Waarom dit nodig is

Termux draait op Android en heeft speciale handling nodig voor packages met native code zoals numpy, scipy, en pandas. Deze kunnen niet via pip gecompileerd worden op Android, maar zijn wel beschikbaar als pre-compiled Termux packages.

## Setup Steps

### 1. Update Termux

```bash
pkg update && pkg upgrade -y
```

### 2. Install System Dependencies

```bash
# Install Python en essentiële tools
pkg install -y python python-pip git postgresql

# Install pre-compiled scientific packages
pkg install -y python-numpy python-scipy

# Install build tools (optioneel, voor andere packages)
pkg install -y clang make cmake
```

### 3. Install Python Dependencies

**Gebruik de Termux-specific requirements file:**

```bash
# Navigate naar project directory
cd ~/projects/content-creator

# Install dependencies (zonder pandas/numpy/scipy)
pip install -r requirements-termux.txt
```

**Belangrijke Note**:
- `numpy` en `scipy` zijn al geïnstalleerd via `pkg`
- `pandas` werkt momenteel niet goed op Termux - we gebruiken het niet in core functionaliteit

### 4. Database Setup

```bash
# Start PostgreSQL
pg_ctl -D $PREFIX/var/lib/postgresql start

# Create database
createdb content_creator

# Create user
psql -c "CREATE USER content_creator_user WITH PASSWORD 'your_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE content_creator TO content_creator_user;"
```

### 5. Configure Environment

```bash
# Copy .env template
cp .env.example .env

# Edit with nano or vi
nano .env
```

**Minimum .env voor testing:**

```env
DATABASE_URL=postgresql://content_creator_user:your_password@localhost:5432/content_creator
ANTHROPIC_API_KEY=your_key_here
TWITTER_API_KEY=skip_for_now
TWITTER_API_SECRET=skip_for_now
TWITTER_ACCESS_TOKEN=skip_for_now
TWITTER_ACCESS_TOKEN_SECRET=skip_for_now
TWITTER_BEARER_TOKEN=skip_for_now
TELEGRAM_BOT_TOKEN=skip_for_now
TELEGRAM_CHANNEL_ID=skip_for_now
HUMAN_IN_THE_LOOP=true
LOG_LEVEL=INFO
```

### 6. Initialize Database

```bash
python init_db.py
```

### 7. Verify Installation

```bash
python verify_system.py
```

## Known Issues & Solutions

### Issue: pandas import errors

**Solution**: De core agents gebruiken pandas niet voor kritieke functionaliteit. Als je `ImportError: cannot import pandas` ziet, is dit meestal in:
- PerformanceAnalyticsAgent (gebruikt alleen numpy voor berekeningen)
- AnalyticsAgent (kan zonder pandas werken)

**Workaround**: Commentaar uit de pandas imports of gebruik alleen de agents die geen pandas nodig hebben.

### Issue: asyncio errors

**Solution**: Termux Python 3.12+ heeft soms issues met asyncio. Als je errors ziet:

```bash
# Downgrade naar Python 3.11 als beschikbaar
pkg install python-3.11
```

### Issue: PostgreSQL niet start

**Solution**:

```bash
# Initialize database cluster eerst
initdb -D $PREFIX/var/lib/postgresql

# Dan start
pg_ctl -D $PREFIX/var/lib/postgresql start

# Auto-start bij Termux startup (optioneel)
echo "pg_ctl -D $PREFIX/var/lib/postgresql start" >> ~/.bashrc
```

### Issue: Disk space problemen

**Solution**:

```bash
# Check disk space
df -h

# Clean pip cache
pip cache purge

# Clean package cache
apt clean
```

## Tested Phases on Termux

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 | ✅ Works | Core pipeline functional |
| Phase 2 | ✅ Works | Engagement & analytics work |
| Phase 3 | ⚠️ Partial | Discord.py kan issues hebben |
| Phase 4 | ✅ Works | A/B testing en optimization werken |

## Running on Termux

### Interactive Mode

```bash
python main.py
```

### Background Mode (recommended)

```bash
# Install termux-services
pkg install termux-services

# Start in background met nohup
nohup python main.py --scheduled > output.log 2>&1 &

# Check if running
ps aux | grep python

# Kill process
pkill -f "python main.py"
```

### Keep Termux Running

Termux sluit apps in background af om battery te sparen. Om 24/7 te draaien:

1. **Enable Termux:Boot** (separate app from F-Droid)
2. **Disable battery optimization** voor Termux in Android settings
3. **Use Termux:Widget** om scripts te starten

## Performance Tips

1. **Reduce Scheduler Frequencies**:
   - Edit `src/scheduler.py`
   - Verhoog intervals (bijv. market scan 30min → 2 hours)
   - Dit bespaart battery en data

2. **Use SQLite instead of PostgreSQL** (lighter):
   ```env
   DATABASE_URL=sqlite:///content_creator.db
   ```

3. **Disable Heavy Agents**:
   - Comment out image generation in scheduler
   - Reduce engagement frequency

## Testing on Termux

```bash
# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_database.py -v

# Skip slow tests
pytest -m "not slow"
```

## Troubleshooting Commands

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check numpy/scipy from pkg
python -c "import numpy; print(numpy.__version__)"
python -c "import scipy; print(scipy.__version__)"

# Check PostgreSQL status
pg_ctl -D $PREFIX/var/lib/postgresql status

# View logs
tail -f logs/content_creator_*.log
```

## Alternative: Docker on Termux

Je kunt ook Docker gebruiken op Termux (requires root):

```bash
# Install Docker (requires proot-distro)
pkg install proot-distro
proot-distro install ubuntu

# Run ubuntu
proot-distro login ubuntu

# Inside ubuntu:
apt update && apt install docker.io
# Then follow normal Docker deployment
```

## Recommended Workflow

Voor development op Termux:

1. ✅ **Use Termux voor testing**
   - Test agents individually
   - Verify database schema
   - Test API integrations

2. ✅ **Deploy to VPS/Cloud voor production**
   - Use a proper Linux VPS
   - Better performance
   - 24/7 reliability
   - Full package support

## Resources

- [Termux Wiki](https://wiki.termux.com/)
- [Termux Scientific Packages](https://wiki.termux.com/wiki/Python)
- [PostgreSQL on Termux](https://wiki.termux.com/wiki/Postgresql)

---

**Note**: Termux is geweldig voor testing en development, maar voor production 24/7 operation wordt een Linux VPS/cloud server aanbevolen (zie DEPLOYMENT.md).

## Current Status

✅ **What Works**:
- Core agents (Phase 1)
- Database operations
- LLM API calls (Anthropic)
- Basic scheduling
- A/B testing
- Performance analytics

⚠️ **What Needs Attention**:
- Some Discord features (voice/audio)
- Heavy concurrent operations
- Long-running tasks (battery drain)

🚀 **Ready to Start**: Ja! Zelfs met beperkingen is Termux perfect voor development en testing.
