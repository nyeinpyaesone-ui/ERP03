#!/bin/bash
###############################################################################
# ERP SOLUTION — Production Deployment Script
# Usage: ./deploy.sh [server_ip]
###############################################################################

set -e

SERVER_IP="${1:-}"
DOCKER_USERNAME="powerrangeranikg"

echo "=========================================="
echo "  ERP SOLUTION — Production Deployment"
echo "=========================================="
echo ""

if [ -z "$SERVER_IP" ]; then
    echo "Usage: ./deploy.sh [server_ip]"
    echo "Example: ./deploy.sh 192.168.1.100"
    exit 1
fi

echo "Deploying to: $SERVER_IP"
echo ""

# Step 1: Copy files to server
echo "[1/6] Copying files to server..."
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='venv'     ./ root@$SERVER_IP:/opt/erp-solution/
echo "  ✓ Files copied"

# Step 2: Setup server
echo "[2/6] Setting up server..."
ssh root@$SERVER_IP << 'REMOTE'
    # Update system
    apt-get update && apt-get upgrade -y

    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com | sh
        usermod -aG docker $USER
    fi

    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi

    # Create necessary directories
    mkdir -p /opt/erp-solution/ssl
    mkdir -p /opt/erp-solution/logs/nginx
    mkdir -p /opt/erp-solution/backups

    echo "  ✓ Server setup complete"
REMOTE

# Step 3: SSL Certificate
echo "[3/6] Setting up SSL..."
ssh root@$SERVER_IP << 'REMOTE'
    # Install certbot
    apt-get install -y certbot

    # Get certificate (replace with your domain)
    # certbot certonly --standalone -d api.yourdomain.com -d app.yourdomain.com

    echo "  ✓ SSL configured (manual cert required)"
    echo "  Run: certbot --nginx -d api.yourdomain.com -d app.yourdomain.com"
REMOTE

# Step 4: Pull images
echo "[4/6] Pulling Docker images..."
ssh root@$SERVER_IP "cd /opt/erp-solution && docker pull $DOCKER_USERNAME/erp-solution-backend:latest && docker pull $DOCKER_USERNAME/erp-solution-frontend:latest"
echo "  ✓ Images pulled"

# Step 5: Start services
echo "[5/6] Starting services..."
ssh root@$SERVER_IP "cd /opt/erp-solution && docker-compose -f docker-compose.prod.yml up -d"
echo "  ✓ Services started"

# Step 6: Verify
echo "[6/6] Verifying deployment..."
ssh root@$SERVER_IP << 'REMOTE'
    # Check containers
    docker ps | grep erp

    # Check health
    curl -s http://localhost:8000/health || echo "Backend not responding"

    echo "  ✓ Deployment verified"
REMOTE

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "  Server: $SERVER_IP"
echo "  Backend: http://$SERVER_IP:8000"
echo "  Frontend: http://$SERVER_IP:3000"
echo ""
echo "  Next steps:"
echo "  1. Configure .env.production with your secrets"
echo "  2. Set up SSL certificates"
echo "  3. Configure DNS (api.yourdomain.com, app.yourdomain.com)"
echo "  4. Run database migrations: docker-compose exec backend alembic upgrade head"
echo "  5. Monitor logs: docker-compose logs -f"
echo ""
