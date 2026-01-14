# Interactive Testing Menu for AKS Arc AI Ops

$API_BASE = "http://localhost:8000/api"

function Show-Menu {
    Clear-Host
    Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   AKS Arc AI Ops - Interactive Tester    ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1.  Health Check" -ForegroundColor Yellow
    Write-Host "2.  View Cluster Status" -ForegroundColor Yellow
    Write-Host "3.  List All Pods" -ForegroundColor Yellow
    Write-Host "4.  List Pods by Namespace" -ForegroundColor Yellow
    Write-Host "5.  View Pod Logs" -ForegroundColor Yellow
    Write-Host "6.  View Pod History" -ForegroundColor Yellow
    Write-Host "7.  View Recent Events" -ForegroundColor Yellow
    Write-Host "8.  Deploy Test Pod (nginx)" -ForegroundColor Yellow
    Write-Host "9.  Delete Test Pod" -ForegroundColor Yellow
    Write-Host "10. Open Dashboard in Browser" -ForegroundColor Yellow
    Write-Host "11. Open API Docs (Swagger)" -ForegroundColor Yellow
    Write-Host "Q.  Quit" -ForegroundColor Red
    Write-Host ""
}

function Test-ServerRunning {
    try {
        $response = Invoke-RestMethod -Uri "$API_BASE/health" -TimeoutSec 2 -ErrorAction Stop
        return $true
    } catch {
        Write-Host "❌ Server not running on http://localhost:8000" -ForegroundColor Red
        Write-Host "   Run: .\start.ps1" -ForegroundColor Yellow
        Read-Host "Press Enter to continue"
        return $false
    }
}

function Show-Health {
    Write-Host "`n📊 Health Check..." -ForegroundColor Cyan
    try {
        $health = Invoke-RestMethod -Uri "$API_BASE/health"
        
        Write-Host "`nOverall Status: " -NoNewline
        if ($health.status -eq "healthy") {
            Write-Host "✅ HEALTHY" -ForegroundColor Green
        } else {
            Write-Host "⚠️  DEGRADED" -ForegroundColor Yellow
        }
        
        Write-Host "`nServices:" -ForegroundColor White
        Write-Host "  Kubernetes:     $(if ($health.services.kubernetes) {'✅'} else {'❌'})" -ForegroundColor $(if ($health.services.kubernetes) {'Green'} else {'Red'})
        Write-Host "  Context Buffer: $(if ($health.services.context_buffer) {'✅'} else {'❌'})" -ForegroundColor $(if ($health.services.context_buffer) {'Green'} else {'Red'})
        Write-Host "  Foundry AI:     $(if ($health.services.foundry) {'✅'} else {'❌'})" -ForegroundColor $(if ($health.services.foundry) {'Green'} else {'Red'})
        
        Write-Host "`nTimestamp: $($health.timestamp)" -ForegroundColor Gray
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
    Read-Host "`nPress Enter to continue"
}

function Show-ClusterStatus {
    Write-Host "`n📊 Cluster Status..." -ForegroundColor Cyan
    try {
        $status = Invoke-RestMethod -Uri "$API_BASE/cluster/status"
        
        Write-Host "`nTimestamp: $($status.timestamp)" -ForegroundColor Gray
        Write-Host "Total Pods: $($status.pods.Count)" -ForegroundColor White
        Write-Host "Total Events: $($status.events.Count)" -ForegroundColor White
        
        $running = ($status.pods | Where-Object {$_.phase -eq "Running"}).Count
        $pending = ($status.pods | Where-Object {$_.phase -eq "Pending"}).Count
        $failed = ($status.pods | Where-Object {$_.phase -eq "Failed"}).Count
        
        Write-Host "`nPod Phases:" -ForegroundColor White
        Write-Host "  Running:  $running" -ForegroundColor Green
        Write-Host "  Pending:  $pending" -ForegroundColor Yellow
        Write-Host "  Failed:   $failed" -ForegroundColor Red
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
    Read-Host "`nPress Enter to continue"
}

function Show-AllPods {
    Write-Host "`n📦 All Pods..." -ForegroundColor Cyan
    try {
        $pods = Invoke-RestMethod -Uri "$API_BASE/cluster/pods"
        
        Write-Host "`nTotal: $($pods.Count) pods`n" -ForegroundColor White
        
        $pods | ForEach-Object {
            $color = switch ($_.phase) {
                "Running" { "Green" }
                "Pending" { "Yellow" }
                "Failed" { "Red" }
                default { "White" }
            }
            
            Write-Host "[$($_.phase)]" -ForegroundColor $color -NoNewline
            Write-Host " $($_.namespace)/$($_.name)" -ForegroundColor White
            Write-Host "  Node: $($_.node) | Ready: $($_.ready)/$($_.total) | Restarts: $($_.restarts)" -ForegroundColor Gray
            Write-Host ""
        }
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
    Read-Host "Press Enter to continue"
}

function Show-PodsByNamespace {
    Write-Host "`n📦 Pods by Namespace..." -ForegroundColor Cyan
    
    # Get namespaces
    try {
        $pods = Invoke-RestMethod -Uri "$API_BASE/cluster/pods"
        $namespaces = $pods | Select-Object -ExpandProperty namespace -Unique | Sort-Object
        
        Write-Host "`nAvailable namespaces:" -ForegroundColor White
        for ($i = 0; $i -lt $namespaces.Count; $i++) {
            Write-Host "  $($i + 1). $($namespaces[$i])" -ForegroundColor Yellow
        }
        
        $selection = Read-Host "`nSelect namespace number"
        $namespace = $namespaces[[int]$selection - 1]
        
        $filtered = Invoke-RestMethod -Uri "$API_BASE/cluster/pods?namespace=$namespace"
        
        Write-Host "`nPods in $namespace ($($filtered.Count) total):`n" -ForegroundColor Cyan
        
        $filtered | ForEach-Object {
            $color = switch ($_.phase) {
                "Running" { "Green" }
                "Pending" { "Yellow" }
                "Failed" { "Red" }
                default { "White" }
            }
            
            Write-Host "[$($_.phase)]" -ForegroundColor $color -NoNewline
            Write-Host " $($_.name)" -ForegroundColor White
            Write-Host "  Node: $($_.node) | Ready: $($_.ready)/$($_.total)" -ForegroundColor Gray
            Write-Host ""
        }
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
    Read-Host "Press Enter to continue"
}

function Show-PodLogs {
    Write-Host "`n📋 Pod Logs..." -ForegroundColor Cyan
    
    try {
        $pods = Invoke-RestMethod -Uri "$API_BASE/cluster/pods"
        
        Write-Host "`nSelect a pod:" -ForegroundColor White
        for ($i = 0; $i -lt [Math]::Min(10, $pods.Count); $i++) {
            $pod = $pods[$i]
            Write-Host "  $($i + 1). $($pod.namespace)/$($pod.name) [$($pod.phase)]" -ForegroundColor Yellow
        }
        
        $selection = Read-Host "`nPod number"
        $selectedPod = $pods[[int]$selection - 1]
        
        $lines = Read-Host "Number of lines (default: 100)"
        if ([string]::IsNullOrWhiteSpace($lines)) { $lines = 100 }
        
        Write-Host "`nFetching logs..." -ForegroundColor Cyan
        $response = Invoke-RestMethod -Uri "$API_BASE/cluster/pods/$($selectedPod.namespace)/$($selectedPod.name)/logs?tail_lines=$lines"
        
        Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Cyan
        Write-Host "Logs: $($selectedPod.namespace)/$($selectedPod.name)" -ForegroundColor White
        Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
        Write-Host $response.logs -ForegroundColor Gray
        Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
    Read-Host "`nPress Enter to continue"
}

function Show-PodHistory {
    Write-Host "`n📊 Pod History..." -ForegroundColor Cyan
    
    try {
        $pods = Invoke-RestMethod -Uri "$API_BASE/cluster/pods"
        
        Write-Host "`nSelect a pod:" -ForegroundColor White
        for ($i = 0; $i -lt [Math]::Min(10, $pods.Count); $i++) {
            $pod = $pods[$i]
            Write-Host "  $($i + 1). $($pod.namespace)/$($pod.name)" -ForegroundColor Yellow
        }
        
        $selection = Read-Host "`nPod number"
        $selectedPod = $pods[[int]$selection - 1]
        
        $hours = Read-Host "Hours to look back (default: 1)"
        if ([string]::IsNullOrWhiteSpace($hours)) { $hours = 1 }
        
        $history = Invoke-RestMethod -Uri "$API_BASE/cluster/pods/$($selectedPod.namespace)/$($selectedPod.name)/history?hours=$hours"
        
        Write-Host "`nHistory for $($selectedPod.namespace)/$($selectedPod.name):" -ForegroundColor Cyan
        Write-Host "Entries: $($history.Count)`n" -ForegroundColor White
        
        $history | ForEach-Object {
            Write-Host "[$($_.phase)] Ready: $($_.ready)/$($_.total) | Restarts: $($_.restarts)" -ForegroundColor Gray
            Write-Host "  Created: $($_.created_at)" -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
    Read-Host "`nPress Enter to continue"
}

function Show-Events {
    Write-Host "`n⚡ Recent Events..." -ForegroundColor Cyan
    
    $hours = Read-Host "Hours to look back (default: 1)"
    if ([string]::IsNullOrWhiteSpace($hours)) { $hours = 1 }
    
    try {
        $events = Invoke-RestMethod -Uri "$API_BASE/cluster/events?hours=$hours"
        
        Write-Host "`nEvents in last $hours hour(s): $($events.Count)`n" -ForegroundColor White
        
        if ($events.Count -eq 0) {
            Write-Host "No events found." -ForegroundColor Yellow
        } else {
            $events | Select-Object -First 20 | ForEach-Object {
                $color = if ($_.type -eq "Warning") { "Yellow" } else { "Green" }
                
                Write-Host "[$($_.type)]" -ForegroundColor $color -NoNewline
                Write-Host " $($_.involved_object)" -ForegroundColor White
                Write-Host "  Reason: $($_.reason)" -ForegroundColor Gray
                Write-Host "  Message: $($_.message)" -ForegroundColor Gray
                Write-Host "  Time: $($_.timestamp)" -ForegroundColor DarkGray
                Write-Host ""
            }
        }
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
    Read-Host "Press Enter to continue"
}

function Deploy-TestPod {
    Write-Host "`n🚀 Deploying Test Pod..." -ForegroundColor Cyan
    
    try {
        kubectl run nginx-test --image=nginx:latest
        Write-Host "✅ Test pod 'nginx-test' deployed" -ForegroundColor Green
        Write-Host "   Wait a few seconds, then refresh the pod list to see it" -ForegroundColor Yellow
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
    Read-Host "`nPress Enter to continue"
}

function Delete-TestPod {
    Write-Host "`n🗑️  Deleting Test Pod..." -ForegroundColor Cyan
    
    try {
        kubectl delete pod nginx-test 2>$null
        Write-Host "✅ Test pod 'nginx-test' deleted" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
    Read-Host "`nPress Enter to continue"
}

function Open-Dashboard {
    Write-Host "`n🌐 Opening Dashboard..." -ForegroundColor Cyan
    $dashboardPath = Join-Path $PSScriptRoot "dashboard.html"
    Start-Process $dashboardPath
    Write-Host "✅ Dashboard opened in your browser" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

function Open-ApiDocs {
    Write-Host "`n📖 Opening API Docs..." -ForegroundColor Cyan
    Start-Process "http://localhost:8000/docs"
    Write-Host "✅ API docs opened in your browser" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

# Main loop
while ($true) {
    Show-Menu
    $choice = Read-Host "Select an option"
    
    if ($choice -eq "Q" -or $choice -eq "q") {
        Write-Host "`n👋 Goodbye!" -ForegroundColor Cyan
        break
    }
    
    # Check server for API calls
    if ($choice -in 1..9) {
        if (-not (Test-ServerRunning)) {
            continue
        }
    }
    
    switch ($choice) {
        "1" { Show-Health }
        "2" { Show-ClusterStatus }
        "3" { Show-AllPods }
        "4" { Show-PodsByNamespace }
        "5" { Show-PodLogs }
        "6" { Show-PodHistory }
        "7" { Show-Events }
        "8" { Deploy-TestPod }
        "9" { Delete-TestPod }
        "10" { Open-Dashboard }
        "11" { Open-ApiDocs }
        default {
            Write-Host "`n❌ Invalid option" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
