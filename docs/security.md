# Security Guidelines

## 🔒 Critical Security Rules

**NEVER commit the following to the repository:**

### 1. Credentials and Secrets
- API keys, tokens, passwords
- Azure credentials or service principal keys
- Private keys (.key, .pem, .p12, .pfx files)
- SSL/TLS certificates
- Database connection strings with credentials
- Any file containing `*secret*`, `*password*`, `*token*`, `*apikey*`

### 2. Kubernetes Configuration
- `kubeconfig` files (contain cluster credentials)
- `cluster-config.yaml` or similar exported configs
- Files in `.kube/` directory
- Helm `secrets.yaml` or `*-secret.yaml` files

### 3. Environment Files
- `.env` files (contain actual configuration)
- `.env.local`, `.env.production`, etc.
- Any `.env.*` except `.env.example`

### 4. Personal Information
- Real IP addresses or domain names (use placeholders)
- Usernames or email addresses
- Organization-specific internal URLs
- Azure subscription IDs or resource group names

## ✅ What You SHOULD Commit

1. **`.env.example`** - Template files with placeholder values
2. **Documentation** - Using generic placeholders like:
   - `http://localhost:<your-port>`
   - `<your-username>`
   - `<your-model-name>`
   - `<your-subscription-id>`
3. **Code** - With environment variable references:
   ```python
   endpoint = os.getenv("FOUNDRY_ENDPOINT")
   ```

## 🛡️ Protection Mechanisms

### 1. .gitignore
The `.gitignore` file blocks sensitive files from being tracked:
- Environment files (`.env`, `.env.*`)
- Kubeconfig files
- Secret/credential files
- Private keys and certificates

### 2. Pre-commit Hooks
Automatically run before each commit:
- **detect-secrets** - Scans for API keys, tokens, passwords
- **detect-private-key** - Blocks private key files
- **check-added-large-files** - Prevents large binary files

To install pre-commit hooks:
```bash
cd backend
pip install pre-commit
pre-commit install
```

### 3. Manual Review
Before committing, always:
1. Review `git status` output
2. Check `git diff` for sensitive data
3. Verify no `.env` files are staged
4. Search for IP addresses, usernames, real endpoints

## 🚨 If You Accidentally Commit Secrets

**DO NOT** simply delete and recommit - the secret is still in git history!

### Immediate Actions:
1. **Revoke the secret immediately** (regenerate API keys, rotate credentials)
2. **Remove from git history**:
   ```bash
   # Using git-filter-repo (recommended)
   pip install git-filter-repo
   git filter-repo --invert-paths --path path/to/secret/file
   
   # Or use BFG Repo-Cleaner
   # https://rtyley.github.io/bfg-repo-cleaner/
   ```
3. **Force push** (coordinate with team first):
   ```bash
   git push --force-with-lease origin main
   ```
4. **Notify team members** to re-clone the repository

## 📋 Pre-Commit Checklist

Before every commit:
- [ ] No `.env` files staged (only `.env.example`)
- [ ] No `kubeconfig` or cluster config files
- [ ] No real IP addresses, endpoints, or URLs
- [ ] No API keys, tokens, or passwords in code
- [ ] All credentials use environment variables
- [ ] Documentation uses placeholders (`<your-value>`)
- [ ] Pre-commit hooks pass successfully

## 🔍 How to Check for Secrets

### Scan entire repository:
```bash
# Install detect-secrets
pip install detect-secrets

# Scan repository
detect-secrets scan --baseline .secrets.baseline

# Audit findings
detect-secrets audit .secrets.baseline
```

### Check specific files:
```bash
# Search for common secret patterns
git grep -iE "(password|token|api.?key|secret)" -- ':!docs/security.md'

# Check for IP addresses
git grep -E "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b"

# Check for email addresses
git grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
```

## 🎯 Best Practices

1. **Use environment variables** for all configuration
2. **Create `.env.example`** templates with safe defaults
3. **Document placeholders** clearly in README and docs
4. **Never hardcode** credentials, even for "testing"
5. **Use Azure Key Vault** or similar for production secrets
6. **Rotate credentials** regularly
7. **Review PRs carefully** for sensitive data
8. **Enable branch protection** on main branch
9. **Require status checks** (including pre-commit hooks)
10. **Audit regularly** using `detect-secrets` and code review

## 📚 Additional Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [detect-secrets documentation](https://github.com/Yelp/detect-secrets)
- [git-filter-repo documentation](https://github.com/newren/git-filter-repo)

## 🚫 Common Mistakes to Avoid

1. ❌ Committing `.env` instead of `.env.example`
2. ❌ Copying `kubeconfig` into project directory
3. ❌ Hardcoding API endpoints in source code
4. ❌ Including real Azure subscription IDs in examples
5. ❌ Committing test credentials "just for testing"
6. ❌ Adding `TODO: remove this secret` comments (and forgetting)
7. ❌ Disabling pre-commit hooks to "save time"
8. ❌ Using `git add .` without reviewing changes
9. ❌ Storing certificates or private keys in repo
10. ❌ Committing `kubectl get` output with real cluster data

---

**Remember**: Once something is committed to git, assume it's permanent. Be vigilant!
