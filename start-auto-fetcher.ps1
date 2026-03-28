# Automated News Fetcher Launcher
# Runs the auto news fetcher service every 15 minutes

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AUTOMATED NEWS FETCHER SERVICE" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Sources: NewsAPI, Reddit, RSS Feeds" -ForegroundColor White
Write-Host "Interval: Every 15 minutes" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if already running
$existingProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*auto_news_fetcher.py*"
}

if ($existingProcess) {
    Write-Host "WARNING: News fetcher is already running" -ForegroundColor Yellow
    $response = Read-Host "Stop existing process and restart? (y/n)"
    if ($response -eq 'y') {
        Stop-Process -Id $existingProcess.Id -Force
        Write-Host "Stopped existing process" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Cancelled. Existing process still running." -ForegroundColor Red
        exit
    }
}

# Start the service
Write-Host "Starting automated news fetcher..." -ForegroundColor Green
Write-Host "The service will run in a new window." -ForegroundColor Cyan
Write-Host "Close that window to stop the service." -ForegroundColor Cyan
Write-Host ""

$backendPath = Join-Path $PSScriptRoot "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; python auto_news_fetcher.py"

Start-Sleep -Seconds 2
Write-Host "News fetcher service started!" -ForegroundColor Green
Write-Host "Check the new window for live updates" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
