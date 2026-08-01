#!/data/data/com.termux/files/usr/bin/bash
# Start Content Creator in background on Termux
# Based on DEPLOYMENT.md deployment options

PROJECT_DIR="$HOME/projects/content-creator"
LOG_DIR="$PROJECT_DIR/logs"

echo "=== Content Creator Startup Script ==="

# Check if PostgreSQL is running
pg_isready -q
if [ $? -ne 0 ]; then
    echo "Starting PostgreSQL..."
    pg_ctl -D $PREFIX/var/lib/postgresql -l $PREFIX/var/lib/postgresql/logfile start
    sleep 2
fi

# Create logs directory
mkdir -p $LOG_DIR

# Change to project directory
cd $PROJECT_DIR

# Check if already running
if pgrep -f "python main.py --scheduled" > /dev/null; then
    echo "⚠ Content Creator is already running!"
    echo "PID: $(pgrep -f 'python main.py --scheduled')"
    echo ""
    echo "To stop: pkill -f 'python main.py --scheduled'"
    exit 1
fi

# Start in background with nohup
echo "Starting Content Creator in background..."
nohup python main.py --scheduled > $LOG_DIR/output.log 2> $LOG_DIR/error.log &

PID=$!
echo "✓ Content Creator started!"
echo "PID: $PID"
echo ""
echo "Logs:"
echo "  Output: tail -f $LOG_DIR/output.log"
echo "  Errors: tail -f $LOG_DIR/error.log"
echo "  System: tail -f $LOG_DIR/content_creator_*.log"
echo ""
echo "To stop: pkill -f 'python main.py --scheduled'"
