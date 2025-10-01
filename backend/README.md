# Turolytics Backend - Domain-Driven Architecture

This backend follows a **Domain-Driven Design (DDD)** approach with clear separation of concerns.

## 📁 Directory Structure

```
backend/
├── core/                     # Shared infrastructure
│   ├── config/               # Logging, environment settings
│   ├── db/                   # Database models and operations
│   │   ├── base.py
│   │   ├── models.py
│   │   ├── operations/
│   │   └── schemas/
│   ├── utils/                # Helper functions
│   └── security/             # Authentication and session management
│
├── turo/                     # Turo domain
│   ├── routes.py             # FastAPI endpoints (/api/turo/*)
│   ├── service.py            # Business logic and scraping
│   ├── earnings.py
│   ├── trips.py
│   ├── vehicles.py
│   └── ...
│
├── plaid/                    # Plaid domain
│   ├── routes.py             # FastAPI endpoints (/api/plaid/*)
│   ├── service.py            # Plaid API integration
│   ├── api.py
│   ├── auth.py
│   └── client.py
│
├── bouncie/                  # Bouncie domain (future)
│   ├── routes.py
│   ├── service.py
│   └── telemetry.py
│
├── main.py                   # FastAPI app entry point
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

3. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 🏗️ Architecture Benefits

### ✅ **Domain Separation**
- Each domain (`turo/`, `plaid/`, `bouncie/`) is self-contained
- Clear boundaries between different business areas
- Easy to understand and maintain

### ✅ **Scalability**
- Adding new integrations is straightforward
- Each domain can evolve independently
- Clear import paths and dependencies

### ✅ **Maintainability**
- Related code is co-located
- Easy to test individual domains
- Clear separation of concerns

### ✅ **Team Development**
- Different developers can work on different domains
- Reduced merge conflicts
- Clear ownership boundaries

## 📡 API Endpoints

### Turo Domain (`/api/turo/`)
- `GET /vehicles` - Get vehicle data
- `GET /trips` - Get trip data
- `GET /reviews` - Get review data
- `GET /earnings` - Get earnings data
- `POST /scrape/*` - Trigger data scraping
- `GET /tasks` - Get scraping task status

### Plaid Domain (`/api/plaid/`)
- `POST /link-token` - Create Plaid link token
- `POST /exchange-token` - Exchange public token
- `GET /accounts/{user_id}` - Get account data
- `GET /transactions/{user_id}` - Get transaction data
- `POST /sync/{user_id}` - Sync all data

### Bouncie Domain (`/api/bouncie/`)
- *Coming soon...*

## 🔧 Development

### Adding a New Domain
1. Create a new directory under `backend/`
2. Add `routes.py` for API endpoints
3. Add `service.py` for business logic
4. Import and include the router in `main.py`

### Adding New Core Features
1. Add to appropriate `core/` subdirectory
2. Update imports across domains as needed
3. Maintain clear separation of concerns

## 🧪 Testing

Each domain should have its own test suite:
- Unit tests for business logic
- Integration tests for API endpoints
- Mock external dependencies

## 📝 Notes

- All domains share the same database and core infrastructure
- Configuration is centralized in `core/config/`
- Database operations are in `core/db/operations/`
- Shared utilities are in `core/utils/`
