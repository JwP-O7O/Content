# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An autonomous AI agent system that generates crypto market analyses, builds a community on social media, converts followers to paid members, and continuously self-optimizes through machine learning. The system implements a complete 4-phase roadmap from basic content creation to fully autonomous self-learning optimization.

**Language**: Dutch (Nederlands) is used in README and documentation, Python code uses English.

## Development Commands

### Database

```bash
# Initialize database (first time setup)
python init_db.py

# Reset database (WARNING: deletes all data)
python init_db.py --reset

# Verify PostgreSQL is running on Termux
pg_ctl -D $PREFIX/var/lib/postgresql status
```

### Running the System

```bash
# Interactive mode with menu
python main.py

# Scheduled mode (daemon) - runs 24/7
python main.py --scheduled
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agents.py -v

# Run tests with script
bash run_tests.sh

# Run single test
pytest tests/test_agents.py::test_specific_function -v
```

### Verification

```bash
# Verify system setup and dependencies
python verify_system.py
```

## Architecture

### Core Design Pattern: Multi-Agent Orchestration

The system uses a **coordinator pattern** where `AgentOrchestrator` (src/orchestrator.py) manages 16 specialized AI agents. Each agent inherits from `BaseAgent` and implements the `execute()` method for its specific task.

**Key principle**: Agents are stateless and communicate through the PostgreSQL database. All shared state lives in the database, not in agent instances.

### Agent Workflow

```
MarketScannerAgent → AnalysisAgent → ContentStrategistAgent → ContentCreationAgent → PublishingAgent
                                              ↓
                                    EngagementAgent ← monitors published content
                                              ↓
                                    ConversionAgent ← identifies high-engagement users
                                              ↓
                                    OnboardingAgent ← welcomes paying members
                                              ↓
                                    FeedbackLoopCoordinator ← optimizes entire system
```

### Phase Structure

The system is organized into 4 phases, each building on the previous:

- **Phase 1** (Foundation): Market scanning, analysis, content creation, publishing
- **Phase 2** (Audience Building): Engagement, analytics, image generation, content repurposing
- **Phase 3** (Monetization): Conversion, onboarding, exclusive content, community moderation
- **Phase 4** (Self-Learning): A/B testing, strategy tuning, performance analytics, feedback loops

Each phase can run independently via menu options or scheduled mode.

### Database Schema

**14 tables** organized by domain:

**Core Pipeline**:
- `market_data` - Price/volume from exchanges
- `news_articles` - Collected news with sentiment
- `sentiment_data` - Social media sentiment
- `insights` - Analyzed market insights (with `InsightType` enum)
- `content_plans` - Content strategy with format/platform/timing
- `published_content` - Published posts with engagement metrics

**Community & Monetization**:
- `community_users` - Users across all platforms with `UserTier` enum (FREE/BASIC/PREMIUM/VIP)
- `user_interactions` - All interactions for engagement scoring
- `subscriptions` - Stripe subscriptions with status tracking
- `conversion_attempts` - DM conversion funnel tracking
- `exclusive_content` - Premium content for paying members
- `moderation_actions` - Community moderation history

**Optimization**:
- `ab_tests` - A/B test experiments with `TestStatus` enum
- `ab_test_variants` - Test variants with statistical results
- `performance_snapshots` - Time-series system performance

**System**:
- `agent_logs` - All agent execution logs (via `BaseAgent._log_activity()`)

### Configuration System

Settings are managed via **Pydantic Settings** (config/config.py):
- Loads from `.env` file (case-insensitive)
- Type-validated at startup
- Global `settings` instance imported throughout codebase

**Critical settings**:
- `HUMAN_IN_THE_LOOP`: If true, content requires approval before publishing
- `CONTENT_PERSONALITY`: LLM personality style (e.g., "hyper-analytical")
- Phase-specific settings (conversion thresholds, A/B test parameters, etc.)

### Async Architecture

The entire system is **async/await** based:
- All agent `execute()` methods are async
- Database operations use context managers (`with get_db() as db`)
- External API calls use `aiohttp` where possible
- Main entry point uses `asyncio.run()`

### LLM Integration

Multiple LLM providers supported (Anthropic/Claude is primary):
- Analysis and content generation use Claude API
- Structured via `anthropic` Python SDK
- Prompts embedded in agent code (see `ContentCreationAgent`, `AnalysisAgent`)
- Personality configured via `CONTENT_PERSONALITY` setting

## Important Implementation Details

### Agent Base Class Pattern

All agents must:
1. Inherit from `BaseAgent`
2. Implement `async def execute(self, *args, **kwargs)`
3. Call via `await agent.run()` (not `execute()` directly) - this handles logging
4. Use `self.log_info()`, `self.log_warning()`, `self.log_error()` for logging

Example:
```python
from src.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyAgent")

    async def execute(self):
        self.log_info("Starting execution")
        # Implementation here
        return {"status": "success"}
```

### Human-in-the-Loop Approval Flow

When `HUMAN_IN_THE_LOOP=true`:
1. Content is created and stored with `status='pending_approval'` in `content_plans`
2. User views pending approvals via menu option 19
3. Approval triggers `PublishingAgent.approve_and_publish(plan_id)`
4. Only then is content published and moved to `published_content`

### Database Connection Pattern

**Always use context manager**:
```python
from src.database.connection import get_db

with get_db() as db:
    result = db.query(Model).filter(...).first()
    db.add(new_object)
    db.commit()
```

Do NOT store db session as instance variable - create new session per operation.

### Termux Compatibility

This codebase runs on **Android/Termux**:
- PostgreSQL runs via `pg_ctl -D $PREFIX/var/lib/postgresql`
- Some packages (like pandas) may be unavailable - graceful degradation implemented
- `AnalysisAgent` is optional (requires pandas) - see orchestrator.py:10-16
- Use `requirements-termux.txt` for Termux-specific dependencies

### Error Handling Philosophy

- Agent errors are logged to `agent_logs` table but **do not halt the pipeline**
- `BaseAgent.run()` catches exceptions, logs them, then re-raises
- Orchestrator catches agent failures and continues with next agent
- Use `try/except` in agents for recoverable errors, let critical errors propagate

### Testing Philosophy

Tests use **pytest-asyncio** and **pytest-mock**:
- Test files mirror src structure (tests/test_agents.py, tests/test_database.py)
- Mock external APIs (Twitter, Telegram, Stripe, etc.) in all tests
- Use fixtures for database setup/teardown
- Focus on agent logic, not API integration details

## Common Patterns & Idioms

### Content Pipeline Flow

1. Insights generated by `AnalysisAgent` → stored in `insights` table
2. `ContentStrategistAgent` reads insights → creates `content_plans`
3. `ContentCreationAgent` reads plans → generates text → stores in `content_plans.generated_content`
4. `PublishingAgent` reads plans → publishes (if approved) → stores in `published_content`

### Engagement Scoring

Users get engagement scores (0-100) calculated by `ConversionAgent._calculate_engagement_score()`:
- Based on `user_interactions` table
- Weighted: replies (high), retweets (medium), likes (low)
- Decays over time (recent interactions weighted more)
- High-engagement users (>60) targeted for conversion

### A/B Testing Flow

1. `ABTestingAgent` creates test with variants in `ab_tests` and `ab_test_variants`
2. `ContentCreationAgent` generates variant content using AI
3. Publishing distributes variants to random users
4. Results tracked in `ab_test_variants.performance_data`
5. Statistical significance calculated via scipy
6. Winner declared when confidence > 95%

### Scheduler Architecture

`ContentCreatorScheduler` (src/scheduler.py):
- Uses APScheduler with AsyncIOScheduler
- Jobs defined per phase (Phase 4 includes all previous phases)
- Mix of interval triggers (every N hours) and cron triggers (specific times)
- Example: Market scan every 30min, content creation every 3hrs, optimization daily at 2 AM UTC

## API Integration Notes

### Twitter/X API (tweepy)

- Uses OAuth 1.0a (requires 4 tokens: key, secret, access token, access secret)
- Rate limits: 300 requests per 15 min window
- Publishing uses v2 API, reading uses v1.1 for better coverage

### Telegram (python-telegram-bot)

- Bot token authentication
- Two channel types: public channel (free content) and private channel (paid)
- Use `application.bot.send_message()` for async sending

### Stripe

- Webhook integration for subscription events (payment, cancellation, upgrade)
- Price IDs configured in .env for each tier (BASIC/PREMIUM/VIP)
- Payment links generated dynamically with discount codes

### Discord (discord.py)

- Bot token authentication
- Role-based access control (assign roles based on subscription tier)
- Moderation actions: delete, warn, mute, ban

## Development Workflow

### Adding a New Agent

1. Create file in `src/agents/` inheriting from `BaseAgent`
2. Implement `async def execute(self)`
3. Add to `AgentOrchestrator.__init__()` in orchestrator.py
4. Add orchestrator method for running (e.g., `run_my_agent_pipeline()`)
5. Add menu option in main.py
6. Add scheduler job if needed in scheduler.py
7. Write tests in tests/test_agents.py

### Adding a New Database Model

1. Define model in `src/database/models.py` inheriting from `Base`
2. Run `python init_db.py` to create table (or use Alembic for migrations)
3. Import model where needed: `from src.database.models import MyModel`

### Modifying Content Strategy

Content strategy logic lives in `ContentStrategistAgent`:
- `_determine_format()` - chooses tweet vs thread vs blog
- `_choose_platform()` - Twitter vs Telegram
- `_calculate_optimal_posting_time()` - timing optimization
- `_should_be_exclusive()` - free vs paid content decision

Strategy is influenced by:
- Insight confidence (high confidence → exclusive content)
- Historical performance (tracked in `published_content`)
- A/B test learnings (from `FeedbackLoopCoordinator`)

## Phase-Specific Notes

### Phase 3 (Monetization)

Requires additional setup:
- Stripe account with webhook endpoint configured
- Discord server with bot permissions and role IDs
- Telegram private channel/group for paid members

Conversion funnel: Engagement scoring → DM outreach → Payment link → Stripe checkout → Onboarding → Role assignment

### Phase 4 (Self-Learning)

The system becomes **fully autonomous**:
- `StrategyTuningAgent` analyzes performance and adjusts strategy automatically
- `ABTestingAgent` creates experiments without human input
- `FeedbackLoopCoordinator` synthesizes all learnings and updates agent behavior
- High-confidence changes (>85%) applied automatically, low-confidence changes flagged for review

System health score (0-100) calculated by `FeedbackLoopCoordinator.get_system_health_score()` based on:
- Content performance
- Engagement rates
- Conversion metrics
- Technical stability
