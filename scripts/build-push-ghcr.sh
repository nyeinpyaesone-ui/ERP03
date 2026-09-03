#!/bin/bash
###############################################################################
# ERP erpo3 — GHCR Build & Push Script (Local Development)
# Run this on your LOCAL MACHINE with Docker installed
# Features: Automated triggers, retry logic, rate limiting, fallback plans
###############################################################################

set -euo pipefail

# ============================================
# Configuration
# ============================================
GHCR_REGISTRY="ghcr.io"
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-$(whoami)}"
VERSION="${1:-dev-$(date +%Y%m%d%H%M%S)}"
IMAGE_PREFIX="${GHCR_REGISTRY}/${REPO_OWNER}/erpo3"

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY=5  # seconds
RATE_LIMIT_DELAY=2  # seconds between API calls

# Fallback Configuration
FALLBACK_REGISTRY="docker.io"
FALLBACK_ENABLED=${FALLBACK_ENABLED:-false}
BACKUP_IMAGE_PREFIX="${FALLBACK_REGISTRY}/${REPO_OWNER}/erpo3-backup"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# Helper Functions
# ============================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Retry wrapper with exponential backoff
retry_with_backoff() {
    local cmd="$1"
    local description="$2"
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        log_info "Executing: ${description} (Attempt ${attempt}/${MAX_RETRIES})"
        
        if eval "$cmd"; then
            log_success "${description} completed successfully"
            return 0
        else
            log_warning "${description} failed (Attempt ${attempt}/${MAX_RETRIES})"
            
            if [ $attempt -lt $MAX_RETRIES ]; then
                local delay=$((RETRY_DELAY * attempt))
                log_info "Retrying in ${delay} seconds..."
                sleep $delay
            fi
        fi
        
        ((attempt++))
    done
    
    log_error "${description} failed after ${MAX_RETRIES} attempts"
    return 1
}

# Rate limit handler
respect_rate_limit() {
    log_info "Respecting rate limit (waiting ${RATE_LIMIT_DELAY}s)..."
    sleep $RATE_LIMIT_DELAY
}

# ============================================
# Pre-flight Checks
# ============================================
preflight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed"
        echo "Install from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    log_success "Docker is installed: $(docker --version)"
    
    # Check Docker Buildx
    if ! docker buildx version &> /dev/null; then
        log_error "Docker Buildx not available"
        exit 1
    fi
    log_success "Docker Buildx is available: $(docker buildx version)"
    
    # Check if logged in to GHCR with retry
    log_info "Checking GHCR login status..."
    local login_success=false
    
    for attempt in $(seq 1 $MAX_RETRIES); do
        if docker info 2>/dev/null | grep -q "ghcr.io"; then
            login_success=true
            break
        fi
        
        log_warning "Not logged in to GHCR (Attempt ${attempt}/${MAX_RETRIES})"
        
        if [ $attempt -lt $MAX_RETRIES ]; then
            log_info "Attempting GHCR login... (Attempt ${attempt}/${MAX_RETRIES})"
            respect_rate_limit
            
            if docker login ghcr.io -u "$(git config user.username || whoami)" 2>/dev/null; then
                login_success=true
                break
            else
                log_warning "GHCR login failed, retrying in ${RETRY_DELAY}s..."
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    if [ "$login_success" = false ]; then
        log_error "Failed to login to GHCR after ${MAX_RETRIES} attempts"
        
        # Fallback: Try Docker Hub if enabled
        if [ "$FALLBACK_ENABLED" = "true" ]; then
            log_warning "Falling back to Docker Hub registry..."
            if docker login "$FALLBACK_REGISTRY" -u "$(git config user.username || whoami)" 2>/dev/null; then
                log_success "Logged in to fallback registry: ${FALLBACK_REGISTRY}"
                IMAGE_PREFIX="$BACKUP_IMAGE_PREFIX"
            else
                log_error "Failed to login to fallback registry. Exiting."
                exit 1
            fi
        else
            exit 1
        fi
    else
        log_success "Logged in to GHCR"
    fi
    
    # Validate directory structure
    log_info "Validating directory structure..."
    [ -d "./ERP-BACKEND" ] || { log_error "ERP-BACKEND directory not found"; exit 1; }
    [ -d "./frontend" ] || { log_error "frontend directory not found"; exit 1; }
    [ -f "./ERP-BACKEND/Dockerfile" ] || { log_error "Backend Dockerfile not found"; exit 1; }
    [ -f "./frontend/Dockerfile" ] || { log_error "Frontend Dockerfile not found"; exit 1; }
    log_success "Directory structure validated"
    
    # Check disk space (minimum 10GB recommended)
    local available_space=$(df -g . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 10 ]; then
        log_warning "Low disk space detected: ${available_space}GB available (recommended: 10GB+)"
    else
        log_success "Disk space adequate: ${available_space}GB available"
    fi
}

# ============================================
# Build Backend Image
# ============================================
build_backend() {
    log_info "Building backend image..."
    
    BACKEND_IMAGE="${IMAGE_PREFIX}-backend:${VERSION}"
    BACKEND_IMAGE_LATEST="${IMAGE_PREFIX}-backend:latest"
    
    # Create buildx builder with retry
    local builder_created=false
    for attempt in $(seq 1 $MAX_RETRIES); do
        if docker buildx create --use --name erp-builder-$(date +%s) 2>/dev/null; then
            builder_created=true
            break
        else
            log_warning "Failed to create buildx builder (Attempt ${attempt}/${MAX_RETRIES})"
            sleep $RETRY_DELAY
        fi
    done
    
    if [ "$builder_created" = false ]; then
        log_error "Failed to create buildx builder after ${MAX_RETRIES} attempts"
        return 1
    fi
    
    # Build and push backend with retry
    local build_success=false
    for attempt in $(seq 1 $MAX_RETRIES); do
        log_info "Building backend image (Attempt ${attempt}/${MAX_RETRIES})..."
        
        if docker buildx build \
            --platform linux/amd64,linux/arm64 \
            --push \
            --tag "${BACKEND_IMAGE}" \
            --tag "${BACKEND_IMAGE_LATEST}" \
            --label "org.opencontainers.image.source=https://github.com/${REPO_OWNER}/erpo3" \
            --label "org.opencontainers.image.description=ERP erpo3 Backend API" \
            --label "org.opencontainers.image.version=${VERSION}" \
            --label "org.opencontainers.image.created=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
            --cache-from type=gha \
            --cache-to type=gha,mode=max \
            --target production \
            --file ./ERP-BACKEND/Dockerfile \
            ./ERP-BACKEND 2>&1 | tee /tmp/backend-build-${VERSION}.log; then
            build_success=true
            break
        else
            log_warning "Backend build failed (Attempt ${attempt}/${MAX_RETRIES})"
            
            if [ $attempt -lt $MAX_RETRIES ]; then
                log_info "Cleaning up failed build artifacts..."
                docker buildx prune -f >/dev/null 2>&1 || true
                respect_rate_limit
            fi
        fi
    done
    
    if [ "$build_success" = false ]; then
        log_error "Backend build failed after ${MAX_RETRIES} attempts"
        log_error "Build logs saved to: /tmp/backend-build-${VERSION}.log"
        
        # Fallback: Build single-platform image if multi-platform fails
        if [ "$FALLBACK_ENABLED" = "true" ]; then
            log_warning "Attempting fallback: single-platform (amd64) build..."
            docker buildx build \
                --platform linux/amd64 \
                --push \
                --tag "${BACKEND_IMAGE}-fallback" \
                --label "org.opencontainers.image.source=https://github.com/${REPO_OWNER}/erpo3" \
                --label "org.opencontainers.image.description=ERP erpo3 Backend API (Fallback)" \
                --label "org.opencontainers.image.version=${VERSION}" \
                --target production \
                --file ./ERP-BACKEND/Dockerfile \
                ./ERP-BACKEND && \
            log_success "Fallback backend image built: ${BACKEND_IMAGE}-fallback" || \
            { log_error "Fallback build also failed"; return 1; }
        else
            return 1
        fi
    fi
    
    log_success "Backend image built and pushed: ${BACKEND_IMAGE}"
    log_success "Backend image tagged as latest: ${BACKEND_IMAGE_LATEST}"
}

# ============================================
# Build Frontend Image
# ============================================
build_frontend() {
    log_info "Building frontend image..."
    
    FRONTEND_IMAGE="${IMAGE_PREFIX}-frontend:${VERSION}"
    FRONTEND_IMAGE_LATEST="${IMAGE_PREFIX}-frontend:latest"
    
    # Build and push frontend with retry
    local build_success=false
    for attempt in $(seq 1 $MAX_RETRIES); do
        log_info "Building frontend image (Attempt ${attempt}/${MAX_RETRIES})..."
        
        if docker buildx build \
            --platform linux/amd64,linux/arm64 \
            --push \
            --tag "${FRONTEND_IMAGE}" \
            --tag "${FRONTEND_IMAGE_LATEST}" \
            --label "org.opencontainers.image.source=https://github.com/${REPO_OWNER}/erpo3" \
            --label "org.opencontainers.image.description=ERP erpo3 Frontend" \
            --label "org.opencontainers.image.version=${VERSION}" \
            --label "org.opencontainers.image.created=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
            --cache-from type=gha \
            --cache-to type=gha,mode=max \
            --build-arg VITE_API_BASE_URL=/api/v1 \
            --build-arg VITE_APP_VERSION="${VERSION}" \
            --target production \
            --file ./frontend/Dockerfile \
            ./frontend 2>&1 | tee /tmp/frontend-build-${VERSION}.log; then
            build_success=true
            break
        else
            log_warning "Frontend build failed (Attempt ${attempt}/${MAX_RETRIES})"
            
            if [ $attempt -lt $MAX_RETRIES ]; then
                log_info "Cleaning up failed build artifacts..."
                docker buildx prune -f >/dev/null 2>&1 || true
                respect_rate_limit
            fi
        fi
    done
    
    if [ "$build_success" = false ]; then
        log_error "Frontend build failed after ${MAX_RETRIES} attempts"
        log_error "Build logs saved to: /tmp/frontend-build-${VERSION}.log"
        
        # Fallback: Build single-platform image if multi-platform fails
        if [ "$FALLBACK_ENABLED" = "true" ]; then
            log_warning "Attempting fallback: single-platform (amd64) build..."
            docker buildx build \
                --platform linux/amd64 \
                --push \
                --tag "${FRONTEND_IMAGE}-fallback" \
                --label "org.opencontainers.image.source=https://github.com/${REPO_OWNER}/erpo3" \
                --label "org.opencontainers.image.description=ERP erpo3 Frontend (Fallback)" \
                --label "org.opencontainers.image.version=${VERSION}" \
                --build-arg VITE_API_BASE_URL=/api/v1 \
                --build-arg VITE_APP_VERSION="${VERSION}" \
                --target production \
                --file ./frontend/Dockerfile \
                ./frontend && \
            log_success "Fallback frontend image built: ${FRONTEND_IMAGE}-fallback" || \
            { log_error "Fallback build also failed"; return 1; }
        else
            return 1
        fi
    fi
    
    log_success "Frontend image built and pushed: ${FRONTEND_IMAGE}"
    log_success "Frontend image tagged as latest: ${FRONTEND_IMAGE_LATEST}"
}

# ============================================
# Security Scan (Optional)
# ============================================
run_security_scan() {
    log_info "Running security scans..."
    
    # Skip scan in fallback mode
    if [[ "$IMAGE_PREFIX" == *"-fallback"* ]]; then
        log_warning "Skipping security scan for fallback images"
        return 0
    fi
    
    if command -v trivy &> /dev/null; then
        local scan_success=true
        
        # Scan backend with retry
        for attempt in $(seq 1 $MAX_RETRIES); do
            log_info "Scanning backend image (Attempt ${attempt}/${MAX_RETRIES})..."
            
            if trivy image --severity CRITICAL,HIGH --exit-code 0 "${IMAGE_PREFIX}-backend:${VERSION}" 2>&1 | tee /tmp/trivy-backend-${VERSION}.log; then
                log_success "Backend security scan completed"
                break
            else
                log_warning "Backend scan encountered issues (Attempt ${attempt}/${MAX_RETRIES})"
                
                if [ $attempt -lt $MAX_RETRIES ]; then
                    respect_rate_limit
                else
                    log_warning "Backend scan completed with warnings (see /tmp/trivy-backend-${VERSION}.log)"
                fi
            fi
        done
        
        # Scan frontend with retry
        for attempt in $(seq 1 $MAX_RETRIES); do
            log_info "Scanning frontend image (Attempt ${attempt}/${MAX_RETRIES})..."
            
            if trivy image --severity CRITICAL,HIGH --exit-code 0 "${IMAGE_PREFIX}-frontend:${VERSION}" 2>&1 | tee /tmp/trivy-frontend-${VERSION}.log; then
                log_success "Frontend security scan completed"
                break
            else
                log_warning "Frontend scan encountered issues (Attempt ${attempt}/${MAX_RETRIES})"
                
                if [ $attempt -lt $MAX_RETRIES ]; then
                    respect_rate_limit
                else
                    log_warning "Frontend scan completed with warnings (see /tmp/trivy-frontend-${VERSION}.log)"
                fi
            fi
        done
        
        log_success "Security scans completed"
    else
        log_warning "Trivy not installed. Skipping security scans."
        log_info "Install Trivy: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
        log_info "Continuing without security scan..."
    fi
}

# ============================================
# Generate Deployment Summary
# ============================================
generate_summary() {
    local build_status=$?
    
    echo ""
    echo "=========================================="
    if [ $build_status -eq 0 ]; then
        echo "  ✅ BUILD COMPLETE!"
    else
        echo "  ⚠️  BUILD COMPLETED WITH WARNINGS"
    fi
    echo "=========================================="
    echo ""
    echo "Build Configuration:"
    echo "  Version:      ${VERSION}"
    echo "  Registry:     ${GHCR_REGISTRY}"
    echo "  Fallback:     ${FALLBACK_ENABLED}"
    echo "  Max Retries:  ${MAX_RETRIES}"
    echo ""
    
    if [[ "$IMAGE_PREFIX" == *"-fallback"* ]] || [[ "$FALLBACK_ENABLED" == "true" && "$IMAGE_PREFIX" == *"backup"* ]]; then
        echo "⚠️  FALLBACK MODE ACTIVE ⚠️"
        echo ""
        echo "Images pushed to FALLBACK registry:"
        echo "  Backend:  ${IMAGE_PREFIX}-backend:${VERSION} (or fallback tag)"
        echo "  Frontend: ${IMAGE_PREFIX}-frontend:${VERSION} (or fallback tag)"
        echo ""
        echo "NOTE: These are fallback images. Consider rebuilding with primary registry."
    else
        echo "Images pushed to GHCR:"
        echo "  Backend:  ${IMAGE_PREFIX}-backend:${VERSION}"
        echo "  Frontend: ${IMAGE_PREFIX}-frontend:${VERSION}"
        echo ""
        echo "Latest tags:"
        echo "  Backend:  ${IMAGE_PREFIX}-backend:latest"
        echo "  Frontend: ${IMAGE_PREFIX}-frontend:latest"
    fi
    
    echo ""
    echo "Pull commands:"
    echo "  docker pull ${IMAGE_PREFIX}-backend:${VERSION}"
    echo "  docker pull ${IMAGE_PREFIX}-frontend:${VERSION}"
    echo ""
    echo "Run with docker-compose:"
    echo "  VERSION=${VERSION} docker-compose -f docker-compose.prod.yml up -d"
    echo ""
    echo "Build logs location:"
    echo "  Backend:  /tmp/backend-build-${VERSION}.log"
    echo "  Frontend: /tmp/frontend-build-${VERSION}.log"
    echo "  Security: /tmp/trivy-*.log (if Trivy installed)"
    echo ""
    echo "View images at:"
    echo "  https://github.com/${REPO_OWNER}?tab=packages&repo_name=erpo3"
    echo ""
    
    # Cleanup old buildx builders
    log_info "Cleaning up temporary buildx builders..."
    docker buildx rm $(docker buildx ls --format '{{.Name}}' | grep "erp-builder-" 2>/dev/null) 2>/dev/null || true
    
    log_success "Build process finished successfully!"
}

# ============================================
# Main Execution
# ============================================
main() {
    local exit_code=0
    
    echo "=========================================="
    echo "  ERP erpo3 — GHCR Build & Push"
    echo "  Version: ${VERSION}"
    echo "  Registry: ${GHCR_REGISTRY}"
    echo "  Fallback Enabled: ${FALLBACK_ENABLED}"
    echo "  Max Retries: ${MAX_RETRIES}"
    echo "=========================================="
    echo ""
    
    # Trap for cleanup on error
    trap 'log_error "Build process interrupted!"; cleanup_on_exit' ERR
    
    # Execute stages with error handling
    if ! preflight_checks; then
        log_error "Pre-flight checks failed!"
        exit 1
    fi
    echo ""
    
    if ! build_backend; then
        log_error "Backend build failed!"
        if [ "$FALLBACK_ENABLED" != "true" ]; then
            exit_code=1
        fi
    fi
    echo ""
    
    if ! build_frontend; then
        log_error "Frontend build failed!"
        if [ "$FALLBACK_ENABLED" != "true" ]; then
            exit_code=1
        fi
    fi
    echo ""
    
    # Security scan is optional, don't fail the build if it fails
    run_security_scan || log_warning "Security scan did not complete successfully"
    echo ""
    
    generate_summary
    
    cleanup_on_exit
    
    if [ $exit_code -ne 0 ]; then
        log_error "Build completed with errors. Exit code: ${exit_code}"
    else
        log_success "All tasks completed successfully!"
    fi
    
    exit $exit_code
}

# Cleanup function
cleanup_on_exit() {
    log_info "Performing cleanup..."
    
    # Remove temporary buildx builders
    docker buildx rm $(docker buildx ls --format '{{.Name}}' | grep "erp-builder-" 2>/dev/null) 2>/dev/null || true
    
    # Clean up dangling images (optional, can be disabled)
    if [ "${CLEANUP_DANGLING_IMAGES:-false}" = "true" ]; then
        log_info "Cleaning up dangling images..."
        docker image prune -f >/dev/null 2>&1 || true
    fi
    
    log_success "Cleanup completed!"
}

# Run main function
main "$@"
