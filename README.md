# Content Creator - Autonomous AI Agent System

Een volledig autonoom systeem van AI-agents dat crypto-marktanalyses genereert, een community opbouwt op sociale media, deze converteert naar een betaalde, exclusieve community, en zichzelf continu optimaliseert.

## Overzicht

Dit systeem implementeert **alle 4 fasen** van de roadmap: van basis content creatie tot volledig zelflerende optimalisatie.

### Agents Geïmplementeerd

#### Fase 1 - Core Agents (Foundation):

1. **MarketScannerAgent** - Scant continu de markt voor data
   - Prijs- en volume data van belangrijke assets (Binance API)
   - Nieuwsartikelen (RSS feeds)
   - Social media sentiment (Twitter API)

2. **AnalysisAgent** - Analyseert data en genereert inzichten
   - Technische analyse (breakouts, volume spikes, etc.)
   - News impact analyse
   - Sentiment analyse
   - LLM-powered analyses (Claude)

3. **ContentStrategistAgent** - Plant content strategie
   - Bepaalt welke inzichten gepubliceerd moeten worden
   - Kiest het beste format (tweet, thread, etc.)
   - Scheidt free vs exclusive content
   - Optimaliseert posting tijden
   - Content repurposing (high-performing content hergebruiken)

4. **ContentCreationAgent** - Genereert content
   - Schrijft tweets, threads, en Telegram berichten
   - Gebruikt LLM's met gedefinieerde persoonlijkheid
   - Past format aan per platform

5. **PublishingAgent** - Publiceert content
   - Publiceert naar Twitter/X en Telegram
   - Human-in-the-loop approval flow
   - Tracked engagement metrics

#### Fase 2 - Audience Building Agents:

6. **EngagementAgent** - Monitort en engageert met de community
   - Automatisch monitoren van mentions en replies
   - Intelligente replies op vragen (LLM-powered)
   - Likes geven op relevante reacties
   - Retweets van influencers
   - Tracked highly engaged users voor conversie

7. **ImageGenerationAgent** - Creëert visuele content
   - Prijs charts met annotaties
   - Sentiment visualisaties
   - News impact infographics
   - Gebruikt QuickChart API voor charts

8. **AnalyticsAgent** - Tracked performance en genereert inzichten
   - Verzamelt engagement metrics van alle platforms
   - Performance reports en trending topics
   - Agent performance monitoring
   - Actionable recommendations voor optimalisatie
   - KPI dashboard

#### Fase 3 - Monetization & Community Management:

9. **ConversionAgent** - Converteert volgers naar betalende leden
   - Berekent engagement scores voor alle gebruikers
   - Identificeert high-engagement free users
   - Genereert gepersonaliseerde DM's met aanbiedingen
   - Creëert Stripe payment links met discount codes
   - Tracked conversion funnel (DM → open → click → subscribe)

10. **OnboardingAgent** - Onboardt nieuwe betalende leden
    - Welcomes nieuwe paying members
    - Assigns Discord roles gebaseerd op tier (Basic/Premium/VIP)
    - Stuurt onboarding materiaal
    - Handles subscription upgrades en cancellations

11. **ExclusiveContentAgent** - Publiceert premium content
    - Publiceert high-confidence insights (85%+) naar paid channels
    - Tier-gated content (Basic/Premium/VIP)
    - Tracked exclusive content engagement
    - Discord en Telegram private channels

12. **CommunityModeratorAgent** - Modereert private channels
    - AI-powered spam/scam detectie
    - Pattern matching voor regelovertredingen
    - Automatische acties (delete, warn, mute, ban)
    - Context-aware moderation met LLM verificatie
    - Logs alle moderation actions

#### Fase 4 - Optimization & Self-Learning:

13. **StrategyTuningAgent** - Optimaliseert systeem strategie automatisch
    - Analyseert content performance per format en insight type
    - Analyseert conversion funnel performance
    - Identificeert optimale posting tijden
    - Genereert AI-powered tuning recommendations
    - Past high-confidence adjustments automatisch toe

14. **ABTestingAgent** - Test content variaties
    - Creëert A/B test experimenten automatisch
    - Genereert test variants met AI
    - Monitort test resultaten
    - Berekent statistische significantie
    - Declareert winnaars en deelt learnings

15. **PerformanceAnalyticsAgent** - Geavanceerde analytics
    - Creëert periodieke performance snapshots
    - Tracked trends over tijd (daily/weekly/monthly)
    - Detecteert performance anomalies
    - Genereert predictive insights met AI
    - Berekent ROI en efficiency metrics

16. **FeedbackLoopCoordinator** - Coördineert continuous learning
    - Orchestreert alle optimization agents
    - Syntheseert learnings van meerdere bronnen
    - Identificeert optimization priorities
    - Tracked improvement over time
    - Genereert system health scores

## Project Structuur

```
content-creator/
├── config/
│   └── config.py                       # Configuratie management
├── src/
│   ├── agents/                         # AI agents (Phase 1-4)
│   │   ├── base_agent.py
│   │   # Phase 1
│   │   ├── market_scanner_agent.py
│   │   ├── analysis_agent.py
│   │   ├── content_strategist_agent.py
│   │   ├── content_creation_agent.py
│   │   ├── publishing_agent.py
│   │   # Phase 2
│   │   ├── engagement_agent.py
│   │   ├── image_generation_agent.py
│   │   ├── analytics_agent.py
│   │   # Phase 3
│   │   ├── conversion_agent.py
│   │   ├── onboarding_agent.py
│   │   ├── exclusive_content_agent.py
│   │   ├── community_moderator_agent.py
│   │   # Phase 4
│   │   ├── strategy_tuning_agent.py
│   │   ├── ab_testing_agent.py
│   │   ├── performance_analytics_agent.py
│   │   └── feedback_loop_coordinator.py
│   ├── api_integrations/               # API clients
│   │   ├── exchange_api.py
│   │   ├── news_api.py
│   │   ├── twitter_api.py
│   │   ├── telegram_api.py
│   │   ├── discord_api.py              # Phase 3
│   │   └── stripe_api.py               # Phase 3
│   ├── database/                       # Database models en connectie
│   │   ├── models.py
│   │   └── connection.py
│   ├── utils/                          # Utilities
│   │   ├── logger.py
│   │   └── metrics_collector.py
│   ├── orchestrator.py                 # Agent coordinator
│   └── scheduler.py                    # Scheduled execution
├── logs/                               # Log files
├── data/                               # Data storage
│   └── images/                        # Generated images
├── init_db.py                         # Database initialization
├── main.py                            # Main entry point
├── requirements.txt                   # Python dependencies
├── .env.example                      # Environment variables template
└── ROADMAP.md                        # Complete roadmap

```

## Setup

### 1. Vereisten

- Python 3.9+
- PostgreSQL database
- API keys voor:
  - Anthropic Claude
  - Twitter/X
  - Telegram Bot
  - Discord Bot (Phase 3)
  - Stripe (Phase 3)
  - (Optioneel) Binance

### 2. Installatie

```bash
# Clone/download het project
cd content-creator

# Installeer dependencies
pip install -r requirements.txt

# Kopieer .env.example naar .env
cp .env.example .env

# Bewerk .env en voeg je API keys toe
nano .env
```

### 3. Database Setup

```bash
# Initialiseer de database
python init_db.py

# Of reset de database (verwijdert alle data!)
python init_db.py --reset
```

### 4. Configuratie

Bewerk `.env` en configureer:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/content_creator

# LLM API Keys
ANTHROPIC_API_KEY=your_key_here

# Social Media API Keys
TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_secret_here
TWITTER_ACCESS_TOKEN=your_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=@your_channel

# Phase 3 - Monetization
DISCORD_BOT_TOKEN=your_discord_token_here
DISCORD_GUILD_ID=your_guild_id_here

STRIPE_API_KEY=your_stripe_key_here
STRIPE_WEBHOOK_SECRET=your_webhook_secret_here
STRIPE_PRICE_ID_BASIC=price_xxx
STRIPE_PRICE_ID_PREMIUM=price_xxx
STRIPE_PRICE_ID_VIP=price_xxx

# Configuration
HUMAN_IN_THE_LOOP=true
CONTENT_PERSONALITY=hyper-analytical
CONVERSION_MIN_ENGAGEMENT_SCORE=60
```

## Gebruik

### Interactive Mode

Start het systeem in interactive mode:

```bash
python main.py
```

Dit opent een menu met opties:

**PHASE 1 - Core Pipeline:**
1. Run Full Pipeline (Scan → Analyze → Create → Publish)
2. Run Market Scan Only
3. Run Analysis Only
4. Run Content Creation Pipeline

**PHASE 2 - Audience Building:**
5. Run Full Phase 2 Pipeline (All agents including engagement)
6. Run Engagement Pipeline (Monitor & Interact)
7. Generate Analytics Report
8. View KPI Dashboard

**PHASE 3 - Monetization:**
9. Run Full Phase 3 Pipeline (Including monetization)
10. Run Monetization Pipeline Only
11. View Conversion Metrics
12. View Subscription Stats

**PHASE 4 - Optimization & Self-Learning:**
13. Run Full Phase 4 Pipeline (Self-optimizing system)
14. Run Optimization Pipeline Only
15. View A/B Test Results
16. View System Health Score
17. Generate Learning Report

**MANAGEMENT:**
18. Start Scheduler (Automated Continuous Operation)
19. View Pending Approvals
20. Exit

### Scheduled Mode (Daemon)

Start het systeem in scheduled mode voor 24/7 operatie:

```bash
python main.py --scheduled
```

Je wordt gevraagd welke fase je wilt draaien (1, 2, 3, of 4).

**Phase 4 Schedule** (bevat alles van Phase 1-3 + nieuw):
- **Market Scan**: Elke 30 minuten
- **Analysis**: Elke 2 uur
- **Content Creation**: Elke 3 uur
- **Engagement**: Elk uur
- **Analytics**: Elke 6 uur
- **Content Repurposing**: Dagelijks om 10 AM UTC
- **Conversion**: Elke 4 uur
- **Onboarding**: Elke 2 uur
- **Exclusive Content**: Elke 3 uur
- **Moderation**: Elke 30 minuten
- **Performance Analytics**: Elke 12 uur
- **A/B Testing**: Elke 8 uur
- **Strategy Tuning**: Dagelijks om 2 AM UTC
- **Feedback Loop**: Dagelijks om 4 AM UTC
- **Full Phase 4 Pipeline**: Dagelijks om 6 AM UTC

### Human-in-the-Loop Approval

Als `HUMAN_IN_THE_LOOP=true` in `.env`:

1. Content wordt gegenereerd maar niet automatisch gepubliceerd
2. Kies optie 19 in het menu om pending approvals te zien
3. Review de content en approve om te publiceren

## Agent Workflow

### Phase 4 Workflow (Complete Zelflerende Systeem):

```
MarketScannerAgent
    ↓ (verzamelt data)
AnalysisAgent
    ↓ (genereert inzichten)
    ↓
ImageGenerationAgent ← (creëert visuals)
    ↓
ContentStrategistAgent
    ↓ (plant content + repurposing)
ContentCreationAgent
    ↓ (schrijft content, A/B test variants)
PublishingAgent
    ↓ (publiceert naar free channels)
    ↓
EngagementAgent ← (monitort reacties, liked, replied, tracked engagement)
    ↓
ConversionAgent ← (DM's naar high-engagement users)
    ↓
OnboardingAgent ← (welcome nieuwe paying members)
    ↓
ExclusiveContentAgent ← (publiceert naar paid channels)
    ↓
CommunityModeratorAgent ← (modereert private channels)
    ↓
PerformanceAnalyticsAgent ← (creëert performance snapshots)
    ↓
ABTestingAgent ← (analyseert test resultaten)
    ↓
StrategyTuningAgent ← (genereert optimization recommendations)
    ↓
FeedbackLoopCoordinator ← (syntheseert learnings, past systeem aan)
    ↓ (feedback loop terug naar ContentStrategistAgent)
ContentStrategistAgent (optimized posting times, formats, etc.)
```

## Database Schema

Het systeem gebruikt PostgreSQL met de volgende tabellen:

**Phase 1-2:**
- `market_data` - Prijs en volume data
- `news_articles` - Nieuwsartikelen
- `sentiment_data` - Social media sentiment
- `insights` - Gegenereerde inzichten
- `content_plans` - Content planning
- `published_content` - Gepubliceerde content met metrics
- `agent_logs` - Agent activiteit logs

**Phase 3 (Monetization):**
- `community_users` - Gebruikers over alle platforms
- `subscriptions` - Stripe subscriptions
- `user_interactions` - Alle user interactions voor engagement scoring
- `conversion_attempts` - DM conversie tracking
- `exclusive_content` - Premium content voor paying members
- `moderation_actions` - Moderatie geschiedenis

**Phase 4 (Optimization):**
- `ab_tests` - A/B test experimenten
- `ab_test_variants` - Test variants met performance metrics
- `performance_snapshots` - Periodieke system performance snapshots

## Key Features

### 🤖 Volledig Autonoom
- Werkt 24/7 zonder menselijke interventie (optioneel approval flow)
- Zelf-optimaliserende AI die leert van performance data
- Automatische A/B testing en strategy tuning

### 💰 Monetization Engine
- Automatische conversie van engaged volgers naar betalende leden
- Tier-based membership (Free/Basic/Premium/VIP)
- Stripe integration voor payment processing
- Discord & Telegram private communities

### 📊 Advanced Analytics
- Real-time performance tracking
- Predictive insights met AI
- ROI en efficiency metrics
- System health monitoring
- Anomaly detection

### 🔬 Continuous Learning
- A/B testing van content variaties
- Performance-based optimization
- Feedback loop tussen alle agents
- Statistical significance testing

### 🛡️ Community Management
- AI-powered moderation
- Spam en scam detectie
- Automatische enforcement
- Context-aware LLM verificatie

## Roadmap Status

- **Fase 1 (Maand 1-2)**: ✅ **COMPLEET**
  - MarketScannerAgent ✅
  - AnalysisAgent ✅
  - ContentStrategistAgent ✅
  - ContentCreationAgent ✅
  - PublishingAgent ✅

- **Fase 2 (Maand 3-6)**: ✅ **COMPLEET**
  - EngagementAgent ✅
  - ImageGenerationAgent ✅
  - AnalyticsAgent ✅
  - Content Repurposing ✅
  - Metrics Collection ✅

- **Fase 3 (Maand 7-9)**: ✅ **COMPLEET**
  - ConversionAgent ✅
  - OnboardingAgent ✅
  - ExclusiveContentAgent ✅
  - CommunityModeratorAgent ✅
  - Stripe Integration ✅
  - Discord Integration ✅

- **Fase 4 (Maand 10+)**: ✅ **COMPLEET**
  - StrategyTuningAgent ✅
  - ABTestingAgent ✅
  - PerformanceAnalyticsAgent ✅
  - FeedbackLoopCoordinator ✅
  - Self-Optimization System ✅

## Troubleshooting

### Database Connection Error

```bash
# Check of PostgreSQL draait
sudo systemctl status postgresql

# Check DATABASE_URL in .env
```

### API Rate Limits

Het systeem heeft ingebouwde rate limiting, maar:
- Twitter: Max 300 requests per 15 min
- Binance: Max 1200 requests per minute
- Pas de scheduler frequencies aan indien nodig

### LLM API Errors

- Check of ANTHROPIC_API_KEY correct is
- Controleer je API credits/quota

### Stripe Webhooks

Voor production gebruik:
```bash
# Install Stripe CLI
stripe listen --forward-to localhost:8000/webhooks/stripe

# Get webhook signing secret en voeg toe aan .env
```

## Performance Metrics

Het systeem tracked:
- **Content Metrics**: Engagement rates, impressions, clicks
- **Audience Metrics**: Follower growth, engagement scores
- **Monetization Metrics**: Conversion rates, revenue, LTV
- **AI Performance**: Insight confidence, accuracy rates
- **System Health**: Overall health score (0-100)

## Contributing

Dit project volgt de roadmap in `ROADMAP.md`. Alle 4 fasen zijn nu volledig geïmplementeerd.

## License

Private project - All rights reserved

---

**Status**: Alle 4 Fasen Compleet! ✅

### Volledig Geïmplementeerd:
✅ 16 AI Agents
✅ 14 Database tabellen
✅ Volledig autonoom systeem
✅ Monetization engine
✅ Self-learning optimization
✅ A/B testing framework
✅ Community management
✅ Advanced analytics

### Next Steps:
- Production deployment
- Monitoring dashboard
- Additional integrations
- Advanced ML models
