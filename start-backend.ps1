# Quick Start Scripts for AI Personalized NewsFeed

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Starting Backend Server" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path "$scriptDir\backend"

# Start Django server
Write-Host "Starting Django development server..." -ForegroundColor Yellow
Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host ""
python manage.py runserver
