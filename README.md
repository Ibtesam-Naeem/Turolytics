# Turolytics - Turo Fleet Analytics Platform

A comprehensive analytics platform for Turo fleet management, featuring automated data scraping, real-time tracking, and financial analytics.

## 🚀 Features

- **Automated Data Scraping**: Playwright-based scraping of Turo host dashboard
- **Real-time Analytics**: Live vehicle tracking and performance metrics
- **Financial Management**: Earnings analysis, payout tracking, and revenue optimization
- **Customer Insights**: Review analysis and customer behavior patterns
- **Machine Learning**: Predictive analytics, clustering, and anomaly detection
- **RESTful API**: FastAPI-based backend with comprehensive endpoints
- **PostgreSQL Database**: Production-ready data storage with optimized queries

## 🏗️ Architecture

```
Turolytics/
├── backend/                 # FastAPI Backend
│   ├── main.py             # Main FastAPI application
│   ├── requirements.txt    # Python dependencies
│   ├── core/               # Core modules
│   │   ├── config/         # Configuration management
│   │   ├── db/             # Database models and operations
│   │   ├── services/       # Business logic services
│   │   └── utils/          # Utility functions
│   ├── turo/               # Turo scraping modules
│   ├── bouncie/            # Bouncie API integration
│   ├── plaid/              # Plaid API integration
│   ├── ml_service/         # Machine Learning service
│   └── documents/          # Document processing
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
- **scikit-learn** - Machine learning algorithms
- **JSON** - Data serialization

### APIs & Integrations
- **Bouncie API** - Vehicle telemetry and tracking
- **Plaid API** - Financial transaction data
- **Turo Scraping** - Host dashboard automation

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
   psql -c "CREATE USER your_user WITH PASSWORD 'your_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE turolytics TO your_user;"
   ```

3. **Configure environment variables**
   ```bash
   # Create .env file in backend/ directory
   cp env.example .env
   # Edit .env with your actual credentials
   
   # Or export directly
   export DATABASE_URL="postgresql://your_user:your_password@localhost:5432/turolytics"
   export SECRET_KEY="your-secret-key-here"
   export DEBUG="true"
   ```

4. **Start the API server**
   ```bash
   python main.py
   # OR
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Start the ML service (optional)**
   ```bash
   cd ml_service
   python -m uvicorn ml_app:app --host 0.0.0.0 --port 8001
   ```

6. **Test the API**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8001/predict/revenue?account_email=demo@example.com&days=7
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

### Machine Learning (Port 8001)
- `GET /predict/revenue` - Revenue forecasting
- `GET /optimize/trips` - Trip optimization recommendations
- `GET /predict/maintenance` - Vehicle maintenance predictions
- `GET /cluster/trip-patterns` - Trip pattern clustering
- `GET /cluster/vehicles` - Vehicle usage clustering
- `GET /anomaly/spending` - Spending anomaly detection
- `GET /anomaly/vehicle-issues` - Vehicle issue detection
- `GET /analytics/comprehensive` - Complete analytics dashboard

## 🔧 Configuration

The application uses environment-based configuration:

```bash
# Database
DATABASE_URL=changed-to-real-deploy-db-
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

# API Keys (add your own)
TURO_EMAIL=your-email@example.com
TURO_PASSWORD=your-password
BOUNCIE_CLIENT_ID=your-bouncie-client-id
BOUNCIE_CLIENT_SECRET=your-bouncie-secret
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
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
- **No hardcoded credentials** - All sensitive data in environment variables
- API key management through `.env` files

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

## 🔐 Security Notice

**Important**: This repository contains no hardcoded credentials or sensitive information. All API keys, database credentials, and other sensitive data are managed through environment variables. 

- Never commit `.env` files to version control
- Use `env.example` as a template for your local configuration
- Rotate API keys regularly in production
- Use strong, unique passwords for all services

## 📄 License

This project is for portfolio and educational purposes.

## 🧠 Machine Learning Features

The platform includes a comprehensive ML service for advanced analytics:

### Predictive Analytics
- **Revenue Forecasting**: Predict future earnings using RandomForest regression
- **Trip Optimization**: Data-driven recommendations for optimal pricing and timing
- **Maintenance Prediction**: Proactive vehicle maintenance scheduling

### Clustering Analysis
- **Trip Patterns**: Group similar trips to identify profitable patterns
- **Vehicle Usage**: Categorize vehicles by performance and profitability
- **Geographic Hotspots**: Identify high-value rental locations

### Anomaly Detection
- **Spending Patterns**: Detect unusual financial transactions
- **Vehicle Issues**: Identify problematic driving patterns
- **Performance Outliers**: Flag underperforming trips or vehicles

## 🎯 Future Enhancements

- [ ] Frontend dashboard (React/Next.js)
- [ ] Real-time notifications
- [ ] Advanced ML model training
- [ ] Mobile app integration
- [ ] Multi-account support
- [ ] Automated reporting
- [ ] Integration with financial tools
- [ ] Real-time ML model updates

---
