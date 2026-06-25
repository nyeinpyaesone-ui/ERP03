# Production Server Setup Guide

## Requirements

- Ubuntu 22.04 LTS (or similar)
- 4GB+ RAM
- 2+ CPU cores
- 50GB+ storage
- Domain name (e.g., erpsolution.com)

## Step-by-Step Setup

### 1. Prepare Server

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install essentials
sudo apt-get install -y curl wget git rsync
```

### 2. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 4. Clone Repository

```bash
git clone https://github.com/nyeinpyaesone-ui/ERP.git /opt/erp-solution
cd /opt/erp-solution
```

### 5. Configure Environment

```bash
cp .env.production .env
# Edit .env with your secrets
nano .env
```

### 6. Setup SSL (Let's Encrypt)

```bash
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d api.yourdomain.com -d app.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/api.yourdomain.com/privkey.pem ./ssl/key.pem
```

### 7. Deploy

```bash
# Pull images
docker pull powerrangeranikg/erp-solution-backend:latest
docker pull powerrangeranikg/erp-solution-frontend:latest

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

### 8. Verify

```bash
# Check containers
docker ps

# Check health
curl https://api.yourdomain.com/health

# Check logs
docker-compose logs -f backend
```

## DNS Configuration

| Record | Type | Value |
|--------|------|-------|
| api.yourdomain.com | A | Your server IP |
| app.yourdomain.com | A | Your server IP |

## Firewall Rules

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## Backup Strategy

```bash
# Database backup
docker-compose exec postgres pg_dump -U erp erp_solution > backup_$(date +%Y%m%d).sql

# Automated backup (add to crontab)
0 2 * * * cd /opt/erp-solution && ./scripts/backup.sh /backups
```

## Monitoring

- **Health checks**: `curl https://api.yourdomain.com/health`
- **Logs**: `docker-compose logs -f`
- **Metrics**: `https://api.yourdomain.com/metrics`

## Support

| Contact | Details |
|---------|---------|
| Email | nyeinpyaesone273@gmail.com |
| LinkedIn | linkedin.com/in/nyein-pyae-sone-3250501ba |
| GitHub | github.com/nyeinpyaesone-ui/ERP |
| Phone | +959699795380 |
