#!/usr/bin/env pwsh
# Test script for the refactored AIOps API

Write-Host "`n🧪 Testing Refactored AIOps API Endpoints" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:8080"

# Test 1: Root endpoint
Write-Host "1️⃣  Testing root endpoint (GET /)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method Get
    Write-Host "   ✅ Success!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 2
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host "`n"

# Test 2: Topology Graph
Write-Host "2️⃣  Testing topology graph (GET /api/v1/topology/graph)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/topology/graph" -Method Get
    Write-Host "   ✅ Success! Found $($response.nodes.Count) nodes" -ForegroundColor Green
    Write-Host "   Pods: $($response.workloads.pods.Count)" -ForegroundColor Cyan
    Write-Host "   Services: $($response.workloads.services.Count)" -ForegroundColor Cyan
    Write-Host "   Communication flows: $($response.communication_flows.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host "`n"

# Test 3: Control Plane Diagnostics
Write-Host "3️⃣  Testing control plane diagnostics (GET /api/v1/diagnostics/control-plane)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/diagnostics/control-plane" -Method Get
    Write-Host "   ✅ Success!" -ForegroundColor Green
    Write-Host "   API Server: $($response.api_server.status)" -ForegroundColor Cyan
    Write-Host "   etcd: $($response.etcd.status)" -ForegroundColor Cyan
    Write-Host "   Arc Agents: $($response.arc_agents.status)" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host "`n"

# Test 4: Reasoning Loop Analysis
Write-Host "4️⃣  Testing reasoning loop (POST /api/v1/reasoning/analyze)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/reasoning/analyze" -Method Post
    Write-Host "   ✅ Success!" -ForegroundColor Green
    Write-Host "   Observations: $($response.observations.Count)" -ForegroundColor Cyan
    Write-Host "   Reasoning: $($response.reasoning)" -ForegroundColor Cyan
    Write-Host "   Actions: $($response.actions.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host "`n"

# Test 5: Mermaid Export
Write-Host "5️⃣  Testing Mermaid export (GET /api/v1/export/mermaid)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/export/mermaid" -Method Get
    Write-Host "   ✅ Success!" -ForegroundColor Green
    $lineCount = ($response.mermaid -split "`n").Count
    Write-Host "   Generated $lineCount lines of Mermaid diagram" -ForegroundColor Cyan
    Write-Host "`n   First 5 lines:" -ForegroundColor Gray
    ($response.mermaid -split "`n" | Select-Object -First 5) | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host "`n"

# Test 6: Support Bundle
Write-Host "6️⃣  Testing support bundle generation (POST /api/v1/export/support-bundle)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/export/support-bundle" -Method Post
    Write-Host "   ✅ Success!" -ForegroundColor Green
    Write-Host "   Bundle size: $($response.Content.Length) bytes" -ForegroundColor Cyan
    Write-Host "   Content type: $($response.Headers.'Content-Type')" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host "`n"
Write-Host "🎉 Testing Complete!" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan
