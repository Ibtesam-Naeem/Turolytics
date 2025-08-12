# 🚘 Turolytics

Turolytics is a **Turo fleet analytics dashboard** designed for car rental hosts. Since Turo does not offer an official API, this project leverages **web automation, third-party integrations, and real-time telemetry** to centralize all operational and financial data in one platform.

---

## 📌 Overview

Turolytics automates data collection and reporting for Turo fleet owners by:

- **Web Automation (Playwright/Selenium):**
  - Logs into your Turo host account (no official API available).
  - Scrapes data for:
    - Bookings and completed trips  
    - Payouts and earnings history  
    - Host performance metrics  
    - Customer reviews  
    - Vehicle details (pricing, availability, status)  
    - Calendar and upcoming trips  

- **Plaid API Integration:**
  - Connects your **business bank account**.
  - Fetches and categorizes transactions.
  - Links payouts to Turo trips for real profit tracking.

- **Bouncie API Integration:**
  - Pulls real-time telemetry for all vehicles:
    - Current **location** (GPS coordinates)  
    - Mileage and trip history  
    - Speed and driving behavior  
    - Vehicle health alerts  
  - Displays car locations on a **live map (Google Maps API)**.

- **Dashboard (Frontend):**
  - Visualizes:
    - Active and completed trips  
    - Vehicle locations and statuses  
    - Revenue, payouts, and expense tracking  
    - Profitability analytics per car and overall fleet  
    - Historical trends and performance insights  

---

## ⚙️ Tech Stack

- **Backend:** Python (FastAPI or Flask)  
- **Automation:** Playwright (headless login and scraping)  
- **Database:** PostgreSQL (data storage for trips, payouts, transactions)  
- **Banking:** Plaid API (financial tracking)  
- **Telemetry:** Bouncie API  
- **Frontend:** React (with Bootstrap or Tailwind)  
- **Mapping:** Google Maps or Leaflet.js for vehicle tracking  

---

## 🚀 Features (Planned Roadmap)

- [ ] Automated Turo login and scraping (bookings, payouts, trips)  
- [ ] Database schema for fleet, trips, and earnings data  
- [ ] Plaid integration for bank account connection and transaction syncing  
- [ ] Bouncie integration for vehicle telemetry  
- [ ] Interactive map showing real-time vehicle locations  
- [ ] Dashboard with KPIs:
  - Total trips, earnings, occupancy rate  
  - Vehicle-wise profitability  
  - Weekly, monthly, yearly analytics  
- [ ] Export reports (CSV, PDF) for bookkeeping  
- [ ] User authentication for multi-fleet owners (future feature)

---

## 📂 Project Status

🚧 **In Development**  
- Initial setup and automation testing in progress.  
- Database schema being drafted.  

---

## 🛠️ Future Enhancements

- Mobile app integration (React Native)  
- Push notifications for car movements and completed trips  
- AI-powered pricing and profitability recommendations  
- Car investment calculator, relale, health

- Upload and manage documents (receipts, registrations, insurance, repairs)
  - Per-car and business-wide file storage
  - Upload via dashboard (PDF, JPG, PNG support)
  - View, download, and organize documents by vehicle

---
