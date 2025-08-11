# TypeRacer Analytics Dashboard

A stateless web application for analyzing TypeRacer race data with an enhanced, minimalist design. Built with React frontend and FastAPI backend using Polars for high-performance data processing.

## Features

- **17 Interactive Charts**: Comprehensive visualization suite including WPM distribution, performance trends, accuracy analysis, outlier detection, and advanced text analysis
- **Intelligent Insights**: AI-generated insights for each chart using backend calculations
- **Stateless Architecture**: No database required - processes data directly from CSV uploads with localStorage persistence
- **Data Upload**: Support for CSV file upload or use included sample data
- **Performance Metrics**: Rolling averages, cumulative statistics, consistency scoring, and win rate analysis
- **Advanced Analytics**: Time between races impact, frequent text improvement tracking, and race difficulty analysis
- **Minimalist Dark Theme**: Clean, modern interface with Spotify-green accents
- **Responsive Design**: Optimized for both desktop and mobile devices with scroll-based chart loading

## Architecture

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and builds
- **Styling**: Tailwind CSS with custom dark theme and Spotify-green accent colors
- **Charts**: Plotly.js for interactive visualizations with dark theme optimization
- **State Management**: Local state with localStorage persistence (stateless design)
- **HTTP Client**: Fetch API for backend communication

### Backend
- **API Framework**: FastAPI 2.0 for high-performance Python API
- **Data Processing**: Polars for lightning-fast DataFrame operations
- **Chart Generation**: Server-side Plotly chart creation with dark theme styling
- **Insights Engine**: Automated insight calculation with fallback handling
- **File Handling**: Direct CSV processing without file storage
- **CORS**: Configured for frontend-backend communication

## Data Processing

The application processes TypeRacer CSV exports containing:
- Race numbers and timestamps
- Words per minute (WPM) scores
- Accuracy percentages
- Race rankings and participant counts
- Text ID references

Polars handles data transformations including datetime parsing, rolling averages, and statistical calculations.

## Setup

### Prerequisites
- Python 3.8+
- Node.js 16+

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and connects to the backend at `http://localhost:8000`.

## API Endpoints

### Core Endpoints
- `GET /health` - Health check endpoint
- `POST /stats` - Get basic statistics summary from CSV data

### Chart Endpoints (All with Insights)
- `POST /charts/wpm-distribution` - WPM histogram with mean/median lines
- `POST /charts/performance-over-time` - Monthly average WPM trends
- `POST /charts/rolling-average` - 100-race rolling average
- `POST /charts/rank-distribution` - Race ranking frequency analysis
- `POST /charts/hourly-performance` - Performance by hour of day
- `POST /charts/accuracy-distribution` - Accuracy histogram analysis
- `POST /charts/daily-performance` - Daily WPM averages over time
- `POST /charts/wpm-vs-accuracy` - WPM vs accuracy correlation scatter plot
- `POST /charts/win-rate-monthly` - Monthly win rate trends
- `POST /charts/top-texts` - Best/worst performing texts (5+ races minimum)
- `POST /charts/consistency-score` - WPM consistency via rolling standard deviation
- `POST /charts/accuracy-by-rank` - Average accuracy by finishing rank
- `POST /charts/cumulative-accuracy` - Cumulative accuracy trends
- `POST /charts/wmp-by-rank-boxplot` - WPM outlier analysis by rank
- `POST /charts/racers-impact` - Impact of number of racers on performance
- `POST /charts/frequent-texts-improvement` - WPM trends for top 5 most frequent texts
- `POST /charts/top-texts-distribution` - WPM distribution boxplots for top 10 texts
- `POST /charts/win-rate-after-win` - Win rate following wins vs losses
- `POST /charts/fastest-slowest-races` - Top 5 fastest and slowest individual races
- `POST /charts/time-between-races` - Performance impact of time gaps between races

## Development

### Running Tests
```bash
# Backend tests (if available)
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
The project uses ESLint for JavaScript/TypeScript linting and follows Python PEP 8 standards. The application is designed to be stateless and requires no database setup.

## Deployment

### Backend Deployment
Compatible with Python hosting services:
- Railway
- Render
- Heroku
- DigitalOcean App Platform
- AWS Lambda (with FastAPI adapter)

### Frontend Deployment
Static site deployment options:
- Vercel (recommended)
- Netlify
- GitHub Pages
- AWS S3 + CloudFront

### Production Notes
- Configure CORS origins in `backend/config.py` for production domains
- The application is fully stateless - no database or persistent storage required
- All data processing happens in-memory with client-side localStorage for session persistence
- Optimized for fast loading with scroll-based chart rendering