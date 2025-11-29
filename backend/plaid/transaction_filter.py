# ------------------------------ IMPORTS ------------------------------
import re
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# ------------------------------ FILTERING RULES ------------------------------

VEHICLE_MERCHANT_KEYWORDS = {
    "gas": ["gas", "shell", "chevron", "bp", "exxon", "mobil", "texaco", "arco", "valero", "citgo", "speedway", "7-eleven", "wawa", "sheetz", "kum & go", "quik trip", "qt", "raceway", "pilot", "flying j", "love's", "ta", "truck stop"],
    "insurance": ["geico", "state farm", "allstate", "progressive", "farmers", "usaa", "nationwide", "liberty mutual", "american family", "travelers", "the general", "esurance", "metlife", "auto insurance", "car insurance"],
    "repair": ["auto repair", "mechanic", "garage", "service center", "auto service", "brake", "tire", "muffler", "transmission", "engine", "auto body", "collision", "jiffy lube", "valvoline", "firestone", "goodyear", "pep boys", "napa", "autozone", "oreilly", "advance auto"],
    "maintenance": ["oil change", "car wash", "detail", "detailing", "lube", "tune up", "inspection", "emissions", "smog check"],
    "parking": ["parking", "meter", "garage", "lot", "valet"],
    "toll": ["toll", "ez pass", "fastrak", "sunpass", "toll road", "tollway"],
    "registration": ["dmv", "dmv", "registration", "license plate", "tags", "vehicle registration"],
    "rental": ["turo", "hertz", "enterprise", "avis", "budget", "national", "alamo", "dollar", "thrifty", "car rental"],
}

PLAID_CATEGORY_MAPPINGS = {
    "gas": ["Gas Stations", "Fuel"],
    "insurance": ["Insurance"],
    "repair": ["Auto Repair", "Auto Parts"],
    "maintenance": ["Auto Repair", "Auto Parts", "Service"],
    "parking": ["Parking"],
    "toll": ["Tolls"],
    "registration": ["Government Services"],
}

EXPENSE_KEYWORDS = ["gas", "insurance", "repair", "maintenance", "parking", "toll", "registration"]
REVENUE_KEYWORDS = ["turo"]

# ------------------------------ FILTERING FUNCTIONS ------------------------------

def normalize_merchant_name(merchant: Optional[str]) -> str:
    """Normalize merchant name for matching."""
    if not merchant:
        return ""
    return merchant.lower().strip()

def matches_keywords(text: str, keywords: List[str]) -> bool:
    """Check if text contains any of the keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)

def calculate_merchant_match_score(merchant: Optional[str], category: str) -> float:
    """Calculate match score based on merchant name (0.0-1.0)."""
    if not merchant:
        return 0.0
    
    merchant_normalized = normalize_merchant_name(merchant)
    keywords = VEHICLE_MERCHANT_KEYWORDS.get(category, [])
    
    if not keywords:
        return 0.0
    
    if any(keyword == merchant_normalized for keyword in keywords):
        return 1.0
    
    if matches_keywords(merchant_normalized, keywords):
        return 0.8
    
    return 0.0

def calculate_category_match_score(plaid_category: Optional[List[str]], category: str) -> float:
    """Calculate match score based on Plaid category (0.0-1.0)."""
    if not plaid_category:
        return 0.0
    
    category_str = " ".join(plaid_category).lower()
    expected_categories = PLAID_CATEGORY_MAPPINGS.get(category, [])
    
    if not expected_categories:
        return 0.0
    
    for expected in expected_categories:
        if expected.lower() in category_str:
            return 1.0
    
    return 0.0

def classify_transaction_type(transaction: Dict[str, Any]) -> Optional[str]:
    """Classify transaction as 'expense' or 'revenue'."""
    amount = transaction.get("amount", 0)
    merchant = normalize_merchant_name(transaction.get("merchant_name") or transaction.get("name", ""))
    category = " ".join(transaction.get("category", [])).lower() if transaction.get("category") else ""
    
    if amount > 0:
        if matches_keywords(merchant + " " + category, REVENUE_KEYWORDS):
            return "revenue"
        return None
    
    if amount < 0:
        if matches_keywords(merchant + " " + category, EXPENSE_KEYWORDS):
            return "expense"
        return "expense"
    
    return None

def determine_vehicle_category(transaction: Dict[str, Any]) -> Tuple[Optional[str], float]:
    """Determine vehicle category and confidence score."""
    merchant = transaction.get("merchant_name") or transaction.get("name", "")
    plaid_category = transaction.get("category", [])
    
    best_category = None
    best_score = 0.0
    
    for category in VEHICLE_MERCHANT_KEYWORDS.keys():
        merchant_score = calculate_merchant_match_score(merchant, category)
        category_score = calculate_category_match_score(plaid_category, category)
        
        combined_score = (merchant_score * 0.7) + (category_score * 0.3)
        
        if combined_score > best_score:
            best_score = combined_score
            best_category = category
    
    if best_score < 0.3:
        return None, 0.0
    
    return best_category, best_score

def is_vehicle_related(transaction: Dict[str, Any]) -> Tuple[bool, Optional[str], float]:
    """Determine if transaction is vehicle-related and return category with confidence."""
    vehicle_category, confidence = determine_vehicle_category(transaction)
    
    if vehicle_category and confidence >= 0.3:
        return True, vehicle_category, confidence
    
    return False, None, 0.0

def filter_vehicle_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter and classify vehicle-related transactions."""
    filtered = []
    
    for transaction in transactions:
        is_vehicle, category, confidence = is_vehicle_related(transaction)
        transaction_type = classify_transaction_type(transaction)
        
        transaction["is_vehicle_related"] = is_vehicle
        transaction["vehicle_category"] = category
        transaction["transaction_type"] = transaction_type
        transaction["match_confidence"] = confidence
        
        if is_vehicle:
            filtered.append(transaction)
    
    return filtered

def categorize_all_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Categorize all transactions with classification."""
    categorized = []
    
    for transaction in transactions:
        is_vehicle, category, confidence = is_vehicle_related(transaction)
        transaction_type = classify_transaction_type(transaction)
        
        transaction["is_vehicle_related"] = is_vehicle
        transaction["vehicle_category"] = category
        transaction["transaction_type"] = transaction_type
        transaction["match_confidence"] = confidence
        
        categorized.append(transaction)
    
    return categorized

# ------------------------------ END OF FILE ------------------------------

