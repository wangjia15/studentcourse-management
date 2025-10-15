#!/bin/bash

# Database backup script for Chinese University Grade Management System
# This script creates automated backups of the database and important files

set -euo pipefail

# Configuration
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-grade_management}
DB_USER=${DB_USER:-postgres}
BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${RETENTION_DAYS:-30}
S3_BUCKET=${S3_BUCKET:-}  # Optional: for cloud storage
ENCRYPT_BACKUP=${ENCRYPT_BACKUP:-true}
GPG_RECIPIENT=${GPG_RECIPIENT:-}  # GPG key ID for encryption

# Logging
LOG_FILE="/var/log/backup.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create backup directory with date
DATE=$(date '+%Y%m%d_%H%M%S')
BACKUP_PATH="$BACKUP_DIR/$DATE"
mkdir -p "$BACKUP_PATH"

log "Starting backup process for $DATE"

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days"
    find "$BACKUP_DIR" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \;
}

# Function to upload to S3 (if configured)
upload_to_s3() {
    if [[ -n "$S3_BUCKET" ]]; then
        log "Uploading backup to S3 bucket: $S3_BUCKET"
        aws s3 sync "$BACKUP_PATH" "s3://$S3_BUCKET/backups/$DATE/" --delete
        log "S3 upload completed"
    fi
}

# Function to encrypt backup
encrypt_file() {
    local input_file="$1"
    local output_file="$2"

    if [[ "$ENCRYPT_BACKUP" == "true" && -n "$GPG_RECIPIENT" ]]; then
        log "Encrypting backup with GPG"
        gpg --trust-model always --encrypt -r "$GPG_RECIPIENT" --output "$output_file.gpg" "$input_file"
        rm "$input_file"
        echo "$output_file.gpg"
    else
        echo "$input_file"
    fi
}

# Database backup
log "Starting database backup"
DB_BACKUP_FILE="$BACKUP_PATH/database_$DATE.sql"

# Create database dump
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-owner --no-privileges --verbose \
    --format=custom --compress=9 \
    --file="$DB_BACKUP_FILE.dump"

# Create plain SQL dump for portability
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-owner --no-privileges --verbose \
    --format=plain --no-acl \
    --file="$DB_BACKUP_FILE.sql"

# Encrypt database backup
DB_BACKUP_FILE=$(encrypt_file "$DB_BACKUP_FILE.dump")

log "Database backup completed: $DB_BACKUP_FILE"

# File system backup
log "Starting file system backup"
FILES_BACKUP_FILE="$BACKUP_PATH/files_$DATE.tar.gz"

# Backup important directories
tar -czf "$FILES_BACKUP_FILE" \
    --exclude='*.log' \
    --exclude='*.tmp' \
    --exclude='cache' \
    --exclude='node_modules' \
    /app/uploads \
    /app/config \
    /app/static

# Encrypt files backup
FILES_BACKUP_FILE=$(encrypt_file "$FILES_BACKUP_FILE")

log "File system backup completed: $FILES_BACKUP_FILE"

# Configuration backup
log "Starting configuration backup"
CONFIG_BACKUP_FILE="$BACKUP_PATH/config_$DATE.tar.gz"

tar -czf "$CONFIG_BACKUP_FILE" \
    /app/.env \
    /app/docker-compose.yml \
    /app/nginx/nginx.conf \
    /app/monitoring/ \
    /app/scripts/

# Encrypt config backup
CONFIG_BACKUP_FILE=$(encrypt_file "$CONFIG_BACKUP_FILE")

log "Configuration backup completed: $CONFIG_BACKUP_FILE"

# Create backup manifest
cat > "$BACKUP_PATH/manifest.txt" << EOF
Backup Date: $DATE
Database Backup: $(basename "$DB_BACKUP_FILE")
Files Backup: $(basename "$FILES_BACKUP_FILE")
Config Backup: $(basename "$CONFIG_BACKUP_FILE")
Database Size: $(du -h "$DB_BACKUP_FILE" | cut -f1)
Files Size: $(du -h "$FILES_BACKUP_FILE" | cut -f1)
Config Size: $(du -h "$CONFIG_BACKUP_FILE" | cut -f1)
Total Size: $(du -sh "$BACKUP_PATH" | cut -f1)
EOF

# Create backup checksums
log "Generating checksums"
cd "$BACKUP_PATH"
sha256sum * > checksums.sha256

# Upload to cloud storage if configured
upload_to_s3

# Test backup integrity
log "Testing backup integrity"
if [[ "$ENCRYPT_BACKUP" == "true" ]]; then
    # Test encrypted backup (this would require decryption)
    log "Encrypted backup created - integrity check requires decryption"
else
    # Test unencrypted backup
    if [[ -f "$DB_BACKUP_FILE" ]]; then
        pg_restore --list "$DB_BACKUP_FILE" > /dev/null 2>&1 && \
            log "Database backup integrity check passed" || \
            log "ERROR: Database backup integrity check failed"
    fi
fi

# Cleanup old backups
cleanup_old_backups

# Create backup summary
BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
log "Backup process completed successfully"
log "Backup location: $BACKUP_PATH"
log "Total backup size: $BACKUP_SIZE"
log "Backup retention: $RETENTION_DAYS days"

# Send notification (optional)
if [[ -n "${WEBHOOK_URL:-}" ]]; then
    curl -X POST "$WEBHOOK_URL" \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Database backup completed successfully\\nDate: $DATE\\nSize: $BACKUP_SIZE\\nLocation: $BACKUP_PATH\"}" || \
        log "Failed to send webhook notification"
fi

exit 0