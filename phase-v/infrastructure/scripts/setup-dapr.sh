#!/bin/bash
#
# setup-dapr.sh - Setup Dapr on Minikube for local development
#
# T129: This script initializes Dapr on Minikube and verifies installation
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DAPR_VERSION="${DAPR_VERSION:-1.10.0}"
DAPR_NAMESPACE="dapr-system"
APP_NAMESPACE="todo-app"

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is configured
check_kubectl() {
    log_info "Checking kubectl configuration..."
    if ! kubectl cluster-info &> /dev/null; then
        log_error "kubectl is not configured or cluster is not accessible"
        exit 1
    fi
    log_info "kubectl is configured"
}

# Check if Dapr CLI is installed
check_dapr_cli() {
    log_info "Checking if Dapr CLI is installed..."
    if ! command -v dapr &> /dev/null; then
        log_info "Installing Dapr CLI..."
        wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash -s ${DAPR_VERSION}
        log_info "Dapr CLI installed: $(dapr --version)"
    else
        log_info "Dapr CLI is already installed: $(dapr --version)"
    fi
}

# Initialize Dapr on Kubernetes
initialize_dapr() {
    log_info "Initializing Dapr ${DAPR_VERSION} on Kubernetes..."

    # Check if Dapr is already installed
    if kubectl get namespace -o name | grep -q "${DAPR_NAMESPACE}"; then
        log_warn "Dapr is already installed in ${DAPR_NAMESPACE} namespace"

        # Ask if user wants to reinstall
        read -p "Do you want to reinstall Dapr? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Uninstalling existing Dapr installation..."
            dapr uninstall --kubernetes
            log_info "Reinstalling Dapr..."
        else
            log_info "Skipping Dapr initialization"
            return
        fi
    fi

    # Initialize Dapr
    dapr init --kubernetes --version ${DAPR_VERSION} --wait

    log_info "Dapr initialized successfully"
}

# Verify Dapr installation
verify_dapr() {
    log_info "Verifying Dapr installation..."

    # Check Dapr pods
    log_info "Dapr pods in ${DAPR_NAMESPACE} namespace:"
    kubectl get pods -n ${DAPR_NAMESPACE}

    # Wait for Dapr sidecar injector to be ready
    log_info "Waiting for Dapr sidecar injector to be ready..."
    kubectl wait --for=condition=ready pod -l app=dapr-sidecar-injector -n ${DAPR_NAMESPACE} --timeout=300s

    # Check Dapr version
    log_info "Dapr version:"
    dapr version --kubernetes

    log_info "Dapr verification completed"
}

# Apply Dapr components
apply_dapr_components() {
    log_info "Applying Dapr components to ${APP_NAMESPACE} namespace..."

    # Create namespace if it doesn't exist
    kubectl create namespace ${APP_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

    # Apply Dapr components
    if [ -d "../kubernetes/base/dapr" ]; then
        kubectl apply -f ../kubernetes/base/dapr/
        log_info "Dapr components applied"
    else
        log_warn "Dapr components directory not found. Skipping component application."
    fi
}

# Display Dapr dashboard information
show_dashboard_info() {
    log_info "Dapr Dashboard:"
    echo "  To start the Dapr dashboard, run:"
    echo "    dapr dashboard --kubernetes"
    echo ""
    echo "  Dashboard will be available at: http://localhost:8080"
}

# Main execution
main() {
    log_info "Starting Dapr setup for Todo Chatbot..."

    check_kubectl
    check_dapr_cli
    initialize_dapr
    verify_dapr
    apply_dapr_components
    show_dashboard_info

    log_info "Dapr setup completed successfully!"
}

# Run main function
main "$@"
