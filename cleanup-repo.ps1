#!/usr/bin/env pwsh
# Cleanup Repository - Remove development docs and ensure no sensitive data

Write-Host "🧹 Cleaning up repository..." -ForegroundColor Cyan

# Remove development documentation files from git tracking
Write-Host "`n📝 Removing development docs from tracking..." -ForegroundColor Yellow
$devDocs = @(
    "REDESIGN_SUMMARY.md",
    "REFACTORING_COMPLETE.md",
    "TOPOLOGY_ENHANCEMENTS.md",
    "SECURITY_AUDIT.md",
    "STARTING_MODELS.md",
    "UI_REDESIGN_COMPLETE.md"
)

foreach ($file in $devDocs) {
    if (Test-Path $file) {
        Write-Host "  Removing $file from git..." -ForegroundColor Gray
        git rm --cached $file 2>$null
    }
}

# Check for any .env files (should not exist)
Write-Host "`n🔒 Checking for sensitive files..." -ForegroundColor Yellow
$sensitivePatterns = @("*.env", "*.key", "*.pem", "*secret*", "kubeconfig*")
$found = $false

foreach ($pattern in $sensitivePatterns) {
    $files = Get-ChildItem -Path . -Filter $pattern -Recurse -ErrorAction SilentlyContinue | 
             Where-Object { $_.FullName -notmatch "node_modules|\.git|\.env\.example" }
    
    if ($files) {
        $found = $true
        Write-Host "  ⚠️  Found sensitive files matching '$pattern':" -ForegroundColor Red
        $files | ForEach-Object { Write-Host "      $_" -ForegroundColor Red }
    }
}

if (-not $found) {
    Write-Host "  ✅ No sensitive files found" -ForegroundColor Green
}

# Verify .gitignore is up to date
Write-Host "`n📋 Verifying .gitignore..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    $gitignoreContent = Get-Content ".gitignore" -Raw
    $requiredPatterns = @(".env", "*.key", "*secret*", "kubeconfig", "docs/development/")
    $allPresent = $true
    
    foreach ($pattern in $requiredPatterns) {
        if ($gitignoreContent -notmatch [regex]::Escape($pattern)) {
            Write-Host "  ⚠️  Missing pattern: $pattern" -ForegroundColor Yellow
            $allPresent = $false
        }
    }
    
    if ($allPresent) {
        Write-Host "  ✅ .gitignore has all required patterns" -ForegroundColor Green
    }
} else {
    Write-Host "  ❌ .gitignore not found!" -ForegroundColor Red
}

# Summary
Write-Host "`n✅ Cleanup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Review changes: git status" -ForegroundColor White
Write-Host "  2. Commit changes: git commit -m 'chore: Remove development docs and secure repository'" -ForegroundColor White
Write-Host "  3. Push to remote: git push" -ForegroundColor White
