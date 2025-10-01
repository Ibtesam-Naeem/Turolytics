# Turolytics - Turo Fleet Analytics Platform

A comprehensive analytics platform for Turo fleet management, featuring automated data scraping, real-time tracking, and financial analytics.

## 🚀 Features

- **Automated Data Scraping**: Playwright-based scraping of Turo host dashboard
- **Real-time Analytics**: Live vehicle tracking and performance metrics
- **Financial Management**: Earnings analysis, payout tracking, and revenue optimization
- **Customer Insights**: Review analysis and customer behavior patterns
- **RESTful API**: FastAPI-based backend with comprehensive endpoints
- **PostgreSQL Database**: Production-ready data storage with optimized queries

## 🏗️ Architecture

```
Turolytics/
├── backend/                 # FastAPI Backend
│   ├── app.py              # Main FastAPI application
│   ├── requirements.txt    # Python dependencies
│   ├── config/             # Configuration management
│   ├── database/           # Database models and operations
│   ├── services/           # Business logic services
│   ├── turo_data/          # Turo scraping modules
│   └── utils/              # Utility functions
└── README.md
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **PostgreSQL** - Production database
- **SQLAlchemy** - ORM and database management
- **Playwright** - Web automation and scraping
- **Pydantic** - Data validation and settings

### Data Processing
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **JSON** - Data serialization

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Node.js 16+ (for frontend)

### Backend Setup

1. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL database**
   ```bash
   # Create database and user
   psql -c "CREATE DATABASE turolytics;"
   psql -c "CREATE USER turolytics_user WITH PASSWORD 'turolyticstestdb';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE turolytics TO turolytics_user;"
   ```

3. **Configure environment variables**
   ```bash
   export DATABASE_URL="postgresql://turolytics_user:turolyticstestdb@localhost:5432/turolytics"
   export SECRET_KEY="your-secret-key-here"
   export DEBUG="true"
   ```

4. **Start the API server**
   ```bash
   python app.py
   # OR
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Test the API**
   ```bash
   curl http://localhost:8000/health
   ```

## 📊 API Endpoints

### Core Endpoints
- `GET /` - API information and status
- `GET /health` - Health check with database status

### Data Endpoints
- `GET /api/vehicles` - Get vehicle data
- `GET /api/trips` - Get trip/booking data
- `GET /api/reviews` - Get customer reviews
- `GET /api/stats` - Get analytics statistics

### Scraping Endpoints
- `POST /api/scrape/vehicles` - Scrape vehicle data
- `POST /api/scrape/trips` - Scrape trip data
- `POST /api/scrape/earnings` - Scrape earnings data
- `POST /api/scrape/reviews` - Scrape review data
- `POST /api/scrape/all` - Scrape all data types

### Task Management
- `GET /api/tasks` - Get all scraping tasks
- `GET /api/tasks/{task_id}` - Get specific task status

## 🔧 Configuration

The application uses environment-based configuration:

```python
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/turolytics
USE_SQLITE=false

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Scraping
SCRAPING_TIMEOUT=300
SCRAPING_HEADLESS=true
MAX_CONCURRENT_TASKS=5

# Security
SECRET_KEY=your-secret-key-here
```

## 📈 Data Models

### Vehicles
- Vehicle information (make, model, year, license plate)
- Performance metrics (rating, trip count, last trip)
- Status tracking (active, maintenance, etc.)

### Trips
- Booking details (dates, customer info, pricing)
- Financial data (earnings, fees, payouts)
- Status tracking (active, completed, cancelled)

### Reviews
- Customer feedback and ratings
- Review content and sentiment
- Response management

## 🔒 Security Features

- Environment-based configuration
- Secure database connections
- Input validation with Pydantic
- Error handling and logging
- CORS configuration

## 🚀 Deployment

### Production Checklist
- [ ] Set production environment variables
- [ ] Configure PostgreSQL with proper credentials
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (nginx)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 Development

### Code Structure
- **Modular Design**: Separated concerns with clear boundaries
- **Type Hints**: Full type annotation for better IDE support
- **Async/Await**: Non-blocking operations throughout
- **Error Handling**: Comprehensive error management
- **Logging**: Structured logging for debugging

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=backend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is for portfolio and educational purposes.

## 🎯 Future Enhancements

- [ ] Frontend dashboard (React/Next.js)
- [ ] Real-time notifications
- [ ] Advanced analytics and ML insights
- [ ] Mobile app integration
- [ ] Multi-account support
- [ ] Automated reporting
- [ ] Integration with financial tools

---
