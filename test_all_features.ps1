$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       MARKETREALITY OS - FULL STACK INTEGRITY AUDIT        " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Health Endpoint
Write-Host "`n[1] Checking /health..." -ForegroundColor Yellow
try {
    $h = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    Write-Host "  -> Health OK: CMC configured: $($h.cmc_configured), Gemini configured: $($h.gemini_configured)" -ForegroundColor Green
} catch {
    Write-Host "  -> Health FAIL: $_" -ForegroundColor Red
}

# 2. Reality Demo (SOL, BTC, ETH)
Write-Host "`n[2] Checking Demo Data for SOL, BTC, ETH..." -ForegroundColor Yellow
foreach ($sym in @("SOL", "BTC", "ETH")) {
    try {
        $d = Invoke-RestMethod -Uri "http://localhost:8000/api/demo/$sym" -TimeoutSec 10
        Write-Host "  -> Demo $sym OK: Price=`$$($d.reality_gap.headline_price), Dims=$($d.dimensions.Count), Venues=$($d.venues.Count)" -ForegroundColor Green
    } catch {
        Write-Host "  -> Demo $sym FAIL: $_" -ForegroundColor Red
    }
}

# 3. Reality Audit (SOL) - uses cache or CMC, allow 20s
Write-Host "`n[3] Checking Reality Audit /api/reality/SOL..." -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "http://localhost:8000/api/reality/SOL" -TimeoutSec 25
    Write-Host "  -> Reality Audit OK: Status=$($r.status), Dims=$($r.dimensions.Count), Venues=$($r.venues.Count)" -ForegroundColor Green
    Write-Host "     Price=`$$($r.reality_gap.headline_price), is_demo=$($r.is_demo)" -ForegroundColor Gray
} catch {
    Write-Host "  -> Reality Audit FAIL: $_" -ForegroundColor Red
}

# 4. Stress Lab Scenarios
Write-Host "`n[4] Checking Stress Scenarios /api/stress/scenarios..." -ForegroundColor Yellow
try {
    $sc = Invoke-RestMethod -Uri "http://localhost:8000/api/stress/scenarios" -TimeoutSec 10
    Write-Host "  -> Scenarios OK: Loaded $($sc.scenarios.Count) predefined stress scenarios" -ForegroundColor Green
} catch {
    Write-Host "  -> Scenarios FAIL: $_" -ForegroundColor Red
}

# 5. Execute Stress Test - needs cache warmup, allow 20s
Write-Host "`n[5] Executing Stress Test on SOL (STRESS-001)..." -ForegroundColor Yellow
try {
    $st = Invoke-RestMethod -Uri "http://localhost:8000/api/stress/SOL?scenario_id=STRESS-001" -Method Post -TimeoutSec 25
    Write-Host "  -> Stress Test OK: $($st.scenario.name)" -ForegroundColor Green
    Write-Host "     Affected: $($st.affected_dimensions -join ', ')" -ForegroundColor Gray
} catch {
    Write-Host "  -> Stress Test FAIL: $_" -ForegroundColor Red
}

# 6. Trade Reality Assessment
Write-Host "`n[6] Testing Trade Reality Assessment..." -ForegroundColor Yellow
try {
    $tradeBody = @{ symbol = "SOL"; trade_size_usd = 50000; side = "BUY" } | ConvertTo-Json
    $tr = Invoke-RestMethod -Uri "http://localhost:8000/api/trade-reality" -Method Post -Body $tradeBody -ContentType "application/json" -TimeoutSec 25
    Write-Host "  -> Trade Reality OK: Verdict=$($tr.result)" -ForegroundColor Green
    Write-Host "     Dimensions: $($tr.dimensions.Count)" -ForegroundColor Gray
} catch {
    Write-Host "  -> Trade Reality FAIL: $_" -ForegroundColor Red
}

# 7. Global Market Data
Write-Host "`n[7] Checking Global Metrics /api/global..." -ForegroundColor Yellow
try {
    $gl = Invoke-RestMethod -Uri "http://localhost:8000/api/global" -TimeoutSec 25
    Write-Host "  -> Global OK: BTC Dom=$($gl.btc_dominance)%, Active Cryptos=$($gl.active_cryptocurrencies)" -ForegroundColor Green
} catch {
    Write-Host "  -> Global FAIL: $_" -ForegroundColor Red
}

# 8. AI Investigation (Demo) - no CMC needed
Write-Host "`n[8] Testing AI Investigation /api/investigate/demo/SOL..." -ForegroundColor Yellow
try {
    $ai = Invoke-RestMethod -Uri "http://localhost:8000/api/investigate/demo/SOL" -TimeoutSec 20
    Write-Host "  -> AI Investigation OK: Status=$($ai.status), Grounded=$($ai.grounded)" -ForegroundColor Green
    if ($ai.verdict) {
        Write-Host "     Verdict preview: $($ai.verdict.Substring(0, [Math]::Min(80, $ai.verdict.Length)))..." -ForegroundColor Gray
    }
} catch {
    Write-Host "  -> AI Investigation FAIL: $_" -ForegroundColor Red
}

# 9. Next.js Web App
Write-Host "`n[9] Checking Frontend (http://localhost:3000)..." -ForegroundColor Yellow
try {
    $web = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 15
    Write-Host "  -> Frontend OK: Status HTTP $($web.StatusCode), Content length: $($web.Content.Length) bytes" -ForegroundColor Green
} catch {
    Write-Host "  -> Frontend FAIL: $_" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "                    AUDIT COMPLETE                          " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
