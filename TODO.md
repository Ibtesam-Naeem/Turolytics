# Turolytics - Development TODO

## Status Overview

### ✅ Complete Features

- **Dashboard** - Complete (except banking integration)
- **Trip History** - Complete (minor mapping bugs to fix)
- **Map** - Complete
- **Settings** - Complete
- **Vehicle Overview** - Complete (documents page redirect needs fixing)
- **Reviews** - Complete
- **ROI Calculator** - Complete (with database integration)

---

## 🔨 Features Needing Work

### 1. Banking Page
**Status:** UI exists with mock data, needs full backend implementation

**Current State:**
- Frontend page exists at `frontend/src/pages/Banking.tsx`
- All data is hardcoded mock data
- No API integration
- No database models

**What Needs to be Done:**

#### Backend:
- [ ] Create database models for:
  - `BankAccount` - Store linked bank accounts
  - `BankTransaction` - Store transactions from linked accounts
  - `PayoutReconciliation` - Match Turo payouts with bank deposits
  - `ExpenseCategory` - Categorize expenses
- [ ] Integrate Plaid API (or similar banking API):
  - OAuth flow for linking accounts
  - Webhook handlers for transaction updates
  - Account balance sync
- [ ] Create API endpoints:
  - `GET /api/banking/accounts` - Get linked accounts
  - `POST /api/banking/accounts/link` - Link new account
  - `DELETE /api/banking/accounts/{id}` - Unlink account
  - `GET /api/banking/transactions` - Get transactions
  - `GET /api/banking/reconciliation` - Get payout reconciliation
  - `POST /api/banking/reconciliation/match` - Match payout to transaction
  - `GET /api/banking/expenses` - Get categorized expenses
- [ ] Create service layer for Plaid integration

#### Frontend:
- [ ] Replace mock data with API calls
- [ ] Add loading states
- [ ] Add error handling
- [ ] Implement "Link Account" functionality
- [ ] Add transaction filtering and search
- [ ] Add reconciliation matching UI
- [ ] Add export functionality (CSV, Excel, PDF)

**Priority:** High (if banking is critical for demo)

---

### 2. Documents Page
**Status:** UI exists, needs S3 integration completion

**Current State:**
- Frontend page exists at `frontend/src/pages/Documents.tsx`
- Some S3 backend exists (`backend/s3/`)
- Document service exists (`frontend/src/services/document-service.ts`)
- Mock data in frontend

**What Needs to be Done:**

#### Backend:
- [ ] Verify S3 service is complete:
  - Upload functionality
  - Download functionality
  - Delete functionality
  - List documents
- [ ] Ensure document categories are properly handled
- [ ] Add document expiry tracking
- [ ] Add document versioning (if needed)
- [ ] Add document sharing/permissions

#### Frontend:
- [ ] Replace mock data with real API calls
- [ ] Complete upload flow:
  - File selection
  - Progress indicator
  - Error handling
  - Success feedback
- [ ] Complete download flow
- [ ] Add document preview (if applicable)
- [ ] Add expiry date warnings
- [ ] Fix vehicle documents page redirect
- [ ] Add document search and filtering
- [ ] Add bulk operations

**Priority:** Medium-High

---

### 3. Maintenance Page
**Status:** UI exists with hardcoded mock data, needs full implementation

**Current State:**
- Frontend page exists at `frontend/src/pages/Maintenance.tsx`
- All data is hardcoded in component
- No backend integration
- No database models

**What Needs to be Done:**

#### Backend:
- [ ] Create database model `MaintenanceRecord`:
  - Vehicle ID (FK)
  - Maintenance type (oil change, tire rotation, brake service, etc.)
  - Scheduled date
  - Completed date
  - Cost
  - Service provider/notes
  - Odometer reading at service
  - Status (scheduled, completed, overdue)
- [ ] Create API endpoints:
  - `GET /api/maintenance/records` - Get all maintenance records
  - `GET /api/maintenance/vehicles/{vehicle_id}` - Get maintenance for a vehicle
  - `POST /api/maintenance/records` - Create new maintenance record
  - `PATCH /api/maintenance/records/{id}` - Update maintenance record
  - `POST /api/maintenance/records/{id}/complete` - Mark as completed
  - `DELETE /api/maintenance/records/{id}` - Delete maintenance record
  - `GET /api/maintenance/upcoming` - Get upcoming maintenance items
  - `GET /api/maintenance/stats` - Get maintenance statistics
- [ ] Integrate with existing DTC codes API (`/api/bouncie/dtc-codes`)
- [ ] Create maintenance service layer

#### Frontend:
- [ ] Replace mock data with API calls
- [ ] Create maintenance service (`maintenance-service.ts`)
- [ ] Connect to vehicle data API
- [ ] Connect to DTC codes API (for urgent issues)
- [ ] Connect to live vehicle data (for engine lights, etc.)
- [ ] Implement "Schedule Service" functionality
- [ ] Implement "Mark as Completed" functionality
- [ ] Add maintenance history view
- [ ] Add cost tracking
- [ ] Add filtering (urgent, scheduled, completed)
- [ ] Add search functionality
- [ ] Calculate maintenance scores based on:
  - Active DTC codes
  - Overdue scheduled maintenance
  - Mileage-based maintenance needs

**Priority:** Medium

---

### 4. Expense Tracking Page
**Status:** UI exists with mock data, needs backend implementation

**Current State:**
- Frontend page exists at `frontend/src/pages/ExpenseTracking.tsx`
- Expenses stored in component state (mock data)
- Some document upload functionality exists
- No backend integration

**What Needs to be Done:**

#### Backend:
- [ ] Create database model `Expense`:
  - Vehicle ID (FK, nullable for fleet-wide expenses)
  - Description
  - Category (Maintenance, Insurance, Fuel, Cleaning, Registration, Repairs, Other)
  - Amount
  - Date
  - Document ID (FK to documents table, nullable)
  - Created/updated timestamps
- [ ] Create API endpoints:
  - `GET /api/expenses` - Get expenses with filtering
  - `POST /api/expenses` - Create new expense
  - `PATCH /api/expenses/{id}` - Update expense
  - `DELETE /api/expenses/{id}` - Delete expense
  - `GET /api/expenses/stats` - Get expense statistics
  - `GET /api/expenses/categories` - Get expenses by category
- [ ] Link with documents service (for receipt uploads)
- [ ] Create expense service layer

#### Frontend:
- [ ] Replace mock data with API calls
- [ ] Create expense service (`expense-service.ts`)
- [ ] Complete expense creation flow:
  - Form validation
  - Document upload integration
  - Vehicle selection
  - Category selection
- [ ] Add expense editing
- [ ] Add expense deletion
- [ ] Add filtering and search
- [ ] Add date range filtering
- [ ] Add category filtering
- [ ] Add export functionality (CSV, PDF)
- [ ] Add expense statistics/charts
- [ ] Link with documents for receipt viewing

**Priority:** Medium

---

### 5. Analytics Page
**Status:** Components exist, likely needs real data integration

**Current State:**
- Frontend page exists at `frontend/src/pages/Analytics.tsx`
- Multiple analytics components exist in `frontend/src/components/analytics/`
- Likely using mock data

**What Needs to be Done:**

#### Backend:
- [ ] Review existing analytics endpoints
- [ ] Create/update analytics endpoints:
  - Revenue vs Expenses data
  - Profit margin calculations
  - Vehicle ROI calculations
  - Depreciation tracking
  - Expense breakdowns
  - Booking metrics
  - Revenue forecasting
  - Cash flow timeline
  - Seasonal demand data
  - Maintenance forecasting
  - Cost per mile
  - Idle days cost
  - Fleet growth simulation
  - Peak hours analysis
  - Rating impact analysis
- [ ] Aggregate data from:
  - Trip data
  - Transaction data
  - Vehicle data
  - Expense data
  - Maintenance data

#### Frontend:
- [ ] Replace mock data with API calls
- [ ] Add loading states to all charts
- [ ] Add error handling
- [ ] Add date range filtering
- [ ] Add vehicle filtering
- [ ] Ensure all charts use real data
- [ ] Add export functionality for reports

**Priority:** Low-Medium (can use mock data for demo)

---

## 🐛 Known Bugs

### Trip History
- [ ] Fix mapping bugs (specific issues to be identified)

### Vehicle Overview
- [ ] Fix documents page redirect

---

## 📋 Implementation Priority

### For Demo/Waitlist Release:
1. **Documents** - Complete S3 integration (Medium effort, high value)
2. **Banking** - If critical for demo, otherwise can wait
3. **Maintenance** - Can use mock data for demo, but real data is better
4. **Expense Tracking** - Can wait if not critical
5. **Analytics** - Can use mock data for demo

### Post-Demo:
1. **Maintenance** - Full implementation
2. **Expense Tracking** - Full implementation
3. **Banking** - Full Plaid integration
4. **Analytics** - Real data integration

---

## 📝 Notes

- All pages have UI/UX complete
- Main work needed is backend integration and data connectivity
- Most features can work with mock data for initial demo
- Database models need to be created for new features
- API endpoints need to be created following existing patterns
- Frontend services need to be created/updated to use real APIs

---

## 🔗 Related Files

### Backend Models Needed:
- `backend/core/database/models/bank_account.py`
- `backend/core/database/models/bank_transaction.py`
- `backend/core/database/models/maintenance_record.py`
- `backend/core/database/models/expense.py`

### Backend Routes Needed:
- `backend/banking/routes.py`
- `backend/maintenance/routes.py`
- `backend/expenses/routes.py`

### Frontend Services Needed:
- `frontend/src/services/maintenance-service.ts`
- `frontend/src/services/expense-service.ts`
- Update `frontend/src/services/document-service.ts`

---

*Last Updated: 2025-01-XX*
