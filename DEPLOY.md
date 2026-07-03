# Deployment Guide

This project can be deployed with Docker (recommended) or manually on any VPS/cloud provider.

## Prerequisites

- Docker and Docker Compose **or**
- Python 3.11+, Node.js 18+
- API keys (see `.env.example` files)

## Quick Deploy (Docker)

1. **Clone the repository**
   ```bash
   git clone https://github.com/deekshashetty7/AI-Personalized-Newsfeed.git
   cd AI-Personalized-Newsfeed
   ```

2. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```
   Edit `backend/.env` and set at minimum:
   - `SECRET_KEY`
   - `DEBUG=False`
   - `ALLOWED_HOSTS` (your backend domain)
   - `CORS_ALLOWED_ORIGINS` (your frontend URL)
   - `NEWS_API_KEY` (and other API keys as needed)

   Edit `frontend/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-domain.com/api
   ```

3. **Start services**
   ```bash
   docker compose up --build -d
   ```

4. **Open the app**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api

## Manual Production Deploy

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements-prod.txt
cp .env.example .env        # then edit values
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn news_backend.wsgi:application --bind 0.0.0.0:8000 --workers 2
```

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env.local  # set NEXT_PUBLIC_API_URL
npm run build
npm run start
```

## Suggested Hosting

| Component | Options |
|-----------|---------|
| Frontend | Vercel, Netlify, Railway |
| Backend | Railway, Render, Fly.io, AWS EC2 |
| Database | SQLite (default) or MongoDB Atlas |

### Vercel (Frontend)

1. Import the GitHub repo
2. Set root directory to `frontend`
3. Add env: `NEXT_PUBLIC_API_URL=https://your-api.com/api`
4. Deploy

### Render / Railway (Backend)

1. Set root directory to `backend`
2. Build: `pip install -r requirements-prod.txt && python manage.py collectstatic --noinput`
3. Start: `python manage.py migrate && gunicorn news_backend.wsgi:application --bind 0.0.0.0:$PORT`
4. Add all variables from `backend/.env.example`

## Post-Deploy Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] CORS points to your frontend domain only
- [ ] API keys set in environment (never commit `.env`)
- [ ] Run migrations on the backend
- [ ] Fetch initial news: `python backend/fast_fetch_today.py`

## Environment Files

| File | Purpose |
|------|---------|
| `backend/.env.example` | Backend template (copy to `.env`) |
| `frontend/.env.example` | Frontend template (copy to `.env.local`) |

Never commit real `.env` or `.env.local` files.
