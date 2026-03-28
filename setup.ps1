# AI Personalized NewsFeed - Complete Setup Script
# Run this script to set up the entire project

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "AI Personalized NewsFeed Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if MongoDB is running
Write-Host "Checking MongoDB..." -ForegroundColor Yellow
$mongoRunning = Get-Process mongod -ErrorAction SilentlyContinue
if ($mongoRunning) {
    Write-Host " MongoDB is running" -ForegroundColor Green
} else {
    Write-Host " MongoDB is not running" -ForegroundColor Red
    Write-Host "  Please start MongoDB before continuing" -ForegroundColor Yellow
    Write-Host "  Run: mongod" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Setting up Backend" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Navigate to backend
Set-Location -Path "d:\new\NEWS\backend"

# Create virtual environment
Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install Python dependencies
Write-Host "Installing Python dependencies (this may take a few minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Yellow
python manage.py makemigrations
python manage.py migrate

Write-Host "✓ Backend setup complete!" -ForegroundColor Green

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Setting up Frontend" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Navigate to frontend
Set-Location -Path "d:\new\NEWS\frontend"

# Install Node dependencies
Write-Host "Installing Node.js dependencies, this may take a few minutes..." -ForegroundColor Yellow
npm install

Write-Host "✓ Frontend setup complete!" -ForegroundColor Green

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Setup Complete! 🎉" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Start the Backend:" -ForegroundColor White
Write-Host "   cd d:\new\NEWS\backend" -ForegroundColor Gray
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   python manage.py runserver" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the Frontend (in a new terminal):" -ForegroundColor White
Write-Host "   cd d:\new\NEWS\frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Open your browser:" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "   Backend API: http://localhost:8000/api" -ForegroundColor Gray
Write-Host "   Admin Panel: http://localhost:8000/admin" -ForegroundColor Gray
Write-Host ""
Write-Host "For more details, see README.md" -ForegroundColor Cyan
Write-Host ""
