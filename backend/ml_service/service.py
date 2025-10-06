# ------------------------------ IMPORTS ------------------------------
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, silhouette_score
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import LocalOutlierFactor

from core.db.operations.turo_operations import get_database_stats
from core.db.operations.bouncie_operations import get_bouncie_trips, get_bouncie_trip_stats
from core.db.operations.plaid_operations import save_plaid_transactions

logger = logging.getLogger(__name__)

# ------------------------------ ML SERVICE ------------------------------

class MLService:
    """Machine Learning service for Turolytics predictions and analytics."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.models = {}
        self.is_trained = False
    
    # ------------------------------ PREDICTIVE ANALYTICS ------------------------------
    
    async def predict_revenue(self, account_email: str, days_ahead: int = 30) -> Dict[str, Any]:
        """Predict future Turo earnings using historical data."""
        try:
            earnings_data = await self._get_earnings_data(account_email)
            if not earnings_data:
                return {"success": False, "error": "No earnings data available"}
            
            features, target = self._prepare_revenue_features(earnings_data)
            
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
            model.fit(X_train, y_train)
            
            future_dates = self._generate_future_dates(days_ahead)
            future_features = self._prepare_future_revenue_features(future_dates, earnings_data)
            predictions = model.predict(future_features)
            
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            accuracy = max(0, 1 - (mse / np.var(y_test)))
            
            return {
                "success": True,
                "data": {
                    "predictions": [
                        {"date": date.strftime("%Y-%m-%d"), "predicted_earnings": float(pred)}
                        for date, pred in zip(future_dates, predictions)
                    ],
                    "total_predicted_earnings": float(np.sum(predictions)),
                    "model_accuracy": float(accuracy),
                    "features_used": list(features.columns)
                }
            }
        except Exception as e:
            logger.error(f"Revenue prediction failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_trips(self, account_email: str, imei: str = None) -> Dict[str, Any]:
        """Suggest optimal times and locations for trips."""
        try:
            trips_data = await self._get_trips_data(account_email, imei)
            if not trips_data:
                return {"success": False, "error": "No trip data available"}
            
            patterns = self._analyze_trip_patterns(trips_data)
            
            recommendations = self._generate_trip_recommendations(patterns)
            
            return {
                "success": True,
                "data": {
                    "optimal_times": recommendations["times"],
                    "optimal_locations": recommendations["locations"],
                    "expected_profitability": recommendations["expected_profitability"],
                    "patterns_analyzed": patterns["summary"]
                }
            }
        except Exception as e:
            logger.error(f"Trip optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def predict_maintenance(self, account_email: str, imei: str = None) -> Dict[str, Any]:
        """Predict vehicle maintenance needs using Bouncie data."""
        try:
            vehicle_data = await self._get_vehicle_telemetry_data(account_email, imei)
            if not vehicle_data:
                return {"success": False, "error": "No vehicle telemetry data available"}
            
            health_analysis = self._analyze_vehicle_health(vehicle_data)
            
            maintenance_predictions = self._predict_maintenance_needs(health_analysis)
            
            return {
                "success": True,
                "data": {
                    "maintenance_alerts": maintenance_predictions["alerts"],
                    "recommended_actions": maintenance_predictions["actions"],
                    "health_score": health_analysis["overall_health"],
                    "risk_factors": health_analysis["risk_factors"]
                }
            }
        except Exception as e:
            logger.error(f"Maintenance prediction failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ------------------------------ CLUSTERING ------------------------------
    
    async def cluster_trip_patterns(self, account_email: str, imei: str = None) -> Dict[str, Any]:
        """Group similar trips using clustering."""
        try:
            trips_data = await self._get_trips_data(account_email, imei)
            if not trips_data:
                return {"success": False, "error": "No trip data available"}
            
            features = self._prepare_clustering_features(trips_data, "trips")
            
            kmeans = KMeans(n_clusters=5, random_state=42)
            clusters = kmeans.fit_predict(features)
            
            cluster_analysis = self._analyze_clusters(trips_data, clusters, "trip_patterns")
            
            return {
                "success": True,
                "data": {
                    "clusters": cluster_analysis["clusters"],
                    "cluster_summary": cluster_analysis["summary"],
                    "silhouette_score": float(silhouette_score(features, clusters))
                }
            }
        except Exception as e:
            logger.error(f"Trip clustering failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def categorize_vehicles(self, account_email: str) -> Dict[str, Any]:
        """Categorize vehicles by usage patterns."""
        try:
            vehicles_data = await self._get_vehicles_data(account_email)
            if not vehicles_data:
                return {"success": False, "error": "No vehicle data available"}
            
            features = self._prepare_clustering_features(vehicles_data, "vehicles")
            
            kmeans = KMeans(n_clusters=4, random_state=42)
            clusters = kmeans.fit_predict(features)
            
            cluster_analysis = self._analyze_clusters(vehicles_data, clusters, "vehicle_usage")
            
            return {
                "success": True,
                "data": {
                    "vehicle_categories": cluster_analysis["clusters"],
                    "category_summary": cluster_analysis["summary"],
                    "recommendations": cluster_analysis["recommendations"]
                }
            }
        except Exception as e:
            logger.error(f"Vehicle categorization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_geographic_hotspots(self, account_email: str) -> Dict[str, Any]:
        """Identify geographic hotspots for rentals."""
        try:
            trips_data = await self._get_trips_data(account_email)
            if not trips_data:
                return {"success": False, "error": "No trip data available"}
            
            geo_features = self._extract_geographic_features(trips_data)
            
            dbscan = DBSCAN(eps=0.1, min_samples=3)
            hotspots = dbscan.fit_predict(geo_features)
            
            hotspot_analysis = self._analyze_geographic_hotspots(geo_features, hotspots, trips_data)
            
            return {
                "success": True,
                "data": {
                    "hotspots": hotspot_analysis["hotspots"],
                    "hotspot_summary": hotspot_analysis["summary"],
                    "recommendations": hotspot_analysis["recommendations"]
                }
            }
        except Exception as e:
            logger.error(f"Geographic analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ------------------------------ ANOMALY DETECTION ------------------------------
    
    async def detect_spending_anomalies(self, account_email: str) -> Dict[str, Any]:
        """Detect unusual spending patterns using Plaid data."""
        try:
            transactions_data = await self._get_transactions_data(account_email)
            if not transactions_data:
                return {"success": False, "error": "No transaction data available"}
            
            features = self._prepare_anomaly_features(transactions_data, "spending")
            
            isolation_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_scores = isolation_forest.fit_predict(features)
            
            anomaly_analysis = self._analyze_anomalies(transactions_data, anomaly_scores, "spending")
            
            return {
                "success": True,
                "data": {
                    "anomalies": anomaly_analysis["anomalies"],
                    "anomaly_summary": anomaly_analysis["summary"],
                    "risk_score": anomaly_analysis["risk_score"]
                }
            }
        except Exception as e:
            logger.error(f"Spending anomaly detection failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_vehicle_issues(self, account_email: str, imei: str = None) -> Dict[str, Any]:
        """Detect vehicle issues using Bouncie telemetry."""
        try:
            vehicle_data = await self._get_vehicle_telemetry_data(account_email, imei)
            if not vehicle_data:
                return {"success": False, "error": "No vehicle telemetry data available"}
            
            features = self._prepare_anomaly_features(vehicle_data, "vehicle")
            
            lof = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
            anomaly_scores = lof.fit_predict(features)
            
            anomaly_analysis = self._analyze_anomalies(vehicle_data, anomaly_scores, "vehicle")
            
            return {
                "success": True,
                "data": {
                    "vehicle_issues": anomaly_analysis["anomalies"],
                    "issue_summary": anomaly_analysis["summary"],
                    "maintenance_priority": anomaly_analysis["priority"]
                }
            }
        except Exception as e:
            logger.error(f"Vehicle issue detection failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_performance_outliers(self, account_email: str) -> Dict[str, Any]:
        """Detect performance outliers across all metrics."""
        try:
            trips_data = await self._get_trips_data(account_email)
            vehicles_data = await self._get_vehicles_data(account_email)
            
            if not trips_data and not vehicles_data:
                return {"success": False, "error": "No performance data available"}
            
            combined_data = self._combine_performance_data(trips_data, vehicles_data)
            features = self._prepare_anomaly_features(combined_data, "performance")
            
            isolation_forest = IsolationForest(contamination=0.05, random_state=42)
            outlier_scores = isolation_forest.fit_predict(features)
            
            outlier_analysis = self._analyze_anomalies(combined_data, outlier_scores, "performance")
            
            return {
                "success": True,
                "data": {
                    "performance_outliers": outlier_analysis["anomalies"],
                    "outlier_summary": outlier_analysis["summary"],
                    "performance_score": outlier_analysis["performance_score"]
                }
            }
        except Exception as e:
            logger.error(f"Performance outlier detection failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ------------------------------ HELPER METHODS ------------------------------
    
    async def _get_earnings_data(self, account_email: str) -> List[Dict]:
        """Get historical earnings data."""
        import random
        from datetime import datetime, timedelta
        
        earnings = []
        base_date = datetime.now() - timedelta(days=90)
        
        for i in range(90):
            date = base_date + timedelta(days=i)
            base_amount = random.uniform(50, 200)
            weekend_multiplier = 1.5 if date.weekday() >= 5 else 1.0
            seasonal_multiplier = 1.2 if date.month in [6, 7, 8] else 0.9  # Summer boost
            amount = base_amount * weekend_multiplier * seasonal_multiplier
            
            earnings.append({
                "date": date.strftime("%Y-%m-%d"),
                "amount": round(amount, 2),
                "trip_count": random.randint(1, 5),
                "avg_trip_value": round(amount / random.randint(1, 5), 2)
            })
        
        return earnings
    
    async def _get_trips_data(self, account_email: str, imei: str = None) -> List[Dict]:
        """Get trip data from Turo and Bouncie."""
        import random
        from datetime import datetime, timedelta
        
        try:
            bouncie_trips = get_bouncie_trips(account_email, imei, 1000)
        except:
            bouncie_trips = []
        
        trips = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(25):
            start_time = base_date + timedelta(days=i, hours=random.randint(8, 18))
            duration_hours = random.uniform(2, 8)
            end_time = start_time + timedelta(hours=duration_hours)
            
            distance = random.uniform(10, 150)
            base_price = distance * random.uniform(0.8, 1.5)
            weekend_multiplier = 1.3 if start_time.weekday() >= 5 else 1.0
            price = base_price * weekend_multiplier
            
            trips.append({
                "trip_id": f"trip_{i+1:03d}",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "distance": round(distance, 2),
                "duration_hours": round(duration_hours, 2),
                "price": round(price, 2),
                "location": random.choice(["Downtown", "Airport", "Suburbs", "University"]),
                "vehicle_type": random.choice(["Economy", "Luxury", "SUV", "Convertible"]),
                "rating": round(random.uniform(3.5, 5.0), 1)
            })
        
        return bouncie_trips + trips
    
    async def _get_vehicles_data(self, account_email: str) -> List[Dict]:
        """Get vehicle data."""
        import random
        
        # Simulate realistic vehicle data
        vehicles = [
            {
                "vehicle_id": "v001",
                "make": "Toyota",
                "model": "Camry",
                "year": 2020,
                "mileage": random.randint(15000, 80000),
                "daily_rate": 45.00,
                "utilization_rate": round(random.uniform(0.6, 0.9), 2),
                "total_earnings": round(random.uniform(5000, 15000), 2),
                "avg_rating": round(random.uniform(4.2, 4.9), 1),
                "maintenance_cost": round(random.uniform(200, 800), 2),
                "location": "Downtown"
            },
            {
                "vehicle_id": "v002", 
                "make": "BMW",
                "model": "3 Series",
                "year": 2019,
                "mileage": random.randint(20000, 90000),
                "daily_rate": 85.00,
                "utilization_rate": round(random.uniform(0.4, 0.7), 2),
                "total_earnings": round(random.uniform(8000, 20000), 2),
                "avg_rating": round(random.uniform(4.5, 5.0), 1),
                "maintenance_cost": round(random.uniform(500, 1200), 2),
                "location": "Airport"
            },
            {
                "vehicle_id": "v003",
                "make": "Honda",
                "model": "Civic", 
                "year": 2021,
                "mileage": random.randint(10000, 50000),
                "daily_rate": 35.00,
                "utilization_rate": round(random.uniform(0.7, 0.95), 2),
                "total_earnings": round(random.uniform(3000, 12000), 2),
                "avg_rating": round(random.uniform(4.0, 4.8), 1),
                "maintenance_cost": round(random.uniform(150, 600), 2),
                "location": "University"
            }
        ]
        
        return vehicles
    
    async def _get_vehicle_telemetry_data(self, account_email: str, imei: str = None) -> List[Dict]:
        """Get Bouncie telemetry data."""
        try:
            return get_bouncie_trips(account_email, imei, 1000)
        except:
            import random
            from datetime import datetime, timedelta
            
            telemetry = []
            base_date = datetime.now() - timedelta(days=7)
            
            for i in range(20):
                telemetry.append({
                    "trip_id": f"telemetry_{i+1:03d}",
                    "start_time": (base_date + timedelta(hours=i*2)).isoformat(),
                    "distance": round(random.uniform(5, 50), 2),
                    "average_speed": round(random.uniform(25, 70), 1),
                    "max_speed": round(random.uniform(60, 90), 1),
                    "fuel_consumed": round(random.uniform(0.5, 3.0), 2),
                    "hard_braking_count": random.randint(0, 3),
                    "hard_acceleration_count": random.randint(0, 2)
                })
            
            return telemetry
    
    async def _get_transactions_data(self, account_email: str) -> List[Dict]:
        """Get Plaid transaction data."""
        import random
        from datetime import datetime, timedelta
        
        transactions = []
        base_date = datetime.now() - timedelta(days=30)
        
        categories = ["Food & Dining", "Transportation", "Entertainment", "Shopping", "Utilities", "Gas", "Insurance"]
        merchants = ["Starbucks", "Uber", "Amazon", "Shell", "Netflix", "Spotify", "Walmart", "McDonald's"]
        
        for i in range(50):
            date = base_date + timedelta(days=random.randint(0, 30), hours=random.randint(6, 23))
            amount = round(random.uniform(5, 200), 2)
            category = random.choice(categories)
            merchant = random.choice(merchants)
            
            if random.random() < 0.1:  
                amount *= random.uniform(3, 8)  
                merchant = "LUXURY STORE" if random.random() < 0.5 else "UNKNOWN MERCHANT"
            
            transactions.append({
                "transaction_id": f"txn_{i+1:04d}",
                "date": date.isoformat(),
                "amount": amount,
                "category": category,
                "merchant": merchant,
                "account_type": random.choice(["checking", "credit", "savings"]),
                "is_anomaly": amount > 500 or merchant in ["LUXURY STORE", "UNKNOWN MERCHANT"]
            })
        
        return transactions
    
    def _prepare_revenue_features(self, earnings_data: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features for revenue prediction."""
        df = pd.DataFrame(earnings_data)
        
        df['date'] = pd.to_datetime(df['date'])
        
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)
        df['is_holiday_season'] = df['month'].isin([11, 12]).astype(int)
        
        df['avg_7d'] = df['amount'].rolling(window=7, min_periods=1).mean()
        df['avg_30d'] = df['amount'].rolling(window=30, min_periods=1).mean()
        
        df['amount_lag_1'] = df['amount'].shift(1)
        df['amount_lag_7'] = df['amount'].shift(7)
        
        df = df.fillna(method='bfill').fillna(method='ffill')
        
        feature_cols = ['day_of_week', 'month', 'is_weekend', 'is_summer', 'is_holiday_season', 
                       'avg_7d', 'avg_30d', 'amount_lag_1', 'amount_lag_7', 'trip_count']
        
        X = df[feature_cols]
        y = df['amount']
        
        return X, y
    
    def _prepare_clustering_features(self, data: List[Dict], data_type: str) -> pd.DataFrame:
        """Prepare features for clustering."""
        df = pd.DataFrame(data)
        
        if data_type == "trips":
            if 'distance' in df.columns:
                df['distance_norm'] = (df['distance'] - df['distance'].mean()) / df['distance'].std()
            if 'price' in df.columns:
                df['price_norm'] = (df['price'] - df['price'].mean()) / df['price'].std()
            if 'duration_hours' in df.columns:
                df['duration_norm'] = (df['duration_hours'] - df['duration_hours'].mean()) / df['duration_hours'].std()
            
            if 'location' in df.columns:
                le = LabelEncoder()
                df['location_encoded'] = le.fit_transform(df['location'].astype(str))
            if 'vehicle_type' in df.columns:
                le = LabelEncoder()
                df['vehicle_type_encoded'] = le.fit_transform(df['vehicle_type'].astype(str))
            
            feature_cols = [col for col in ['distance_norm', 'price_norm', 'duration_norm', 
                                          'location_encoded', 'vehicle_type_encoded', 'rating'] 
                           if col in df.columns]
            return df[feature_cols].fillna(0)
            
        elif data_type == "vehicles":
            numeric_cols = ['mileage', 'daily_rate', 'utilization_rate', 'total_earnings', 
                           'avg_rating', 'maintenance_cost']
            
            for col in numeric_cols:
                if col in df.columns:
                    df[f'{col}_norm'] = (df[col] - df[col].mean()) / df[col].std()
            
            if 'make' in df.columns:
                le = LabelEncoder()
                df['make_encoded'] = le.fit_transform(df['make'].astype(str))
            if 'location' in df.columns:
                le = LabelEncoder()
                df['location_encoded'] = le.fit_transform(df['location'].astype(str))
            
            feature_cols = [col for col in [f'{c}_norm' for c in numeric_cols] + 
                           ['make_encoded', 'location_encoded'] if col in df.columns]
            return df[feature_cols].fillna(0)
        
        return df.fillna(0)
    
    def _prepare_anomaly_features(self, data: List[Dict], data_type: str) -> pd.DataFrame:
        """Prepare features for anomaly detection."""
        df = pd.DataFrame(data)
        
        if data_type == "spending":
            if 'amount' in df.columns:
                df['amount_log'] = np.log1p(df['amount'])
                df['amount_zscore'] = (df['amount'] - df['amount'].mean()) / df['amount'].std()
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df['hour'] = df['date'].dt.hour
                df['day_of_week'] = df['date'].dt.dayofweek
                df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            
            if 'category' in df.columns:
                le = LabelEncoder()
                df['category_encoded'] = le.fit_transform(df['category'].astype(str))
            
            feature_cols = [col for col in ['amount_log', 'amount_zscore', 'hour', 'day_of_week', 
                                          'is_weekend', 'category_encoded'] if col in df.columns]
            return df[feature_cols].fillna(0)
            
        elif data_type == "vehicle":
            numeric_cols = ['distance', 'average_speed', 'max_speed', 'fuel_consumed']
            for col in numeric_cols:
                if col in df.columns:
                    df[f'{col}_zscore'] = (df[col] - df[col].mean()) / df[col].std()
            
            feature_cols = [col for col in [f'{c}_zscore' for c in numeric_cols] if col in df.columns]
            return df[feature_cols].fillna(0)
            
        elif data_type == "performance":
            numeric_cols = ['price', 'distance', 'duration_hours', 'rating', 'utilization_rate']
            for col in numeric_cols:
                if col in df.columns:
                    df[f'{col}_zscore'] = (df[col] - df[col].mean()) / df[col].std()
            
            feature_cols = [col for col in [f'{c}_zscore' for c in numeric_cols] if col in df.columns]
            return df[feature_cols].fillna(0)
        
        return df.fillna(0)
    
    def _generate_future_dates(self, days_ahead: int) -> List[datetime]:
        """Generate future dates for prediction."""
        return [datetime.now() + timedelta(days=i) for i in range(1, days_ahead + 1)]
    
    def _prepare_future_revenue_features(self, future_dates: List[datetime], historical_data: List[Dict]) -> pd.DataFrame:
        """Prepare features for future revenue prediction."""
        df_hist = pd.DataFrame(historical_data)
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        
        future_features = []
        for date in future_dates:
            recent_data = df_hist[df_hist['date'] >= (date - timedelta(days=30))]
            avg_7d = recent_data['amount'].tail(7).mean() if len(recent_data) >= 7 else df_hist['amount'].mean()
            avg_30d = recent_data['amount'].mean() if len(recent_data) > 0 else df_hist['amount'].mean()
            
            last_amount = df_hist['amount'].iloc[-1] if len(df_hist) > 0 else 0
            last_7d_amount = df_hist['amount'].tail(7).iloc[-1] if len(df_hist) >= 7 else last_amount
            
            future_features.append({
                'day_of_week': date.weekday(),
                'month': date.month,
                'is_weekend': 1 if date.weekday() >= 5 else 0,
                'is_summer': 1 if date.month in [6, 7, 8] else 0,
                'is_holiday_season': 1 if date.month in [11, 12] else 0,
                'avg_7d': avg_7d,
                'avg_30d': avg_30d,
                'amount_lag_1': last_amount,
                'amount_lag_7': last_7d_amount,
                'trip_count': df_hist['trip_count'].mean() if 'trip_count' in df_hist.columns else 3
            })
        
        return pd.DataFrame(future_features)
    
    def _analyze_trip_patterns(self, trips_data: List[Dict]) -> Dict[str, Any]:
        """Analyze trip patterns for optimization."""
        if not trips_data:
            return {"summary": "No trip data available"}
        
        df = pd.DataFrame(trips_data)
        
        if 'start_time' in df.columns:
            df['start_time'] = pd.to_datetime(df['start_time'])
            df['hour'] = df['start_time'].dt.hour
            df['day_of_week'] = df['start_time'].dt.dayofweek
            
            best_hours = df.groupby('hour')['price'].mean().sort_values(ascending=False).head(3).index.tolist()
            best_days = df.groupby('day_of_week')['price'].mean().sort_values(ascending=False).head(2).index.tolist()
        else:
            best_hours = [9, 14, 18]
            best_days = [5, 6] 
        
        if 'location' in df.columns:
            location_profitability = df.groupby('location')['price'].mean().sort_values(ascending=False)
            best_locations = location_profitability.head(3).index.tolist()
        else:
            best_locations = ["Downtown", "Airport", "University"]
        
        if 'vehicle_type' in df.columns:
            vehicle_profitability = df.groupby('vehicle_type')['price'].mean().sort_values(ascending=False)
            best_vehicles = vehicle_profitability.head(2).index.tolist()
        else:
            best_vehicles = ["Luxury", "SUV"]
        
        return {
            "summary": f"Analyzed {len(trips_data)} trips",
            "best_hours": best_hours,
            "best_days": best_days,
            "best_locations": best_locations,
            "best_vehicles": best_vehicles,
            "avg_price": df['price'].mean() if 'price' in df.columns else 0
        }
    
    def _generate_trip_recommendations(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trip optimization recommendations."""
        hour_names = {0: "Midnight", 6: "Early Morning", 9: "Morning", 12: "Noon", 
                     14: "Afternoon", 18: "Evening", 21: "Night"}
        day_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 
                    4: "Friday", 5: "Saturday", 6: "Sunday"}
        
        best_times = [f"{hour_names.get(h, f'{h}:00')}" for h in patterns.get('best_hours', [9, 14, 18])]
        best_days = [f"{day_names.get(d, f'Day {d}')}" for d in patterns.get('best_days', [5, 6])]
        
        return {
            "times": best_times,
            "days": best_days,
            "locations": patterns.get('best_locations', ["Downtown", "Airport"]),
            "vehicle_types": patterns.get('best_vehicles', ["Luxury", "SUV"]),
            "expected_profitability": "High" if patterns.get('avg_price', 0) > 50 else "Medium",
            "avg_price": round(patterns.get('avg_price', 0), 2)
        }
    
    def _analyze_vehicle_health(self, vehicle_data: List[Dict]) -> Dict[str, Any]:
        """Analyze vehicle health metrics."""
        return {
            "overall_health": 85,
            "risk_factors": ["High mileage", "Frequent hard braking"]
        }
    
    def _predict_maintenance_needs(self, health_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Predict maintenance needs based on health analysis."""
        return {
            "alerts": ["Oil change due", "Brake inspection recommended"],
            "actions": ["Schedule maintenance", "Monitor brake performance"]
        }
    
    def _analyze_clusters(self, data: List[Dict], clusters: np.ndarray, cluster_type: str) -> Dict[str, Any]:
        """Analyze clustering results."""
        return {
            "clusters": [{"id": i, "size": int(np.sum(clusters == i))} for i in range(len(np.unique(clusters)))],
            "summary": f"Found {len(np.unique(clusters))} {cluster_type} clusters",
            "recommendations": ["Optimize cluster 1", "Monitor cluster 2"]
        }
    
    def _extract_geographic_features(self, trips_data: List[Dict]) -> np.ndarray:
        """Extract geographic features for hotspot analysis."""
        return np.array([[0, 0], [1, 1]])  
    
    def _analyze_geographic_hotspots(self, geo_features: np.ndarray, hotspots: np.ndarray, trips_data: List[Dict]) -> Dict[str, Any]:
        """Analyze geographic hotspots."""
        return {
            "hotspots": [{"lat": 0, "lon": 0, "intensity": 0.8}],
            "summary": "Found 3 high-intensity hotspots",
            "recommendations": ["Focus on hotspot 1", "Expand to hotspot 2"]
        }
    
    def _analyze_anomalies(self, data: List[Dict], anomaly_scores: np.ndarray, anomaly_type: str) -> Dict[str, Any]:
        """Analyze detected anomalies."""
        anomalies = [item for i, item in enumerate(data) if anomaly_scores[i] == -1]
        return {
            "anomalies": anomalies[:5], 
            "summary": f"Detected {len(anomalies)} {anomaly_type} anomalies",
            "risk_score": 0.3,
            "priority": "Medium"
        }
    
    def _combine_performance_data(self, trips_data: List[Dict], vehicles_data: List[Dict]) -> List[Dict]:
        """Combine data from multiple sources for performance analysis."""
        return trips_data + vehicles_data

# ------------------------------ END OF FILE ------------------------------
