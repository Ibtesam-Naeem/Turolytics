
# ------------------------------ URLS ------------------------------
LOGIN_URL = "https://turo.com/ca/en/login"
TRIPS_BOOKED_URL = "https://turo.com/ca/en/trips/booked"
TRIPS_HISTORY_URL = "https://turo.com/ca/en/trips/history"

VEHICLES_LISTINGS_URL = "https://turo.com/ca/en/vehicles/listings"
BUSINESS_RATINGS_URL = "https://turo.com/ca/en/business/reviews"
BUSINESS_EARNINGS_URL = "https://turo.com/ca/en/business/earnings"

# ------------------------------ LOGIN SELECTORS ------------------------------

CONTINUE_WITH_EMAIL_SELECTOR = ".css-131npuy"
EMAIL_SELECTOR = 'input[type="email"][name="email"], #email'
PASSWORD_SELECTOR = 'input[type="password"][name="password"], #password'
TEXT_CODE_BUTTON = 'button.buttonSchumi--purple'
CODE_INPUT_SELECTOR = '#challengeCode'
FINAL_CONTINUE_BUTTON = 'button:has-text("Submit")'
CONTINUE_BUTTON_TEXT_SELECTOR = "button:has-text('Continue')"

# Login success indicators 
LOGIN_SUCCESS_URLS = [
    "**/dashboard", "**/trips", "**/trips/booked", 
    "**/trips/booked?recentUpdates=true", "**/account", "**/profile"
]

LOGIN_SUCCESS_SELECTORS = [
    '[data-testid="user-menu"]', '.user-menu', '.account-menu',
    '[aria-label*="Account"]', '[aria-label*="Profile"]', '.avatar', '.user-avatar'
]

# ------------------------------ PAGE SELECTORS ------------------------------

TRIPS_UPCOMING_LIST = '[data-testid="trips-upcoming-trips-list"]'
TRIP_HISTORY_LIST = '[data-testid="trip-history-list"]'

TRIP_CARD = '[data-testid="baseTripCard"]'

VEHICLE_CARD = '[data-testid="vehicle-listing-details-card"]'

MONTH_HEADER_SELECTORS = [
    '[data-testid="month-header"]',  # Primary
    '.css-4pg9bw-StyledText'         # Fallback
]
DATE_HEADER_SELECTORS = [
    '[data-testid="date-header"]',  # Primary
    '.css-14bos0l-StyledText'       # Fallback
]

# ------------------------------ TRIP CARD SELECTORS ------------------------------

TRIP_DATE_SELECTORS = [
    '.css-uhvnse-StyledText-TripHistoryCard',  # Completed trips
    '.css-iinurx-StyledText-TripHistoryCard',  # Cancelled trips
    '[class*="TripHistoryCard"]',              # Fallback
    'p:first-child'                            # Fallback
]

VEHICLE_SELECTORS = [
    '.css-1s9awq7-StyledText',                 # Primary
    '[class*="StyledText"]:not([class*="TripHistoryCard"])',  # Alternative
    'p:nth-child(2)'                          # Fallback
]

CUSTOMER_SELECTORS = [
    '.css-sc8osv-StyledText',                  # Primary
    '[class*="StyledText"]',                   # Alternative
    'p'                                        # Fallback
]

CANCELLATION_SELECTOR = '.css-x4dp90-StyledText'

LICENSE_PLATE_SELECTORS = [
    '.css-15h68s2-StyledText',                # Primary
    'p:last-child',                           # Fallback
    '[class*="StyledText"]:last-child'        # Fallback
]

# ------------------------------ BOOKED TRIPS SELECTORS ------------------------------

TIME_INFO = '.css-18fknbt' 
LOCATION = '.css-j2jl8y-StyledText'

# ------------------------------ TRIP DETAIL PAGE SELECTORS ------------------------------

TRIP_DETAILS_CONTAINER = '[data-testid="reservationTripDetails"]'

SCHEDULE_DATE_SELECTOR = '[data-testid="schedule-date"]'
SCHEDULE_TIME_START_SELECTOR = '.css-hrgeud-StyledText-StyledScheduleDateTime'
SCHEDULE_TIME_END_SELECTOR = '.css-qfa5m1-StyledText-StyledScheduleDateTime'

LOCATION_SECTION_LABEL_SELECTOR = '.detailsSection-label'
LOCATION_ADDRESS_SELECTOR = '.reservationLocation-address .css-j2jl8y-StyledText'

DETAIL_VEHICLE_NAME_SELECTOR = '.css-1d4ywag-StyledText'

KILOMETERS_INCLUDED_SELECTOR = '.detailsSection .css-14bos0l-StyledText'  
KILOMETERS_DRIVEN_SELECTOR = '.detailsSection .css-14bos0l-StyledText'  
KILOMETERS_OVERAGE_SELECTOR = '.distanceIncluded-overageMessage'

EARNINGS_SECTION_SELECTOR = '.reservationDetails-totalEarnings'
EARNINGS_AMOUNT_SELECTOR = '.reservationDetails-totalEarnings .css-14bos0l-StyledText span'
EARNINGS_RECEIPT_LINK_SELECTOR = '.reservationDetails-totalEarnings .css-1ycxd8s-linkStyles'

PROTECTION_PLAN_SELECTOR = '.reservationDetails-protection .css-jkt5rs-Button'
PROTECTION_DEDUCTIBLE_SELECTOR = '.reservationDetails-protection .css-1hf155s-StyledText'

RESERVATION_NUMBER_SELECTOR = '.css-1exfdxm-StyledText'

# ------------------------------ VEHICLE CARD SELECTORS ------------------------------

VEHICLE_STATUS_SELECTORS = [
    '.css-116zd9t-VehicleDetailsCard div',  # Snoozed/Listed status
    '.css-1fx8k8t',                         # Listed status
    '.css-1h7k5xv'                          # Snoozed status
]

VEHICLE_NAME_SELECTORS = ['.css-1s9awq7-StyledText'] + [
    f'p[title*="{year}"]' for year in range(2017, 2026)
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

VEHICLE_BRANDS = [
    'Hyundai', 'Toyota', 'Honda', 'Nissan', 'Ford', 'Chevrolet', 
    'BMW', 'Mercedes', 'Audi', 'Volkswagen', 'Mazda', 'Subaru', 'Genesis'
]

VEHICLE_STATUSES = ['Listed', 'Snoozed', 'Unavailable', 'Maintenance']

# ------------------------------ DATE PATTERNS ------------------------------

MONTH_NAMES = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]

VALID_YEARS = [str(year) for year in range(2017, 2026)]

YEAR_PATTERN_REGEX = r'\b(' + '|'.join(VALID_YEARS) + r')\b'
YEAR_PATTERN_NON_CAPTURING = r'\b(?:' + '|'.join(VALID_YEARS) + r')\b'

# ------------------------------ RATINGS SELECTORS ------------------------------

RATINGS_OVERALL_SELECTOR = '[data-testid="cardAccordion-headerSuffix"] p.css-1vmc2vr-StyledText'
RATINGS_OVERALL_CATEGORY_SELECTOR = '[data-testid="cardAccordion-header"] p.css-1vmc2vr-StyledText'

RATINGS_TRIPS_COUNT_SELECTOR = '[data-testid="ratingsDetails-trips"] p.css-13mmra7-StyledText'
RATINGS_RATINGS_COUNT_SELECTOR = '[data-testid="ratingsDetails-ratings"] p.css-13mmra7-StyledText'
RATINGS_AVERAGE_SELECTOR = '[data-testid="ratingsDetails-average"] .css-xbnzaw-StyledText-categoryAverageMetricStyles'

REVIEWS_HEADER_SELECTORS = [
    '[data-testid="reviews-header"]',                    # Primary
    '.css-1rqnw09-reviewsColumnHeaderStyles h2'          # Fallback
]
REVIEWS_CATEGORY_SELECTOR = '.css-1rqnw09-reviewsColumnHeaderStyles p.css-v7tkns-StyledText'

REVIEW_LIST_CONTAINER_SELECTOR = '[data-testid="reviewList-container"]'
REVIEW_ITEM_SELECTOR = '[data-testid="reviewList-review"]'

REVIEW_CUSTOMER_LINK_SELECTOR = 'a[rel="nofollow"][href*="/drivers/"]'
REVIEW_STAR_RATING_SELECTOR = '.css-1qr3nc0-StarRating-Container [aria-label*="Rating:"]'
REVIEW_CUSTOMER_NAME_SELECTOR = '.css-ov1ktg p.css-j2jl8y-StyledText span:first-child'
REVIEW_DATE_SELECTOR = '.css-ov1ktg p.css-j2jl8y-StyledText span.css-s0p4kp-StyledText'
REVIEW_VEHICLE_INFO_SELECTOR = '.css-1e0dz7l-ReviewBody p.css-j2jl8y-StyledText:not(.css-ov1ktg p)'
REVIEW_TEXT_SELECTOR = '.css-1e0dz7l-ReviewBody p.css-14bos0l-StyledText'

REVIEW_AREAS_IMPROVEMENT_SELECTOR = '[data-testid="reviewsAreasOfImprovement-badge"]'
REVIEW_HOST_RESPONSE_SELECTOR = '.css-1ojqf3u-Well-ReviewReplyContainer'

REVIEW_FILLED_STAR_SELECTOR = '.css-10pswck svg[fill="#121214"]'

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

VEHICLE_EARNINGS_NAME_SELECTOR = 'p.css-nmsfeq-StyledText-StyledMakeModelYear'
VEHICLE_EARNINGS_DETAILS_SELECTOR = 'p.css-47w2m9-StyledText-StyledMakeModelYear-StyledLicenseAndTrim'
VEHICLE_EARNINGS_AMOUNT_SELECTOR = 'p.css-14bos0l-StyledText span'

# ------------------------------ HELPER FUNCTIONS ------------------------------

def contains_month_name(text: str | None) -> bool:
    """Return True if the text contains any month name."""
    if not text:
        return False
    
    return any(month in text for month in MONTH_NAMES)

def contains_vehicle_brand(text: str | None) -> bool:
    """Return True if the given text contains a known vehicle brand."""
    if not text:
        return False
    
    return any(brand in text for brand in VEHICLE_BRANDS)