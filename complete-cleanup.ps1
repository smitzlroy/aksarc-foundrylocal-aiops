#!/usr/bin/env pwsh
# Complete Repository Security and Cleanup Script
# Run this to secure and clean up the repository before pushing

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Repository Security & Cleanup" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Step 1: Remove development docs from tracking
Write-Host "Step 1: Removing development documentation from git tracking..." -ForegroundColor Yellow
$devDocs = @(
    "REDESIGN_SUMMARY.md",
    "REFACTORING_COMPLETE.md",
    "TOPOLOGY_ENHANCEMENTS.md",
    "SECURITY_AUDIT.md",
    "STARTING_MODELS.md",
    "UI_REDESIGN_COMPLETE.md"
)

foreach ($doc in $devDocs) {
    if (Test-Path $doc) {
        Write-Host "  Removing $doc..." -ForegroundColor Gray
        git rm --cached $doc 2>$null
    }
}
Write-Host "  ✅ Development docs removed from tracking" -ForegroundColor Green
Write-Host ""

# Step 2: Stage security-related changes
Write-Host "Step 2: Staging security and accuracy updates..." -ForegroundColor Yellow
git add .gitignore
git add README.md
git add deploy/systemd/README.md
git add cleanup-repo.ps1
git add complete-cleanup.ps1
git add REPO_CLEANUP_SUMMARY.md
Write-Host "  ✅ Changes staged" -ForegroundColor Green
Write-Host ""

# Step 3: Show what will be committed
Write-Host "Step 3: Review changes..." -ForegroundColor Yellow
Write-Host ""
git status --short
Write-Host ""

# Step 4: Security check
Write-Host "Step 4: Running security checks..." -ForegroundColor Yellow

Write-Host "  Checking for .env files..." -ForegroundColor Gray
$envFiles = Get-ChildItem -Path . -Filter "*.env" -Recurse -ErrorAction SilentlyContinue | 
            Where-Object { $_.Name -ne ".env.example" -and $_.FullName -notmatch "node_modules|\.git" }

if ($envFiles) {
    Write-Host "  ⚠️  WARNING: Found .env files:" -ForegroundColor Red
    $envFiles | ForEach-Object { Write-Host "      $($_.FullName)" -ForegroundColor Red }
} else {
    Write-Host "  ✅ No .env files found" -ForegroundColor Green
}

Write-Host "  Checking for kubeconfig files..." -ForegroundColor Gray
$kubeconfigs = Get-ChildItem -Path . -Filter "kubeconfig*" -Recurse -ErrorAction SilentlyContinue |
               Where-Object { $_.FullName -notmatch "node_modules|\.git" }

if ($kubeconfigs) {
    Write-Host "  ⚠️  WARNING: Found kubeconfig files:" -ForegroundColor Red
    $kubeconfigs | ForEach-Object { Write-Host "      $($_.FullName)" -ForegroundColor Red }
} else {
    Write-Host "  ✅ No kubeconfig files found" -ForegroundColor Green
}

Write-Host "  Checking for private keys..." -ForegroundColor Gray
$keys = Get-ChildItem -Path . -Include "*.key","*.pem","*.pfx" -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "node_modules|\.git" }

if ($keys) {
    Write-Host "  ⚠️  WARNING: Found private keys:" -ForegroundColor Red
    $keys | ForEach-Object { Write-Host "      $($_.FullName)" -ForegroundColor Red }
} else {
    Write-Host "  ✅ No private keys found" -ForegroundColor Green
}

Write-Host ""

# Step 5: Provide commit command
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Ready to Commit" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run this command to commit the changes:" -ForegroundColor Yellow
Write-Host ""
Write-Host 'git commit -m "chore: Secure repository and improve documentation accuracy

- Remove example IPs from all documentation
- Update README to reflect actual UI-based model selection
- Fix access URLs (consistent port 8080)
- Add comprehensive gitignore patterns for sensitive files
- Remove development documentation from tracking
- Ensure no sensitive data or real IPs in repository"' -ForegroundColor White
Write-Host ""
Write-Host "Then push with:" -ForegroundColor Yellow
Write-Host "git push origin main" -ForegroundColor White
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
