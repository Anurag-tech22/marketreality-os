$r = Invoke-RestMethod 'http://localhost:8000/api/demo/SOL'
Write-Host "asset:   $($r.asset)"
Write-Host "status:  $($r.status)"
Write-Host "price:   $($r.reality_gap.headline_price)"
Write-Host "mcap:    $($r.reality_gap.headline_market_cap)"
Write-Host "vol24h:  $($r.reality_gap.headline_volume_24h)"
Write-Host "dims:    $($r.dimensions.Count)"
Write-Host "venues:  $($r.venues.Count)"
Write-Host "is_demo: $($r.is_demo)"
Write-Host "--- BTC ---"
$b = Invoke-RestMethod 'http://localhost:8000/api/demo/BTC'
Write-Host "asset:   $($b.asset)"
Write-Host "price:   $($b.reality_gap.headline_price)"
Write-Host "--- health ---"
$h = Invoke-RestMethod 'http://localhost:8000/health'
Write-Host "cmc_configured:    $($h.cmc_configured)"
Write-Host "gemini_configured: $($h.gemini_configured)"
