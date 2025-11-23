#!/data/data/com.termux/files/usr/bin/bash
# Backup script for Content Creator on Termux
# Based on DEPLOYMENT.md backup strategy

BACKUP_DIR="$HOME/projects/content-creator/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "=== Content Creator Backup ==="
echo "Date: $DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Backing up PostgreSQL database..."
pg_dump -U content_creator_user content_creator > "$BACKUP_DIR/db_$DATE.sql"
if [ $? -eq 0 ]; then
    echo "✓ Database backed up to db_$DATE.sql"
else
    echo "✗ Database backup failed"
    exit 1
fi

# Config backup
echo "Backing up configuration..."
cp $HOME/projects/content-creator/.env "$BACKUP_DIR/env_$DATE"
echo "✓ Config backed up to env_$DATE"

# Logs backup
echo "Backing up logs..."
if [ -d "$HOME/projects/content-creator/logs" ]; then
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" $HOME/projects/content-creator/logs/
    echo "✓ Logs backed up to logs_$DATE.tar.gz"
else
    echo "⚠ No logs directory found"
fi

# Delete backups older than 30 days
echo "Cleaning old backups (>30 days)..."
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "env_*" -mtime +30 -delete

echo ""
echo "=== Backup Summary ==="
echo "Location: $BACKUP_DIR"
echo "Files created:"
ls -lh $BACKUP_DIR/db_$DATE.sql 2>/dev/null
ls -lh $BACKUP_DIR/env_$DATE 2>/dev/null
ls -lh $BACKUP_DIR/logs_$DATE.tar.gz 2>/dev/null

echo ""
echo "✅ Backup completed successfully!"
