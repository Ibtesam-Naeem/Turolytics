
# ------------------------------ URLS ------------------------------
TRIPS_BOOKED_URL = "https://turo.com/ca/en/trips/booked"
TRIPS_HISTORY_URL = "https://turo.com/ca/en/trips/history"

VEHICLES_LISTINGS_URL = "https://turo.com/ca/en/vehicles/listings"
BUSINESS_EARNINGS_URL = "https://turo.com/ca/en/business/earnings"
BUSINESS_RATINGS_URL = "https://turo.com/ca/en/business/reviews"
INBOX_MESSAGES_URL = "https://turo.com/ca/en/inbox/messages/thread"

# ------------------------------ PAGE SELECTORS ------------------------------

TRIPS_UPCOMING_LIST = '[data-testid="trips-upcoming-trips-list"]'
TRIP_HISTORY_LIST = '[data-testid="trip-history-list"]'

TRIP_CARD = '[data-testid="baseTripCard"]'

VEHICLES_LISTINGS_GRID = '.css-3j7pzn-VehicleListingsGrid'
VEHICLE_CARD = '[data-testid="vehicle-listing-details-card"]'
VEHICLES_VIEW = '.css-7r5omw-VehiclesView'

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

CANCELLATION_SELECTOR = '.css-x4dp90-StyledText'

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

# ------------------------------ VEHICLE CARD SELECTORS ------------------------------

VEHICLE_STATUS_SELECTORS = [
    '.css-116zd9t-VehicleDetailsCard div',  # Snoozed/Listed status
    '.css-1fx8k8t',                         # Listed status
    '.css-1h7k5xv'                          # Snoozed status
]

VEHICLE_IMAGE_SELECTORS = [
    '.css-uev5fr-StyledImage-StyledVehicleImage-vehicleImage',
    'img[alt*="vehicle"]',
    '.css-yu07v3-vehicleImageContainer img'
]

VEHICLE_NAME_SELECTORS = [
    '.css-1s9awq7-StyledText',
    'p[title*="2017"]',
    'p[title*="2018"]',
    'p[title*="2019"]',
    'p[title*="2020"]',
    'p[title*="2021"]',
    'p[title*="2022"]',
    'p[title*="2023"]',
    'p[title*="2024"]',
    'p[title*="2025"]'
]

VEHICLE_DETAILS_SELECTORS = [
    '.css-1u90aiw-StyledText-VehicleDetailsCard',
    '.css-sivu8m-VehicleDetailsCard p'
]

VEHICLE_TRIP_INFO_SELECTORS = [
    '.css-j2jl8y-StyledText',
    '.css-s1wb9o-spaceBetween p:first-child'
]

VEHICLE_RATINGS_SELECTORS = [
    '.css-1xs83q-StyledText-VehicleListingRatingsText',
    '.css-s1wb9o-spaceBetween p:last-child'
]

VEHICLE_LISTINGS_COUNT = '.css-18mfln5-StyledText' 

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

# ------------------------------ EARNINGS SELECTORS ------------------------------

EARNINGS_TOTAL_SELECTOR = 'h2[data-testid="earningsFilterSummary-total"] span'
EARNINGS_TOTAL_TEXT_SELECTOR = 'h2[data-testid="earningsFilterSummary-total"]'

EARNINGS_LEGEND_SELECTOR = '.legend'
EARNINGS_LEGEND_TAG_SELECTOR = '.legend-tag'

EARNINGS_AMOUNT_SELECTOR = '.css-bgx7g9-StyledText'
EARNINGS_TYPE_SELECTOR = '.css-foqw77-StyledText'
EARNINGS_TOOLTIP_SELECTOR = 'span[data-testid="tooltipPanel-content"] span.css-1afgvk6-StyledText'

VEHICLE_EARNINGS_HEADER_SELECTOR = '.css-1wmkkoy-StyledTableHeaderRow'
VEHICLE_EARNINGS_ROW_SELECTOR = '.css-4a2atv-StyledTableRow'

VEHICLE_EARNINGS_IMAGE_SELECTOR = 'div.css-q4kmj6-MediaObjectWrapper img'
VEHICLE_EARNINGS_NAME_SELECTOR = 'p.css-nmsfeq-StyledText-StyledMakeModelYear'
VEHICLE_EARNINGS_DETAILS_SELECTOR = 'p.css-47w2m9-StyledText-StyledMakeModelYear-StyledLicenseAndTrim'
VEHICLE_EARNINGS_AMOUNT_SELECTOR = 'p.css-14bos0l-StyledText span'

# ------------------------------ RATINGS SELECTORS ------------------------------

RATINGS_OVERALL_SELECTOR = '[data-testid="cardAccordion-headerSuffix"] p.css-1vmc2vr-StyledText'
RATINGS_OVERALL_CATEGORY_SELECTOR = '[data-testid="cardAccordion-header"] p.css-1vmc2vr-StyledText'

RATINGS_TRIPS_COUNT_SELECTOR = '[data-testid="ratingsDetails-trips"] p.css-13mmra7-StyledText'
RATINGS_RATINGS_COUNT_SELECTOR = '[data-testid="ratingsDetails-ratings"] p.css-13mmra7-StyledText'
RATINGS_AVERAGE_SELECTOR = '[data-testid="ratingsDetails-average"] .css-xbnzaw-StyledText-categoryAverageMetricStyles'

REVIEWS_HEADER_SELECTOR = '.css-1rqnw09-reviewsColumnHeaderStyles h2'
REVIEWS_COUNT_SELECTOR = '.css-1rqnw09-reviewsColumnHeaderStyles h2'
REVIEWS_CATEGORY_SELECTOR = '.css-1rqnw09-reviewsColumnHeaderStyles p.css-v7tkns-StyledText'

REVIEW_LIST_CONTAINER_SELECTOR = '[data-testid="reviewList-container"]'
REVIEW_ITEM_SELECTOR = '[data-testid="reviewList-review"]'

REVIEW_CUSTOMER_LINK_SELECTOR = 'a[rel="nofollow"][href*="/drivers/"]'
REVIEW_CUSTOMER_IMAGE_SELECTOR = 'a[rel="nofollow"][href*="/drivers/"] svg, a[rel="nofollow"][href*="/drivers/"] img'
REVIEW_STAR_RATING_SELECTOR = '.css-1qr3nc0-StarRating-Container [aria-label*="Rating:"]'
REVIEW_CUSTOMER_NAME_SELECTOR = '.css-ov1ktg p.css-j2jl8y-StyledText span:first-child'
REVIEW_DATE_SELECTOR = '.css-ov1ktg p.css-j2jl8y-StyledText span.css-s0p4kp-StyledText'
REVIEW_VEHICLE_INFO_SELECTOR = '.css-1e0dz7l-ReviewBody p.css-j2jl8y-StyledText:not(.css-ov1ktg p)'
REVIEW_TEXT_SELECTOR = '.css-1e0dz7l-ReviewBody p.css-14bos0l-StyledText'

REVIEW_AREAS_IMPROVEMENT_SELECTOR = '[data-testid="reviewsAreasOfImprovement-badge"]'
REVIEW_HOST_RESPONSE_SELECTOR = '.css-1ojqf3u-Well-ReviewReplyContainer'

REVIEW_SEE_FULL_BUTTON_SELECTOR = 'button:has-text("See full review")'
REVIEW_RESPOND_BUTTON_SELECTOR = '[data-testid="respondToReviewView-showForm"]'