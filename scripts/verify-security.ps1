#!/usr/bin/env pwsh
# Security Verification Script
# Run this before committing to ensure no sensitive data is included

$ErrorActionPreference = "Stop"
$WarningCount = 0
$ErrorCount = 0

Write-Host "🔒 Running Security Verification..." -ForegroundColor Cyan
Write-Host ""

# Function to report findings
function Report-Finding {
    param(
        [string]$Type,
        [string]$Message,
        [string]$Details = ""
    )
    
    if ($Type -eq "ERROR") {
        Write-Host "❌ ERROR: $Message" -ForegroundColor Red
        if ($Details) { Write-Host "   $Details" -ForegroundColor Gray }
        $script:ErrorCount++
    }
    elseif ($Type -eq "WARNING") {
        Write-Host "⚠️  WARNING: $Message" -ForegroundColor Yellow
        if ($Details) { Write-Host "   $Details" -ForegroundColor Gray }
        $script:WarningCount++
    }
    else {
        Write-Host "✅ $Message" -ForegroundColor Green
    }
}

# Check 1: Verify no .env files are staged
Write-Host "📋 Check 1: Environment files..." -ForegroundColor Cyan
$stagedEnvFiles = git diff --cached --name-only | Select-String -Pattern "\.env$" | Where-Object { $_ -notmatch "\.env\.example" }
if ($stagedEnvFiles) {
    Report-Finding "ERROR" ".env file(s) are staged for commit" "$stagedEnvFiles"
} else {
    Report-Finding "PASS" "No .env files staged"
}

# Check 2: Verify no kubeconfig files
Write-Host "📋 Check 2: Kubernetes config files..." -ForegroundColor Cyan
$stagedKubeFiles = git diff --cached --name-only | Select-String -Pattern "kubeconfig|\.kube"
if ($stagedKubeFiles) {
    Report-Finding "ERROR" "Kubeconfig file(s) are staged for commit" "$stagedKubeFiles"
} else {
    Report-Finding "PASS" "No kubeconfig files staged"
}

# Check 3: Verify no private keys
Write-Host "📋 Check 3: Private key files..." -ForegroundColor Cyan
$stagedKeyFiles = git diff --cached --name-only | Select-String -Pattern "\.(key|pem|pfx|p12|crt)$"
if ($stagedKeyFiles) {
    Report-Finding "ERROR" "Private key file(s) are staged for commit" "$stagedKeyFiles"
} else {
    Report-Finding "PASS" "No private key files staged"
}

# Check 4: Scan staged changes for secrets
Write-Host "📋 Check 4: Scanning for secrets in staged changes..." -ForegroundColor Cyan
$secretPatterns = @(
    'password\s*[=:]\s*[''"]?[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};'':,.<>?\/]{8,}',
    'api[_-]?key\s*[=:]\s*[''"]?[a-zA-Z0-9]{20,}',
    'secret[_-]?key\s*[=:]\s*[''"]?[a-zA-Z0-9]{20,}',
    'bearer\s+[a-zA-Z0-9\-._~+\/]+=*',
    'token\s*[=:]\s*[''"]?[a-zA-Z0-9]{20,}',
    'aws_access_key_id\s*[=:]\s*[''"]?[A-Z0-9]{20}',
    'aws_secret_access_key\s*[=:]\s*[''"]?[a-zA-Z0-9/+=]{40}',
    '-----BEGIN\s+(RSA\s+)?PRIVATE KEY-----'
)

$stagedDiff = git diff --cached
$foundSecrets = $false

foreach ($pattern in $secretPatterns) {
    $matches = $stagedDiff | Select-String -Pattern $pattern -CaseSensitive
    if ($matches) {
        $foundSecrets = $true
        Report-Finding "ERROR" "Potential secret detected matching pattern: $pattern"
        foreach ($match in $matches | Select-Object -First 3) {
            Write-Host "   Line: $($match.Line.Substring(0, [Math]::Min(80, $match.Line.Length)))" -ForegroundColor Gray
        }
    }
}

if (-not $foundSecrets) {
    Report-Finding "PASS" "No secrets detected in staged changes"
}

# Check 5: Verify no hardcoded IPs (except localhost)
Write-Host "📋 Check 5: Checking for hardcoded IP addresses..." -ForegroundColor Cyan
$ipPattern = "\b(?!127\.0\.0\.1|0\.0\.0\.0)([0-9]{1,3}\.){3}[0-9]{1,3}\b"
$stagedIPs = git diff --cached | Select-String -Pattern $ipPattern
if ($stagedIPs) {
    Report-Finding "WARNING" "Hardcoded IP address(es) detected"
    foreach ($ip in $stagedIPs | Select-Object -First 3) {
        Write-Host "   $($ip.Line.Trim().Substring(0, [Math]::Min(80, $ip.Line.Trim().Length)))" -ForegroundColor Gray
    }
} else {
    Report-Finding "PASS" "No hardcoded IPs detected"
}

# Check 6: Verify .gitignore has required patterns
Write-Host "📋 Check 6: Verifying .gitignore patterns..." -ForegroundColor Cyan
$gitignoreContent = Get-Content .gitignore -Raw
$requiredPatterns = @(".env", "kubeconfig", "*secret*", "*.key", "*.pem")
$missingPatterns = @()

foreach ($pattern in $requiredPatterns) {
    if ($gitignoreContent -notmatch [regex]::Escape($pattern)) {
        $missingPatterns += $pattern
    }
}

if ($missingPatterns) {
    Report-Finding "ERROR" ".gitignore missing required patterns" ($missingPatterns -join ", ")
} else {
    Report-Finding "PASS" ".gitignore properly configured"
}

# Check 7: Verify .env.example files exist
Write-Host "📋 Check 7: Verifying .env.example templates..." -ForegroundColor Cyan
$missingTemplates = @()
if (-not (Test-Path "backend/.env.example")) { $missingTemplates += "backend/.env.example" }
if (-not (Test-Path "frontend/.env.example")) { $missingTemplates += "frontend/.env.example" }

if ($missingTemplates) {
    Report-Finding "ERROR" "Missing .env.example template(s)" ($missingTemplates -join ", ")
} else {
    Report-Finding "PASS" ".env.example templates present"
}

# Check 8: Verify no email addresses in code (except allowed files)
Write-Host "📋 Check 8: Checking for email addresses..." -ForegroundColor Cyan
$emailPattern = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
$stagedEmails = git diff --cached -- ':!package*.json' ':!*pyproject.toml' | Select-String -Pattern $emailPattern
if ($stagedEmails) {
    Report-Finding "WARNING" "Email address(es) detected in staged changes"
    foreach ($email in $stagedEmails | Select-Object -First 3) {
        Write-Host "   $($email.Line.Trim().Substring(0, [Math]::Min(80, $email.Line.Trim().Length)))" -ForegroundColor Gray
    }
} else {
    Report-Finding "PASS" "No email addresses detected"
}

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 Security Verification Summary" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "✅ ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your changes are safe to commit!" -ForegroundColor Green
    exit 0
}
elseif ($ErrorCount -eq 0) {
    Write-Host "⚠️  WARNINGS FOUND: $WarningCount" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Review the warnings above. If intentional, you may proceed." -ForegroundColor Yellow
    Write-Host "To commit anyway, use: git commit --no-verify" -ForegroundColor Gray
    exit 0
}
else {
    Write-Host "❌ ERRORS FOUND: $ErrorCount" -ForegroundColor Red
    Write-Host "⚠️  WARNINGS FOUND: $WarningCount" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "COMMIT BLOCKED - Fix errors before committing!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  - Remove .env files from staging: git restore --staged *.env" -ForegroundColor Gray
    Write-Host "  - Remove kubeconfig: git restore --staged kubeconfig*" -ForegroundColor Gray
    Write-Host "  - Use environment variables instead of hardcoded secrets" -ForegroundColor Gray
    Write-Host "  - Add sensitive files to .gitignore" -ForegroundColor Gray
    exit 1
}
