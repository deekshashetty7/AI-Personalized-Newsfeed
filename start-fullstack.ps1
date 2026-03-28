# AI Personalized NewsFeed - Complete Startup Guide
# ================================================

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "AI Personalized NewsFeed Startup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if MongoDB is running (optional - fallback data available)
Write-Host "Checking MongoDB connection..." -ForegroundColor Yellow
try {
    $mongoProcess = Get-Process mongod -ErrorAction SilentlyContinue
    if ($mongoProcess) {
        Write-Host "MongoDB is running" -ForegroundColor Green
    } else {
        Write-Host "MongoDB not detected - using fallback data" -ForegroundColor Yellow
        Write-Host "   To install MongoDB: https://www.mongodb.com/try/download/community" -ForegroundColor Gray
    }
} catch {
    Write-Host "MongoDB check failed - using fallback data" -ForegroundColor Yellow
}

Write-Host ""

# Get the script directory for relative paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start Backend
Write-Host "Starting Backend Server..." -ForegroundColor Green
Write-Host "   - Django REST API with JWT authentication" -ForegroundColor Gray
Write-Host "   - AI modules: Sentiment Analysis, Recommendations, Spam Detection" -ForegroundColor Gray
Write-Host "   - NewsAPI integration with fallback data" -ForegroundColor Gray
Write-Host ""

Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\backend'; python manage.py runserver"

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend Server..." -ForegroundColor Green
Write-Host "   - Next.js with TypeScript and TailwindCSS" -ForegroundColor Gray
Write-Host "   - Google News-inspired professional design" -ForegroundColor Gray
Write-Host "   - Responsive and mobile-friendly" -ForegroundColor Gray
Write-Host ""

Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\frontend'; npm run dev"

# Wait for servers to fully start
Start-Sleep -Seconds 5

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Servers Starting Successfully!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Frontend (UI):      http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend (API):      http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/api/" -ForegroundColor Cyan
Write-Host ""

Write-Host "Features Available:" -ForegroundColor Yellow
Write-Host "   - Real-time news fetching from NewsAPI" -ForegroundColor White
Write-Host "   - AI-powered sentiment analysis" -ForegroundColor White
Write-Host "   - Personalized recommendations" -ForegroundColor White
Write-Host "   - Spam detection and filtering" -ForegroundColor White
Write-Host "   - User authentication (JWT)" -ForegroundColor White
Write-Host "   - Interactive news cards with actions" -ForegroundColor White
Write-Host "   - Trending articles tracking" -ForegroundColor White
Write-Host "   - Professional Google News-style design" -ForegroundColor White
Write-Host "   - Mobile-responsive interface" -ForegroundColor White
Write-Host "   - Reading streak tracking" -ForegroundColor White
Write-Host ""

Write-Host "Quick Test Endpoints:" -ForegroundColor Yellow
Write-Host "   GET  /api/news/           - Fetch latest news" -ForegroundColor Gray
Write-Host "   GET  /api/trending/       - Trending articles" -ForegroundColor Gray
Write-Host "   POST /api/auth/register/  - User registration" -ForegroundColor Gray
Write-Host "   POST /api/auth/login/     - User login" -ForegroundColor Gray
Write-Host "   GET  /api/recommendations/ - AI recommendations" -ForegroundColor Gray
Write-Host ""

Write-Host "Usage Instructions:" -ForegroundColor Yellow
Write-Host "   1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "   2. Browse news without registration (public access)" -ForegroundColor White
Write-Host "   3. Register/Login for personalized features:" -ForegroundColor White
Write-Host "      - AI recommendations based on interests" -ForegroundColor White
Write-Host "      - Like/Save articles" -ForegroundColor White
Write-Host "      - Reading streak tracking" -ForegroundColor White
Write-Host "      - Personalized news categories" -ForegroundColor White
Write-Host "   4. Interact with articles to improve AI recommendations" -ForegroundColor White
Write-Host ""

Write-Host "Development Notes:" -ForegroundColor Yellow
Write-Host "   - Frontend auto-reloads on file changes" -ForegroundColor White
Write-Host "   - Backend serves both API and fallback data" -ForegroundColor White
Write-Host "   - MongoDB optional (fallback data available)" -ForegroundColor White
Write-Host "   - All AI modules are lightweight and fast" -ForegroundColor White
Write-Host ""

# Try to open browser
try {
    Start-Sleep -Seconds 2
    Write-Host "Opening browser..." -ForegroundColor Green
    Start-Process "http://localhost:3000"
} catch {
    Write-Host "Please manually open http://localhost:3000 in your browser" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Ready to explore your AI-powered news experience!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan