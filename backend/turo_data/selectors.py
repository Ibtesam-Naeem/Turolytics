
# ------------------------------ URLS ------------------------------
TRIPS_BOOKED_URL = "https://turo.com/ca/en/trips/booked"
TRIPS_HISTORY_URL = "https://turo.com/ca/en/trips/history"

VEHICLES_LISTINGS_URL = "https://turo.com/ca/en/vehicles/listings"
BUSINESS_EARNINGS_URL = "https://turo.com/ca/en/business/earnings"
INBOX_MESSAGES_URL = "https://turo.com/ca/en/inbox/messages/thread"

# ------------------------------ PAGE SELECTORS ------------------------------

TRIPS_UPCOMING_LIST = '[data-testid="trips-upcoming-trips-list"]'
TRIP_HISTORY_LIST = '[data-testid="trip-history-list"]'

TRIP_CARD = '[data-testid="baseTripCard"]'

MONTH_HEADER = '.css-4pg9bw-StyledText'
DATE_HEADER = '.css-14bos0l-StyledText'

# ------------------------------ TRIP CARD SELECTORS ------------------------------

TRIP_DATE_SELECTORS = [
    '.css-uhvnse-StyledText-TripHistoryCard',  # Completed trips
    '.css-iinurx-StyledText-TripHistoryCard',  # Cancelled trips
    '[class*="TripHistoryCard"]',              # Fallback
    'p:first-child'                            # Generic fallback
]

VEHICLE_SELECTORS = [
    '.css-1s9awq7-StyledText',                 # Standard vehicle text
    '[class*="StyledText"]:not([class*="TripHistoryCard"])',  # Alternative
    'p:nth-child(2)'                          # fallback
]

CUSTOMER_SELECTORS = [
    '.css-sc8osv-StyledText',                  # Primary customer selector
    '[class*="StyledText"]',                   # Broader search
    'p'                                        # fallback
]

# Trip status and cancellation
CANCELLATION_SELECTOR = '.css-x4dp90-StyledText'

# License plate
LICENSE_PLATE_SELECTORS = [
    '.css-15h68s2-StyledText',                # Primary license plate
    'p:last-child',                           # fallback
    '[class*="StyledText"]:last-child'        # fallback
]

ALL_IMAGES = 'img'
VEHICLE_IMAGE = '.css-vov8zg-StyledImage-StyledVehicleImage'
CUSTOMER_PROFILE_IMAGE = '[data-testid="profilePhoto-image"]'

# ------------------------------ BOOKED TRIPS SELECTORS ------------------------------

TIME_INFO = '.css-18fknbt' 
LOCATION = '.css-j2jl8y-StyledText' 

# ------------------------------ IMAGE CLASSIFICATION ------------------------------

VEHICLE_IMAGE_KEYWORDS = ['vehicle', 'media/vehicle']
CUSTOMER_IMAGE_KEYWORDS = ['profilePhoto', 'driver']

VEHICLE_BRANDS = [
    'Hyundai', 'Toyota', 'Honda', 'Nissan', 'Ford', 'Chevrolet', 
    'BMW', 'Mercedes', 'Audi', 'Volkswagen', 'Mazda', 'Subaru'
]

# ------------------------------ DATE PATTERNS ------------------------------

MONTH_NAMES = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]

DATE_SEPARATORS = ['-', 'to', '–', '—']

# ------------------------------ HELPER FUNCTIONS ------------------------------

def is_vehicle_related(text, src_url):
    """
    Check if an image is vehicle-related based on alt text or URL.
    
    Args:
        text: Alt text of the image
        src_url: Source URL of the image
        
    Returns:
        bool: True if image is vehicle-related, False otherwise
    """
    if not text and not src_url:
        return False
    
    text_lower = (text or '').lower()
    url_lower = (src_url or '').lower()
    
    return any(keyword in text_lower or keyword in url_lower 
              for keyword in VEHICLE_IMAGE_KEYWORDS)

def is_customer_related(data_testid, src_url):
    """
    Check if an image is customer-related based on attributes.
    
    Args:
        data_testid: Data-testid attribute of the image
        src_url: Source URL of the image
        
    Returns:
        bool: True if image is customer-related, False otherwise
    """
    if not data_testid and not src_url:
        return False
    
    testid_check = data_testid and any(keyword in data_testid 
                                      for keyword in CUSTOMER_IMAGE_KEYWORDS)
    url_check = src_url and any(keyword in src_url.lower() 
                               for keyword in CUSTOMER_IMAGE_KEYWORDS)
    
    return testid_check or url_check

def contains_month_name(text):
    """
    Check if text contains any month name.
    
    Args:
        text: Text to check for month names
        
    Returns:
        bool: True if text contains any month name, False otherwise
    """
    if not text:
        return False
    
    return any(month in text for month in MONTH_NAMES)

def contains_vehicle_brand(text):
    """
    Check if text contains any vehicle brand.
    
    Args:
        text: Text to check for vehicle brands
        
    Returns:
        bool: True if text contains any vehicle brand, False otherwise
    """
    if not text:
        return False
    
    return any(brand in text for brand in VEHICLE_BRANDS)