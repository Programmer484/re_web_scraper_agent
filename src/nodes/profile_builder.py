"""Profile builder for creating search queries"""

import json
import os
from pathlib import Path
from ..models import SearchQuery


def build_query(filters: dict = None, filters_file: str = None) -> SearchQuery:
    """
    Build search query from filters dict or JSON file.
    
    Args:
        filters: Dictionary of search filters (preferred for agent workflows)
        filters_file: Path to JSON file containing search filters (fallback)
        
    Returns:
        SearchQuery object with filters applied
    """
    # Prefer direct filters dict over file
    if filters:
        return SearchQuery(**filters)
    
    # Fallback to file if provided
    if filters_file:
        filters_path = Path(filters_file)
        if filters_path.exists():
            try:
                with open(filters_path, 'r') as f:
                    filters_data = json.load(f)
                return SearchQuery(**filters_data)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                pass
        else:
            pass
    
    # Default fallback - Austin, TX area
    return SearchQuery(
        listing_type="both",
        latitude=30.2672,
        longitude=-97.7431,
        radius_miles=10.0
    )


def create_example_filters():
    """Create an example filters file to show the expected format"""
    example_filters = {
        "listing_type": "rental",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "radius_miles": 5.0,
        "min_rent_price": 1000,
        "max_rent_price": 3000,
        "min_beds": 1,
        "max_beds": 3,
        "min_baths": 1.0,
        "home_types": ["CONDO", "SINGLE_FAMILY", "TOWNHOUSE"]
    }
    
    with open("example_search_filters.json", "w") as f:
        json.dump(example_filters, f, indent=2)
    
    print("Created example_search_filters.json - rename to search_filters.json to use") 