# Deployment Guide

## Overview

This guide covers deploying the AKS Arc AI Ops Assistant to:
1. Local k3s cluster (development/testing)
2. Azure AKS Arc cluster (production)

## Prerequisites

### General Requirements

- kubectl configured and connected to target cluster
- Helm 3.x installed
- Azure AI Foundry Local accessible from cluster
- Sufficient cluster resources:
  - CPU: 1 core minimum, 2 cores recommended
  - Memory: 2GB minimum, 4GB recommended
  - Storage: 5GB for container images

### For AKS Arc Deployment

- Azure subscription with AKS Arc enabled
- Azure CLI installed and authenticated
- Appropriate RBAC permissions on AKS Arc cluster

## Helm Chart Structure

```
helm/aiops-assistant/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default configuration values
├── values-dev.yaml         # Development overrides
├── values-prod.yaml        # Production overrides
├── templates/
│   ├── deployment.yaml     # Backend deployment
│   ├── service.yaml        # Service definitions
│   ├── serviceaccount.yaml # ServiceAccount for K8s access
│   ├── rbac.yaml           # RBAC rules
│   ├── configmap.yaml      # Configuration
│   ├── secret.yaml         # Secrets (Foundry endpoint, etc.)
│   └── ingress.yaml        # Ingress (optional)
└── README.md               # Helm chart documentation
```

## Configuration

### Core Configuration Values

Key values in `values.yaml`:

```yaml
# Backend configuration
backend:
  image:
    repository: aksarc-aiops-assistant
    tag: latest
    pullPolicy: IfNotPresent
  
  replicas: 1
  
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi
  
  foundry:
    endpoint: "http://127.0.0.1:58366"
    model: "qwen2.5-0.5b"
  
  context:
    bufferHours: 2
    maxBufferSizeMB: 500

# ServiceAccount and RBAC
serviceAccount:
  create: true
  name: aiops-assistant
  
rbac:
  create: true
  # Permissions: read pods, events, logs across all namespaces
  clusterRole: true

# Service configuration
service:
  type: ClusterIP
  port: 8000
  targetPort: 8000

# Ingress (optional)
ingress:
  enabled: false
  className: nginx
  annotations: {}
  hosts:
    - host: aiops.local
      paths:
        - path: /
          pathType: Prefix
  tls: []
```

### Environment-Specific Overrides

**Development** (`values-dev.yaml`):
```yaml
backend:
  replicas: 1
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
  foundry:
    endpoint: "http://host.k3d.internal:58366"
```

**Production** (`values-prod.yaml`):
```yaml
backend:
  replicas: 2
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  foundry:
    endpoint: "http://foundry-local.foundry.svc.cluster.local:8080"

ingress:
  enabled: true
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: aiops.yourdomain.com
```

## Local Deployment (k3s)

### Step 1: Build Docker Image

```bash
# From project root
docker build -t aksarc-aiops-assistant:latest -f backend/Dockerfile .

# For k3s, import image directly
k3s ctr images import aksarc-aiops-assistant-latest.tar

# Or if using k3d
k3d image import aksarc-aiops-assistant:latest -c mycluster
```

### Step 2: Create Namespace

```bash
kubectl create namespace aiops
kubectl config set-context --current --namespace=aiops
```

### Step 3: Configure Foundry Endpoint

Since Foundry Local is running on host, update endpoint:

```bash
# Create secret with Foundry endpoint
kubectl create secret generic foundry-config \
  --from-literal=endpoint=http://host.k3d.internal:58366 \
  --from-literal=model=qwen2.5-0.5b \
  -n aiops
```

### Step 4: Deploy with Helm

```bash
# From project root
helm install aiops-assistant ./helm/aiops-assistant \
  --namespace aiops \
  --values ./helm/aiops-assistant/values-dev.yaml
```

### Step 5: Verify Deployment

```bash
# Check pod status
kubectl get pods -n aiops

# Check logs
kubectl logs -f deployment/aiops-assistant -n aiops

# Port forward to test locally
kubectl port-forward svc/aiops-assistant 8000:8000 -n aiops
```

### Step 6: Access Application

```bash
# Backend API
curl http://localhost:8000/api/health

# Frontend (if served by backend)
open http://localhost:8000
```

## AKS Arc Deployment

### Step 1: Authenticate to Azure

```bash
az login
az account set --subscription <subscription-id>

# Connect to AKS Arc cluster
az connectedk8s proxy -n <cluster-name> -g <resource-group>
```

### Step 2: Configure Container Registry

```bash
# Create Azure Container Registry (if not exists)
az acr create --name <acr-name> --resource-group <rg> --sku Basic

# Attach ACR to AKS Arc
az connectedk8s enable-features \
  -n <cluster-name> \
  -g <resource-group> \
  --features cluster-connect azure-rbac

# Build and push image
az acr build --registry <acr-name> \
  --image aksarc-aiops-assistant:latest \
  --file backend/Dockerfile .
```

### Step 3: Create Image Pull Secret

```bash
# Get ACR credentials
ACR_NAME=<acr-name>
ACR_PASSWORD=$(az acr credential show -n $ACR_NAME --query "passwords[0].value" -o tsv)

# Create secret
kubectl create secret docker-registry acr-secret \
  --docker-server=$ACR_NAME.azurecr.io \
  --docker-username=$ACR_NAME \
  --docker-password=$ACR_PASSWORD \
  --namespace aiops
```

### Step 4: Configure Foundry Endpoint

For AKS Arc, Foundry Local should be deployed as a service in cluster or accessible via network:

```bash
kubectl create secret generic foundry-config \
  --from-literal=endpoint=http://foundry-local.foundry.svc.cluster.local:8080 \
  --from-literal=model=qwen2.5-0.5b \
  -n aiops
```

### Step 5: Deploy with Helm

```bash
helm install aiops-assistant ./helm/aiops-assistant \
  --namespace aiops \
  --values ./helm/aiops-assistant/values-prod.yaml \
  --set backend.image.repository=<acr-name>.azurecr.io/aksarc-aiops-assistant \
  --set backend.image.pullSecrets[0].name=acr-secret
```

### Step 6: Configure Ingress (Optional)

```bash
# Install ingress controller if not present
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# Update values to enable ingress
helm upgrade aiops-assistant ./helm/aiops-assistant \
  --namespace aiops \
  --values ./helm/aiops-assistant/values-prod.yaml \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=aiops.yourdomain.com
```

## RBAC Configuration

The application requires read access to Kubernetes resources:

```yaml
# ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aiops-assistant
  namespace: aiops

---
# ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: aiops-assistant
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "events", "namespaces"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets", "statefulsets"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["services", "endpoints"]
    verbs: ["get", "list"]

---
# ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: aiops-assistant
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: aiops-assistant
subjects:
  - kind: ServiceAccount
    name: aiops-assistant
    namespace: aiops
```

## Monitoring and Logging

### View Logs

```bash
# Stream logs
kubectl logs -f deployment/aiops-assistant -n aiops

# View logs from specific pod
kubectl logs <pod-name> -n aiops

# View logs with timestamps
kubectl logs deployment/aiops-assistant -n aiops --timestamps
```

### Check Resource Usage

```bash
# Pod resource usage
kubectl top pod -n aiops

# Node resource usage
kubectl top nodes
```

### Health Checks

```bash
# Check pod health
kubectl get pods -n aiops

# Check endpoint
kubectl port-forward svc/aiops-assistant 8000:8000 -n aiops
curl http://localhost:8000/api/health
```

## Upgrades and Updates

### Upgrade Application

```bash
# Update values or image tag
helm upgrade aiops-assistant ./helm/aiops-assistant \
  --namespace aiops \
  --values ./helm/aiops-assistant/values-prod.yaml \
  --set backend.image.tag=v0.2.0
```

### Rollback

```bash
# View release history
helm history aiops-assistant -n aiops

# Rollback to previous version
helm rollback aiops-assistant -n aiops

# Rollback to specific revision
helm rollback aiops-assistant 2 -n aiops
```

## Uninstallation

```bash
# Uninstall Helm release
helm uninstall aiops-assistant -n aiops

# Delete namespace
kubectl delete namespace aiops
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n aiops

# Check logs for errors
kubectl logs <pod-name> -n aiops

# Common issues:
# - Image pull errors: Check image name and pull secrets
# - Resource limits: Check node capacity
# - RBAC issues: Verify ServiceAccount permissions
```

### Cannot Connect to Foundry Local

```bash
# Test connectivity from pod
kubectl exec -it <pod-name> -n aiops -- curl http://foundry-endpoint:port/health

# Check network policies
kubectl get networkpolicies -n aiops

# Verify Foundry endpoint in secret
kubectl get secret foundry-config -n aiops -o yaml
```

### High Memory Usage

```bash
# Check current usage
kubectl top pod -n aiops

# Adjust buffer size in values.yaml
helm upgrade aiops-assistant ./helm/aiops-assistant \
  --set backend.context.bufferHours=1 \
  --set backend.context.maxBufferSizeMB=256
```

## Security Best Practices

1. **Use Secrets for Sensitive Data**: Never hardcode Foundry endpoints or credentials
2. **Limit RBAC Permissions**: Only grant necessary permissions
3. **Use Network Policies**: Restrict pod-to-pod communication
4. **Enable TLS**: Use HTTPS for ingress
5. **Scan Images**: Regularly scan container images for vulnerabilities
6. **Resource Limits**: Set appropriate CPU/memory limits
7. **Regular Updates**: Keep dependencies and base images updated

## Production Checklist

Before deploying to production AKS Arc:

- [ ] Container image scanned for vulnerabilities
- [ ] Resource limits configured appropriately
- [ ] RBAC permissions reviewed and minimized
- [ ] Secrets properly configured (not hardcoded)
- [ ] Monitoring and alerting set up
- [ ] Backup and disaster recovery plan in place
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Runbook created for operational tasks
- [ ] Security review completed
