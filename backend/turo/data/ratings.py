# ------------------------------ IMPORTS ------------------------------
from datetime import datetime
from typing import Any, Optional
from playwright.async_api import Page

from core.utils.logger import logger
from core.utils.browser_helpers import safe_text, try_selectors
from core.utils.data_helpers import extract_with_regex
from .selectors import (
    BUSINESS_RATINGS_URL, RATINGS_OVERALL_SELECTOR, RATINGS_OVERALL_CATEGORY_SELECTOR,
    RATINGS_TRIPS_COUNT_SELECTOR, RATINGS_RATINGS_COUNT_SELECTOR, RATINGS_AVERAGE_SELECTOR,
    REVIEWS_HEADER_SELECTORS, REVIEWS_CATEGORY_SELECTOR,
    REVIEW_LIST_CONTAINER_SELECTOR, REVIEW_ITEM_SELECTOR, REVIEW_CUSTOMER_LINK_SELECTOR,
    REVIEW_STAR_RATING_SELECTOR, REVIEW_CUSTOMER_NAME_SELECTOR,
    REVIEW_DATE_SELECTOR, REVIEW_VEHICLE_INFO_SELECTOR, REVIEW_TEXT_SELECTOR,
    REVIEW_AREAS_IMPROVEMENT_SELECTOR, REVIEW_HOST_RESPONSE_SELECTOR, REVIEW_FILLED_STAR_SELECTOR
)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def extract_number(text: str) -> Optional[float]:
    """Extract number from text using regex."""
    match = extract_with_regex(text, r'(\d+\.?\d*)')
    return float(match) if match else None

# ------------------------------ RATINGS PAGE SCRAPING ------------------------------


async def extract_overall_rating(page: Page) -> dict[str, str | None]:
    """Extract overall rating percentage and category."""
    try:
        percentage_element = await page.query_selector(RATINGS_OVERALL_SELECTOR)
        percentage = await safe_text(percentage_element)
        
        category_element = await page.query_selector(RATINGS_OVERALL_CATEGORY_SELECTOR)
        category = await safe_text(category_element)
        
        return {
            'percentage': percentage,
            'category': category
        }
    except Exception as e:
        logger.debug(f"Error extracting overall rating: {e}")
        return {'percentage': None, 'category': None}

async def extract_trip_metrics(page: Page) -> dict[str, int | float | None]:
    """Extract trip counts, ratings count, and average rating."""
    try:
        trips_text = await safe_text(await page.query_selector(RATINGS_TRIPS_COUNT_SELECTOR))
        ratings_text = await safe_text(await page.query_selector(RATINGS_RATINGS_COUNT_SELECTOR))
        average_text = await safe_text(await page.query_selector(RATINGS_AVERAGE_SELECTOR))
        
        return {
            'trips_count': int(trips_text) if trips_text else None,
            'ratings_count': int(ratings_text) if ratings_text else None,
            'average_rating': extract_number(average_text) if average_text else None
        }
    except Exception as e:
        logger.debug(f"Error extracting trip metrics: {e}")
        return {'trips_count': None, 'ratings_count': None, 'average_rating': None}

async def extract_reviews_header(page: Page) -> dict[str, str | int | None]:
    """Extract reviews section header information."""
    try:
        title_element = await page.query_selector(REVIEWS_HEADER_SELECTORS[0])
        title_text = await safe_text(title_element)
        
        category_element = await page.query_selector(REVIEWS_CATEGORY_SELECTOR)
        category_text = await safe_text(category_element)
        
        count = None
        if title_text:
            count_match = extract_with_regex(title_text, r'\((\d+)\)')
            count = int(count_match) if count_match else None
        
        return {
            'title': title_text,
            'count': count,
            'category': category_text
        }
    except Exception as e:
        logger.debug(f"Error extracting reviews header: {e}")
        return {'title': None, 'count': None, 'category': None}

async def extract_star_rating(review_element) -> int | None:
    """Extract star rating from a review element."""
    try:
        rating_element = await review_element.query_selector(REVIEW_STAR_RATING_SELECTOR)
        if rating_element:
            aria_label = await rating_element.get_attribute('aria-label')
            if aria_label:
                rating_match = extract_with_regex(aria_label, r'Rating:\s*(\d+)\s*out of 5')
                if rating_match:
                    return int(rating_match)
        
        filled_stars = await review_element.query_selector_all(REVIEW_FILLED_STAR_SELECTOR)
        return len(filled_stars) if filled_stars else None
    
    except Exception as e:
        logger.debug(f"Error extracting star rating: {e}")
        return None

async def extract_individual_review(review_element, review_index: int) -> dict[str, Any]:
    """Extract individual review data from a review element."""
    try:
        customer_link = await review_element.query_selector(REVIEW_CUSTOMER_LINK_SELECTOR)
        customer_id = None
        if customer_link:
            href = await customer_link.get_attribute('href')
            customer_id = extract_with_regex(href or '', r'/drivers/(\d+)') if href else None
        
        customer_name = await try_selectors(review_element, [REVIEW_CUSTOMER_NAME_SELECTOR])
        if not customer_name:
            alternative_selectors = ['p span:first-child', '.css-j2jl8y-StyledText span', 'span:first-child', 'p span', 'span']
            customer_name = await try_selectors(review_element, alternative_selectors)
        
        date_text = await safe_text(await review_element.query_selector(REVIEW_DATE_SELECTOR))
        date = date_text.replace('•', '').strip() if date_text else None
        
        vehicle_info = await safe_text(await review_element.query_selector(REVIEW_VEHICLE_INFO_SELECTOR))
        review_text = await safe_text(await review_element.query_selector(REVIEW_TEXT_SELECTOR))
        
        improvement_elements = await review_element.query_selector_all(REVIEW_AREAS_IMPROVEMENT_SELECTOR)
        areas_of_improvement = [await safe_text(element) for element in improvement_elements if await safe_text(element)]
        
        response_text = await safe_text(await review_element.query_selector(REVIEW_HOST_RESPONSE_SELECTOR))
        has_host_response = bool(response_text)
        
        return {
            'customer_name': customer_name,
            'customer_id': customer_id,
            'rating': await extract_star_rating(review_element),
            'date': date,
            'vehicle_info': vehicle_info,
            'review_text': review_text,
            'areas_of_improvement': areas_of_improvement,
            'host_response': response_text,
            'has_host_response': has_host_response
        }
    except Exception as e:
        logger.debug(f"Error extracting individual review {review_index}: {e}")
        return {
            'customer_name': None, 'customer_id': None,
            'rating': None, 'date': None, 'vehicle_info': None, 'review_text': None,
            'areas_of_improvement': [], 'host_response': None, 'has_host_response': False
        }

async def extract_all_reviews(page: Page) -> list[dict[str, Any]]:
    """Extract all reviews from the reviews section."""
    try:
        await page.wait_for_selector(REVIEW_LIST_CONTAINER_SELECTOR, timeout=10000)
        review_elements = await page.query_selector_all(REVIEW_ITEM_SELECTOR)
        logger.info(f"Found {len(review_elements)} review elements")
        
        reviews = []
        for i, review_element in enumerate(review_elements):
            try:
                review_data = await extract_individual_review(review_element, i)
                reviews.append(review_data)
                
                customer_name = review_data.get('customer_name') or 'Unknown'
                rating = review_data.get('rating') or 'N/A'
                logger.info(f"Scraped review {i+1}: {customer_name} - {rating}")
            
            except Exception as e:
                logger.debug(f"Error extracting review {i+1}: {e}")
                continue
        
        return reviews

    except Exception as e:
        logger.debug(f"Error extracting all reviews: {e}")
        return []

async def scrape_ratings_data(page: Page) -> dict[str, Any] | None:
    """Scrape all ratings and reviews data from the business ratings page."""
    try:
        logger.info("Starting to scrape ratings data...")
        
        logger.info("Navigating to Business Reviews page...")
        await page.goto(BUSINESS_RATINGS_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        overall_rating = await extract_overall_rating(page)
        trip_metrics = await extract_trip_metrics(page)
        reviews_header = await extract_reviews_header(page)
        reviews = await extract_all_reviews(page)
        
        individual_ratings = [r.get('rating') for r in reviews if r.get('rating') is not None]
        calculated_average = sum(individual_ratings) / len(individual_ratings) if individual_ratings else None
        
        ratings_data = {
            'overall_rating': overall_rating,
            'trip_metrics': trip_metrics,
            'reviews_header': reviews_header,
            'reviews': reviews,
            'summary': {
                'total_reviews': len(reviews),
                'reviews_with_ratings': len(individual_ratings),
                'reviews_with_responses': len([r for r in reviews if r.get('has_host_response')]),
                'calculated_average_rating': calculated_average,
                'scraped_at': datetime.utcnow().isoformat()
            }
        }
        
        logger.info("Ratings data scraping completed successfully!")
        return ratings_data

    except Exception as e:
        logger.exception(f"Error scraping ratings data: {e}")
        return None

# ------------------------------ COMBINED RATINGS SCRAPING ------------------------------

async def scrape_all_ratings_data(page: Page) -> dict[str, Any] | None:
    """Scrape all ratings and reviews data including overall rating, metrics, and individual reviews."""
    try:
        logger.info("Starting to scrape all ratings data...")
        
        ratings_data = await scrape_ratings_data(page)
        if not ratings_data:
            logger.warning("Failed to scrape ratings data")
            ratings_data = {
                'overall_rating': {'percentage': None, 'category': None},
                'trip_metrics': {'trips_count': None, 'ratings_count': None, 'average_rating': None},
                'reviews_header': {'title': None, 'count': None, 'category': None},
                'reviews': [],
                'summary': {'total_reviews': 0, 'reviews_with_ratings': 0, 'reviews_with_responses': 0, 'calculated_average_rating': None, 'scraped_at': datetime.utcnow().isoformat()}
            }
        
        all_ratings_data = {
            'ratings': ratings_data,
            'scraping_success': {'ratings': ratings_data is not None}
        }
        
        logger.info("All ratings data scraping completed!")
        return all_ratings_data

    except Exception as e:
        logger.exception(f"Error scraping all ratings data: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------