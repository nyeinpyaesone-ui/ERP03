# ERP03 Systemd Service Units

These systemd unit files manage ERP03 backup automation on a production Linux host.

## Installation

```bash
# Copy unit files to systemd directory
sudo cp scripts/systemd/erp03-backup.service /etc/systemd/system/
sudo cp scripts/systemd/erp03-backup.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the backup timer
sudo systemctl enable --now erp03-backup.timer

# Check timer status
sudo systemctl list-timers erp03-backup.timer
```

## Backup Schedule

- Runs daily at 02:00 UTC
- Persistent: missed runs execute on startup
- Backups stored in `BACKUP_DIR` (default: `/data/backups`)
- Retention: 7 days (configurable via `BACKUP_RETENTION_DAYS`)

## Alternative: Cron

If systemd is not available, use cron instead:

```cron
0 2 * * * /path/to/ERP03/scripts/backup.sh >> /var/log/erp03-backup.log 2>&1
```

Required environment variable: `RESTIC_REPOSITORY` (S3/GCS/local path for offsite storage)
