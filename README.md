# AI Personalized NewsFeed - Complete Project

A full-stack AI-powered personalized news application with intelligent recommendations, sentiment analysis, and spam detection.

## 🎯 Features

- **AI-Powered Recommendations**: Hybrid recommendation engine combining content-based and collaborative filtering
- **Sentiment Analysis**: Real-time sentiment detection on articles using TextBlob
- **Spam Detection**: Advanced spam and clickbait detection
- **User Authentication**: Secure JWT-based authentication
- **Personalized Feed**: News tailored to user interests
- **Trending Articles**: Real-time trending news based on user interactions
- **Interactive UI**: Like, save, share, and comment on articles
- **Reading Streak**: Track user engagement
- **MongoDB Database**: Flexible NoSQL database for storing articles and user data

## 🛠️ Tech Stack

### Backend
- **Python 3.9+**
- **Django 4.2** - Web framework
- **Django REST Framework** - API development
- **MongoDB** - NoSQL database (via Djongo)
- **TextBlob** - Sentiment analysis
- **Scikit-learn** - Recommendation engine
- **NewsAPI** - News data source

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **Axios** - HTTP client
- **Lucide Icons** - Icon library
- **date-fns** - Date formatting

## 📁 Project Structure

```
NEWS/
├── backend/                    # Django backend
│   ├── api/                   # Main API app
│   │   ├── ai_modules/       # AI/ML modules
│   │   │   ├── sentiment_analysis.py
│   │   │   ├── spam_detection.py
│   │   │   └── recommendation.py
│   │   ├── models.py         # Database models
│   │   ├── serializers.py    # DRF serializers
│   │   ├── views.py          # API endpoints
│   │   ├── urls.py           # URL routing
│   │   └── services.py       # News fetching service
│   ├── news_backend/         # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── manage.py
│   ├── requirements.txt
│   └── .env
│
└── frontend/                  # Next.js frontend
    ├── src/
    │   ├── app/              # Next.js pages
    │   │   ├── page.tsx      # Public home
    │   │   ├── login/
    │   │   ├── register/
    │   │   ├── home/         # Personalized feed
    │   │   └── profile/
    │   ├── components/       # Reusable components
    │   │   ├── Header.tsx
    │   │   ├── NewsCard.tsx
    │   │   ├── AIPanel.tsx
    │   │   └── LoadingSpinner.tsx
    │   ├── contexts/         # React contexts
    │   │   └── AuthContext.tsx
    │   ├── lib/              # Utilities
    │   │   └── api.ts        # API client
    │   └── types/            # TypeScript types
    │       └── index.ts
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.js
    └── .env.local
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- MongoDB (running locally on port 27017)
- NewsAPI key (already configured: `ab8030efca974e9ab9cd0281b632b5fb`)

### Backend Setup

1. **Navigate to backend directory:**
   ```powershell
   cd d:\NEWS\backend
   ```

2. **Create and activate virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - The `.env` file is already created with default values
   - Update if needed (MongoDB connection, API keys, etc.)

5. **Run migrations:**
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser (optional):**
   ```powershell
   python manage.py createsuperuser
   ```

7. **Start the development server:**
   ```powershell
   python manage.py runserver
   ```

   Backend will run on: `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```powershell
   cd d:\NEWS\frontend
   ```

2. **Install dependencies:**
   ```powershell
   npm install
   ```

3. **Configure environment variables:**
   - The `.env.local` file is already created
   - It points to `http://localhost:8000/api` by default

4. **Start the development server:**
   ```powershell
   npm run dev
   ```

   Frontend will run on: `http://localhost:3000`

## 📊 Database Collections

### users
- User account information
- Interests and preferences
- Reading streak tracking

### news_articles
- Article content and metadata
- AI-generated sentiment scores
- Spam detection flags

### news_sources
- Configured news sources
- Credibility scores

### user_preferences
- User category preferences
- AI-learned preference weights

### interactions
- User interactions (like, save, share, etc.)
- Sentiment analysis of comments

### recommendations
- Generated article recommendations
- Model version tracking

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login user

### User Profile
- `GET /api/user/profile/` - Get user profile
- `PUT /api/user/profile/update/` - Update profile

### News
- `GET /api/news/` - Get news articles (with filters)
- `GET /api/news/<id>/` - Get article details
- `POST /api/news/refresh/` - Refresh news from API
- `GET /api/categories/` - Get available categories
- `GET /api/trending/` - Get trending articles

### Interactions
- `POST /api/interactions/` - Create interaction
- `GET /api/interactions/my/` - Get user interactions

### Recommendations
- `GET /api/recommendations/` - Get personalized recommendations

## 🤖 AI Modules

### 1. Sentiment Analysis
- **Model**: TextBlob
- **Input**: Article text (title + content)
- **Output**: Sentiment score (-1 to 1)
- **Features**:
  - Text cleaning and preprocessing
  - Polarity detection
  - Sentiment categorization (positive/neutral/negative)

### 2. Recommendation Engine
- **Type**: Hybrid (Content-based + Collaborative)
- **Components**:
  - TF-IDF vectorization for content similarity
  - User interaction history analysis
  - Trending articles boosting
- **Weights**:
  - Content-based: 40%
  - Collaborative: 35%
  - Trending: 25%

### 3. Spam Detection
- **Type**: Rule-based pattern matching
- **Detection**:
  - Spam keywords identification
  - Clickbait pattern recognition
  - Excessive capitalization/punctuation
- **Threshold**: 0.5 spam score

## 🎨 UI Design

### Color Palette
- **Primary**: #1A73E8 (Google Blue)
- **Background**: #F5F5F5 (Light Gray)
- **Text**: #333333 (Dark Gray)
- **Text Secondary**: #5F6368 (Medium Gray)

### Typography
- **Font Family**: Inter, Roboto, system-ui

### Layout
- Clean three-column grid
- Sticky header navigation
- Right-side AI insights panel
- Responsive design (mobile-first)

## 📱 Pages

### Public Home (`/`)
- Hero section with CTA
- Feature showcase
- Latest news preview
- No authentication required

### Login (`/login`)
- Email and password authentication
- JWT token-based sessions
- Error handling

### Register (`/register`)
- User registration form
- Interest selection
- Password confirmation

### Personalized Home (`/home`)
- AI-powered newsfeed
- Category filtering
- Three tabs: All, For You, Trending
- AI insights panel
- Interactive article cards

### Profile (`/profile`)
- User information display/edit
- Reading statistics
- Interest management
- Streak tracking

## 🔒 Authentication Flow

1. User registers or logs in
2. Backend generates JWT access and refresh tokens
3. Tokens stored in localStorage
4. Access token sent with each API request
5. Automatic token refresh on expiration
6. Protected routes redirect to login if not authenticated

## 📈 Recommendation Algorithm

1. **Content Analysis**: TF-IDF vectorization of articles and user interests
2. **Collaborative Filtering**: Find similar users based on interaction patterns
3. **Trending Boost**: Recent popular articles get higher weights
4. **Sentiment Weighting**: Positive interactions increase category preferences
5. **Final Score**: Weighted combination of all factors

## 🛡️ Security Features

- JWT token-based authentication
- Password hashing (Django's built-in)
- CORS protection
- Input validation
- SQL injection prevention (ORM)
- XSS protection

## 🚦 Running in Production

### Backend
```powershell
# Set DEBUG=False in .env
# Configure proper database credentials
# Set up proper SECRET_KEY
python manage.py collectstatic
gunicorn news_backend.wsgi:application
```

### Frontend
```powershell
npm run build
npm start
```

## 🐛 Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running: `mongod`
- Check connection string in `.env`
- Verify port 27017 is not blocked

### NewsAPI Rate Limits
- Free tier: 100 requests/day
- Hardcoded fallback news available
- Consider caching articles

### CORS Errors
- Check CORS_ALLOWED_ORIGINS in `settings.py`
- Ensure frontend URL is whitelisted

## 📝 Notes

- The project includes hardcoded fallback news data for when NewsAPI is unavailable
- All TypeScript/JSX lint errors are expected until `npm install` is run
- MongoDB should be running before starting the backend
- First-time users should select interests during registration for better recommendations

## 👨‍💻 Development

### Adding New Features
1. Backend: Create views in `api/views.py`
2. Add URL patterns in `api/urls.py`
3. Frontend: Create components in `src/components/`
4. Add pages in `src/app/`

### Testing
- Backend: `python manage.py test`
- Frontend: `npm test`

## 📄 License

This project is created for educational purposes.

## 🤝 Contributing

This is a complete project template. Feel free to customize and extend!

---

**Happy Coding! 🚀**
#   A I - P e r s o n a l i z e d - N e w s f e e d  
 #   A I - P e r s o n a l i z e d - N e w s f e e d  
 