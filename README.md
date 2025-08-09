# TypeRacer Analytics Dashboard

Web application for analyzing TypeRacer race data. Built with React frontend and FastAPI backend using Polars for high-performance data processing.

## Features

- **Interactive Charts**: 15+ chart types including WPM distribution, performance trends, accuracy analysis, and rank statistics
- **Data Upload**: Support for CSV file upload or use included sample data
- **Performance Metrics**: Rolling averages, cumulative statistics, and consistency scoring
- **Time Analysis**: Performance by hour of day, time between races, and monthly trends
- **Text Analysis**: Performance breakdown by specific TypeRacer text passages
- **Responsive Design**: Works across desktop and mobile devices

## Architecture

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and builds
- **Styling**: Tailwind CSS for utility-first styling
- **Charts**: Plotly.js for interactive visualizations
- **HTTP Client**: Fetch API for backend communication

### Backend
- **API Framework**: FastAPI for high-performance Python API
- **Data Processing**: Polars for fast DataFrame operations
- **Chart Generation**: Plotly for server-side chart creation
- **File Handling**: Python multipart for CSV uploads
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

### Data Management
- `POST /upload-data` - Upload CSV file for analysis
- `POST /use-sample-data` - Load included sample race data
- `GET /stats` - Get basic statistics summary

### Chart Endpoints
- `GET /charts/wpm-distribution` - WPM histogram with mean/median
- `GET /charts/performance-over-time` - Monthly average WPM trends
- `GET /charts/rolling-average` - 100-race rolling average
- `GET /charts/rank-distribution` - Race ranking frequency
- `GET /charts/hourly-performance` - Performance by hour of day
- `GET /charts/accuracy-distribution` - Accuracy histogram
- `GET /charts/daily-performance` - Daily WPM averages
- `GET /charts/wpm-vs-accuracy` - Scatter plot analysis
- `GET /charts/win-rate-monthly` - Monthly win rate trends
- `GET /charts/top-texts` - Best/worst performing texts
- `GET /charts/consistency-score` - WPM consistency over time
- `GET /charts/accuracy-by-rank` - Accuracy correlation with ranking
- `GET /charts/cumulative-accuracy` - Cumulative accuracy trends

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
The project uses ESLint for JavaScript/TypeScript linting and follows Python PEP 8 standards.

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
- Vercel
- Netlify
- GitHub Pages
- AWS S3 + CloudFront

Configure CORS origins in the backend for production domains.