# Quick Start Guide: Phase V - Advanced Cloud Deployment

**Last Updated**: 2026-02-10
**Target Audience**: Developers, DevOps Engineers

---

## Overview

This guide covers:
1. **Local Development**: Docker Compose setup for full stack (frontend, backend, database, Kafka)
2. **Minikube Deployment**: Local Kubernetes cluster with Dapr
3. **Production Deployment**: DigitalOcean Kubernetes (DOKS) with monitoring

---

## Prerequisites

### Required Tools
- **Docker**: 20.10+ (for local development)
- **Minikube**: 1.30+ (for local Kubernetes)
- **kubectl**: 1.28+ (Kubernetes CLI)
- **Helm**: 3.12+ (Kubernetes package manager)
- **Python**: 3.12+ (backend development)
- **Node.js**: 20+ (frontend development)
- **Git**: For cloning the repository

### Optional Tools
- **Dapr CLI**: 1.14+ (for local Dapr development)
- **GitHub CLI**: For CI/CD setup

### Account Requirements
- **Neon Database**: Free account (https://neon.tech)
- **Redpanda Cloud**: Free account (https://redpanda.com/cloud) - for production Kafka
- **DigitalOcean**: Account with $200 free credit (https://digitalocean.com)
- **GitHub Account**: For CI/CD

---

## Part 1: Local Development with Docker Compose

### 1.1 Clone Repository

```bash
git clone https://github.com/your-org/hackathon-ii.git
cd hackathon-ii/phase-v
```

### 1.2 Configure Environment Variables

**Backend `.env`**:
```bash
cd backend
cp .env.example .env
```

Edit `.env`:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET=your-secret-key-here

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-key

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000

# Kafka (local Redpanda)
KAFKA_BROKERS=localhost:9092

# Dapr (local)
DAPR_HTTP_ENDPOINT=http://localhost:3500
DAPR_GRPC_ENDPOINT=localhost:50001
```

**Frontend `.env.local`**:
```bash
cd frontend
cp .env.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 1.3 Start Services with Docker Compose

```bash
# From phase-v root
docker-compose up -d
```

This starts:
- **PostgreSQL**: Port 5432
- **Redpanda (Kafka)**: Ports 9092 (Kafka), 8081 (Schema Registry)
- **Backend**: Port 8000
- **Frontend**: Port 3000

### 1.4 Run Database Migrations

```bash
cd backend
source venv/bin/activate  # or activate your virtual environment
alembic upgrade head
```

### 1.5 Verify Services

**Backend Health Check**:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-10T12:00:00Z"
}
```

**Frontend**:
Open browser to http://localhost:3000

**Kafka Topics** (verify Redpanda is running):
```bash
docker exec -it redpanda rpk topic list
```

Expected output:
```
NAME                    PARTITIONS  REPLICAS
task-events             1           1
reminders               1           1
task-updates            1           1
```

### 1.6 Stop Services

```bash
docker-compose down
```

---

## Part 2: Local Minikube Deployment with Dapr

### 2.1 Quick Setup with Automated Script

**T130**: The fastest way to get started on Minikube is using the automated setup script:

```bash
cd infrastructure/scripts
./setup-minikube.sh
```

This script will:
1. Check if Minikube is installed and start it
2. Enable required addons (ingress, metrics-server, dashboard)
3. Install and initialize Dapr
4. Build and deploy Docker images to Minikube
5. Deploy all Kubernetes manifests
6. Verify deployment and display access information

**Prerequisites**:
- Minikube installed
- kubectl configured
- Docker running
- Sufficient system resources (4+ CPUs, 8+ GB RAM)

### 2.2 Manual Setup (Alternative)

If you prefer manual setup or need to customize the deployment:

#### 2.2.1 Start Minikube

```bash
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=50gb \
  --driver=docker
```

Verify:
```bash
kubectl get nodes
```

Expected output:
```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   1m    v1.28.x
```

#### 2.2.2 Enable Ingress and Registry

```bash
minikube addons enable ingress
minikube addons enable registry
minikube addons enable metrics-server
```

#### 2.2.3 Install Dapr on Minikube

```bash
# Option 1: Use setup script
cd infrastructure/scripts
./setup-dapr.sh

# Option 2: Manual installation
dapr init -k

# Verify Dapr is installed
kubectl get pods -n dapr-system
```

Expected output:
```
NAME                                     READY   STATUS    RESTARTS   AGE
dapr-dashboard-7b5f8d8b6c-xxx            1/1     Running   0          2m
dapr-operator-5d8f7d9b4d-xxx              1/1     Running   0          2m
dapr-placement-server-7c8d9d8b5c-xxx      1/1     Running   0          2m
dapr-sidecar-injector-6d7f8d9b5d-xxx      1/1     Running   0          2m
dapr-sentry-8c9d9d8b5d-xxx                1/1     Running   0          2m
```

#### 2.2.4 Deploy Application

```bash
# Apply namespace and base manifests
kubectl apply -f infrastructure/kubernetes/base/namespace.yaml
kubectl apply -f infrastructure/kubernetes/base/secrets.yaml
kubectl apply -f infrastructure/kubernetes/base/configmaps.yaml

# Apply Dapr components
kubectl apply -f infrastructure/kubernetes/base/dapr/

# Apply Kafka (Redpanda)
kubectl apply -f infrastructure/kubernetes/base/kafka/

# Wait for Kafka to be ready
kubectl wait --for=condition=ready pod -l app=redpanda -n todo-app --timeout=300s

# Apply backend manifests
kubectl apply -f infrastructure/kubernetes/base/backend/

# Apply frontend manifests
kubectl apply -f infrastructure/kubernetes/base/frontend/
```

### 2.3 Verify Deployment

**Run infrastructure validation tests**:

```bash
cd infrastructure/tests
./test_minikube.sh
```

This test will verify:
- Minikube is running
- Namespace exists
- Dapr is installed
- Kafka is running
- Backend and frontend pods are ready
- Services and ingress are configured
- HPA is configured

**Manual verification**:

```bash
# Check pods
kubectl get pods -n todo-app

# Check services
kubectl get svc -n todo-app

# Check ingress
kubectl get ingress -n todo-app
```

### 2.4 Run End-to-End Tests

**T109**: Verify the application works end-to-end:

```bash
cd infrastructure/tests
./test_local_e2e.sh
```

This test will:
1. Check backend accessibility
2. Create a test user
3. Login and get JWT token
4. Create a test task
5. Verify task was created
6. Check for Kafka events
7. Complete the task
8. Verify audit trail
9. Clean up test data

### 2.5 Access Application

```bash
# Option 1: Use Minikube tunnel (recommended)
minikube tunnel
# Then visit: http://todo.local (add to /etc/hosts: $(minikube ip) todo.local)

# Option 2: Get ingress URL
minikube service frontend-service --namespace todo-app --url

# Option 3: Use Minikube dashboard
minikube dashboard
```

### 2.6 Troubleshooting Minikube Deployment

**Issue: Pods not starting**
```bash
# Check pod logs
kubectl logs -n todo-app <pod-name>

# Check pod events
kubectl describe pod -n todo-app <pod-name>

# Check Dapr sidecar logs
kubectl logs -n todo-app <pod-name> -c daprd
```

**Issue: Ingress not working**
```bash
# Verify ingress controller is running
kubectl get pods -n ingress-nginx

# Check ingress logs
kubectl logs -n ingress-nginx <ingress-pod>
```

**Issue: Kafka connection errors**
```bash
# Check Kafka pod status
kubectl get pods -n todo-app -l app=redpanda

# Port forward to Kafka locally
kubectl port-forward -n todo-app svc/kafka-service 9092:9092
```

### 2.7 Clean Up

```bash
# Delete all resources in namespace
kubectl delete namespace todo-app

# Or delete specific resources
kubectl delete -f infrastructure/kubernetes/minikube/

# Stop Minikube (optional)
minikube stop
```

---

## Part 3: Production Deployment on DigitalOcean

### 3.1 Create DigitalOcean Kubernetes Cluster

1. Log in to DigitalOcean: https://cloud.digitalocean.com
2. Navigate to **Kubernetes** → **Create Cluster**
3. Choose:
   - **Region**: Nearest to your users (e.g., NYC, SFO, FRA)
   - **Kubernetes Version**: Latest stable
   - **Node Plan**: Basic (2GB RAM, 1 vCPU) × 2 nodes (minimum for HA)
   - **Node Count**: 2 (for $48/month estimate)
4. Click **Create Cluster**

Wait 5-10 minutes for cluster provisioning.

### 3.2 Configure kubectl for DigitalOcean

```bash
# Install doctl (DigitalOcean CLI)
# macOS
brew install doctl

# Linux
curl -sL https://github.com/digitalocean/doctl/releases/download/v1.100.0/doctl-1.100.0-linux-amd64.tar.gz | tar xz
sudo mv doctl /usr/local/bin

# Authenticate
doctl auth init

# Get cluster ID
doctl kubernetes cluster list

# Configure kubectl
doctl kubernetes cluster kubeconfig save <cluster-id>

# Verify
kubectl get nodes
```

### 3.3 Set up Redpanda Cloud (Kafka)

1. Sign up at https://redpanda.com/cloud (free tier)
2. Create a **Serverless Cluster**
3. Create topics:
   - `task-events` (3 partitions, replication factor 3)
   - `reminders` (3 partitions, replication factor 3)
   - `task-updates` (3 partitions, replication factor 3)
4. Copy **Bootstrap Server URL** and **API Key**
5. Save to Kubernetes Secrets (see step 3.5)

### 3.4 Set up Neon Database (Already done from Phase III/IV)

Use your existing Neon database URL from Phase III/IV.

### 3.5 Create Kubernetes Secrets

```bash
# Database URL
kubectl create secret generic neon-db-url \
  --namespace todo-app \
  --from-literal=database-url="postgresql://user:password@ep-cool-neon.us-east-2.aws.neon.tech/neondb?sslmode=require"

# JWT Secret
kubectl create secret generic jwt-secret \
  --namespace todo-app \
  --from-literal=jwt-secret="$(openssl rand -hex 32)"

# OpenAI API Key
kubectl create secret generic openai-api-key \
  --namespace todo-app \
  --from-literal=openai-api-key="sk-your-openai-key"

# Redpanda Credentials
kubectl create secret generic redpanda-credentials \
  --namespace todo-app \
  --from-literal=bootstrap-server="your-cluster.redpanda.cloud:9092" \
  --from-literal=username="your-username" \
  --from-literal=password="your-password" \
  --from-literal=api-key="your-api-key"
```

### 3.6 Deploy with Helm

```bash
# Create namespace
kubectl create namespace todo-app

# Install Dapr (if not already installed)
dapr init -k

# Deploy application
cd infrastructure/helm/todo-chatbot
helm install todo-app . --namespace todo-app \
  --values values-production.yaml \
  --set ingress.host=todo-app.yourdomain.com \
  --set redpanda.enabled=false \
  --set redpanda.external=true
```

### 3.7 Set up SSL/TLS with cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer (Let's Encrypt)
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Update ingress to use cert-manager
kubectl annotate ingress todo-app-frontend \
  --namespace todo-app \
  cert-manager.io/clusterissuer=letsencrypt-prod
```

### 3.8 Verify Deployment

```bash
# Check pods
kubectl get pods -n todo-app

# Check ingress
kubectl get ingress -n todo-app

# Get production URL
kubectl get ingress todo-app-frontend -n todo-app
```

### 3.9 Set up Monitoring

**T170: Comprehensive monitoring with Prometheus, Grafana, and Loki**

```bash
# Apply monitoring stack manifests
kubectl apply -f infrastructure/kubernetes/base/monitoring/

# Verify monitoring components are running
kubectl get pods -n monitoring

# Run monitoring validation tests
cd infrastructure/tests
./test_monitoring.sh
```

**Access Monitoring Dashboards:**

```bash
# Grafana (visualization)
kubectl port-forward -n monitoring svc/grafana 3000:80
# Open: http://localhost:3000 (admin/admin - change in production!)

# Prometheus (metrics)
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Open: http://localhost:9090

# Loki (logs - optional)
kubectl port-forward -n monitoring svc/loki 3100:3100
```

**Import Grafana Dashboards:**

1. Login to Grafana (http://localhost:3000)
2. Navigate to Dashboards → Import
3. Upload dashboard JSONs from `infrastructure/monitoring/dashboards/`:
   - `application.json` - Application metrics (requests/sec, error rate, latency)
   - `kafka.json` - Kafka message throughput and consumer lag
   - `infrastructure.json` - Pod CPU, memory, network usage

**Key Metrics to Monitor:**

- **Application Health**:
  - Requests per second (RPS)
  - Error rate (target: < 5%)
  - P95 latency (target: < 500ms)

- **Infrastructure**:
  - Pod CPU/Memory usage
  - Database connection pool
  - Kafka consumer lag

- **Alerts**:
  - High error rate (> 5% triggers warning, > 15% triggers critical)
  - High latency (> 1s P95)
  - Pod crash looping
  - Kafka consumer lag > 1000 messages

**Viewing Logs in Grafana:**

1. Add Loki datasource (http://loki:3100)
2. Explore logs with LogQL queries:
   - `{job="todo-backend"}` - All backend logs
   - `{job="todo-backend"} |= "error"` - Backend errors
   - `{job="todo-backend"} |~ "task_id.*123"` - Search for task ID

---

## Part 4: CI/CD Pipeline with GitHub Actions

### 4.1 Set up GitHub Secrets

Navigate to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

Add the following secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql://...` |
| `JWT_SECRET` | JWT signing secret | `hex-encoded-secret` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `REDPANDA_BOOTSTRAP_SERVER` | Redpanda bootstrap server | `cluster.redpanda.com:9092` |
| `REDPANDA_USERNAME` | Redpanda username | `your-username` |
| `REDPANDA_PASSWORD` | Redpanda password | `your-password` |
| `DIGITALOCEAN_TOKEN` | DigitalOcean API token | `dop_v1_...` |
| `DIGITALOCEAN_CLUSTER_ID` | Kubernetes cluster ID | `xxxx-xxxx-xxxx` |
| `REGISTRY_USERNAME` | Docker registry username | `username` |
| `REGISTRY_PASSWORD` | Docker registry password | `password` |

### 4.2 Enable GitHub Actions

Workflows are automatically run on:
- Pull requests to `main` branch (tests)
- Push to `main` branch (build and deploy)

### 4.3 Deploy on Push

```bash
# Make a change and push
git add .
git commit -m "feat: Add new feature"
git push origin main
```

GitHub Actions will:
1. Run tests
2. Build Docker images
3. Push images to registry
4. Deploy to DigitalOcean Kubernetes

### 4.4 Monitor Deployment

```bash
# Watch rollout status
kubectl rollout status deployment/todo-app-backend --namespace todo-app

# Check pods
kubectl get pods -n todo-app --watch
```

---

## Troubleshooting

### Issue: Minikube starts slowly
**Solution**: Increase Docker resources (Docker Desktop → Settings → Resources → Memory: 8GB, CPUs: 4)

### Issue: Kafka connection errors
**Solution**: Verify Redpanda is running:
```bash
docker-compose ps redpanda
docker-compose logs redpanda
```

### Issue: Dapr sidecar not starting
**Solution**: Check Dapr logs:
```bash
kubectl logs -n todo-app <pod-name> -c daprd
```

### Issue: Database migration fails
**Solution**: Rollback and retry:
```bash
alembic downgrade -1
alembic upgrade head
```

### Issue: Helm chart deployment fails
**Solution**: Debug with `--dry-run`:
```bash
helm install todo-app . --namespace todo-app --values values-minikube.yaml --dry-run --debug
```

---

## Cost Estimates

### Local Development
- **Free** (using Docker on your machine)

### Minikube
- **Free** (local Kubernetes cluster)

### DigitalOcean Production (1,000 users)
- **Kubernetes Cluster**: $48/month (2 nodes × $24/month)
- **Load Balancer**: $12/month
- **Neon Database**: Free tier (up to 3GB storage)
- **Redpanda Cloud**: Free tier (up to 10GB/month)
- **Registry**: Free (Docker Hub) or $5/month (DigitalOcean)
- **Total**: ~$60-65/month

### Scale to 10,000 users
- **Kubernetes Cluster**: $96/month (4 nodes × $24/month)
- **Total**: ~$110-120/month

---

## Next Steps

1. ✅ Complete local development setup
2. ✅ Deploy to Minikube
3. ✅ Set up CI/CD pipeline
4. ✅ Deploy to DigitalOcean production
5. 📊 Configure monitoring and alerting
6. 📝 Document custom configurations

---

**END OF QUICK START GUIDE**
