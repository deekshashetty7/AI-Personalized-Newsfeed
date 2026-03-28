# Full restart script for NEWS application

Write-Host "🛑 Stopping all servers..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -eq "python" -or $_.ProcessName -eq "node"} | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "🗑️ Cleaning Next.js cache..." -ForegroundColor Yellow
if (Test-Path "d:\new\NEWS\frontend\.next") {
    Remove-Item "d:\new\NEWS\frontend\.next" -Recurse -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2

Write-Host "🚀 Starting backend server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd d:\new\NEWS\backend; python manage.py runserver"

Start-Sleep -Seconds 3

Write-Host "🚀 Starting frontend server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd d:\new\NEWS\frontend; npm run dev"

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "✅ Servers started!" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️ IMPORTANT: Open in INCOGNITO/PRIVATE window to avoid cache issues!" -ForegroundColor Yellow
Write-Host "   Chrome: Ctrl+Shift+N" -ForegroundColor White
Write-Host "   Firefox: Ctrl+Shift+P" -ForegroundColor White
Write-Host "   Edge: Ctrl+Shift+N" -ForegroundColor White
