# ------------------------------ IMPORTS ------------------------------
import re
from datetime import datetime
from typing import Any
from playwright.async_api import Page

from utils.logger import logger
from .selectors import (
    BUSINESS_RATINGS_URL, RATINGS_OVERALL_SELECTOR, RATINGS_OVERALL_CATEGORY_SELECTOR,
    RATINGS_TRIPS_COUNT_SELECTOR, RATINGS_RATINGS_COUNT_SELECTOR, RATINGS_AVERAGE_SELECTOR,
    REVIEWS_HEADER_SELECTOR, REVIEWS_CATEGORY_SELECTOR,
    REVIEW_LIST_CONTAINER_SELECTOR, REVIEW_ITEM_SELECTOR, REVIEW_CUSTOMER_LINK_SELECTOR,
    REVIEW_CUSTOMER_IMAGE_SELECTOR, REVIEW_STAR_RATING_SELECTOR, REVIEW_CUSTOMER_NAME_SELECTOR,
    REVIEW_DATE_SELECTOR, REVIEW_VEHICLE_INFO_SELECTOR, REVIEW_TEXT_SELECTOR,
    REVIEW_AREAS_IMPROVEMENT_SELECTOR, REVIEW_HOST_RESPONSE_SELECTOR, REVIEW_FILLED_STAR_SELECTOR
)

# ------------------------------ RATINGS PAGE SCRAPING ------------------------------

async def navigate_to_ratings_page(page: Page) -> bool:
    """Navigate to the business ratings page."""
    try:
        logger.info("Navigating to Business Reviews page...")
        await page.goto(BUSINESS_RATINGS_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        if "business/reviews" in page.url:
            logger.info("Successfully navigated to Business Reviews page")
            return True
        else:
            logger.warning(f"Navigation may have failed. Current URL: {page.url}")
            return False
            
    except Exception as e:
        logger.exception(f"Error navigating to Business Reviews: {e}")
        return False

async def extract_overall_rating(page: Page) -> dict[str, str | None]:
    """Extract overall rating percentage and category."""
    try:
        overall_rating = {
            'percentage': None,
            'category': None
        }
        
        percentage_element = await page.query_selector(RATINGS_OVERALL_SELECTOR)
        if percentage_element:
            percentage_text = await percentage_element.text_content()
            if percentage_text:
                overall_rating['percentage'] = percentage_text.strip()
        
        category_element = await page.query_selector(RATINGS_OVERALL_CATEGORY_SELECTOR)
        if category_element:
            category_text = await category_element.text_content()
            if category_text:
                overall_rating['category'] = category_text.strip()
        
        return overall_rating
        
    except Exception as e:
        logger.debug(f"Error extracting overall rating: {e}")
        return {'percentage': None, 'category': None}

async def extract_trip_metrics(page: Page) -> dict[str, int | float | None]:
    """Extract trip counts, ratings count, and average rating."""
    try:
        trip_metrics = {
            'trips_count': None,
            'ratings_count': None,
            'average_rating': None
        }
        
        trips_element = await page.query_selector(RATINGS_TRIPS_COUNT_SELECTOR)
        if trips_element:
            trips_text = await trips_element.text_content()
            if trips_text:
                trip_metrics['trips_count'] = int(trips_text.strip())
        
        ratings_element = await page.query_selector(RATINGS_RATINGS_COUNT_SELECTOR)
        if ratings_element:
            ratings_text = await ratings_element.text_content()
            if ratings_text:
                trip_metrics['ratings_count'] = int(ratings_text.strip())
        
        average_element = await page.query_selector(RATINGS_AVERAGE_SELECTOR)
        if average_element:
            average_text = await average_element.text_content()
            if average_text:
                rating_match = re.search(r'(\d+\.?\d*)', average_text)
                if rating_match:
                    trip_metrics['average_rating'] = float(rating_match.group(1))
        
        return trip_metrics
        
    except Exception as e:
        logger.debug(f"Error extracting trip metrics: {e}")
        return {'trips_count': None, 'ratings_count': None, 'average_rating': None}

async def extract_reviews_header(page: Page) -> dict[str, str | int | None]:
    """Extract reviews section header information."""
    try:
        reviews_header = {
            'title': None,
            'count': None,
            'category': None
        }
        
        title_element = await page.query_selector(REVIEWS_HEADER_SELECTOR)
        if title_element:
            title_text = await title_element.text_content()
            if title_text:
                reviews_header['title'] = title_text.strip()
                count_match = re.search(r'\((\d+)\)', title_text)
                if count_match:
                    reviews_header['count'] = int(count_match.group(1))
        
        category_element = await page.query_selector(REVIEWS_CATEGORY_SELECTOR)
        if category_element:
            category_text = await category_element.text_content()
            if category_text:
                reviews_header['category'] = category_text.strip()
        
        return reviews_header
        
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
                rating_match = re.search(r'Rating:\s*(\d+)\s*out of 5', aria_label)
                if rating_match:
                    return int(rating_match.group(1))
        
        filled_stars = await review_element.query_selector_all(REVIEW_FILLED_STAR_SELECTOR)
        if filled_stars:
            return len(filled_stars)
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting star rating: {e}")
        return None

async def extract_individual_review(review_element, review_index: int) -> dict[str, Any]:
    """Extract individual review data from a review element."""
    try:
        review_data = {
            'customer_name': None,
            'customer_id': None,
            'customer_image_url': None,
            'customer_image_alt': None,
            'rating': None,
            'date': None,
            'vehicle_info': None,
            'review_text': None,
            'areas_of_improvement': [],
            'host_response': None,
            'has_host_response': False
        }
        
        customer_link = await review_element.query_selector(REVIEW_CUSTOMER_LINK_SELECTOR)
        if customer_link:
            href = await customer_link.get_attribute('href')
            if href:
                id_match = re.search(r'/drivers/(\d+)', href)
                if id_match:
                    review_data['customer_id'] = id_match.group(1)
        
        customer_image = await review_element.query_selector(REVIEW_CUSTOMER_IMAGE_SELECTOR)
        if customer_image:
            if await customer_image.evaluate('el => el.tagName') == 'IMG':
                review_data['customer_image_url'] = await customer_image.get_attribute('src')
                review_data['customer_image_alt'] = await customer_image.get_attribute('alt')
            else:
                review_data['customer_image_url'] = None
                review_data['customer_image_alt'] = None
        
        name_element = await review_element.query_selector(REVIEW_CUSTOMER_NAME_SELECTOR)
        if name_element:
            name_text = await name_element.text_content()
            if name_text:
                review_data['customer_name'] = name_text.strip()
        
        review_data['rating'] = await extract_star_rating(review_element)
        
        date_element = await review_element.query_selector(REVIEW_DATE_SELECTOR)
        if date_element:
            date_text = await date_element.text_content()
            if date_text:
                clean_date = date_text.replace('•', '').strip()
                review_data['date'] = clean_date
        
        vehicle_element = await review_element.query_selector(REVIEW_VEHICLE_INFO_SELECTOR)
        if vehicle_element:
            vehicle_text = await vehicle_element.text_content()
            if vehicle_text:
                review_data['vehicle_info'] = vehicle_text.strip()
        
        text_element = await review_element.query_selector(REVIEW_TEXT_SELECTOR)
        if text_element:
            text_content = await text_element.text_content()
            if text_content:
                review_data['review_text'] = text_content.strip()
        
        improvement_elements = await review_element.query_selector_all(REVIEW_AREAS_IMPROVEMENT_SELECTOR)
        for element in improvement_elements:
            improvement_text = await element.text_content()
            if improvement_text:
                review_data['areas_of_improvement'].append(improvement_text.strip())
        
        response_element = await review_element.query_selector(REVIEW_HOST_RESPONSE_SELECTOR)
        if response_element:
            response_text = await response_element.text_content()
            if response_text:
                review_data['host_response'] = response_text.strip()
                review_data['has_host_response'] = True
        
        return review_data
        
    except Exception as e:
        logger.debug(f"Error extracting individual review {review_index}: {e}")
        return {
            'customer_name': None,
            'customer_id': None,
            'customer_image_url': None,
            'customer_image_alt': None,
            'rating': None,
            'date': None,
            'vehicle_info': None,
            'review_text': None,
            'areas_of_improvement': [],
            'host_response': None,
            'has_host_response': False
        }

async def extract_all_reviews(page: Page) -> list[dict[str, Any]]:
    """Extract all reviews from the reviews section."""
    try:
        reviews = []
        
        await page.wait_for_selector(REVIEW_LIST_CONTAINER_SELECTOR, timeout=10000)
        
        review_elements = await page.query_selector_all(REVIEW_ITEM_SELECTOR)
        logger.info(f"Found {len(review_elements)} review elements")
        
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
        
        if not await navigate_to_ratings_page(page):
            logger.error("Failed to navigate to ratings page")
            return None
        
        overall_rating = await extract_overall_rating(page)
        
        trip_metrics = await extract_trip_metrics(page)
        
        reviews_header = await extract_reviews_header(page)
        
        reviews = await extract_all_reviews(page)
        
        total_reviews = len(reviews)
        reviews_with_ratings = len([r for r in reviews if r.get('rating') is not None])
        reviews_with_responses = len([r for r in reviews if r.get('has_host_response')])
                
        individual_ratings = [r.get('rating') for r in reviews if r.get('rating') is not None]
        calculated_average = sum(individual_ratings) / len(individual_ratings) if individual_ratings else None
        
        ratings_data = {
            'overall_rating': overall_rating,
            'trip_metrics': trip_metrics,
            'reviews_header': reviews_header,
            'reviews': reviews,
            'summary': {
                'total_reviews': total_reviews,
                'reviews_with_ratings': reviews_with_ratings,
                'reviews_with_responses': reviews_with_responses,
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
            
        all_ratings_data = {
            'ratings': ratings_data if ratings_data else {
                'overall_rating': {'percentage': None, 'category': None},
                'trip_metrics': {'trips_count': None, 'ratings_count': None, 'average_rating': None},
                'reviews_header': {'title': None, 'count': None, 'category': None},
                'reviews': [],
                'summary': {'total_reviews': 0, 'reviews_with_ratings': 0, 'reviews_with_responses': 0, 'calculated_average_rating': None, 'scraped_at': datetime.utcnow().isoformat()}
            },
            'scraping_success': {
                'ratings': ratings_data is not None
            }
        }
        
        logger.info("All ratings data scraping completed!")
        return all_ratings_data
        
    except Exception as e:
        logger.exception(f"Error scraping all ratings data: {e}")
        return None
