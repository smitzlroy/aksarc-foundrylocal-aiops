# 🔐 Secure Development Workflow

## Overview

This document outlines the **mandatory security practices** for all development on this repository. These practices ensure no sensitive data is ever committed to the public GitHub repository.

---

## 🛡️ Security Philosophy

**Golden Rule**: Treat every commit as if it will be public forever, because it will be.

### What We Protect Against
- ❌ Credentials (API keys, tokens, passwords)
- ❌ Kubernetes configurations (kubeconfig, certificates)
- ❌ Private keys and certificates
- ❌ Internal IP addresses and endpoints
- ❌ Personal or organizational information
- ❌ Production secrets of any kind

---

## 🔄 Daily Development Workflow

### 1. Starting Work

```powershell
# Update repository
git pull origin main

# Create feature branch (optional but recommended)
git checkout -b feature/your-feature-name

# Verify security protections are active
git config --get core.hooksPath  # Should show hooks are enabled
```

### 2. Configuration Setup

**Every time you clone or start fresh:**

```powershell
# Copy environment templates
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit with your LOCAL values (these files are gitignored)
code backend/.env  # Add your actual configuration
code frontend/.env
```

**⚠️ NEVER commit `.env` files - they're in `.gitignore`**

### 3. Making Changes

```powershell
# Make your code changes
code backend/src/services/kubernetes.py

# Use environment variables for ALL configuration
# ✅ GOOD:
#   endpoint = os.getenv("FOUNDRY_ENDPOINT")
# ❌ BAD:
#   endpoint = "http://192.168.1.100:8000"
```

### 4. Before Committing - MANDATORY CHECKS

**Run the security verification script:**

```powershell
# This runs automatically with pre-commit hooks, but you can run manually
.\scripts\verify-security.ps1
```

**Manual verification:**

```powershell
# 1. Review what you're committing
git status
git diff

# 2. Check for sensitive data
git diff | Select-String -Pattern "password|token|secret|api.?key"

# 3. Verify no sensitive files
git status --short | Select-String -Pattern "\.env$|kubeconfig|\.key$"
```

### 5. Committing

```powershell
# Stage your changes
git add <specific-files>  # Be explicit, avoid 'git add .'

# Commit (pre-commit hooks run automatically)
git commit -m "feat: add kubernetes watcher service"

# If hooks fail, FIX THE ISSUES - do not bypass with --no-verify
```

**Commit Message Format:**
```
<type>: <description>

[optional body]

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- refactor: Code refactoring
- test: Adding tests
- chore: Maintenance tasks
- security: Security improvements
```

### 6. Pushing to GitHub

```powershell
# Push to your branch
git push origin feature/your-feature-name

# Or if working on main
git push origin main
```

**⚠️ GitHub Actions will run security scans on every push**

---

## 🚨 Security Checkpoints

### Pre-Commit (Automatic)

Pre-commit hooks run **automatically** before every commit:

1. ✅ **detect-secrets** - Scans for API keys, tokens, passwords
2. ✅ **detect-private-key** - Blocks private key files
3. ✅ **verify-security.ps1** - Custom security verification
4. ✅ **check-yaml, check-json** - Validates config files
5. ✅ **black, isort, mypy, pylint** - Python code quality
6. ✅ **prettier, eslint** - Frontend code quality

**If any check fails, commit is BLOCKED.**

### Post-Push (Automatic)

GitHub Actions runs on every push:

1. ✅ **Gitleaks** - Enterprise-grade secret scanner
2. ✅ **detect-secrets** - Additional secret detection
3. ✅ **File type checks** - Verifies no .env, kubeconfig, keys
4. ✅ **IP address scan** - Detects hardcoded IPs
5. ✅ **.gitignore validation** - Ensures protection patterns present

**If any check fails, you'll be notified via GitHub.**

### Weekly (Automatic)

GitHub Actions runs **every Monday at 9am UTC**:

- Full repository security audit
- Historical commit scan for secrets
- Dependency vulnerability scan
- Security policy compliance check

---

## 🔧 Configuration Management

### Environment Variables

**ALL configuration MUST use environment variables:**

```python
# ✅ CORRECT - Using environment variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    foundry_endpoint: str
    foundry_model: str
    api_key: str
    
    class Config:
        env_file = ".env"

# Load settings
settings = Settings()
```

```python
# ❌ WRONG - Hardcoded values
FOUNDRY_ENDPOINT = "http://10.0.0.50:8000"
API_KEY = "sk-abcd1234efgh5678"
```

### Kubernetes Configuration

```python
# ✅ CORRECT - Load from environment or default location
from kubernetes import config

# Load from KUBECONFIG env var or ~/.kube/config
config.load_kube_config()
```

```python
# ❌ WRONG - Hardcoded kubeconfig path
config.load_kube_config(config_file="/path/to/specific/kubeconfig")
```

### Documentation Examples

```markdown
# ✅ CORRECT - Using placeholders
FOUNDRY_ENDPOINT=http://localhost:<your-port>
CLUSTER_NAME=<your-cluster-name>
AZURE_SUBSCRIPTION=<your-subscription-id>
```

```markdown
# ❌ WRONG - Real values
FOUNDRY_ENDPOINT=http://10.0.0.50:8366
CLUSTER_NAME=prod-aks-arc-01
AZURE_SUBSCRIPTION=12345678-1234-1234-1234-123456789abc
```

---

## 🎯 Testing Locally

### With Local Kubernetes (k3s/k3d)

```powershell
# Use local cluster
$env:KUBECONFIG = "$HOME\.kube\config"

# Run backend
cd backend
.\venv\Scripts\Activate.ps1
uvicorn src.main:app --reload
```

### With Lab AKS Arc Cluster

```powershell
# Set kubeconfig for your lab cluster (NOT committed to git)
$env:KUBECONFIG = "C:\Users\$env:USERNAME\.kube\lab-cluster-config"

# Verify connection
kubectl cluster-info
kubectl get nodes

# Run application
cd backend
.\venv\Scripts\Activate.ps1
uvicorn src.main:app --reload
```

**⚠️ Never commit your lab kubeconfig file**

---

## 🆘 What If Security Checks Fail?

### Pre-Commit Hook Failure

```powershell
# Hook failed - see what's wrong
git status

# If .env file was accidentally staged
git restore --staged backend/.env

# If kubeconfig was accidentally staged
git restore --staged kubeconfig

# If secret detected in code
# 1. Remove the secret from code
# 2. Move to environment variable
# 3. Update .env (which won't be committed)
# 4. Try commit again
```

### GitHub Actions Failure

```powershell
# Check the GitHub Actions tab for details
# https://github.com/<owner>/<repo>/actions

# Fix the issue locally
# Test with security verification script
.\scripts\verify-security.ps1

# Commit the fix
git add <fixed-files>
git commit -m "security: remove accidentally committed secret"
git push
```

### Accidentally Committed a Secret

**⚠️ CRITICAL - Follow these steps immediately:**

1. **Revoke/Rotate the secret** (API key, token, etc.)
   - Generate new credentials
   - Update your local `.env` file
   
2. **Remove from git history** (if already pushed):
   ```powershell
   # Install git-filter-repo
   pip install git-filter-repo
   
   # Remove the sensitive file from all history
   git filter-repo --invert-paths --path path/to/secret/file
   
   # Force push (destructive - coordinate with team)
   git push --force-with-lease origin main
   ```

3. **Update security audit log**:
   - Document the incident in `SECURITY_AUDIT.md`
   - Note what was exposed and remediation steps

---

## 📊 Security Audit Process

### Before Making Repository Public

Run complete audit:

```powershell
# 1. Run security verification
.\scripts\verify-security.ps1

# 2. Manual scan for secrets
git grep -iE "(password|token|api.?key|secret)" -- ':!SECURITY_AUDIT.md' ':!docs/'

# 3. Check for sensitive files
git ls-files | Select-String -Pattern "\.env$|kubeconfig|\.key$|\.pem$"

# 4. Scan for IP addresses
git grep -E "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | Select-String -NotMatch "127.0.0.1|0.0.0.0"

# 5. Review git history
git log --all --oneline
git log --all --full-history -- "*.env" "kubeconfig*"
```

### Monthly Security Review

**First Monday of every month:**

1. Review `SECURITY_AUDIT.md` checklist
2. Run full repository scan
3. Check GitHub Security Advisories
4. Review dependency vulnerabilities (Dependabot)
5. Update security documentation if needed
6. Document findings in audit log

---

## 🎓 Security Training

### Required Reading

All contributors must read:

1. **`docs/security.md`** - Comprehensive security guidelines
2. **`SECURITY_AUDIT.md`** - Audit checklist and procedures
3. **This document** - Secure development workflow

### Common Pitfalls

❌ **Using `git add .` without reviewing**
✅ Stage files explicitly: `git add backend/src/services/kubernetes.py`

❌ **Bypassing pre-commit hooks with `--no-verify`**
✅ Fix the security issue instead

❌ **Committing `.env` "just for testing"**
✅ Use `.env.example` with placeholders

❌ **Hardcoding secrets "temporarily"**
✅ Always use environment variables from the start

❌ **Committing TODO comments with secrets**
✅ Never include secrets, even in comments

---

## 🔐 Access Control

### Who Can Commit?

- Repository owner: Full access
- Collaborators: Must sign security agreement
- Community contributors: PRs reviewed for security before merge

### Branch Protection (Recommended)

Enable on `main` branch:
- ✅ Require pull request reviews
- ✅ Require status checks (GitHub Actions)
- ✅ No force pushes
- ✅ No deletions

---

## 📞 Security Contact

**Found a security issue?**

1. **DO NOT** create a public GitHub issue
2. **DO NOT** commit the finding to the repository
3. **DO** report via GitHub Security Advisories:
   - Go to repository → Security → Advisories → New draft advisory
   - Provide details of the vulnerability
   - Wait for confirmation before public disclosure

---

## ✅ Quick Reference

**Before Every Commit:**
```powershell
git status              # Review what you're committing
git diff                # Check the actual changes
# Pre-commit hooks run automatically
git commit -m "..."     # Commit if hooks pass
```

**If Hooks Fail:**
```powershell
# Fix the issue (don't bypass with --no-verify)
git restore --staged <sensitive-file>  # Unstage sensitive file
# Add to .gitignore if needed
# Move secrets to environment variables
```

**Weekly Verification:**
```powershell
.\scripts\verify-security.ps1  # Run security scan
git log --oneline -10          # Review recent commits
```

---

**Remember**: Security is everyone's responsibility. When in doubt, ask!
