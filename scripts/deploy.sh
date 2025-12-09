#!/bin/bash

##############################################################################
# TabWrap API Deployment Script
#
# Automates deployment of TabWrap API updates to production server.
# Handles git updates, dependency installation, and service restart.
#
# Usage:
#   ./scripts/deploy.sh              # Deploy latest from main branch
#   ./scripts/deploy.sh v1.3.0       # Deploy specific version tag
#   ./scripts/deploy.sh main         # Explicitly deploy main branch
#
# Prerequisites:
#   - Must be run on the production server (aegis VPS)
#   - Requires sudo access for systemd service management
#   - Poetry must be installed and in PATH
##############################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/tabwrap-api"
SERVICE_NAME="tabwrap-api"
HEALTH_ENDPOINT="http://127.0.0.1:8000/api/health"

# Parse arguments
VERSION="${1:-main}"

##############################################################################
# Helper Functions
##############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
    echo ""
}

##############################################################################
# Main Deployment Steps
##############################################################################

print_header "TabWrap API Deployment"

# Verify we're in the deployment directory
if [ ! -d "$DEPLOY_DIR" ]; then
    log_error "Deployment directory $DEPLOY_DIR does not exist"
    exit 1
fi

cd "$DEPLOY_DIR"
log_info "Changed to deployment directory: $DEPLOY_DIR"

# Step 1: Fetch latest code
print_header "Step 1/5: Fetching latest code from GitHub"
log_info "Running: git fetch origin"
git fetch origin

# Step 2: Checkout specified version
print_header "Step 2/5: Checking out version: $VERSION"

if git rev-parse "$VERSION" >/dev/null 2>&1; then
    log_info "Checking out: $VERSION"
    git checkout "$VERSION"

    if [ "$VERSION" = "main" ]; then
        log_info "Pulling latest changes from main"
        git pull origin main
    fi
else
    log_error "Version/branch '$VERSION' does not exist"
    log_info "Available tags:"
    git tag -l | tail -10
    exit 1
fi

CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)
log_success "Now at: $CURRENT_VERSION"

# Step 3: Install dependencies
print_header "Step 3/5: Installing dependencies with Poetry"

# Ensure Poetry is in PATH
export PATH="$HOME/.local/bin:$PATH"

if ! command -v poetry &> /dev/null; then
    log_error "Poetry not found in PATH"
    log_info "Please install Poetry: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

log_info "Poetry version: $(poetry --version)"
log_info "Running: poetry install --extras api --without dev"

poetry config virtualenvs.in-project true
poetry install --extras api --without dev

log_success "Dependencies installed"

# Step 4: Restart systemd service
print_header "Step 4/5: Restarting systemd service"

log_info "Stopping service: $SERVICE_NAME"
sudo systemctl stop "$SERVICE_NAME" || true

log_info "Starting service: $SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# Wait for service to start
log_info "Waiting for service to start..."
sleep 3

# Check service status
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "Service $SERVICE_NAME is running"
else
    log_error "Service $SERVICE_NAME failed to start"
    log_error "Check logs with: sudo journalctl -xeu $SERVICE_NAME"
    exit 1
fi

# Step 5: Verify deployment
print_header "Step 5/5: Verifying deployment"

log_info "Checking health endpoint: $HEALTH_ENDPOINT"

# Try health check up to 3 times with 2 second delays
for i in {1..3}; do
    if curl -sf "$HEALTH_ENDPOINT" > /dev/null; then
        HEALTH_DATA=$(curl -s "$HEALTH_ENDPOINT")
        log_success "API is healthy!"
        log_info "Health check response: $HEALTH_DATA"
        break
    else
        if [ $i -eq 3 ]; then
            log_error "Health check failed after 3 attempts"
            log_warning "Service may still be starting up. Check manually with:"
            log_warning "  curl $HEALTH_ENDPOINT"
            exit 1
        fi
        log_warning "Health check attempt $i/3 failed, retrying..."
        sleep 2
    fi
done

# Show service status
log_info "Service status:"
sudo systemctl status "$SERVICE_NAME" --no-pager --lines=10

# Final summary
print_header "Deployment Summary"
echo "  Version deployed: $CURRENT_VERSION"
echo "  Service status:   $(sudo systemctl is-active $SERVICE_NAME)"
echo "  Health endpoint:  $HEALTH_ENDPOINT"
echo ""
log_success "Deployment completed successfully!"

# Show resource usage
log_info "Resource usage:"
sudo systemctl show "$SERVICE_NAME" --property=MemoryCurrent --property=TasksCurrent | \
    sed 's/MemoryCurrent=/  Memory: /; s/$/MB/; s/TasksCurrent=/  Tasks:  /'

echo ""
log_info "View logs with: sudo journalctl -fu $SERVICE_NAME"
