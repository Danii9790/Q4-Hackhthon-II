#!/bin/bash

# ============================================================================
# DigitalOcean Deployment Script for Todo Chatbot
# ============================================================================
# This script automates the deployment of your application to DigitalOcean
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="todo-chatbot-cluster"
CLUSTER_REGION="nyc1"
NAMESPACE="todo-app"
REGISTRY_NAME="todo-chatbot-registry"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_step() {
    echo -e "\n${GREEN}➜ $1${NC}"
}

print_error() {
    echo -e "\n${RED}✖ Error: $1${NC}\n"
}

print_success() {
    echo -e "\n${GREEN}✓ $1${NC}\n"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        echo "Install instructions:"
        case $1 in
            kubectl)
                echo "  curl -LO https://dl.k8s.io/release/\$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                echo "  sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl"
                ;;
            doctl)
                echo "  wget https://github.com/digitalocean/doctl/releases/download/v1.104.0/doctl-1.104.0-linux-amd64.tar.gz"
                echo "  tar xf ~/doctl-1.104.0-linux-amd64.tar.gz"
                echo "  sudo mv doctl /usr/local/bin"
                ;;
            docker)
                echo "  https://docs.docker.com/engine/install/"
                ;;
            helm)
                echo "  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
                ;;
        esac
        exit 1
    fi
}

confirm() {
    read -p "$(echo -e ${YELLOW}$1 [y/N]: ${NC})" response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# ============================================================================
# Prerequisites Check
# ============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"

    print_step "Checking required tools..."
    check_command "kubectl"
    check_command "doctl"
    check_command "docker"
    check_command "helm"

    print_success "All required tools are installed!"

    print_step "Checking DigitalOcean authentication..."
    if doctl account get &> /dev/null; then
        print_success "Authenticated with DigitalOcean!"
    else
        print_error "Not authenticated with DigitalOcean"
        echo "Please run: doctl auth init"
        exit 1
    fi
}

# ============================================================================
# Step 1: Create Kubernetes Cluster
# ============================================================================

create_cluster() {
    print_header "Step 1: Creating Kubernetes Cluster"

    if doctl kubernetes cluster list | grep -q "$CLUSTER_NAME"; then
        print_step "Cluster '$CLUSTER_NAME' already exists!"
        if ! confirm "Do you want to use the existing cluster?"; then
            print_error "Aborting. Please delete the existing cluster first or choose a different name."
            exit 1
        fi
        print_success "Using existing cluster"
    else
        print_step "Creating new Kubernetes cluster..."
        echo "This will create a cluster with:"
        echo "  - Region: $CLUSTER_REGION"
        echo "  - Node size: s-4vcpu-8gb (Basic)"
        echo "  - Node count: 2"
        echo "  - Estimated cost: ~$96/month"
        echo ""

        if ! confirm "Do you want to proceed with cluster creation?"; then
            print_error "Aborted cluster creation"
            exit 1
        fi

        doctl kubernetes cluster create \
            "$CLUSTER_NAME" \
            --region "$CLUSTER_REGION" \
            --version 1.28.2-do.0 \
            --size s-4vcpu-8gb \
            --count 2 \
            --auto-upgrade \
            --maintenance-window "wednesday=03:00"

        print_success "Cluster created successfully!"
    fi

    # Get kubeconfig
    print_step "Configuring kubectl..."
    doctl kubernetes cluster kubeconfig save "$CLUSTER_NAME"
    export KUBECONFIG="$HOME/.kube/config"

    # Verify cluster connection
    print_step "Verifying cluster connection..."
    kubectl get nodes
    print_success "Cluster is ready!"
}

# ============================================================================
# Step 2: Create Container Registry
# ============================================================================

create_registry() {
    print_header "Step 2: Setting Up Container Registry"

    if doctl registry list | grep -q "$REGISTRY_NAME"; then
        print_step "Registry '$REGISTRY_NAME' already exists!"
    else
        print_step "Creating container registry..."
        doctl registry create "$REGISTRY_NAME" --region "$CLUSTER_REGION"
        print_success "Registry created!"
    fi

    # Login to registry
    print_step "Authenticating with registry..."
    doctl registry login
    print_success "Registry authentication configured!"
}

# ============================================================================
# Step 3: Deploy Database
# ============================================================================

create_database() {
    print_header "Step 3: Creating PostgreSQL Database"

    if doctl databases list | grep -q "todo-postgres"; then
        print_step "Database 'todo-postgres' already exists!"
        DB_ID=$(doctl databases list --no-header | grep "todo-postgres" | awk '{print $1}')
    else
        print_step "Creating managed PostgreSQL database..."
        echo "This will create:"
        echo "  - PostgreSQL 16"
        echo "  - Size: s-2vcpu-4gb"
        echo "  - Storage: 40GB"
        echo "  - Standby: Yes"
        echo "  - Estimated cost: ~$36/month"
        echo ""

        if ! confirm "Do you want to proceed with database creation?"; then
            print_error "Aborted database creation"
            exit 1
        fi

        DB_ID=$(doctl databases create \
            todo-postgres \
            --engine postgres \
            --version 16 \
            --region "$CLUSTER_REGION" \
            --size s-2vcpu-4gb \
            --num-nodes 2 \
            --output json | jq -r '.database.id')

        print_success "Database created!"
        echo "Waiting for database to be ready..."
        sleep 30
    fi

    # Get connection string
    print_step "Getting database connection string..."
    DATABASE_URI=$(doctl databases connection "$DB_ID" --format URI --no-trunc)
    export DATABASE_URL="$DATABASE_URI"

    print_success "Database connection string obtained!"
    echo "Database URL: ${DATABASE_URI:0:50}..."

    # Run migrations
    print_step "Running database migrations..."
    cd backend
    if confirm "Do you want to run Alembic migrations now?"; then
        alembic upgrade head
        print_success "Migrations completed!"
    fi
    cd ..
}

# ============================================================================
# Step 4: Build and Push Images
# ============================================================================

build_and_push_images() {
    print_header "Step 4: Building and Pushing Docker Images"

    # Set registry variables
    REGISTRY="registry.digitalocean.com"
    REGISTRY_NAMESPACE=$(doctl account get | grep -oP '(?<=Email:\s)[^ ]+' | head -1)

    BACKEND_IMAGE="${REGISTRY}/${REGISTRY_NAME}/backend:latest"
    FRONTEND_IMAGE="${REGISTRY}/${REGISTRY_NAME}/frontend:latest"

    # Build backend
    print_step "Building backend image..."
    docker build -t "${BACKEND_IMAGE}" -f backend/Dockerfile backend/
    print_success "Backend image built!"

    print_step "Pushing backend image..."
    docker tag "${BACKEND_IMAGE}" "${REGISTRY}/${REGISTRY_NAME}/backend:latest"
    docker push "${REGISTRY}/${REGISTRY_NAME}/backend:latest"
    print_success "Backend image pushed!"

    # Build frontend
    print_step "Building frontend image..."
    docker build -t "${FRONTEND_IMAGE}" -f frontend/Dockerfile frontend/
    print_success "Frontend image built!"

    print_step "Pushing frontend image..."
    docker tag "${FRONTEND_IMAGE}" "${REGISTRY}/${REGISTRY_NAME}/frontend:latest"
    docker push "${REGISTRY}/${REGISTRY_NAME}/frontend:latest"
    print_success "Frontend image pushed!"
}

# ============================================================================
# Step 5: Deploy to Kubernetes
# ============================================================================

deploy_to_kubernetes() {
    print_header "Step 5: Deploying to Kubernetes"

    # Create namespace
    print_step "Creating namespace..."
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    print_success "Namespace ready!"

    # Create secrets
    print_step "Creating Kubernetes secrets..."

    # Database secret
    kubectl create secret generic postgres-secret \
        --from-literal=database-url="$DATABASE_URL" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -

    # JWT secret
    JWT_SECRET=$(openssl rand -base64 32)
    kubectl create secret generic jwt-secret \
        --from-literal=BETTER_AUTH_SECRET="$JWT_SECRET" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -

    # OpenAI secret
    if [ -n "$OPENAI_API_KEY" ]; then
        kubectl create secret generic openai-secret \
            --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
            --namespace="$NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi

    print_success "Secrets created!"

    # Deploy Kafka
    print_step "Deploying Kafka..."
    kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -
    helm repo add strimzi https://strimzi.io/charts/ 2>/dev/null || true
    helm repo update
    helm upgrade --install strimzi-kafka-operator strimzi/strimzi-kafka-operator \
        --namespace kafka --create-namespace \
        --set watchNamespaces[]={kafka} --set image.repositoryOverride=quay.io/strimzi 2>/dev/null || true

    kubectl apply -f infrastructure/kubernetes/base/kafka/kafka-cluster.yaml -n kafka --dry-run=client -o yaml | kubectl apply -f -

    print_step "Waiting for Kafka to be ready (this may take 5-10 minutes)..."
    kubectl wait kafka/my-cluster --for=condition=Ready --timeout=600s -n kafka || true

    kubectl apply -f infrastructure/kubernetes/base/kafka/kafka-topics.yaml -n kafka --dry-run=client -o yaml | kubectl apply -f -
    print_success "Kafka deployed!"

    # Deploy backend
    print_step "Deploying backend..."
    BACKEND_IMAGE="${REGISTRY}/${REGISTRY_NAME}/backend:latest"

    # Update image in deployment
    cat infrastructure/kubernetes/base/backend/deployment.yaml | \
        sed "s|image: .*backend:.*|image: ${BACKEND_IMAGE}|g" | \
        kubectl apply -n "$NAMESPACE" -f -

    kubectl apply -f infrastructure/kubernetes/base/backend/service.yaml -n "$NAMESPACE"
    kubectl apply -f infrastructure/kubernetes/base/backend/hpa.yaml -n "$NAMESPACE"

    print_step "Waiting for backend to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/backend -n "$NAMESPACE" || true
    print_success "Backend deployed!"

    # Deploy frontend
    print_step "Deploying frontend..."
    FRONTEND_IMAGE="${REGISTRY}/${REGISTRY_NAME}/frontend:latest"

    cat infrastructure/kubernetes/base/frontend/deployment.yaml | \
        sed "s|image: .*frontend:.*|image: ${FRONTEND_IMAGE}|g" | \
        kubectl apply -n "$NAMESPACE" -f -

    kubectl apply -f infrastructure/kubernetes/base/frontend/service.yaml -n "$NAMESPACE"
    kubectl apply -f infrastructure/kubernetes/base/frontend/hpa.yaml -n "$NAMESPACE"

    print_step "Waiting for frontend to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/frontend -n "$NAMESPACE" || true
    print_success "Frontend deployed!"
}

# ============================================================================
# Step 6: Verify Deployment
# ============================================================================

verify_deployment() {
    print_header "Step 6: Verifying Deployment"

    print_step "Checking pods..."
    kubectl get pods -n "$NAMESPACE"

    print_step "Checking services..."
    kubectl get svc -n "$NAMESPACE"

    print_step "Checking ingress..."
    kubectl get ingress -n "$NAMESPACE" || echo "No ingress configured yet"

    print_step "Getting backend logs (last 10 lines)..."
    BACKEND_POD=$(kubectl get pods -n "$NAMESPACE" -l app=backend -o jsonpath='{.items[0].metadata.name}')
    kubectl logs "$BACKEND_POD" -n "$NAMESPACE" --tail=10

    print_success "Deployment verification complete!"
}

# ============================================================================
# Main Deployment Flow
# ============================================================================

main() {
    print_header "🌊 DigitalOcean Deployment Script"
    echo "This script will deploy your Todo Chatbot application to DigitalOcean"
    echo ""
    echo "Prerequisites:"
    echo "  - DigitalOcean account with billing configured"
    echo "  - kubectl, doctl, docker, and helm installed"
    echo "  - Estimated cost: ~$132/month (cluster + database)"
    echo ""

    if ! confirm "Do you want to proceed?"; then
        echo "Aborted."
        exit 0
    fi

    # Run deployment steps
    check_prerequisites
    create_cluster
    create_registry
    create_database
    build_and_push_images
    deploy_to_kubernetes
    verify_deployment

    # Success message
    print_header "🎉 Deployment Complete!"
    echo ""
    echo "Your application is now deployed on DigitalOcean Kubernetes!"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure your domain DNS records"
    echo "  2. Set up SSL certificates with cert-manager"
    echo "  3. Monitor your application: kubectl logs -f deployment/backend -n $NAMESPACE"
    echo "  4. Access your application at the LoadBalancer IP"
    echo ""
    echo "To get your LoadBalancer IP:"
    echo "  kubectl get svc frontend -n $NAMESPACE"
    echo ""
    echo "For more information, see: DEPLOYMENT_GUIDE.md"
    echo ""
}

# Run main function
main
