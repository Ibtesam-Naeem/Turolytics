# ------------------------------ IMPORTS ------------------------------
import asyncio
import re
from datetime import datetime
from typing import Optional, Any, List, Dict
from playwright.async_api import Page
import logging

from core.config.settings import TIMEOUT_SELECTOR_WAIT, DELAY_SHORT, DELAY_MEDIUM, DELAY_LONG

logger = logging.getLogger(__name__)
from .helpers import (
    navigate_to_page, 
    get_text, 
    scraping_function
)
from core.utils.route_helpers import parse_amount
from .selectors import (
    BUSINESS_EARNINGS_URL,
    TRANSACTIONS_URL,
    TRANSACTIONS_TABLE_CONTAINER,
    TRANSACTIONS_TABLE_SCROLLABLE,
    TRANSACTIONS_TABLE_ROW,
    TRANSACTION_TYPE_CELL,
    TRANSACTION_RESERVATION_CELL,
    TRANSACTION_DATE_CELL,
    TRANSACTION_EARNINGS_CELL,
    TRANSACTION_PAYMENT_CELL,
    TRANSACTION_TRIP_LINK,
    TRANSACTION_TRIP_VEHICLE,
    TRANSACTION_PAYMENT_TYPE,
    TRANSACTION_PAYMENT_DETAILS,
    TRANSACTION_EARNINGS_AMOUNT,
    TRANSACTION_PAYMENT_AMOUNT,
    TRANSACTIONS_YEAR_SELECT,
    TRANSACTIONS_YEAR_SELECT_OPTION,
    TRANSACTION_HISTORY_LINK,
    TRANSACTION_HISTORY_LINK_TEXT
)

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def scroll_to_load_all_rows(page: Page, scrollable_container: str, row_selector: str) -> int:
    """Scroll the transaction table to load all rows (handles virtual scrolling).
    
    Args:
        page: Playwright page object
        scrollable_container: Selector for the scrollable container
        row_selector: Selector for table rows
    
    Returns:
        Total number of rows loaded
    """
    try:
        container = await page.query_selector(scrollable_container)
        if not container:
            logger.warning("Could not find scrollable container")
            return 0
        
        previous_count = 0
        current_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 100  # Increased significantly for virtual scrolling
        no_change_count = 0  # Track consecutive attempts with no change
        max_no_change = 10  # Increased significantly - virtual scrolling needs more patience
        
        # Get initial scroll height
        initial_scroll_height = await container.evaluate("element => element.scrollHeight")
        logger.debug(f"Initial scroll height: {initial_scroll_height}px")
        
        while scroll_attempts < max_scroll_attempts:
            # Count current DOM rows (virtual scrolling renders all rows in DOM)
            rows = await page.query_selector_all(row_selector)
            current_count = len(rows)
            
            # If count hasn't changed, increment no_change_count
            if current_count == previous_count and scroll_attempts > 0:
                no_change_count += 1
                if no_change_count >= max_no_change:
                    logger.info(f"All rows loaded (no change for {max_no_change} attempts). Total rows: {current_count}")
                    break
            else:
                no_change_count = 0  # Reset if count changed
            
            # Scroll incrementally for virtual scrolling
            try:
                scroll_height = await container.evaluate("element => element.scrollHeight")
                scroll_top = await container.evaluate("element => element.scrollTop")
                client_height = await container.evaluate("element => element.clientHeight")
                
                # Calculate how far we are from bottom
                distance_from_bottom = scroll_height - (scroll_top + client_height)
                
                # Scroll down by a large increment (virtual scrolling needs bigger jumps)
                scroll_increment = client_height * 0.8  # Scroll 80% of viewport height
                new_scroll_top = min(scroll_top + scroll_increment, scroll_height)
                
                await container.evaluate(f"element => element.scrollTop = {new_scroll_top}")
                
                # Wait for virtual scrolling to render new rows
                await page.wait_for_timeout(DELAY_LONG)  # Longer wait for virtual scrolling
                
                # Check if we've reached the bottom
                new_scroll_top_after = await container.evaluate("element => element.scrollTop")
                new_scroll_height = await container.evaluate("element => element.scrollHeight")
                
                # If we're at the bottom and height hasn't changed, we're done
                if new_scroll_top_after + client_height >= new_scroll_height - 10:
                    if no_change_count >= 3:  # Need multiple confirmations for virtual scrolling
                        logger.info(f"Reached bottom of scrollable container. Total rows: {current_count}")
                        break
                
            except Exception as e:
                logger.debug(f"Error during scroll: {e}")
                # Don't break on error, continue trying
                pass
            
            previous_count = current_count
            scroll_attempts += 1
            
            if scroll_attempts % 10 == 0:
                logger.debug(f"Scrolled {scroll_attempts} times, found {current_count} rows so far")
        
        # Final count after all scrolling - query all rows in DOM
        final_rows = await page.query_selector_all(row_selector)
        logger.info(f"Finished scrolling after {scroll_attempts} attempts. Total rows loaded: {len(final_rows)}")
        
        # If we got more rows than before, log it
        if len(final_rows) > current_count:
            logger.info(f"Found additional rows after final count: {len(final_rows)} vs {current_count}")
        
        return len(final_rows)
    
    except Exception as e:
        logger.error(f"Error scrolling to load rows: {e}")
        # Return count of rows we managed to load
        rows = await page.query_selector_all(row_selector)
        return len(rows)

async def extract_transaction_type(row) -> Dict[str, Optional[str]]:
    """Extract transaction type information from a row.
    
    Returns:
        Dictionary with 'type', 'trip_name', 'vehicle_name', 'payment_details'
    """
    try:
        type_cell = await row.query_selector(TRANSACTION_TYPE_CELL)
        if not type_cell:
            return {'type': None, 'trip_name': None, 'vehicle_name': None, 'payment_details': None}
        
        # Check if it's a trip (has a link) or payment
        trip_link = await type_cell.query_selector(TRANSACTION_TRIP_LINK)
        payment_type = await type_cell.query_selector(TRANSACTION_PAYMENT_TYPE)
        
        if trip_link:
            # It's a trip transaction
            trip_name = (await trip_link.text_content() or '').strip()
            
            vehicle_text = await get_text(type_cell, TRANSACTION_TRIP_VEHICLE)
            vehicle_name = vehicle_text.replace('With ', '').strip() if vehicle_text else None
            
            return {
                'type': 'trip',
                'trip_name': trip_name,
                'vehicle_name': vehicle_name,
                'payment_details': None
            }
        elif payment_type:
            # It's a payment transaction
            payment_type_text = (await payment_type.text_content() or '').strip()
            
            payment_details_text = await get_text(type_cell, TRANSACTION_PAYMENT_DETAILS)
            
            return {
                'type': 'payment',
                'trip_name': None,
                'vehicle_name': None,
                'payment_details': payment_details_text
            }
        else:
            # Fallback: try to get any text
            cell_text = (await type_cell.text_content() or '').strip()
            return {
                'type': 'unknown',
                'trip_name': None,
                'vehicle_name': None,
                'payment_details': cell_text
            }
    except Exception as e:
        logger.debug(f"Error extracting transaction type: {e}")
        return {'type': None, 'trip_name': None, 'vehicle_name': None, 'payment_details': None}

async def extract_transaction_row(row, row_index: int) -> Optional[Dict[str, Any]]:
    """Extract transaction data from a single row."""
    try:
        # Verify row is still attached to DOM
        try:
            await row.evaluate("element => element.offsetHeight")
        except Exception as e:
            logger.warning(f"Row {row_index} is detached from DOM: {e}")
            return None
        
        # Extract type information
        type_info = await extract_transaction_type(row)
        
        if not type_info.get('type'):
            logger.debug(f"Row {row_index}: Could not determine transaction type")
            # Don't return None yet - try to extract other fields
        
        # Extract reservation ID
        reservation_cell = await row.query_selector(TRANSACTION_RESERVATION_CELL)
        reservation_id = None
        if reservation_cell:
            reservation_text = await get_text(reservation_cell, 'p')
            reservation_id = reservation_text.strip() if reservation_text else None
        
        # Extract date
        date_cell = await row.query_selector(TRANSACTION_DATE_CELL)
        date_text = None
        if date_cell:
            date_text = await get_text(date_cell, 'p')
            date_text = date_text.strip() if date_text else None
        
        # If we don't have at least a date or type, this row is invalid
        if not date_text and not type_info.get('type'):
            logger.debug(f"Row {row_index}: Missing both date and type, skipping")
            return None
        
        # Extract earnings amount
        earnings_cell = await row.query_selector(TRANSACTION_EARNINGS_CELL)
        earnings_amount = None
        earnings_amount_numeric = None
        if earnings_cell:
            earnings_span = await earnings_cell.query_selector(TRANSACTION_EARNINGS_AMOUNT)
            if earnings_span:
                earnings_text = (await earnings_span.text_content() or '').strip()
                if earnings_text:
                    earnings_amount = earnings_text
                    earnings_amount_numeric = parse_amount(earnings_text)
        
        # Extract payment amount
        payment_cell = await row.query_selector(TRANSACTION_PAYMENT_CELL)
        payment_amount = None
        payment_amount_numeric = None
        if payment_cell:
            payment_span = await payment_cell.query_selector(TRANSACTION_PAYMENT_AMOUNT)
            if payment_span:
                payment_text = (await payment_span.text_content() or '').strip()
                if payment_text:
                    payment_amount = payment_text
                    payment_amount_numeric = parse_amount(payment_text)
        
        result = {
            'type': type_info.get('type') or 'unknown',
            'trip_name': type_info.get('trip_name'),
            'vehicle_name': type_info.get('vehicle_name'),
            'payment_details': type_info.get('payment_details'),
            'reservation_id': reservation_id,
            'date': date_text or 'Unknown',
            'earnings_amount': earnings_amount,
            'earnings_amount_numeric': earnings_amount_numeric,
            'payment_amount': payment_amount,
            'payment_amount_numeric': payment_amount_numeric
        }
        
        return result
    except Exception as e:
        logger.error(f"Error extracting transaction row {row_index}: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None

async def extract_transactions_for_year(page: Page, year: str) -> List[Dict[str, Any]]:
    """Extract all transactions for a specific year."""
    try:
        logger.info(f"Extracting transactions for year {year}...")
        
        # Wait for page to update after year selection
        await page.wait_for_timeout(DELAY_MEDIUM)
        
        # Check if there are no transactions for this year (before trying to scroll)
        no_transactions_selector = 'p.css-76lyvq-StyledText'
        no_transactions_elements = await page.query_selector_all(no_transactions_selector)
        for element in no_transactions_elements:
            try:
                text = await element.text_content()
                if text and "There aren't any transactions" in text and year in text:
                    logger.info(f"No transactions found for year {year} - skipping extraction (message: {text.strip()})")
                    return []
            except:
                continue
        
        # Wait for table to be visible (if transactions exist)
        try:
            await page.wait_for_selector(TRANSACTIONS_TABLE_CONTAINER, timeout=5000)
        except:
            # Table might not exist if there are no transactions
            logger.debug(f"Transactions table not found for year {year}, checking for no transactions message...")
            # Double-check for no transactions message
            no_transactions_elements = await page.query_selector_all(no_transactions_selector)
            for element in no_transactions_elements:
                try:
                    text = await element.text_content()
                    if text and "There aren't any transactions" in text:
                        logger.info(f"No transactions found for year {year} - skipping extraction")
                        return []
                except:
                    continue
            logger.warning(f"Transactions table not found and no 'no transactions' message found for year {year}")
            return []
        
        await page.wait_for_timeout(DELAY_MEDIUM)
        
        # Check if there are any rows before scrolling
        initial_rows = await page.query_selector_all(TRANSACTIONS_TABLE_ROW)
        if len(initial_rows) == 0:
            logger.info(f"No transaction rows found for year {year} (table exists but empty)")
            return []
        
        # Scroll to load all rows (only if we have rows)
        # For virtual scrolling, we need to scroll through the entire tbody height
        logger.info(f"Starting to scroll to load all rows for year {year}...")
        
        # First, get the tbody height to know how much we need to scroll
        tbody_height = None
        try:
            tbody = await page.query_selector('tbody')
            if tbody:
                # Get the actual height from style attribute or computed height
                tbody_height = await tbody.evaluate("""
                    element => {
                        const style = window.getComputedStyle(element);
                        const height = element.style.height || style.height || element.offsetHeight || element.scrollHeight;
                        return parseInt(height) || 0;
                    }
                """)
                logger.info(f"Tbody height: {tbody_height}px - this indicates how many rows should exist (~{tbody_height // 80} rows)")
        except Exception as e:
            logger.debug(f"Could not get tbody height: {e}")
        
        # Get the scrollable container
        container = await page.query_selector(TRANSACTIONS_TABLE_SCROLLABLE)
        if not container:
            logger.error("Could not find scrollable container")
            return []
        
        # Get scroll dimensions
        scroll_height = await container.evaluate("element => element.scrollHeight")
        client_height = await container.evaluate("element => element.clientHeight")
        logger.info(f"Container scroll height: {scroll_height}px, client height: {client_height}px")
        
        # VIRTUAL SCROLLING STRATEGY: Extract rows incrementally as we scroll
        # Virtual scrollers only keep ~15 rows in DOM at a time, so we must extract
        # rows at each scroll position and collect unique transactions
        logger.info("Using incremental extraction strategy for virtual scrolling...")
        
        # Store unique transactions by their unique key (date + reservation_id + type)
        seen_transactions = set()
        all_transactions = []
        
        # Calculate scroll steps - we need to scroll through the entire range
        # Each row is ~80px, so we'll scroll in increments smaller than row height
        row_height = 80
        scroll_increment = row_height // 2  # Scroll in half-row increments to ensure we don't miss any
        steps = int(scroll_height / scroll_increment) + 1
        
        logger.info(f"Scrolling through {steps} steps (increment: {scroll_increment}px) to extract all rows...")
        
        # Start from top and scroll down incrementally
        for step in range(steps + 1):
            scroll_pos = min(step * scroll_increment, scroll_height)
            await container.evaluate(f"element => element.scrollTop = {scroll_pos}")
            await page.wait_for_timeout(DELAY_SHORT)  # Short wait for virtual scrolling to render
            
            # Extract rows at this scroll position
            current_rows = await page.query_selector_all(TRANSACTIONS_TABLE_ROW)
            
            if step % 20 == 0 or step == steps:
                logger.info(f"Step {step}/{steps}: scroll_pos={scroll_pos:.0f}px, found {len(current_rows)} rows, total unique transactions: {len(seen_transactions)}")
            
            # Extract data from each row at this position
            for row in current_rows:
                try:
                    # Extract key fields to create unique identifier
                    date_cell = await row.query_selector(TRANSACTION_DATE_CELL)
                    date_text = await date_cell.text_content() if date_cell else None
                    
                    reservation_cell = await row.query_selector(TRANSACTION_RESERVATION_CELL)
                    reservation_text = await reservation_cell.text_content() if reservation_cell else None
                    reservation_id = reservation_text.strip() if reservation_text else None
                    
                    type_info = await extract_transaction_type(row)
                    transaction_type = type_info.get('type', 'unknown')
                    
                    # Create unique key for this transaction
                    if date_text:
                        unique_key = (date_text.strip(), reservation_id or '', transaction_type)
                        
                        # Only process if we haven't seen this transaction before
                        if unique_key not in seen_transactions:
                            seen_transactions.add(unique_key)
                            
                            # Extract full transaction data
                            transaction_data = await extract_transaction_row(row, len(all_transactions) + 1)
                            if transaction_data:
                                transaction_data['year'] = year
                                all_transactions.append(transaction_data)
                                
                                if len(all_transactions) % 10 == 0:
                                    logger.debug(f"Collected {len(all_transactions)} unique transactions so far...")
                except Exception as e:
                    logger.debug(f"Error extracting row at step {step}: {e}")
                    continue
        
        # Also scroll backwards to catch any rows we might have missed
        logger.info("Scrolling backwards to catch any missed rows...")
        for step in range(steps, -1, -1):
            scroll_pos = min(step * scroll_increment, scroll_height)
            await container.evaluate(f"element => element.scrollTop = {scroll_pos}")
            await page.wait_for_timeout(DELAY_SHORT)
            
            current_rows = await page.query_selector_all(TRANSACTIONS_TABLE_ROW)
            
            for row in current_rows:
                try:
                    date_cell = await row.query_selector(TRANSACTION_DATE_CELL)
                    date_text = await date_cell.text_content() if date_cell else None
                    
                    reservation_cell = await row.query_selector(TRANSACTION_RESERVATION_CELL)
                    reservation_text = await reservation_cell.text_content() if reservation_cell else None
                    reservation_id = reservation_text.strip() if reservation_text else None
                    
                    type_info = await extract_transaction_type(row)
                    transaction_type = type_info.get('type', 'unknown')
                    
                    if date_text:
                        unique_key = (date_text.strip(), reservation_id or '', transaction_type)
                        
                        if unique_key not in seen_transactions:
                            seen_transactions.add(unique_key)
                            transaction_data = await extract_transaction_row(row, len(all_transactions) + 1)
                            if transaction_data:
                                transaction_data['year'] = year
                                all_transactions.append(transaction_data)
                except Exception as e:
                    logger.debug(f"Error extracting row during backward scroll: {e}")
                    continue
        
        logger.info(f"Finished incremental extraction. Found {len(all_transactions)} unique transactions for year {year}")
        
        if len(all_transactions) == 0:
            logger.warning(f"No transactions extracted for year {year}")
            return []
        
        # Log date range
        dates_found = [t.get('date') for t in all_transactions if t.get('date')]
        if dates_found:
            logger.info(f"Date range: {min(dates_found)} to {max(dates_found)}")
            logger.info(f"Total unique dates: {len(set(dates_found))}")
        
        # Log first few transactions
        logger.info(f"Sample of extracted transactions (first 10):")
        for i, txn in enumerate(all_transactions[:10], 1):
            logger.info(f"  {i}. {txn.get('type', 'N/A')} | {txn.get('date', 'N/A')} | {txn.get('reservation_id', 'N/A')}")
        
        # Log all extracted transactions
        logger.info(f"All extracted transactions for {year}:")
        for i, txn in enumerate(all_transactions, 1):
            logger.info(f"  {i}. {txn.get('type')} | {txn.get('trip_name') or txn.get('payment_details')} | {txn.get('date')} | {txn.get('reservation_id') or 'N/A'} | Earnings: {txn.get('earnings_amount')} | Payment: {txn.get('payment_amount')}")
        
        return all_transactions
    
    except Exception as e:
        logger.error(f"Error extracting transactions for year {year}: {e}")
        return []

async def get_available_years(page: Page) -> List[str]:
    """Get list of available years from the transactions page select element."""
    try:
        # Wait for select element to be visible
        logger.debug("Waiting for year select element to be visible...")
        select_element = await page.wait_for_selector(
            TRANSACTIONS_YEAR_SELECT,
            timeout=TIMEOUT_SELECTOR_WAIT
        )
        if not select_element:
            logger.warning("Could not find year select element")
            return []
        
        # Ensure select is in view
        await select_element.scroll_into_view_if_needed()
        await page.wait_for_timeout(DELAY_SHORT)
        
        # Get all option elements
        option_elements = await page.query_selector_all(TRANSACTIONS_YEAR_SELECT_OPTION)
        available_years = []
        
        for option in option_elements:
            try:
                value = await option.get_attribute('value')
                if value and value.isdigit() and len(value) == 4:
                    available_years.append(value)
            except Exception as e:
                logger.debug(f"Error extracting year from option: {e}")
                continue
        
        logger.info(f"Found available years: {available_years}")
        return sorted(available_years, reverse=True)  # Most recent first
    
    except Exception as e:
        logger.error(f"Error getting available years: {e}")
        return []

async def select_transactions_year(page: Page, year: str) -> bool:
    """Select a year from the transactions page select element.
    
    Args:
        page: Playwright page object
        year: Year to select (e.g., "2025", "2026")
    
    Returns:
        True if year was successfully selected, False otherwise
    """
    try:
        logger.info(f"Selecting year {year} from transactions select...")
        
        # Wait for select element to be visible
        select_element = await page.wait_for_selector(
            TRANSACTIONS_YEAR_SELECT,
            timeout=TIMEOUT_SELECTOR_WAIT
        )
        if not select_element:
            logger.error(f"Could not find year select element")
            return False
        
        # Ensure select is in view
        await select_element.scroll_into_view_if_needed()
        await page.wait_for_timeout(DELAY_SHORT)
        
        # Verify select is visible
        is_visible = await select_element.is_visible()
        if not is_visible:
            logger.error("Select element is not visible")
            return False
        
        # Use Playwright's select_option method (proper way to handle <select> elements)
        logger.debug(f"Selecting option with value '{year}'...")
        await select_element.select_option(value=year)
        
        # Wait for page to update after selection
        await page.wait_for_timeout(DELAY_LONG)
        
        # Verify the selection was successful by checking the selected value
        selected_value = await select_element.evaluate("element => element.value")
        if selected_value == year:
            logger.info(f"Successfully selected year {year}")
            return True
        else:
            logger.warning(f"Selected value ({selected_value}) does not match requested year ({year})")
            return False
        
    except Exception as e:
        logger.error(f"Error selecting year {year}: {e}")
        return False

# ------------------------------ TRANSACTIONS SCRAPING ------------------------------

@scraping_function("transactions")
async def scrape_transactions_data(page: Page, is_initial_scrape: bool = False) -> Optional[Dict[str, Any]]:
    """Scrape transaction history data from the earnings page.
    
    Args:
        page: Playwright page object
        is_initial_scrape: If True, scrape all available years. 
                          If False, scrape current year and previous year.
    
    Returns:
        Dictionary with transactions data aggregated across all scraped years
    """
    try:
        # First navigate to earnings page (same as earnings scraper)
        if not await navigate_to_page(page, BUSINESS_EARNINGS_URL, "Business Earnings"):
            logger.error("Failed to navigate to earnings page")
            return None
        
        # Wait for page to load
        await page.wait_for_timeout(DELAY_MEDIUM)
        
        # Click on "Transaction history" link
        logger.info("Looking for Transaction history link...")
        transaction_link = None
        
        # Try multiple strategies to find the link
        try:
            # Strategy 1: Find by list item selector (most reliable)
            transaction_link = await page.wait_for_selector(
                TRANSACTION_HISTORY_LINK,
                timeout=TIMEOUT_SELECTOR_WAIT
            )
            logger.debug("Found Transaction history link using list item selector")
        except Exception:
            logger.debug("List item selector failed, trying alternative methods...")
            # Strategy 2: Find by searching all links with the href and matching text
            all_links = await page.query_selector_all('a[href="/us/en/earnings"]')
            for link in all_links:
                text = await link.text_content()
                if text and "Transaction history" in text.strip():
                    transaction_link = link
                    logger.debug("Found Transaction history link by searching all links")
                    break
        
        if not transaction_link:
            logger.error("Could not find Transaction history link on earnings page")
            return None
        
        # Click the link
        logger.info("Clicking Transaction history link...")
        await transaction_link.scroll_into_view_if_needed()
        await page.wait_for_timeout(DELAY_SHORT)
        await transaction_link.click(force=True)
        
        # Wait for navigation to complete and page to load
        await page.wait_for_load_state("networkidle", timeout=30000)
        await page.wait_for_timeout(DELAY_LONG)
        
        # Wait for the transactions table to be visible (indicates page is loaded)
        try:
            await page.wait_for_selector(
                TRANSACTIONS_TABLE_CONTAINER,
                timeout=TIMEOUT_SELECTOR_WAIT
            )
            logger.debug("Transactions table is visible, page loaded")
        except Exception as e:
            logger.warning(f"Transactions table not found, but continuing: {e}")
        
        # Verify we're on the transactions page
        current_url = page.url
        logger.debug(f"Current URL after clicking link: {current_url}")
        if "earnings" not in current_url:
            logger.warning(f"URL doesn't contain 'earnings' - may have been redirected. Current URL: {current_url}")
        
        # Get available years (now the page should be fully loaded)
        available_years = await get_available_years(page)
        if not available_years:
            logger.warning("No years found in dropdown, using default years")
            current_year = datetime.now().year
            available_years = [str(current_year), str(current_year - 1)]
        
        # Determine which years to scrape
        if is_initial_scrape:
            years_to_scrape = available_years
            logger.info(f"Initial scrape detected - will scrape all years: {years_to_scrape}")
        else:
            # For regular scrape, scrape current year and previous year
            current_year = datetime.now().year
            years_to_scrape = [str(current_year), str(current_year - 1)]
            # Only include years that are available
            years_to_scrape = [y for y in years_to_scrape if y in available_years]
            logger.info(f"Regular scrape - will scrape years: {years_to_scrape}")
        
        # Aggregate data across all years
        all_transactions = []
        
        for year in years_to_scrape:
            try:
                logger.info(f"Scraping transactions for year {year}...")
                
                # Select year from dropdown (transactions page uses different selector)
                if not await select_transactions_year(page, year):
                    logger.warning(f"Failed to select year {year}, skipping...")
                    continue
                
                # Wait for table to update
                await page.wait_for_timeout(DELAY_MEDIUM)
                
                # Check if there are no transactions for this year
                no_transactions_message = await page.query_selector('p.css-76lyvq-StyledText:has-text("There aren\'t any transactions")')
                if no_transactions_message:
                    message_text = await no_transactions_message.text_content()
                    if "There aren't any transactions" in message_text:
                        logger.info(f"No transactions found for year {year} - skipping (message: {message_text.strip()})")
                        continue
                
                # Extract transactions for this year
                year_transactions = await extract_transactions_for_year(page, year)
                
                if year_transactions:
                    all_transactions.extend(year_transactions)
                    logger.info(f"Successfully scraped {len(year_transactions)} transactions for year {year}")
                else:
                    logger.warning(f"No transactions found for year {year}")
                
            except Exception as e:
                logger.error(f"Error scraping transactions for year {year}: {e}")
                continue
        
        # If no data was scraped, return None
        if not all_transactions:
            logger.warning("No transaction data was scraped from any year")
            return None
        
        return {
            'transactions': all_transactions,
            'total_transactions': len(all_transactions),
            'years_scraped': years_to_scrape,
            'scraped_at': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error scraping transactions: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------
