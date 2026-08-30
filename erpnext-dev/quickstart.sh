#!/bin/bash
# ERPNext Development Environment Quick Start Script
# This script automates the setup of a local ERPNext development environment

set -e

echo "=============================================="
echo "ERPNext Development Environment Setup"
echo "=============================================="
echo ""

# Configuration
ERPNEXT_VERSION="v16.31.1"
FRAPPE_BRANCH="version-16"
FRAPPE_DOCKER_REF="v3.2.1"
SITE_NAME="erp.localhost"
DB_PASSWORD="development_password_123"
ADMIN_PASSWORD="admin123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    log_info "Docker version: $docker_version"
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose V2."
        exit 1
    fi
    
    compose_version=$(docker compose version | cut -d' ' -f4 | cut -d'v' -f2)
    log_info "Docker Compose version: $compose_version"
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    log_info "All prerequisites met!"
    echo ""
}

# Clone Frappe Docker repository
clone_frappe_docker() {
    log_info "Cloning Frappe Docker repository (ref: $FRAPPE_DOCKER_REF)..."
    
    if [ -d "frappe_docker" ]; then
        log_warn "frappe_docker directory already exists. Skipping clone."
    else
        git clone --depth 1 --branch "$FRAPPE_DOCKER_REF" https://github.com/frappe/frappe_docker.git
        log_info "Frappe Docker cloned successfully!"
    fi
    echo ""
}

# Prepare configuration files
prepare_config() {
    log_info "Preparing configuration files..."
    
    # Create apps.json in frappe_docker directory
    cp apps.json frappe_docker/apps.json
    log_info "apps.json copied to frappe_docker/"
    
    # Create .env file
    cat > frappe_docker/.env << EOF
ERPNEXT_VERSION=$ERPNEXT_VERSION
FRAPPE_BRANCH=$FRAPPE_BRANCH
FRAPPE_PATH=https://github.com/frappe/frappe
SITE_NAME=$SITE_NAME
SITES_RULE=Host(\`$SITE_NAME\`)
DB_PASSWORD=$DB_PASSWORD
ADMIN_PASSWORD=$ADMIN_PASSWORD
REDIS_CACHE=redis-cache:6379
REDIS_QUEUE=redis-queue:6379
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
GUNICORN_TIMEOUT=120
MIGRATE_SITES=true
EOF
    log_info ".env file created!"
    echo ""
}

# Build custom image
build_image() {
    log_info "Building custom ERPNext image (this may take 10-20 minutes)..."
    
    cd frappe_docker
    
    DOCKER_BUILDKIT=1 docker build \
        --file images/layered/Containerfile \
        --tag erp03-erpnext:dev \
        --build-arg FRAPPE_PATH=https://github.com/frappe/frappe \
        --build-arg FRAPPE_BRANCH=$FRAPPE_BRANCH \
        --secret id=apps_json,src=apps.json \
        .
    
    cd ..
    log_info "Image built successfully!"
    echo ""
}

# Start services
start_services() {
    log_info "Starting ERPNext services..."
    
    cd frappe_docker
    
    # Use the production compose architecture with necessary overrides
    docker compose -f compose.yaml \
        -f overrides/compose.mariadb.yaml \
        -f overrides/compose.redis.yaml \
        -f overrides/compose.noproxy.yaml \
        up -d
    
    cd ..
    log_info "Services started! Waiting for them to be ready..."
    
    # Wait for services to be healthy
    sleep 30
    
    log_info "Checking service status..."
    docker compose -f frappe_docker/compose.yaml \
        -f frappe_docker/overrides/compose.mariadb.yaml \
        -f frappe_docker/overrides/compose.redis.yaml \
        -f frappe_docker/overrides/compose.noproxy.yaml \
        ps
    
    echo ""
}

# Create site and install ERPNext
setup_site() {
    log_info "Creating ERPNext site..."
    
    # Wait for backend to be ready
    log_info "Waiting for backend service to be ready (up to 2 minutes)..."
    for i in {1..24}; do
        if docker compose -f frappe_docker/compose.yaml \
            -f frappe_docker/overrides/compose.mariadb.yaml \
            -f frappe_docker/overrides/compose.redis.yaml \
            -f frappe_docker/overrides/compose.noproxy.yaml \
            exec -T backend bench --version 2>/dev/null; then
            log_info "Backend is ready!"
            break
        fi
        if [ $i -eq 24 ]; then
            log_error "Backend did not become ready in time. Check logs with: docker compose logs backend"
            exit 1
        fi
        sleep 5
    done
    
    # Create new site
    log_info "Creating new site: $SITE_NAME..."
    docker compose -f frappe_docker/compose.yaml \
        -f frappe_docker/overrides/compose.mariadb.yaml \
        -f frappe_docker/overrides/compose.redis.yaml \
        -f frappe_docker/overrides/compose.noproxy.yaml \
        exec backend bench new-site $SITE_NAME \
        --mariadb-root-password $DB_PASSWORD \
        --admin-password $ADMIN_PASSWORD \
        --no-mariadb-socket || {
        log_warn "Site may already exist. Continuing..."
    }
    
    # Install ERPNext
    log_info "Installing ERPNext app..."
    docker compose -f frappe_docker/compose.yaml \
        -f frappe_docker/overrides/compose.mariadb.yaml \
        -f frappe_docker/overrides/compose.redis.yaml \
        -f frappe_docker/overrides/compose.noproxy.yaml \
        exec backend bench --site $SITE_NAME install-app erpnext || {
        log_warn "ERPNext may already be installed. Continuing..."
    }
    
    # Set as current site
    log_info "Setting $SITE_NAME as current site..."
    docker compose -f frappe_docker/compose.yaml \
        -f frappe_docker/overrides/compose.mariadb.yaml \
        -f frappe_docker/overrides/compose.redis.yaml \
        -f frappe_docker/overrides/compose.noproxy.yaml \
        exec backend bench use $SITE_NAME
    
    log_info "Site setup complete!"
    echo ""
}

# Add hosts entry
setup_hosts() {
    log_info "Setting up hosts file..."
    
    if ! grep -q "$SITE_NAME" /etc/hosts; then
        echo "127.0.0.1 $SITE_NAME" | sudo tee -a /etc/hosts > /dev/null
        log_info "Added $SITE_NAME to /etc/hosts"
    else
        log_warn "$SITE_NAME already exists in /etc/hosts"
    fi
    echo ""
}

# Display access information
show_access_info() {
    echo ""
    echo "=============================================="
    echo "ERPNext Development Environment Ready!"
    echo "=============================================="
    echo ""
    echo "Access URL: http://$SITE_NAME:8000"
    echo "Username:   Administrator"
    echo "Password:   $ADMIN_PASSWORD"
    echo ""
    echo "Useful commands:"
    echo "  - View logs:          docker compose -f frappe_docker/compose.yaml ... logs -f"
    echo "  - Stop services:      docker compose -f frappe_docker/compose.yaml ... down"
    echo "  - Restart services:   docker compose -f frappe_docker/compose.yaml ... restart"
    echo "  - Open bench console: docker compose exec backend bench --site $SITE_NAME console"
    echo ""
    echo "Next steps:"
    echo "  1. Open your browser and navigate to http://$SITE_NAME:8000"
    echo "  2. Login with the credentials above"
    echo "  3. Complete the setup wizard"
    echo "  4. Start developing!"
    echo ""
}

# Main execution
main() {
    check_prerequisites
    clone_frappe_docker
    prepare_config
    
    # Ask before building (time-consuming step)
    read -p "Do you want to build the Docker image now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_image
        start_services
        setup_site
        setup_hosts
        show_access_info
    else
        echo ""
        log_info "Image build skipped."
        echo ""
        echo "To build and start the environment later, run:"
        echo "  ./quickstart.sh --resume"
        echo ""
        echo "Or manually:"
        echo "  1. cd frappe_docker"
        echo "  2. DOCKER_BUILDKIT=1 docker build -f images/layered/Containerfile -t erp03-erpnext:dev --build-arg FRAPPE_BRANCH=version-16 --secret id=apps_json,src=apps.json ."
        echo "  3. docker compose -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.noproxy.yaml up -d"
        echo ""
    fi
}

# Handle resume flag
if [ "$1" == "--resume" ]; then
    check_prerequisites
    prepare_config
    build_image
    start_services
    setup_site
    setup_hosts
    show_access_info
else
    main
fi
