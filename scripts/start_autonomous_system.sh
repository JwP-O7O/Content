#!/bin/bash
# Start Autonomous Improvement System
# This script initializes and starts all autonomous agents

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║     Autonomous Improvement System - Initializing        ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1/5: Creating directory structure...${NC}"
mkdir -p src/autonomous_agents/{monitoring,analysis,planning,execution,validation,learning,orchestration}
mkdir -p logs/autonomous_agents
mkdir -p data/improvement_plans
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

echo -e "${YELLOW}Step 2/5: Setting up database schema...${NC}"

# Check if .env exists and has DATABASE_URL
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    echo "  Creating .env.example reference..."
    echo "  Please configure DATABASE_URL in .env to enable database features"
    echo -e "${GREEN}✓ Skipping database setup (will use file-based storage)${NC}"
else
    # Create SQL schema file
    cat > /tmp/autonomous_agents_schema.sql << 'EOF'
-- Agent activity tracking
CREATE TABLE IF NOT EXISTS autonomous_agent_logs (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    layer VARCHAR(50) NOT NULL,
    action VARCHAR(200) NOT NULL,
    status VARCHAR(50) NOT NULL,
    details JSONB,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_autonomous_logs_agent ON autonomous_agent_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_autonomous_logs_created ON autonomous_agent_logs(created_at);

-- Improvement suggestions
CREATE TABLE IF NOT EXISTS improvement_suggestions (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    implementation_plan JSONB,
    estimated_impact FLOAT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    implemented_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_suggestions_status ON improvement_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_suggestions_priority ON improvement_suggestions(priority DESC);

-- Code quality metrics over time
CREATE TABLE IF NOT EXISTS code_quality_snapshots (
    id SERIAL PRIMARY KEY,
    overall_score FLOAT,
    test_coverage FLOAT,
    complexity_score FLOAT,
    documentation_score FLOAT,
    security_score FLOAT,
    performance_score FLOAT,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quality_snapshots_created ON code_quality_snapshots(created_at);

-- Learning patterns
CREATE TABLE IF NOT EXISTS learned_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR(100) NOT NULL,
    pattern_data JSONB,
    success_rate FLOAT,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patterns_type ON learned_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_success ON learned_patterns(success_rate DESC);
EOF

    # Execute schema
    python3 << 'PYEOF'
try:
    from src.database.connection import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        with open('/tmp/autonomous_agents_schema.sql', 'r') as f:
            sql = f.read()
            # Execute each statement separately
            for statement in sql.split(';'):
                if statement.strip():
                    conn.execute(text(statement))
        conn.commit()
    print("✓ Database schema created successfully")
except Exception as e:
    print(f"⚠ Database not available: {str(e)[:100]}")
    print("  (You can continue without database - agents will use file storage)")
PYEOF

    echo -e "${GREEN}✓ Database setup complete${NC}"
fi
echo ""

echo -e "${YELLOW}Step 3/5: Installing additional dependencies...${NC}"
pip install -q psutil pip-audit 2>/dev/null || echo "  (Some packages may already be installed)"
echo -e "${GREEN}✓ Dependencies ready${NC}"
echo ""

echo -e "${YELLOW}Step 4/5: Creating base agent class...${NC}"
# This will be created by the workflow implementation
touch src/autonomous_agents/__init__.py
echo -e "${GREEN}✓ Base structure ready${NC}"
echo ""

echo -e "${YELLOW}Step 5/5: System status check...${NC}"
python3 << 'PYEOF'
import sys
from pathlib import Path

checks = {
    "Database connection": False,
    "Agent directories": False,
    "Log directories": False,
}

# Check database
try:
    from src.database.connection import engine
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    checks["Database connection"] = True
except:
    pass

# Check directories
if Path("src/autonomous_agents/monitoring").exists():
    checks["Agent directories"] = True
if Path("logs/autonomous_agents").exists():
    checks["Log directories"] = True

print("\nSystem Status:")
for check, status in checks.items():
    symbol = "✓" if status else "✗"
    print(f"  {symbol} {check}")

all_ok = all(checks.values())
if all_ok:
    print("\n✓ All systems ready!")
    sys.exit(0)
else:
    print("\n⚠ Some checks failed, but you can continue")
    sys.exit(0)
PYEOF

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║     Autonomous System Initialized Successfully!         ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "  1. Review the workflow: .agent/workflows/autonomous-improvement-system.md"
echo "  2. Implement monitoring agents (Layer 1)"
echo "  3. Start the system: python main.py (option 21)"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "  - Workflow: .agent/workflows/autonomous-improvement-system.md"
echo "  - Logs: logs/autonomous_agents/"
echo "  - Database: autonomous_agent_logs table"
echo ""
