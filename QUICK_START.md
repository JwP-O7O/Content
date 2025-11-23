# Quick Start Guide

Snelle start instructies voor het Content Creator systeem.

## Kies je Platform

### 🚀 Production (Linux VPS/Cloud) - RECOMMENDED

Voor 24/7 operation en volledige functionaliteit:

```bash
# 1. Clone project
cd /opt
git clone <repo-url> content-creator
cd content-creator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database (PostgreSQL)
sudo -u postgres createdb content_creator

# 4. Configure
cp .env.example .env
nano .env  # Add your API keys

# 5. Initialize
python init_db.py

# 6. Verify
python verify_system.py

# 7. Run!
python main.py --scheduled
```

**Full Guide**: Zie `DEPLOYMENT.md`

---

### 📱 Termux (Android) - TESTING/DEVELOPMENT

Voor testing en development op Android:

```bash
# 1. Install system packages
pkg update && pkg upgrade
pkg install python postgresql python-numpy python-scipy

# 2. Install Python packages
pip install -r requirements-termux.txt
# Of voor snelle setup:
pip install -r requirements-minimal.txt

# 3. Setup database
pg_ctl -D $PREFIX/var/lib/postgresql start
createdb content_creator

# 4. Configure
cp .env.example .env
nano .env  # Add minimum: ANTHROPIC_API_KEY and DATABASE_URL

# 5. Initialize
python init_db.py

# 6. Test run
python main.py
```

**Full Guide**: Zie `TERMUX_SETUP.md`

---

## Minimum Configuration

Voor eerste tests heb je alleen dit nodig in `.env`:

```env
# Database (SQLite voor simpelste setup)
DATABASE_URL=sqlite:///content_creator.db

# LLM (required)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Social Media (voor Phase 1 skip deze)
TWITTER_API_KEY=skip
TWITTER_API_SECRET=skip
TWITTER_ACCESS_TOKEN=skip
TWITTER_ACCESS_TOKEN_SECRET=skip
TWITTER_BEARER_TOKEN=skip
TELEGRAM_BOT_TOKEN=skip
TELEGRAM_CHANNEL_ID=skip

# Settings
HUMAN_IN_THE_LOOP=true
LOG_LEVEL=INFO
```

## Feature Levels

### Level 1: Core Testing (No External APIs)
```bash
# Requirements
pip install python-dotenv pydantic sqlalchemy anthropic

# Can test:
✅ Database models
✅ Agent initialization
✅ Base functionality
✅ Tests (pytest)
```

### Level 2: Phase 1 (Foundation)
```bash
# Additional Requirements
pip install tweepy python-telegram-bot requests

# Can run:
✅ Market scanning (with Binance API)
✅ Analysis agents
✅ Content creation (requires Twitter/Telegram APIs)
✅ Publishing (with APIs)
```

### Level 3: Phase 2 (Audience)
```bash
# Additional Requirements
pip install APScheduler aiohttp

# Can run:
✅ Engagement automation
✅ Image generation
✅ Analytics tracking
✅ Scheduler (automated operation)
```

### Level 4: Phase 3 (Monetization)
```bash
# Additional Requirements
pip install stripe discord.py

# Can run:
✅ Conversion pipeline
✅ Onboarding automation
✅ Exclusive content
✅ Community moderation
```

### Level 5: Phase 4 (Optimization)
```bash
# Additional Requirements
pip install scipy (or via pkg on Termux)

# Can run:
✅ A/B testing
✅ Strategy tuning
✅ Performance analytics
✅ Self-optimization
```

## Quick Commands

### Run Tests
```bash
pytest                    # All tests
pytest -v                 # Verbose
bash run_tests.sh        # Quick runner
```

### Verify System
```bash
python verify_system.py  # Check installation
```

### Interactive Menu
```bash
python main.py
# Choose from 20 options for different pipelines
```

### Automated Mode
```bash
python main.py --scheduled
# Choose phase (1-4)
# System runs 24/7
```

### Check Logs
```bash
tail -f logs/content_creator_*.log
grep "ERROR" logs/*.log
```

### Database
```bash
# PostgreSQL
psql content_creator

# SQLite
sqlite3 content_creator.db
```

## Troubleshooting

### Import Errors
```bash
# Check installed packages
pip list | grep -i anthropic
pip list | grep -i sqlalchemy

# Reinstall if needed
pip install --force-reinstall anthropic
```

### Database Errors
```bash
# Reset database
python init_db.py --reset

# Check connection
python -c "from src.database.connection import engine; engine.connect()"
```

### API Errors
```bash
# Test Anthropic
python -c "from anthropic import Anthropic; c=Anthropic(api_key='your_key'); print('OK')"

# Check .env
cat .env | grep API_KEY
```

## Next Steps

1. ✅ **Start Simple**: Run tests eerst
   ```bash
   pytest tests/test_database.py -v
   ```

2. ✅ **Verify Installation**
   ```bash
   python verify_system.py
   ```

3. ✅ **Test Interactive Mode**
   ```bash
   python main.py
   # Try option 1: Run Full Pipeline
   ```

4. ✅ **Check Logs**
   ```bash
   tail -f logs/content_creator_*.log
   ```

5. 🚀 **Go Production** (when ready)
   - Follow DEPLOYMENT.md
   - Setup monitoring
   - Configure alerts

## Help & Documentation

- **README.md** - Complete system overview
- **DEPLOYMENT.md** - Production deployment
- **TERMUX_SETUP.md** - Android/Termux specific
- **IMPROVEMENTS.md** - Recent improvements
- **CHANGELOG.md** - Version history
- **tests/README.md** - Testing guide

## Support

**Issues Found?**
1. Check logs: `logs/content_creator_*.log`
2. Run verify: `python verify_system.py`
3. Check config: `.env` file
4. Review docs: Above documentation files

**Common Solutions**:
- Missing dependencies → `pip install -r requirements.txt`
- Database errors → `python init_db.py --reset`
- API errors → Check `.env` keys
- Import errors → Check Python version (3.9+)

---

**Status**: Complete autonomous AI system ready to deploy! 🎉

Choose your path:
- 🧪 **Testing**: Use requirements-minimal.txt on Termux
- 🚀 **Production**: Use requirements.txt on Linux VPS
- 📚 **Learning**: Read docs and run tests

**Let's go!** 🚀
