# GEMINI.md - Content Creator

## Project Overview

This project is a sophisticated, autonomous AI agent system built with Python. Its primary purpose is to perform crypto-market analysis, generate content based on that analysis, and manage a social media community. The system is designed to be fully autonomous, with a multi-phase roadmap that includes core content creation, audience building, monetization, and self-learning optimization.

The architecture is modular, with a clear separation of concerns. It uses a series of specialized AI agents, each responsible for a specific task in the content pipeline. The agents are coordinated by an orchestrator, which manages the overall workflow. The system is data-driven, with a PostgreSQL database for storing market data, generated insights, content, and user information.

**Key Technologies:**

*   **Backend:** Python, asyncio
*   **Database:** PostgreSQL, SQLAlchemy
*   **AI/ML:** Anthropic Claude, Google Gemini, pandas, numpy, scipy, ta
*   **APIs:** Twitter, Telegram, Binance, Stripe, Discord
*   **Configuration:** pydantic-settings
*   **Scheduling:** APScheduler

## Building and Running

### Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment:**
    *   Copy `.env.example` to `.env`.
    *   Fill in the required API keys and database URL in the `.env` file.

3.  **Initialize Database:**
    ```bash
    python init_db.py
    ```

### Running the System

The system can be run in two modes:

1.  **Interactive Mode:**
    ```bash
    python main.py
    ```
    This will present a menu with various options for running different parts of the content pipeline.

2.  **Scheduled Mode (Daemon):**
    ```bash
    python main.py --scheduled
    ```
    This will run the system continuously in the background, executing tasks according to a predefined schedule.

    A convenience script is also provided for running in a production-like environment on Termux:
    ```bash
    ./scripts/start_content_creator.sh
    ```

### Testing

The project includes a suite of tests that can be run using pytest:

```bash
pytest
```

## Development Conventions

*   **Modular Architecture:** The system is built around a series of independent agents, each with a specific responsibility. This makes it easy to extend and maintain.
*   **Asynchronous Operations:** The use of `asyncio` allows for efficient handling of I/O-bound tasks, such as making API calls.
*   **Configuration Management:** The `pydantic-settings` library is used to manage configuration from environment variables, providing a clean and robust way to handle settings.
*   **Database Migrations:** While not explicitly stated, the use of SQLAlchemy and the presence of `init_db.py` suggest that database schema management is handled carefully.
*   **Comprehensive Logging:** The `loguru` library is used for logging, providing detailed and structured logs for debugging and monitoring.
*   **Human-in-the-Loop:** The system includes a "human-in-the-loop" feature, which allows for manual approval of content before it's published. This is a crucial feature for ensuring content quality.
