#!/bin/bash

# Backup Let's Encrypt certificates
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/letsencrypt_backup_$TIMESTAMP.tar.gz"

echo "Backing up Let's Encrypt certificates..."
mkdir -p $BACKUP_DIR

tar -czf $BACKUP_FILE ./certbot/conf/

echo "Backup created: $BACKUP_FILE"
ls -lh $BACKUP_FILE