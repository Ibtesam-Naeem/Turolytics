# ------------------------------ IMPORTS ------------------------------
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from core.utils.logger import logger

# Data storage directory
DATA_DIR = Path("backend/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------ FILE STORAGE FUNCTIONS ------------------------------

def save_scraped_data_to_json(account_id: int, scraped_data: Dict[str, Any], task_id: str = None) -> Optional[str]:
    """Save scraped data to a JSON file.
    
    Args:
        account_id: Account ID to organize data files
        scraped_data: Dictionary containing scraped data
        task_id: Optional task ID for filename
        
    Returns:
        Path to saved JSON file or None if failed
    """
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if task_id:
            filename = f"scraped_data_{account_id}_{task_id}_{timestamp}.json"
        else:
            filename = f"scraped_data_{account_id}_{timestamp}.json"
        
        file_path = DATA_DIR / filename
        
        # Prepare data with metadata
        output_data = {
            "account_id": account_id,
            "scraped_at": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "data": scraped_data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Scraped data saved to {file_path}")
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Failed to save scraped data to JSON: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------

