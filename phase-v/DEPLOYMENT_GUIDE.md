# 🌊 Complete DigitalOcean Deployment Guide
## Step-by-Step Manual Deployment for Todo Chatbot Application

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [DigitalOcean Account Setup](#digitalocean-account-setup)
3. [Create Kubernetes Cluster](#create-kubernetes-cluster)
4. [Install Local Tools](#install-local-tools)
5. [Set Up Container Registry](#set-up-container-registry)
6. [Deploy Database (PostgreSQL)](#deploy-database-postgresql)
7. [Deploy Kafka (Event Streaming)](#deploy-kafka-event-streaming)
8. [Build & Push Docker Images](#build--push-docker-images)
9. [Create Kubernetes Secrets](#create-kubernetes-secrets)
10. [Deploy Backend Application](#deploy-backend-application)
11. [Deploy Frontend Application](#deploy-frontend-application)
12. [Configure Domain & SSL](#configure-domain--ssl)
13. [Verify Deployment](#verify-deployment)
14. [Monitoring & Logs](#monitoring--logs)
15. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### Required Accounts:
- ✅ DigitalOcean account (create at https://www.digitalocean.com)
- ✅ GitHub account (already have your code)
- ✅ OpenAI API key (for chatbot features)

### Required Local Tools:
```bash
# Check what you have installed
which kubectl    # Kubernetes CLI
which docker     # Docker for building images
which helm       # Helm package manager
```

---

## 2. DigitalOcean Account Setup

### Step 2.1: Create Account & Add Billing
1. Go to https://www.digitalocean.com
2. Sign up / Log in
3. Add payment method (credit card required for free credits)

### Step 2.2: Get $200 Free Credits
- Use referral code or check for promotions
- New accounts often get 60-day free trial

---

## 3. Create Kubernetes Cluster

### Step 3.1: Create Cluster via Web UI

1. **Navigate to Kubernetes**
   - Go to: https://cloud.digitalocean.com/kubernetes
   - Click "Create Kubernetes Cluster"

2. **Choose Cluster Configuration**
   ```
   Cluster Name: todo-chatbot-cluster
   Region: New York (nyc1)         # Choose closest to your users
   Kubernetes Version: 1.28.x-do.0 # Latest stable
   ```

3. **Choose Node Pool**
   ```
   Plan: Basic ($48/month per node)
   Node Size: s-4vcpu-8gb          # 4 CPUs, 8GB RAM
   Number of Nodes: 2              # For high availability
   ```

   **💰 Cost Estimate**: ~$96/month (can scale down later)

4. **Select Authentication**
   - ✅ Generate a token for doctl (recommended)
   - Download kubeconfig file

5. **Create Cluster**
   - Click "Create Cluster"
   - Wait 5-10 minutes for cluster provisioning

### Step 3.2: Verify Cluster is Ready

```bash
# When cluster shows "Running" in UI, click "Connect to Cluster"
# Or download kubeconfig:

# Save this as ~/.kube/config-do
export KUBECONFIG=~/.kube/config-do

# Verify connection
kubectl get nodes

# Expected output:
# NAME                                STATUS   ROLES    AGE   VERSION
# pool-xxx-yyy                        Ready    <none>   5m    v1.28.2-do.0
# pool-xxx-zzz                        Ready    <none>   5m    v1.28.2-do.0
```

---

## 4. Install Local Tools

### Step 4.1: Install kubectl (Kubernetes CLI)

```bash
# Download kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify
kubectl version --client
```

### Step 4.2: Install doctl (DigitalOcean CLI)

```bash
# Download doctl
wget https://github.com/digitalocean/doctl/releases/download/v1.104.0/doctl-1.104.0-linux-amd64.tar.gz

# Extract
tar xf ~/doctl-1.104.0-linux-amd64.tar.gz

# Install
sudo mv doctl /usr/local/bin

# Authenticate
doctl auth init
# Enter your DigitalOcean API token (generate at: https://cloud.digitalocean.com/settings/api/tokens)
```

### Step 4.3: Install helm (Package Manager)

```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify
helm version
```

### Step 4.4: Configure kubectl for DigitalOcean

```bash
# Get kubeconfig from DigitalOcean
doctl kubernetes cluster kubeconfig save todo-chatbot-cluster

# Verify
kubectl cluster-info
# Expected: Kubernetes control plane is running at https://...
```

---

## 5. Set Up Container Registry

### Step 5.1: Create Container Registry

1. **Go to Container Registry**
   - Navigate: https://cloud.digitalocean.com/registry
   - Click "Create Registry"

2. **Configure Registry**
   ```
   Registry Name: todo-chatbot-registry
   Region: New York (nyc1)            # Same as cluster
   Subscription: Basic                # Free tier includes 500MB storage
   ```

3. **Create Registry**

### Step 5.2: Authenticate with Registry

```bash
# Login to registry
doctl registry login

# Verify
docker login registry.digitalocean.com
# Username: your-do-token
# Password: <press enter, token used as username>
```

---

## 6. Deploy Database (PostgreSQL)

### Step 6.1: Create Managed PostgreSQL Database

1. **Go to Databases**
   - Navigate: https://cloud.digitalocean.com/databases
   - Click "Create Database"

2. **Configure PostgreSQL**
   ```
   Database Engine: PostgreSQL
   Version: 16 (latest stable)
   Name: todo-postgres
   Region: New York (nyc1)

   Node Plan: Basic ($15/month)
   - Size: s-2vcpu-4gb           # 2 CPUs, 4GB RAM
   - Storage: 40GB              # Can be expanded
   - Standby: Yes               # For high availability
   ```

3. **Configure Database User**
   ```
   Username: todoadmin
   Password: [Generate strong password - SAVE THIS!]
   Database Name: tododb
   ```

4. **Create Database** (wait 5-10 minutes)

### Step 6.2: Get Connection Details

```bash
# List databases
doctl databases list

# Get connection string
doctl databases connection todo-postgres --format URI

# Expected: postgresql://todoadmin:password@todo-postgres-do-user-xxx.nyc1.db.ondigitalocean.com:25060/defaultdb

# SAVE THIS CONNECTION STRING!
```

### Step 6.3: Run Database Migrations

```bash
# Set database URL as environment variable
export DATABASE_URL="postgresql://todoadmin:password@todo-postgres-do-user-xxx.nyc1.db.ondigitalocean.com:25060/tododb"

# Run Alembic migrations
cd phase-v/backend
alembic upgrade head

# Verify tables created
psql "$DATABASE_URL" -c "\dt"
# Expected: List of tables - users, tasks, task_events, recurring_tasks, reminders, conversations, messages
```

---

## 7. Deploy Kafka (Event Streaming)

### Option A: Use Managed Kafka (Recommended - Easiest)

**Note**: DigitalOcean doesn't offer managed Kafka. Skip to Option B.

### Option B: Self-Hosted Kafka on Kubernetes

```bash
# Create Kafka namespace
kubectl create namespace kafka

# Install Strimzi Kafka Operator
helm repo add strimzi https://strimzi.io/charts/
helm repo update

helm install strimzi-kafka-operator strimzi/strimzi-kafka-operator \
  --namespace kafka \
  --create-namespace

# Deploy Kafka Cluster
kubectl apply -f phase-v/infrastructure/kubernetes/base/kafka/kafka-cluster.yaml -n kafka

# Wait for Kafka to be ready (5-10 minutes)
kubectl wait kafka/my-cluster --for=condition=Ready --timeout=600s -n kafka

# Create Kafka Topics
kubectl apply -f phase-v/infrastructure/kubernetes/base/kafka/kafka-topics.yaml -n kafka

# Verify topics
kubectl exec -it my-cluster-kafka-0 -n kafka -- kafka-topics.sh --bootstrap-server localhost:9092 --list
```

---

## 8. Build & Push Docker Images

### Step 8.1: Set Environment Variables

```bash
# Set your registry name
export REGISTRY="registry.digitalocean.com"
export REGISTRY_NAMESPACE="your-username"  # Your DigitalOcean username

# Set image tags
export BACKEND_IMAGE="${REGISTRY}/${REGISTRY_NAMESPACE}/todo-backend:latest"
export FRONTEND_IMAGE="${REGISTRY}/${REGISTRY_NAMESPACE}/todo-frontend:latest"
```

### Step 8.2: Build Backend Image

```bash
cd phase-v/backend

# Build image
docker build -t ${BACKEND_IMAGE} .

# Tag for registry
docker tag ${BACKEND_IMAGE} ${BACKEND_IMAGE}

# Push to registry
docker push ${BACKEND_IMAGE}

# Verify
doctl repository list | grep todo-backend
```

### Step 8.3: Build Frontend Image

```bash
cd phase-v/frontend

# Build image
docker build -t ${FRONTEND_IMAGE} .

# Tag for registry
docker tag ${FRONTEND_IMAGE} ${FRONTEND_IMAGE}

# Push to registry
docker push ${FRONTEND_IMAGE}

# Verify
doctl repository list | grep todo-frontend
```

---

## 9. Create Kubernetes Secrets

### Step 9.1: Create Namespace

```bash
kubectl create namespace todo-app
```

### Step 9.2: Create Database Secret

```bash
# Replace with your actual database URL
export DATABASE_URL="postgresql://todoadmin:password@todo-postgres-do-user-xxx.nyc1.db.ondigitalocean.com:25060/tododb"

kubectl create secret generic postgres-secret \
  --from-literal=database-url="$DATABASE_URL" \
  --namespace=todo-app

# Verify
kubectl get secret postgres-secret -n todo-app
```

### Step 9.3: Create JWT Secret

```bash
# Generate strong secret
JWT_SECRET=$(openssl rand -base64 32)

kubectl create secret generic jwt-secret \
  --from-literal=BETTER_AUTH_SECRET="$JWT_SECRET" \
  --namespace=todo-app

# Verify
kubectl get secret jwt-secret -n todo-app
```

### Step 9.4: Create OpenAI API Secret

```bash
# Your OpenAI API key
export OPENAI_API_KEY="sk-your-openai-api-key"

kubectl create secret generic openai-secret \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --namespace=todo-app

# Verify
kubectl get secret openai-secret -n todo-app
```

### Step 9.5: Create Frontend Environment Secret

```bash
# Backend URL (we'll set this after backend deployment)
kubectl create secret generic frontend-secrets \
  --from-literal=NEXT_PUBLIC_API_URL="https://api.your-domain.com" \
  --namespace=todo-app

# Verify
kubectl get secret frontend-secrets -n todo-app
```

---

## 10. Deploy Backend Application

### Step 10.1: Create Backend Deployment

```bash
cd phase-v/infrastructure/kubernetes/base/backend

# Update deployment.yaml with your image
sed -i "s|image: .*backend:.*|image: ${BACKEND_IMAGE}|g" deployment.yaml

# Apply deployment
kubectl apply -f deployment.yaml -n todo-app

# Apply service
kubectl apply -f service.yaml -n todo-app

# Apply HPA (Horizontal Pod Autoscaler)
kubectl apply -f hpa.yaml -n todo-app
```

### Step 10.2: Wait for Backend to Start

```bash
# Watch pods starting
kubectl get pods -n todo-app -w

# Wait for pod to be Ready
kubectl wait --for=condition=ready pod -l app=backend -n todo-app --timeout=300s
```

### Step 10.3: Check Backend Logs

```bash
# Get backend pod name
BACKEND_POD=$(kubectl get pods -n todo-app -l app=backend -o jsonpath='{.items[0].metadata.name}')

# View logs
kubectl logs -f ${BACKEND_POD} -n todo-app

# Expected to see:
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 10.4: Test Backend API

```bash
# Port forward to test locally
kubectl port-forward svc/backend 8000:80 -n todo-app

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Expected: {"status":"healthy"}
```

---

## 11. Deploy Frontend Application

### Step 11.1: Create Frontend Deployment

```bash
cd phase-v/infrastructure/kubernetes/base/frontend

# Update deployment.yaml with your image
sed -i "s|image: .*frontend:.*|image: ${FRONTEND_IMAGE}|g" deployment.yaml

# Apply deployment
kubectl apply -f deployment.yaml -n todo-app

# Apply service
kubectl apply -f service.yaml -n todo-app

# Apply HPA
kubectl apply -f hpa.yaml -n todo-app
```

### Step 11.2: Wait for Frontend to Start

```bash
# Watch pods
kubectl get pods -n todo-app -w

# Wait for ready
kubectl wait --for=condition=ready pod -l app=frontend -n todo-app --timeout=300s
```

### Step 11.3: Check Frontend Logs

```bash
# Get frontend pod name
FRONTEND_POD=$(kubectl get pods -n todo-app -l app=frontend -o jsonpath='{.items[0].metadata.name}')

# View logs
kubectl logs -f ${FRONTEND_POD} -n todo-app
```

---

## 12. Configure Domain & SSL

### Step 12.1: Buy/Configure Domain

**Option A: Buy Domain from DigitalOcean**
1. Go to: https://cloud.digitalocean.com/networking/domains
2. Click "Buy Domain"
3. Search for your domain (e.g., `yourapp.com`)
4. Purchase (~$12-15/year)

**Option B: Use Existing Domain**
1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Add DigitalOcean Nameservers:
   - `ns1.digitalocean.com`
   - `ns2.digitalocean.com`
   - `ns3.digitalocean.com`

### Step 12.2: Add Domain to DigitalOcean

```bash
# Add domain via doctl
doctl domains create yourapp.com

# Or add via UI at: https://cloud.digitalocean.com/networking/domains
```

### Step 12.3: Create DNS Records

```bash
# API subdomain (for backend)
doctl records create yourapp.com \
  --type A \
  --name api \
  --data <load-balancer-ip>

# WWW subdomain (for frontend)
doctl records create yourapp.com \
  --type A \
  --name www \
  --data <load-balancer-ip>

# Root domain
doctl records create yourapp.com \
  --type A \
  --name @ \
  --data <load-balancer-ip>
```

### Step 12.4: Install cert-manager for SSL

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# Verify
kubectl get pods -n cert-manager
```

### Step 12.5: Create ClusterIssuer for Let's Encrypt

```bash
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
```

### Step 12.6: Update Ingress with Domain

```bash
cd phase-v/infrastructure/kubernetes/base/frontend

# Edit ingress.yaml
# Replace your-domain.com with your actual domain
# Update the host field:
# spec:
#   rules:
#   - host: yourapp.com
#     http:
#   - host: www.yourapp.com

# Apply ingress
kubectl apply -f ingress.yaml -n todo-app
```

### Step 12.7: Verify SSL Certificate

```bash
# Check certificate
kubectl get certificate -n todo-app

# Expected:
# NAME     READY   SECRET           AGE
# tls-cert True    tls-cert-secret   5m
```

---

## 13. Verify Deployment

### Step 13.1: Check All Pods

```bash
kubectl get pods -n todo-app

# Expected output:
# NAME                                READY   STATUS    RESTARTS   AGE
# backend-xxx-yyy                     2/2     Running   0          5m
# frontend-xxx-yyy                    1/1     Running   0          3m
# my-cluster-kafka-0                  1/1     Running   0          15m
# my-cluster-zookeeper-0              1/1     Running   0          15m
```

### Step 13.2: Check Services

```bash
kubectl get svc -n todo-app

# Expected:
# NAME      TYPE           EXTERNAL-IP      PORT(S)
# backend   ClusterIP      10.245.0.5       80/TCP
# frontend   LoadBalancer   167.99.0.1      80:30000/TCP
```

### Step 13.3: Test Your Application

```bash
# Test backend API
curl https://api.yourapp.com/health

# Test frontend
curl https://yourapp.com

# Both should return 200 OK
```

### Step 13.4: Access Your Application

1. **Frontend**: https://yourapp.com
2. **Backend API**: https://api.yourapp.com
3. **API Documentation**: https://api.yourapp.com/docs

---

## 14. Monitoring & Logs

### Step 14.1: View Real-Time Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n todo-app

# Frontend logs
kubectl logs -f deployment/frontend -n todo-app

# All logs
kubectl logs -f -n todo-app -l app=backend
kubectl logs -f -n todo-app -l app=frontend
```

### Step 14.2: Check Pod Status

```bash
# Detailed pod information
kubectl describe pod <pod-name> -n todo-app

# Resource usage
kubectl top pods -n todo-app

# Events
kubectl get events -n todo-app --sort-by='.lastTimestamp'
```

### Step 14.3: Access Application Metrics

Your backend has Prometheus metrics built-in at:
- **Metrics Endpoint**: https://api.yourapp.com/metrics

### Step 14.4: Set Up Basic Monitoring (Optional)

```bash
# Install Kubernetes Dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Create admin user
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
EOF

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
EOF

# Access dashboard
kubectl proxy
# Open: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

---

## 15. Troubleshooting

### Common Issues & Solutions

#### Issue 1: Pod is CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n todo-app --previous

# Common causes:
# 1. Database connection failed - Check DATABASE_URL
# 2. Missing secrets - Verify all secrets exist
# 3. Image pull error - Check registry authentication
```

#### Issue 2: Cannot Connect to Database

```bash
# Test database connection from pod
kubectl run -it --rm debug --image=postgres:16 --restart=Never -n todo-app -- \
  psql "$DATABASE_URL"

# If fails, check:
# 1. Database is running: doctl databases list
# 2. Trusted sources are configured: doctl databases mysql <db-id> --update-trusted-src
# 3. Firewall allows connection
```

#### Issue 3: SSL Certificate Not Issuing

```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Describe certificate
kubectl describe certificate tls-cert -n todo-app

# Common issues:
# 1. DNS not propagated - Wait 24-48 hours
# 2. Ingress not accessible - Check LoadBalancer IP
# 3. Rate limiting - Wait and retry
```

#### Issue 4: High Memory/CPU Usage

```bash
# Check resource usage
kubectl top pods -n todo-app

# Scale up if needed
kubectl scale deployment backend --replicas=3 -n todo-app

# Edit resource limits
kubectl edit deployment backend -n todo-app
# Increase resources.requests and resources.limits
```

#### Issue 5: 502 Bad Gateway

```bash
# Check if backend is ready
kubectl get pods -n todo-app -l app=backend

# Check service endpoints
kubectl get endpoints backend -n todo-app

# Restart deployment
kubectl rollout restart deployment/backend -n todo-app
```

### Get Help

```bash
# DigitalOcean support
# https://cloud.digitalocean.com/support

# Kubernetes documentation
# https://kubernetes.io/docs/

# Your project docs
# phase-v/README.md
# phase-v/specs/006-advanced-cloud-deployment/quickstart.md
```

---

## 🎉 Congratulations!

Your Todo Chatbot application is now running on DigitalOcean Kubernetes!

### What's Deployed:
- ✅ Backend API (FastAPI)
- ✅ Frontend (Next.js)
- ✅ PostgreSQL Database
- ✅ Kafka Event Streaming
- ✅ SSL/HTTPS Certificate
- ✅ Auto-scaling (HPA)
- ✅ Monitoring & Logging

### Next Steps:
1. **Set up CI/CD**: Use GitHub Actions in `.github/workflows/`
2. **Configure Monitoring**: Install Prometheus/Grafana
3. **Set up Alerts**: Configure notification for failures
4. **Backup Database**: Enable automated backups
5. **Monitor Costs**: Check DigitalOcean billing dashboard

### Cost Management:
```bash
# Check current costs
doctl projects list

# Scale down when not needed
kubectl scale deployment backend --replicas=1 -n todo-app
kubectl scale deployment frontend --replicas=1 -n todo-app

# Delete cluster when done
doctl kubernetes cluster delete todo-chatbot-cluster
```

### Quick Reference:

| Service | URL | Command |
|---------|-----|---------|
| Frontend | https://yourapp.com | `kubectl get svc frontend -n todo-app` |
| Backend API | https://api.yourapp.com | `kubectl get svc backend -n todo-app` |
| Database | - | `doctl databases get todo-postgres` |
| Kubernetes | - | `kubectl get nodes` |
| Logs | - | `kubectl logs -f deployment/backend -n todo-app` |

---

## 📚 Additional Resources

- **DigitalOcean Kubernetes Docs**: https://docs.digitalocean.com/products/kubernetes/
- **Kubernetes Documentation**: https://kubernetes.io/docs/
- **Your Project README**: phase-v/README.md
- **Deployment Quickstart**: phase-v/specs/006-advanced-cloud-deployment/quickstart.md

---

**Last Updated**: 2026-02-11
**Version**: 1.0
