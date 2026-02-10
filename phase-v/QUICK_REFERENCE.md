# 🚀 Quick Reference Card - DigitalOcean Deployment

## ⚡ Quick Start Commands

### 1. Initial Setup
```bash
# Install tools (one-time)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

wget https://github.com/digitalocean/doctl/releases/download/v1.104.0/doctl-1.104.0-linux-amd64.tar.gz
tar xf ~/doctl-1.104.0-linux-amd64.tar.gz
sudo mv doctl /usr/local/bin

curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Authenticate
doctl auth init
```

### 2. Automated Deployment
```bash
cd phase-v
./deploy-do.sh
```

### 3. Manual Deployment (Step-by-Step)
See `DEPLOYMENT_GUIDE.md` for detailed instructions.

---

## 📊 Essential Commands

### Check Cluster Status
```bash
# List clusters
doctl kubernetes cluster list

# Get nodes
kubectl get nodes

# Get all pods
kubectl get pods -n todo-app

# Watch pods in real-time
kubectl get pods -n todo-app -w
```

### View Logs
```bash
# Backend logs
kubectl logs -f deployment/backend -n todo-app

# Frontend logs
kubectl logs -f deployment/frontend -n todo-app

# All logs
kubectl logs -f -n todo-app -l app=backend
```

### Scale Applications
```bash
# Scale backend up
kubectl scale deployment/backend --replicas=3 -n todo-app

# Scale backend down
kubectl scale deployment/backend --replicas=1 -n todo-app

# Check replica status
kubectl get pods -n todo-app
```

### Restart Deployments
```bash
# Restart backend
kubectl rollout restart deployment/backend -n todo-app

# Restart frontend
kubectl rollout restart deployment/frontend -n todo-app

# Check rollout status
kubectl rollout status deployment/backend -n todo-app
```

### Access Application
```bash
# Port forward to test locally
kubectl port-forward svc/backend 8000:80 -n todo-app

# Get LoadBalancer IP
kubectl get svc frontend -n todo-app

# Get external URL
echo "$(kubectl get svc frontend -n todo-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
```

---

## 🔧 Troubleshooting Commands

### Pod Issues
```bash
# Describe pod (detailed info)
kubectl describe pod <pod-name> -n todo-app

# Pod logs (if crashed, get previous)
kubectl logs <pod-name> -n todo-app --previous

# Exec into pod
kubectl exec -it <pod-name> -n todo-app -- /bin/bash

# Check pod events
kubectl get events -n todo-app --sort-by='.lastTimestamp'
```

### Database Issues
```bash
# List databases
doctl databases list

# Get database connection string
doctl databases connection <db-id> --format URI

# Test connection from pod
kubectl run -it --rm debug --image=postgres:16 --restart=Never -n todo-app -- \
  psql "$DATABASE_URL"
```

### Service/Ingress Issues
```bash
# Check service endpoints
kubectl get endpoints backend -n todo-app

# Test service from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n todo-app -- \
  curl http://backend.todo-app.svc.cluster.local/health

# Check ingress
kubectl describe ingress -n todo-app

# Check SSL certificates
kubectl get certificate -n todo-app
```

---

## 📈 Monitoring Commands

### Resource Usage
```bash
# Top pods (resource usage)
kubectl top pods -n todo-app

# Top nodes
kubectl top nodes

# Node resource usage
kubectl describe nodes | grep Allocated -A 5
```

### Application Metrics
```bash
# Get metrics endpoint (Prometheus format)
curl http://<backend-ip>/metrics

# Health check
curl https://api.yourdomain.com/health

# API documentation
curl https://api.yourdomain.com/docs
```

---

## 🔄 Update & Rollback

### Update Application
```bash
# Build new image
docker build -t registry.digitalocean.com/your-namespace/backend:v2 -f backend/Dockerfile backend/

# Push new image
docker push registry.digitalocean.com/your-namespace/backend:v2

# Update deployment (set new image)
kubectl set image deployment/backend backend=registry.digitalocean.com/your-namespace/backend:v2 -n todo-app

# Watch rollout
kubectl rollout status deployment/backend -n todo-app
```

### Rollback
```bash
# View rollout history
kubectl rollout history deployment/backend -n todo-app

# Rollback to previous version
kubectl rollout undo deployment/backend -n todo-app

# Rollback to specific version
kubectl rollout undo deployment/backend --to-revision=2 -n todo-app
```

---

## 🗑️ Cleanup Commands

### Delete Application
```bash
# Delete all resources in namespace
kubectl delete namespace todo-app

# Delete Kafka
kubectl delete namespace kafka
helm uninstall strimzi-kafka-operator -n kafka

# Delete registry
doctl registry delete todo-chatbot-registry
```

### Delete Cluster
```bash
# Delete Kubernetes cluster
doctl kubernetes cluster delete todo-chatbot-cluster

# Delete database
doctl databases delete <database-id>
```

---

## 📝 Environment Variables

### Required Secrets
```bash
# Database URL
kubectl create secret generic postgres-secret \
  --from-literal=database-url="postgresql://user:pass@host:port/db" \
  -n todo-app

# JWT Secret
kubectl create secret generic jwt-secret \
  --from-literal=BETTER_AUTH_SECRET="$(openssl rand -base64 32)" \
  -n todo-app

# OpenAI API Key
kubectl create secret generic openai-secret \
  --from-literal=OPENAI_API_KEY="sk-your-key" \
  -n todo-app
```

---

## 🌐 Access Points

| Service | URL | Port Forward |
|---------|-----|-------------|
| Frontend | https://yourdomain.com | `kubectl port-forward svc/frontend 3000:80 -n todo-app` |
| Backend API | https://api.yourdomain.com | `kubectl port-forward svc/backend 8000:80 -n todo-app` |
| API Docs | https://api.yourdomain.com/docs | (same as backend) |
| Metrics | https://api.yourdomain.com/metrics | (same as backend) |

---

## 💰 Cost Breakdown (Monthly)

| Service | Plan | Cost |
|---------|------|------|
| Kubernetes Cluster | 2 x s-4vcpu-8gb | ~$96 |
| PostgreSQL Database | s-2vcpu-4gb + Standby | ~$36 |
| Container Registry | Basic (500MB) | Free |
| Load Balancer | Included with cluster | Free |
| **Total** | | **~$132/month** |

**💡 Cost Saving Tips:**
- Use 1 node instead of 2 for dev: ~$48/month
- Use s-2vcpu-4gb nodes instead of s-4vcpu-8gb: ~$48/month
- Scale down replicas when not in use
- Delete cluster when not developing

---

## 📞 Help & Support

### Documentation
- Full Guide: `DEPLOYMENT_GUIDE.md`
- Project README: `README.md`
- Quickstart: `specs/006-advanced-cloud-deployment/quickstart.md`

### Useful Links
- DigitalOcean Docs: https://docs.digitalocean.com/
- Kubernetes Docs: https://kubernetes.io/docs/
- Docker Docs: https://docs.docker.com/

### Get Help
```bash
# DigitalOcean support
https://cloud.digitalocean.com/support

# Kubernetes community
https://kubernetes.slack.com/
https://stackoverflow.com/questions/tagged/kubernetes
```

---

## ⚙️ Configuration Files

| File | Purpose |
|------|---------|
| `infrastructure/kubernetes/base/backend/deployment.yaml` | Backend deployment config |
| `infrastructure/kubernetes/base/frontend/deployment.yaml` | Frontend deployment config |
| `infrastructure/kubernetes/base/backend/service.yaml` | Backend service config |
| `infrastructure/kubernetes/base/frontend/ingress.yaml` | Frontend ingress/SSL config |
| `infrastructure/helm/todo-chatbot/values.yaml` | Helm chart values |
| `.github/workflows/deploy.yml` | CI/CD deployment workflow |

---

## ✅ Deployment Checklist

### Before Deployment
- [ ] DigitalOcean account created
- [ ] Payment method added
- [ ] Domain purchased (optional)
- [ ] OpenAI API key obtained
- [ ] Local tools installed (kubectl, doctl, docker, helm)

### During Deployment
- [ ] Kubernetes cluster created
- [ ] Container registry created
- [ ] PostgreSQL database created
- [ ] Database migrations run
- [ ] Kafka cluster deployed
- [ ] Docker images built and pushed
- [ ] Kubernetes secrets created
- [ ] Backend deployed
- [ ] Frontend deployed
- [ ] Pods are running
- [ ] Services are accessible

### After Deployment
- [ ] DNS configured (if using custom domain)
- [ ] SSL certificates issued
- [ ] Application tested
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Backups enabled
- [ ] CI/CD configured

---

**Last Updated**: 2026-02-11
