#!/usr/bin/env python3
"""
Turo Data Seed Script

This script seeds the database with realistic Turo data for development and testing.
It uses the API endpoints to ensure data is properly validated and saved.

Usage:
    python seed_turo_data.py

The script will prompt you for:
    - Account email
    - Account password
"""

# ------------------------------ IMPORTS ------------------------------
import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ------------------------------ CONFIGURATION ------------------------------

# Default values
DEFAULT_API_URL = os.getenv("API_URL", "http://localhost:8000")
DEFAULT_EMAIL = os.getenv("SEED_EMAIL", "seed@turolytics.com")
DEFAULT_PASSWORD = os.getenv("SEED_PASSWORD", "SeedPassword123!")

# Vehicle data templates
VEHICLE_MAKES_MODELS = [
    ("Toyota", "Camry", "LE", "ABC-1234"),
    ("Honda", "Civic", "EX", "DEF-5678"),
    ("Tesla", "Model 3", "Standard Range", "GHI-9012"),
    ("BMW", "3 Series", "330i", "JKL-3456"),
    ("Mercedes-Benz", "C-Class", "C300", "MNO-7890"),
    ("Audi", "A4", "Premium", "PQR-1234"),
    ("Ford", "Mustang", "EcoBoost", "STU-5678"),
    ("Chevrolet", "Camaro", "LT", "VWX-9012"),
    ("Nissan", "Altima", "SV", "YZA-3456"),
    ("Hyundai", "Elantra", "Limited", "BCD-7890"),
    ("Mazda", "CX-5", "Touring", "EFG-1234"),
    ("Subaru", "Outback", "Premium", "HIJ-5678"),
    ("Volkswagen", "Jetta", "SE", "KLM-9012"),
    ("Jeep", "Wrangler", "Sport", "NOP-3456"),
    ("Lexus", "ES 350", "Base", "QRS-7890"),
]

# Customer names for trips and reviews
CUSTOMER_NAMES = [
    "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis",
    "David Wilson", "Jessica Martinez", "Christopher Anderson", "Amanda Taylor",
    "Matthew Thomas", "Ashley Jackson", "Daniel White", "Lauren Harris",
    "James Martin", "Megan Thompson", "Robert Garcia", "Nicole Martinez",
    "William Rodriguez", "Stephanie Lewis", "Joseph Lee", "Michelle Walker",
]

# Review texts
REVIEW_TEXTS = [
    "Great car, very clean and reliable! Would rent again.",
    "Perfect vehicle for our trip. Everything worked as expected.",
    "Amazing experience! The car was in excellent condition.",
    "Good car overall, but had some minor issues with the AC.",
    "The vehicle was clean and well-maintained. Highly recommend!",
    "Smooth ride and great fuel economy. Very satisfied.",
    "Car was exactly as described. Host was very responsive.",
    "Had a wonderful experience. The car exceeded expectations.",
    "Minor scratches but overall good condition. Would rent again.",
    "Excellent service and a great car. No complaints!",
]

AREAS_OF_IMPROVEMENT = [
    ["Cleanliness", "Communication"],
    ["Vehicle condition"],
    ["Punctuality"],
    ["Communication", "Cleanliness"],
    [],
    [],
    ["Vehicle condition", "Cleanliness"],
    [],
    ["Communication"],
    [],
]

# ------------------------------ LOGGING SETUP ------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def format_date(date: datetime) -> str:
    """Format datetime as Turo date string (e.g., 'Sat, Nov 1')."""
    return date.strftime("%a, %b %d")

def format_time(date: datetime) -> str:
    """Format datetime as Turo time string (e.g., '4:30 p.m.')."""
    hour = date.hour
    minute = date.minute
    period = "a.m." if hour < 12 else "p.m."
    hour_12 = hour if hour <= 12 else hour - 12
    if hour_12 == 0:
        hour_12 = 12
    minute_str = f":{minute:02d}" if minute > 0 else ""
    return f"{hour_12}{minute_str} {period}"

def generate_trip_id() -> str:
    """Generate a realistic Turo trip ID."""
    return f"TR{random.randint(100000, 999999)}"

def generate_customer_id() -> str:
    """Generate a realistic Turo customer ID."""
    return f"CUST{random.randint(10000, 99999)}"

# ------------------------------ DATA GENERATION FUNCTIONS ------------------------------

def generate_vehicles_data() -> Dict[str, Any]:
    """Generate vehicles data."""
    vehicles = []
    years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]
    statuses = ["Listed", "Snoozed", "Listed", "Listed", "Listed"]  # Mostly listed
    trip_info_options = [
        "No upcoming trips",
        "1 upcoming trip",
        "2 upcoming trips",
        "3 upcoming trips",
    ]
    
    for make, model, trim, plate in VEHICLE_MAKES_MODELS:
        year = random.choice(years)
        status = random.choice(statuses)
        trip_info = random.choice(trip_info_options)
        rating = round(random.uniform(4.0, 5.0), 1)
        trip_count = random.randint(5, 150)
        
        vehicles.append({
            "name": f"{make} {model}",
            "year": year,
            "trim": trim,
            "license_plate": plate,
            "status": status,
            "trip_info": trip_info,
            "rating": rating,
            "trip_count": trip_count,
        })
    
    return {
        "vehicles": vehicles,
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }

def generate_trips_data(vehicle_plates: List[str]) -> Dict[str, Any]:
    """Generate trips data with variety: completed, cancelled, upcoming, current.
    
    Creates realistic scenarios:
    - Vehicles returning today (trips ending today)
    - Vehicles returning tomorrow (trips ending tomorrow)
    - Vehicles booked for today (trips starting today)
    - Vehicles booked for tomorrow (trips starting tomorrow)
    - Active trips in progress
    - Upcoming trips in the future
    - Completed trips in history
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1) - timedelta(seconds=1)
    tomorrow_start = today_start + timedelta(days=1)
    tomorrow_end = tomorrow_start + timedelta(days=1) - timedelta(seconds=1)
    
    booked_trips = []
    history_trips = []
    
    # Helper function to create a trip
    def create_trip(
        start_date: datetime,
        end_date: datetime,
        status: str,
        license_plate: str,
        is_history: bool = False,
        kms_driven: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a trip dictionary with all required fields."""
        trip_data = {
            "trip_id": generate_trip_id(),
            "trip_url": f"https://turo.com/trip/{generate_trip_id()}",
            "customer_name": random.choice(CUSTOMER_NAMES),
            "status": status,
            "license_plate": license_plate,
            "schedule": {
                "start_date": format_date(start_date),
                "start_time": format_time(start_date),
                "end_date": format_date(end_date),
                "end_time": format_time(end_date),
            },
            "location": {
                "location_type": random.choice(["Delivery", "Location"]),
                "address": f"{random.randint(100, 9999)} Main St, City, State {random.randint(10000, 99999)}",
            },
            "kilometers": {
                "kilometers_included": random.randint(200, 1000),
                "kilometers_driven": kms_driven,
                "overage_rate": round(random.uniform(0.30, 0.50), 2),
            },
            "earnings": {
                "total_earnings": round(random.uniform(50, 500), 2) if not is_history or status == "COMPLETED" else None,
            },
            "protection": {
                "protection_plan": random.choice(["60 plan", "75 plan", "90 plan"]),
                "deductible": random.choice(["$0", "$500", "$1,000", "$2,000"]),
            },
        }
        
        if is_history and status == "CANCELLED":
            cancelled_by = random.choice(["Guest", "Host"])
            trip_data["cancellation_info"] = f"Cancelled by {cancelled_by}"
            trip_data["cancelled_by"] = cancelled_by
            trip_data["cancelled_date"] = format_date(start_date - timedelta(days=1))
        
        return trip_data
    
    # ========== COMPLETED TRIPS (trip_history) ==========
    # Generate completed trips from the past
    for i in range(30):
        days_ago = random.randint(1, 90)
        start_date = now - timedelta(days=days_ago)
        duration_days = random.randint(1, 7)
        end_date = start_date + timedelta(days=duration_days)
        
        status = random.choice(["COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED", "CANCELLED"])
        kms_driven = random.randint(50, 500) if status == "COMPLETED" else None
        
        history_trips.append(create_trip(
            start_date, end_date, status, random.choice(vehicle_plates),
            is_history=True, kms_driven=kms_driven
        ))
    
    # ========== ACTIVE TRIPS (booked_trips) ==========
    
    # 1. Trips ending TODAY (vehicles returning today) - 5 trips
    for i in range(5):
        days_ago = random.randint(1, 5)
        start_date = now - timedelta(days=days_ago)
        # End date is today, at various times (some already passed, some later today)
        if random.choice([True, False]):  # 50% chance end time is later today
            end_hour = random.randint(now.hour + 1, 22) if now.hour < 22 else random.randint(10, 20)
            end_minute = random.choice([0, 15, 30, 45])
            end_date = today_start.replace(hour=min(end_hour, 22), minute=end_minute)
        else:  # End time already passed today
            end_hour = random.randint(8, max(8, now.hour - 1))
            end_minute = random.choice([0, 15, 30, 45])
            end_date = today_start.replace(hour=end_hour, minute=end_minute)
        
        booked_trips.append(create_trip(
            start_date, end_date, "IN_PROGRESS", random.choice(vehicle_plates),
            kms_driven=random.randint(100, 400)
        ))
    
    # 2. Trips ending TOMORROW (vehicles returning tomorrow) - 4 trips
    for i in range(4):
        days_ago = random.randint(0, 3)
        start_date = now - timedelta(days=days_ago)
        # End date is tomorrow
        end_hour = random.randint(10, 20)
        end_minute = random.choice([0, 15, 30, 45])
        end_date = tomorrow_start.replace(hour=end_hour, minute=end_minute)
        
        booked_trips.append(create_trip(
            start_date, end_date, "IN_PROGRESS", random.choice(vehicle_plates),
            kms_driven=random.randint(50, 300)
        ))
    
    # 3. Trips starting TODAY (vehicles booked for today) - 4 trips
    for i in range(4):
        # Mix of trips that already started today and trips starting later today
        if random.choice([True, False]):  # 50% already started
            # Trip already started today
            start_hour = random.randint(6, max(6, now.hour - 1))
            start_minute = random.choice([0, 15, 30, 45])
            start_date = today_start.replace(hour=start_hour, minute=start_minute)
            status = "IN_PROGRESS"
            kms_driven = random.randint(10, 150)
        else:  # Trip starting later today
            start_hour = random.randint(now.hour + 1, 22) if now.hour < 22 else random.randint(14, 18)
            start_minute = random.choice([0, 15, 30, 45])
            start_date = today_start.replace(hour=min(start_hour, 22), minute=start_minute)
            status = "UPCOMING"
            kms_driven = None
        
        duration_days = random.randint(1, 5)
        end_date = start_date + timedelta(days=duration_days)
        
        booked_trips.append(create_trip(
            start_date, end_date, status, random.choice(vehicle_plates),
            kms_driven=kms_driven
        ))
    
    # 4. Trips starting TOMORROW - 5 trips
    for i in range(5):
        # Start date is tomorrow
        start_hour = random.randint(8, 18)
        start_minute = random.choice([0, 15, 30, 45])
        start_date = tomorrow_start.replace(hour=start_hour, minute=start_minute)
        
        duration_days = random.randint(1, 7)
        end_date = start_date + timedelta(days=duration_days)
        
        booked_trips.append(create_trip(
            start_date, end_date, "UPCOMING", random.choice(vehicle_plates)
        ))
    
    # 5. Trips starting in 2-3 days - 4 trips
    for i in range(4):
        days_ahead = random.randint(2, 3)
        start_date = today_start + timedelta(days=days_ahead)
        start_hour = random.randint(8, 18)
        start_minute = random.choice([0, 15, 30, 45])
        start_date = start_date.replace(hour=start_hour, minute=start_minute)
        
        duration_days = random.randint(1, 7)
        end_date = start_date + timedelta(days=duration_days)
        
        booked_trips.append(create_trip(
            start_date, end_date, "UPCOMING", random.choice(vehicle_plates)
        ))
    
    # 6. Trips ending in 2-3 days (currently active) - 3 trips
    for i in range(3):
        days_ago = random.randint(1, 2)
        start_date = now - timedelta(days=days_ago)
        days_ahead = random.randint(2, 3)
        end_date = today_start + timedelta(days=days_ahead)
        end_hour = random.randint(10, 20)
        end_minute = random.choice([0, 15, 30, 45])
        end_date = end_date.replace(hour=end_hour, minute=end_minute)
        
        booked_trips.append(create_trip(
            start_date, end_date, "IN_PROGRESS", random.choice(vehicle_plates),
            kms_driven=random.randint(100, 350)
        ))
    
    # 7. More upcoming trips (4-30 days ahead) - 10 trips
    for i in range(10):
        days_ahead = random.randint(4, 30)
        start_date = now + timedelta(days=days_ahead)
        start_hour = random.randint(8, 18)
        start_minute = random.choice([0, 15, 30, 45])
        start_date = start_date.replace(hour=start_hour, minute=start_minute)
        
        duration_days = random.randint(1, 7)
        end_date = start_date + timedelta(days=duration_days)
        
        booked_trips.append(create_trip(
            start_date, end_date, "UPCOMING", random.choice(vehicle_plates)
        ))
    
    return {
        "booked_trips": {
            "trips": booked_trips,
            "scraped_at": datetime.now(timezone.utc).isoformat()
        },
        "trip_history": {
            "trips": history_trips,
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }
    }

def generate_reviews_data(vehicles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate reviews data with variety."""
    reviews = []
    
    for i in range(30):
        customer_id = generate_customer_id()
        rating = random.choice([4.0, 4.5, 5.0, 5.0, 5.0, 4.5, 5.0])  # Mostly positive
        days_ago = random.randint(1, 180)
        review_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
        
        # Select a random vehicle for this review
        vehicle = random.choice(vehicles_data)
        vehicle_info = f"{vehicle['name']} {vehicle['year']} • {vehicle['license_plate']}"
        
        has_response = random.choice([True, False, False, False])  # 25% have responses
        host_response = None
        if has_response:
            host_response = random.choice([
                "Thank you for the feedback! We're glad you enjoyed the car.",
                "We appreciate your review. Hope to host you again soon!",
                "Thanks for choosing our vehicle. Safe travels!",
            ])
        
        review_text_idx = i % len(REVIEW_TEXTS)
        areas = AREAS_OF_IMPROVEMENT[review_text_idx % len(AREAS_OF_IMPROVEMENT)]
        
        reviews.append({
            "customer_name": random.choice(CUSTOMER_NAMES),
            "customer_id": customer_id,
            "vehicle_info": vehicle_info,
            "rating": rating,
            "date": review_date.isoformat(),
            "review_text": REVIEW_TEXTS[review_text_idx],
            "areas_of_improvement": areas,
            "host_response": host_response,
            "has_host_response": has_response,
        })
    
    return {
        "reviews": reviews,
        "summary": {
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }
    }

def generate_earnings_data(vehicles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate earnings data."""
    current_year = datetime.now().year
    
    # Earnings breakdown
    earnings_breakdown = [
        {
            "type": "Trip earnings",
            "amount": f"${random.randint(5000, 50000):,}",
            "year": str(current_year),
        },
        {
            "type": "Upcoming earnings",
            "amount": f"${random.randint(1000, 10000):,}",
            "year": str(current_year),
        },
        {
            "type": "Total earnings",
            "amount": f"${random.randint(10000, 100000):,}",
            "year": str(current_year),
        },
    ]
    
    # Vehicle earnings (match with actual vehicles)
    vehicle_earnings = []
    for vehicle in vehicles_data[:10]:  # Top 10 vehicles
        vehicle_earnings.append({
            "vehicle_name": f"{vehicle['name']} {vehicle['year']}",
            "license_plate": vehicle["license_plate"],
            "trim": vehicle.get("trim"),
            "earnings_amount": f"${random.randint(1000, 15000):,}.{random.randint(0, 99):02d}",
        })
    
    return {
        "earnings_breakdown": earnings_breakdown,
        "vehicle_earnings": vehicle_earnings,
    }

# ------------------------------ API CLIENT FUNCTIONS ------------------------------

class APIClient:
    """Simple API client for seeding data."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.access_token: Optional[str] = None
    
    def register(self, email: str, password: str) -> bool:
        """Register a new account."""
        url = f"{self.base_url}/api/auth/register"
        data = {
            "email": email,
            "password": password,
            "firstName": "Seed",
            "lastName": "User",
        }
        
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 201:
                logger.info(f"Successfully registered account: {email}")
                return True
            elif response.status_code == 400:
                logger.info(f"Account already exists: {email}")
                return True  # Account exists, that's fine
            else:
                logger.error(f"Failed to register: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error registering account: {e}")
            return False
    
    def login(self, email: str, password: str) -> bool:
        """Login and get access token."""
        url = f"{self.base_url}/api/auth/login/json"
        data = {
            "email": email,
            "password": password,
        }
        
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                if self.access_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.access_token}"
                    })
                    logger.info(f"Successfully logged in: {email}")
                    return True
            logger.error(f"Failed to login: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error logging in: {e}")
            return False
    
    def seed_data(self, vehicles: Dict[str, Any], trips: Dict[str, Any], 
                  reviews: Dict[str, Any], earnings: Dict[str, Any], 
                  overwrite: bool = True) -> bool:
        """Seed data using the API."""
        url = f"{self.base_url}/api/turo/seed"
        data = {
            "vehicles": vehicles,
            "trips": trips,
            "reviews": reviews,
            "earnings": earnings,
            "overwrite": overwrite,
        }
        
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    counts = result.get("data", {}).get("counts", {})
                    logger.info(f"Successfully seeded data: {counts}")
                    return True
            logger.error(f"Failed to seed data: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error seeding data: {e}")
            return False
    
    def create_turo_integration(self, turo_email: str, turo_password: str) -> bool:
        """Create Turo integration record via seed endpoint (no login required)."""
        url = f"{self.base_url}/api/turo/seed/integration"
        params = {
            "turo_email": turo_email
        }
        
        try:
            response = self.session.post(url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info("Turo integration created successfully!")
                    return True
            
            logger.warning(f"Failed to create Turo integration: {response.status_code} - {response.text}")
            return False
            
        except Exception as e:
            logger.warning(f"Error creating Turo integration: {e}")
            return False

# ------------------------------ MAIN FUNCTION ------------------------------

def main():
    """Main function to seed data."""
    print("=" * 60)
    print("Turo Data Seed Script")
    print("=" * 60)
    print()
    
    # Get email and password
    email = input("Enter account email: ").strip()
    if not email:
        logger.error("Email is required. Exiting.")
        sys.exit(1)
    
    password = input("Enter account password: ").strip()
    if not password:
        logger.error("Password is required. Exiting.")
        sys.exit(1)
    
    print()
    logger.info("=" * 60)
    logger.info("Turo Data Seed Script")
    logger.info("=" * 60)
    logger.info(f"API URL: {DEFAULT_API_URL}")
    logger.info(f"Email: {email}")
    logger.info("")
    
    # Initialize API client
    client = APIClient(DEFAULT_API_URL)
    
    # Register account
    logger.info("Step 1: Registering account...")
    if not client.register(email, password):
        logger.error("Failed to register account. Exiting.")
        sys.exit(1)
    
    # Login
    logger.info("Step 2: Logging in...")
    if not client.login(email, password):
        logger.error("Failed to login. Exiting.")
        sys.exit(1)
    
    # Generate data
    logger.info("Step 3: Generating seed data...")
    vehicles_data = generate_vehicles_data()
    vehicle_plates = [v["license_plate"] for v in vehicles_data["vehicles"]]
    
    trips_data = generate_trips_data(vehicle_plates)
    reviews_data = generate_reviews_data(vehicles_data["vehicles"])
    earnings_data = generate_earnings_data(vehicles_data["vehicles"])
    
    logger.info(f"Generated:")
    logger.info(f"  - {len(vehicles_data['vehicles'])} vehicles")
    logger.info(f"  - {len(trips_data['booked_trips']['trips'])} booked trips")
    logger.info(f"  - {len(trips_data['trip_history']['trips'])} history trips")
    logger.info(f"  - {len(reviews_data['reviews'])} reviews")
    logger.info(f"  - {len(earnings_data['earnings_breakdown'])} earnings breakdowns")
    logger.info(f"  - {len(earnings_data['vehicle_earnings'])} vehicle earnings")
    logger.info("")
    
    # Seed data (always overwrite)
    logger.info("Step 4: Seeding data via API...")
    if not client.seed_data(vehicles_data, trips_data, reviews_data, earnings_data, overwrite=True):
        logger.error("Failed to seed data. Exiting.")
        sys.exit(1)
    
    # Create Turo integration (so frontend shows connected status)
    logger.info("Step 5: Creating Turo integration...")
    # Use the same email/password for Turo integration
    if not client.create_turo_integration(email, password):
        logger.warning("Failed to create Turo integration. Data is seeded but integration may not show as connected.")
    else:
        logger.info("Turo integration created successfully!")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Seed completed successfully!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

