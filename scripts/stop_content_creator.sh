#!/data/data/com.termux/files/usr/bin/bash
# Stop Content Creator on Termux

echo "=== Content Creator Shutdown Script ==="

# Check if running
if ! pgrep -f "python main.py --scheduled" > /dev/null; then
    echo "⚠ Content Creator is not running"
    exit 0
fi

PID=$(pgrep -f "python main.py --scheduled")
echo "Stopping Content Creator (PID: $PID)..."

# Graceful stop
pkill -TERM -f "python main.py --scheduled"

# Wait for shutdown
sleep 2

# Check if still running
if pgrep -f "python main.py --scheduled" > /dev/null; then
    echo "⚠ Process still running, forcing stop..."
    pkill -KILL -f "python main.py --scheduled"
    sleep 1
fi

if ! pgrep -f "python main.py --scheduled" > /dev/null; then
    echo "✓ Content Creator stopped successfully"
else
    echo "✗ Failed to stop Content Creator"
    exit 1
fi
