# ------------------------------ IMPORTS ------------------------------
import asyncio
from datetime import datetime
from typing import Any, Optional
from playwright.async_api import Page

from core.utils.logger import logger
from core.config.settings import TIMEOUT_SELECTOR_WAIT
from .helpers import navigate_to_page, extract_with_regex, try_selectors, get_text, process_items_in_parallel, extract_texts_from_elements
from .selectors import (
    BUSINESS_RATINGS_URL,
    REVIEW_LIST_CONTAINER_SELECTOR, REVIEW_ITEM_SELECTOR, REVIEW_CUSTOMER_LINK_SELECTOR,
    REVIEW_STAR_RATING_SELECTOR, REVIEW_CUSTOMER_NAME_SELECTOR,
    REVIEW_DATE_SELECTOR, REVIEW_VEHICLE_INFO_SELECTOR, REVIEW_TEXT_SELECTOR,
    REVIEW_AREAS_IMPROVEMENT_SELECTOR, REVIEW_HOST_RESPONSE_SELECTOR, REVIEW_FILLED_STAR_SELECTOR
)

# ------------------------------ RATINGS PAGE SCRAPING ------------------------------

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
        
        date_text = await get_text(review_element, REVIEW_DATE_SELECTOR)
        date = date_text.replace('•', '').strip() if date_text else None
        
        vehicle_info = await get_text(review_element, REVIEW_VEHICLE_INFO_SELECTOR)
        review_text = await get_text(review_element, REVIEW_TEXT_SELECTOR)
        
        areas_of_improvement = await extract_texts_from_elements(review_element, REVIEW_AREAS_IMPROVEMENT_SELECTOR)
        
        response_text = await get_text(review_element, REVIEW_HOST_RESPONSE_SELECTOR)
        
        return {
            'customer_name': customer_name,
            'customer_id': customer_id,
            'rating': await extract_star_rating(review_element),
            'date': date,
            'vehicle_info': vehicle_info,
            'review_text': review_text,
            'areas_of_improvement': areas_of_improvement,
            'host_response': response_text,
            'has_host_response': bool(response_text)
        }
    except Exception as e:
        logger.debug(f"Error extracting individual review {review_index}: {e}")
        return {
            'customer_name': None, 'customer_id': None,
            'rating': None, 'date': None, 'vehicle_info': None, 'review_text': None,
            'areas_of_improvement': [], 'host_response': None, 'has_host_response': False
        }

async def extract_all_reviews(page: Page) -> list[dict[str, Any]]:
    """Extract all reviews from the reviews section using parallel processing."""
    try:
        await page.wait_for_selector(REVIEW_LIST_CONTAINER_SELECTOR, timeout=TIMEOUT_SELECTOR_WAIT)
        review_elements = await page.query_selector_all(REVIEW_ITEM_SELECTOR)
        logger.debug(f"Found {len(review_elements)} review elements")
        
        reviews = await process_items_in_parallel(
            review_elements,
            extract_individual_review,
            item_type="review"
        )
        
        return reviews

    except Exception as e:
        logger.debug(f"Error extracting all reviews: {e}")
        return []

async def scrape_ratings_data(page: Page) -> dict[str, Any] | None:
    """Scrape all ratings and reviews data from the business ratings page."""
    try:
        logger.info("Starting to scrape ratings data...")
        
        if not await navigate_to_page(page, BUSINESS_RATINGS_URL, "Business Reviews"):
            logger.error("Failed to navigate to ratings page")
            return None
        
        reviews = await extract_all_reviews(page)
        
        individual_ratings = [r.get('rating') for r in reviews if r.get('rating') is not None]
        calculated_average = sum(individual_ratings) / len(individual_ratings) if individual_ratings else None
        
        ratings_data = {
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


# ------------------------------ END OF FILE ------------------------------