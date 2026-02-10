#!/bin/bash
#
# setup-minikube.sh - Setup Minikube for local Todo Chatbot development
#
# T128: This script initializes Minikube, installs dependencies, and deploys the application
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MINIKUBE_DRIVER="${MINIKUBE_DRIVER:-docker}"  # Use docker by default
MINIKUBE_CPUS="${MINIKUBE_CPUS:-4}"
MINIKUBE_MEMORY="${MINIKUBE_MEMORY:-8192}"
MINIKUBE_DISK="${MINIKUBE_DISK:-50g}"
NAMESPACE="todo-app"

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

# Check if Minikube is installed
check_minikube() {
    log_info "Checking if Minikube is installed..."
    if ! command -v minikube &> /dev/null; then
        log_error "Minikube is not installed. Please install it from:"
        echo "  https://minikube.sigs.k8s.io/docs/start/"
        exit 1
    fi
    log_info "Minikube is installed: $(minikube version)"
}

# Start Minikube
start_minikube() {
    log_info "Starting Minikube with ${MINIKUBE_DRIVER} driver..."
    log_info "CPUs: ${MINIKUBE_CPUS}, Memory: ${MINIKUBE_MEMORY}MB, Disk: ${MINIKUBE_DISK}"

    if minikube status | grep -q "Running"; then
        log_warn "Minikube is already running. Skipping start."
    else
        minikube start \
            --driver="${MINIKUBE_DRIVER}" \
            --cpus="${MINIKUBE_CPUS}" \
            --memory="${MINIKUBE_MEMORY}" \
            --disk="${MINIKUBE_DISK}" \
            --container-runtime=docker
        log_info "Minikube started successfully"
    fi
}

# Enable Minikube addons
enable_addons() {
    log_info "Enabling Minikube addons..."

    minikube addons enable ingress
    minikube addons enable metrics-server
    minikube addons enable dashboard

    log_info "Addons enabled"
}

# Install Dapr CLI
install_dapr_cli() {
    log_info "Checking if Dapr CLI is installed..."
    if ! command -v dapr &> /dev/null; then
        log_info "Installing Dapr CLI..."
        wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash -s 1.10.0
        log_info "Dapr CLI installed"
    else
        log_info "Dapr CLI is already installed: $(dapr --version)"
    fi
}

# Initialize Dapr on Minikube
initialize_dapr() {
    log_info "Initializing Dapr on Minikube..."

    # Check if Dapr is already installed
    if kubectl get namespace -o name | grep -q "dapr-system"; then
        log_warn "Dapr is already installed. Skipping initialization."
    else
        dapr init --kubernetes --wait
        log_info "Dapr initialized"
    fi
}

# Build and push Docker images to Minikube
build_images() {
    log_info "Building Docker images..."

    # Set Docker environment to Minikube
    eval $(minikube docker-env)

    # Build backend image
    log_info "Building backend image..."
    cd ../../backend
    docker build -t todo-backend:dev .
    cd -

    # Build frontend image
    log_info "Building frontend image..."
    cd ../../frontend
    docker build -t todo-frontend:dev .
    cd -

    log_info "Docker images built successfully"
}

# Deploy application to Minikube
deploy_application() {
    log_info "Deploying application to Minikube..."

    # Apply base manifests
    kubectl apply -f ../kubernetes/base/namespace.yaml

    # Apply secrets
    kubectl apply -f ../kubernetes/base/secrets.yaml

    # Apply Dapr components
    kubectl apply -f ../kubernetes/base/dapr/

    # Apply Kafka manifests
    kubectl apply -f ../kubernetes/base/kafka/

    # Wait for Kafka to be ready
    log_info "Waiting for Kafka to be ready..."
    kubectl wait --for=condition=ready pod -l app=redpanda -n ${NAMESPACE} --timeout=300s || true

    # Apply ConfigMaps
    kubectl apply -f ../kubernetes/base/configmaps.yaml

    # Apply backend manifests
    kubectl apply -f ../kubernetes/base/backend/

    # Apply frontend manifests
    kubectl apply -f ../kubernetes/base/frontend/

    log_info "Application deployed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check pods
    log_info "Pods in ${NAMESPACE} namespace:"
    kubectl get pods -n ${NAMESPACE}

    # Check services
    log_info "Services in ${NAMESPACE} namespace:"
    kubectl get services -n ${NAMESPACE}

    # Check ingress
    log_info "Ingress resources:"
    kubectl get ingress -n ${NAMESPACE}

    # Get Minikube IP
    MINIKUBE_IP=$(minikube ip)
    log_info "Minikube IP: ${MINIKUBE_IP}"

    # Display access information
    log_info "Application will be available at:"
    echo "  Frontend: http://${MINIKUBE_IP}"
    echo "  Backend API: http://${MINIKUBE_IP}/api"
    echo "  Minikube Dashboard: Run 'minikube dashboard'"
}

# Main execution
main() {
    log_info "Starting Minikube setup for Todo Chatbot..."

    check_minikube
    start_minikube
    enable_addons
    install_dapr_cli
    initialize_dapr
    build_images
    deploy_application
    verify_deployment

    log_info "Minikube setup completed successfully!"
    log_info "To access the application:"
    echo "  1. Run: minikube tunnel (in a separate terminal for ingress)"
    echo "  2. Visit: http://todo.local (add to /etc/hosts: $(minikube ip) todo.local)"
    echo "  3. Or run: minikube dashboard"
}

# Run main function
main "$@"
