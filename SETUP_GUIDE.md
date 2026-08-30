# ERP03 System Setup Guide

## Current Status

**⚠️ Docker Daemon Issue**: The current environment doesn't support running Docker daemon due to:
- iptables permission restrictions
- Overlay filesystem not available
- Container security policies

## Recommended Setup Options

### Option 1: Run on a Local Machine with Docker Support

#### Prerequisites
- Docker & Docker Compose v2+
- Git
- At least 8GB RAM recommended
- 20GB free disk space

#### Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/nyeinpyaesone-ui/ERP03.git
cd ERP03

# 2. Configure environment secrets
mkdir -p secrets
echo "erp" > secrets/db_user.txt
echo "your_secure_password_here" > secrets/db_password.txt
echo "your_jwt_secret_key_min_32_chars" > secrets/jwt_secret.txt

# 3. Copy production environment
cp .env.example .env.production
# Edit .env.production with your secure values

# 4. Start all services
docker-compose up -d

# 5. Verify health
./scripts/health-check.sh

# 6. Access the application
# - API: http://localhost:8000
# - Frontend: http://localhost:80
# - Swagger UI: http://localhost:8000/docs
```

### Option 2: Development Mode Without Full Docker Stack

For development without full Docker infrastructure:

#### Backend Setup (Local Python Environment)

```bash
cd ERP-BACKEND

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="sqlite:///./erp.db"
export SECRET_KEY="your-super-secret-key-change-in-production-must-be-32-chars-min"
export ACCESS_TOKEN_EXPIRE_MINUTES=15

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup (Local Node.js Environment)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Option 3: Use External Docker Host

If you have access to a remote Docker host:

```bash
# Set Docker host
export DOCKER_HOST=tcp://your-docker-host:2375

# Then run normal docker-compose commands
docker-compose up -d
```

## Architecture Overview

The ERP03 system consists of:

1. **ERP-BACKEND** - Core FastAPI backend with PostgreSQL
2. **Frontend** - React web dashboard
3. **Mobile** - React Native mobile app
4. **Database** - PostgreSQL 15
5. **Cache** - Redis 7
6. **Worker** - Celery task queue
7. **Flower** - Celery monitoring

## Configuration Files

### Required Secrets

Create the following files in `/workspace/secrets/`:

```bash
# secrets/db_user.txt
erp

# secrets/db_password.txt
your_secure_password_here

# secrets/jwt_secret.txt
your_jwt_secret_key_min_32_characters_long
```

### Environment Variables (.env.production)

Key variables to configure:

```bash
POSTGRES_USER=erp03_user
POSTGRES_PASSWORD=SuperSecurePassword123!
POSTGRES_DB=erp03_prod
DATABASE_URL=postgresql+asyncpg://erp03_user:SuperSecurePassword123!@db:5432/erp03_prod
REDIS_URL=redis://redis:6379/0
JWT_SECRET=jwt_secret_key_production_ready_12345
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Services and Ports

| Service | Port | Description |
|---------|------|-------------|
| ERP API | 8000 | FastAPI REST backend |
| Frontend | 80 | React web dashboard |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & session store |
| Flower | 5555 | Celery monitoring |

## Health Check

After starting the system, verify all services:

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check frontend
curl http://localhost:80/

# View logs
docker-compose logs -f
```

## Troubleshooting

### Docker Daemon Issues

If Docker daemon fails to start:

1. **Check if running in a container**: Docker-in-Docker requires privileged mode
2. **Use external Docker host**: Connect to a remote Docker daemon
3. **Run locally**: Install Docker Desktop on your machine

### Database Connection Issues

```bash
# Check database container
docker-compose ps db

# View database logs
docker-compose logs db

# Test connection
docker-compose exec db pg_isready -U erp -d erp03_prod
```

### Permission Issues

```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo docker-compose up -d
```

## Next Steps

1. **Choose your setup option** based on your environment
2. **Configure secrets and environment variables**
3. **Start the services** using the appropriate method
4. **Run health checks** to verify everything is working
5. **Access the application** through the web interface or API

## Additional Resources

- [README.md](README.md) - Main documentation
- [docs/](docs/) - Detailed documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [ROADMAP.md](ROADMAP.md) - Project roadmap

## Support

For issues and questions:
- GitHub Issues: https://github.com/nyeinpyaesone-ui/ERP03/issues
- Documentation: /docs directory
