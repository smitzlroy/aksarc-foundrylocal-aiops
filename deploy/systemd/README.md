# Systemd Service Deployment (Linux Jumpbox)

Deploy K8s AI Assistant as a systemd service on Linux servers (jumpbox, bastion, dev server).

## Prerequisites

- Linux server with systemd
- kubectl configured with cluster access
- Python 3.11+ installed
- Network access for your team to reach the server

## Installation

```bash
# 1. Clone repository
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/smitzlroy/aksarc-foundrylocal-aiops.git
cd aksarc-foundrylocal-aiops

# 2. Create service user
sudo useradd -r -s /bin/bash -d /opt/aksarc-foundrylocal-aiops aiops

# 3. Install Python dependencies
cd backend
sudo pip3 install -r requirements.txt
cd ..

# 4. Copy kubectl config to service user
sudo mkdir -p /home/aiops/.kube
sudo cp ~/.kube/config /home/aiops/.kube/config
sudo chown -R aiops:aiops /home/aiops/.kube
sudo chown -R aiops:aiops /opt/aksarc-foundrylocal-aiops

# 5. Install systemd service
sudo cp deploy/systemd/aiops.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aiops
sudo systemctl start aiops

# 6. Check status
sudo systemctl status aiops
```

## Access

Once running, team can access at:
- **Web UI**: http://YOUR_SERVER_IP:8080/
- **API Docs**: http://YOUR_SERVER_IP:8080/docs

Example: If jumpbox IP is YOUR_SERVER_IP:
- http://YOUR_SERVER_IP:8080/

## Service Management

```bash
# Start service
sudo systemctl start aiops

# Stop service
sudo systemctl stop aiops

# Restart service
sudo systemctl restart aiops

# View logs
sudo journalctl -u aiops -f

# Check status
sudo systemctl status aiops

# Disable auto-start
sudo systemctl disable aiops
```

## Firewall Configuration

If using firewall, allow port 8080:

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 8080/tcp

# firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

## Security Considerations

### For Internal Network (Recommended)
- Deploy on private network jumpbox
- Access via VPN only
- No additional auth needed (network is the security boundary)

### For External Access (Advanced)
If exposing externally, add reverse proxy with auth:

```bash
# Install nginx
sudo apt install nginx

# Configure with basic auth
sudo htpasswd -c /etc/nginx/.htpasswd admin

# nginx config:
server {
    listen 80;
    server_name aiops.example.com;
    
    location / {
        auth_basic "K8s AI Assistant";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://localhost:8080;
    }
}
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u aiops -n 50

# Test manually
sudo -u aiops python3 /opt/aksarc-foundrylocal-aiops/backend/run.py
```

### Can't connect to cluster
```bash
# Verify kubectl works as service user
sudo -u aiops kubectl get nodes

# Check kubeconfig
sudo -u aiops cat /home/aiops/.kube/config
```

### Port already in use
```bash
# Check what's using port 8080
sudo lsof -i :8080

# Or change port in .env:
echo "API_PORT=8081" | sudo tee /opt/aksarc-foundrylocal-aiops/backend/.env
sudo systemctl restart aiops
```

## Updating

```bash
cd /opt/aksarc-foundrylocal-aiops
sudo git pull
sudo systemctl restart aiops
```

## Uninstallation

```bash
sudo systemctl stop aiops
sudo systemctl disable aiops
sudo rm /etc/systemd/system/aiops.service
sudo systemctl daemon-reload
sudo userdel aiops
sudo rm -rf /opt/aksarc-foundrylocal-aiops
```
