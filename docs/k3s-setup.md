# k3s Setup Guide for Windows 11

## Overview

This guide walks you through setting up a local Kubernetes cluster using k3s on Windows 11. k3s is a lightweight Kubernetes distribution perfect for development and testing.

## Setup Options

You have three options for running k3s on Windows 11:

1. **k3d (Recommended)**: Runs k3s in Docker containers
2. **WSL2 + k3s**: Runs k3s directly in WSL2
3. **Docker Desktop Kubernetes**: Built-in Kubernetes (simpler but less flexible)

## Option 1: k3d (Recommended for Development)

### What is k3d?

k3d is a wrapper around k3s that runs it in Docker containers. It's fast, easy to set up, and perfect for local development.

### Prerequisites

- Docker Desktop for Windows installed and running
- PowerShell or Windows Terminal

### Installation Steps

#### 1. Install k3d

Using PowerShell:

```powershell
# Download k3d
curl.exe -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.ps1 | powershell

# Or using Chocolatey (if installed)
choco install k3d
```

Verify installation:

```powershell
k3d version
```

#### 2. Create k3s Cluster

```powershell
# Create a single-node cluster
k3d cluster create aiops-dev `
  --port 8000:8000@loadbalancer `
  --port 3000:3000@loadbalancer `
  --api-port 6550

# This creates:
# - A k3s cluster named "aiops-dev"
# - Maps ports 8000 and 3000 for our application
# - API server accessible on port 6550
```

#### 3. Verify Cluster

```powershell
# Get cluster info
kubectl cluster-info

# Check nodes
kubectl get nodes

# You should see something like:
# NAME                     STATUS   ROLES                  AGE   VERSION
# k3d-aiops-dev-server-0   Ready    control-plane,master   1m    v1.27.x
```

#### 4. Configure kubectl Context

```powershell
# k3d automatically configures kubectl, but you can verify:
kubectl config current-context
# Should show: k3d-aiops-dev

# View all contexts
kubectl config get-contexts
```

#### 5. Access Foundry Local from k3s

Since Foundry Local runs on your Windows host (127.0.0.1:58366), you need to access it from containers:

```powershell
# k3d provides host.k3d.internal that resolves to host IP
# Your backend should connect to: http://host.k3d.internal:58366
```

When deploying, use this endpoint in your configuration:

```yaml
# In values-dev.yaml
backend:
  foundry:
    endpoint: "http://host.k3d.internal:58366"
```

#### 6. Test the Cluster

```powershell
# Create a test deployment
kubectl create deployment nginx --image=nginx

# Expose it
kubectl expose deployment nginx --port=80 --type=NodePort

# Check it's running
kubectl get pods
kubectl get svc

# Clean up test
kubectl delete deployment nginx
kubectl delete svc nginx
```

### Managing k3d Cluster

```powershell
# Stop cluster (preserves data)
k3d cluster stop aiops-dev

# Start cluster
k3d cluster start aiops-dev

# Delete cluster (removes all data)
k3d cluster delete aiops-dev

# List all clusters
k3d cluster list

# Get cluster info
k3d cluster get aiops-dev
```

### Troubleshooting k3d

**Issue**: Docker is not running
```powershell
# Start Docker Desktop first
# Then retry k3d commands
```

**Issue**: Port conflicts
```powershell
# Delete and recreate with different ports
k3d cluster delete aiops-dev
k3d cluster create aiops-dev --port 8080:8000@loadbalancer
```

**Issue**: Cannot access host services
```powershell
# Use host.k3d.internal instead of 127.0.0.1 or localhost
# Example: http://host.k3d.internal:58366
```

## Option 2: WSL2 + k3s

### Prerequisites

- WSL2 installed with Ubuntu
- systemd enabled in WSL2

### Installation Steps

#### 1. Enable systemd in WSL2

Edit `/etc/wsl.conf` in your WSL2 Ubuntu instance:

```bash
# In WSL2 terminal
sudo nano /etc/wsl.conf
```

Add:

```ini
[boot]
systemd=true
```

Restart WSL:

```powershell
# In PowerShell
wsl --shutdown
wsl
```

#### 2. Install k3s

```bash
# In WSL2 terminal
curl -sfL https://get.k3s.io | sh -

# Verify installation
sudo k3s kubectl get nodes
```

#### 3. Configure kubectl

```bash
# Copy k3s config to standard kubectl location
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# Test kubectl
kubectl get nodes
```

#### 4. Access from Windows

```powershell
# In PowerShell
# Copy kubeconfig from WSL to Windows
$env:KUBECONFIG = "$env:USERPROFILE\.kube\config"

# Copy config from WSL
wsl cat ~/.kube/config | Set-Content -Path "$env:USERPROFILE\.kube\config"
```

Edit the config to change server address:

```yaml
# Change from:
server: https://127.0.0.1:6443

# To (get WSL IP first):
# In WSL: hostname -I
server: https://<WSL_IP>:6443
```

#### 5. Access Foundry Local

```bash
# Get Windows host IP from WSL
ip route | grep default | awk '{print $3}'

# Use this IP as Foundry endpoint
# Example: http://172.x.x.x:58366
```

### Managing k3s in WSL2

```bash
# Start k3s (if not auto-started)
sudo systemctl start k3s

# Stop k3s
sudo systemctl stop k3s

# Check status
sudo systemctl status k3s

# View logs
sudo journalctl -u k3s -f

# Uninstall k3s
/usr/local/bin/k3s-uninstall.sh
```

## Option 3: Docker Desktop Kubernetes

### Enable Kubernetes

1. Open Docker Desktop
2. Go to Settings → Kubernetes
3. Check "Enable Kubernetes"
4. Click "Apply & Restart"
5. Wait for Kubernetes to start (takes 2-5 minutes)

### Verify

```powershell
kubectl config current-context
# Should show: docker-desktop

kubectl get nodes
# Should show one node
```

### Access Foundry Local

Docker Desktop Kubernetes can access Windows host via `host.docker.internal`:

```yaml
# In your config
foundry:
  endpoint: "http://host.docker.internal:58366"
```

### Limitations

- Single node only
- Less flexible than k3d
- Cannot easily recreate/reset
- Larger resource footprint

## Recommended Setup for This Project

**Use k3d** for the following reasons:

1. ✅ Fast cluster creation/deletion
2. ✅ Easy to reset if something breaks
3. ✅ Multiple clusters support
4. ✅ Good host networking support
5. ✅ Lightweight and efficient
6. ✅ Closer to production k3s experience

### Complete Setup Script

Save this as `setup-k3s.ps1`:

```powershell
# Setup k3s development environment

Write-Host "🚀 Setting up k3s cluster for AKS Arc AI Ops development..." -ForegroundColor Cyan

# Check if Docker is running
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if k3d is installed
$k3dInstalled = Get-Command k3d -ErrorAction SilentlyContinue
if (-not $k3dInstalled) {
    Write-Host "📦 Installing k3d..." -ForegroundColor Yellow
    curl.exe -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.ps1 | powershell
}

# Create cluster
Write-Host "🔧 Creating k3s cluster..." -ForegroundColor Yellow
k3d cluster create aiops-dev `
    --port 8000:8000@loadbalancer `
    --port 3000:3000@loadbalancer `
    --api-port 6550 `
    --agents 0 `
    --wait

# Verify cluster
Write-Host "✅ Verifying cluster..." -ForegroundColor Yellow
kubectl cluster-info
kubectl get nodes

Write-Host "`n✅ k3s cluster is ready!" -ForegroundColor Green
Write-Host "📝 Cluster name: aiops-dev" -ForegroundColor Cyan
Write-Host "📝 Foundry endpoint in cluster: http://host.k3d.internal:58366" -ForegroundColor Cyan
Write-Host "📝 To delete cluster: k3d cluster delete aiops-dev" -ForegroundColor Cyan
```

Run it:

```powershell
.\setup-k3s.ps1
```

## Testing the Setup

### 1. Deploy a Test Pod

```powershell
# Create test namespace
kubectl create namespace test

# Run a test pod
kubectl run test-pod --image=nginx -n test

# Check pod status
kubectl get pods -n test

# Port forward to test
kubectl port-forward pod/test-pod 8080:80 -n test

# In browser: http://localhost:8080
# Should show nginx welcome page

# Clean up
kubectl delete namespace test
```

### 2. Test Foundry Local Access

Create `test-foundry.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-foundry
spec:
  containers:
  - name: curl
    image: curlimages/curl:latest
    command: ['sleep', '3600']
```

Test connectivity:

```powershell
# Deploy test pod
kubectl apply -f test-foundry.yaml

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/test-foundry --timeout=60s

# Test connection to Foundry Local
# For k3d:
kubectl exec test-foundry -- curl -v http://host.k3d.internal:58366

# For Docker Desktop:
kubectl exec test-foundry -- curl -v http://host.docker.internal:58366

# Clean up
kubectl delete pod test-foundry
```

## Next Steps

Once k3s is running:

1. ✅ Verify kubectl is configured: `kubectl get nodes`
2. ✅ Test Foundry Local connectivity from cluster
3. ✅ Deploy the AI Ops Assistant: See `deployment.md`
4. ✅ Test the application end-to-end

## Useful Commands Reference

```powershell
# Cluster management
k3d cluster list                    # List all clusters
k3d cluster start aiops-dev        # Start cluster
k3d cluster stop aiops-dev         # Stop cluster
k3d cluster delete aiops-dev       # Delete cluster

# kubectl basics
kubectl get nodes                   # List nodes
kubectl get pods -A                 # List all pods
kubectl get namespaces              # List namespaces
kubectl cluster-info                # Cluster information

# Context management
kubectl config get-contexts         # List contexts
kubectl config use-context k3d-aiops-dev  # Switch context

# Troubleshooting
kubectl describe pod <pod-name>     # Pod details
kubectl logs <pod-name>             # Pod logs
kubectl logs <pod-name> -f          # Stream logs
kubectl exec -it <pod-name> -- sh   # Shell into pod
```

## Common Issues

### Port Already in Use

```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or create cluster with different port
k3d cluster create aiops-dev --port 8001:8000@loadbalancer
```

### Cluster Won't Start

```powershell
# Delete and recreate
k3d cluster delete aiops-dev
k3d cluster create aiops-dev

# Check Docker logs
docker logs k3d-aiops-dev-server-0
```

### kubectl Not Working

```powershell
# Check kubeconfig
$env:KUBECONFIG
kubectl config view

# Reset kubeconfig
k3d kubeconfig merge aiops-dev --kubeconfig-merge-default
```

## Resources

- [k3d Documentation](https://k3d.io/)
- [k3s Documentation](https://docs.k3s.io/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Docker Desktop Kubernetes](https://docs.docker.com/desktop/kubernetes/)
