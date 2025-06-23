"""PropertySearch-Agent package

This package provides a clean interface for property search functionality
that can be easily integrated into web applications.
"""

from typing import List, Dict, Any, Optional
from .models import Listing, SearchQuery
from .nodes import profile_builder, zillow_node, normalizer


def search_properties(filters: Dict[str, Any]) -> List[Listing]:
    """
    Pure Python function for property search that can be called from external systems.
    
    Args:
        filters: Dictionary containing search parameters:
            - city (str): City/location to search
            - state (str, optional): State abbreviation
            - price_cap (int, optional): Maximum price
            - beds (int, optional): Minimum number of bedrooms
            - baths (float, optional): Minimum number of bathrooms
    
    Returns:
        List of Listing objects containing normalized property data
        
    Example:
        >>> filters = {
        ...     "city": "Chicago Loop",
        ...     "state": "IL",
        ...     "price_cap": 1000000,
        ...     "beds": 2,
        ...     "baths": 2.0
        ... }
        >>> listings = search_properties(filters)
    """
    # Convert filters dict to SearchQuery object
    query = SearchQuery(
        city=filters["city"],
        state=filters.get("state"),
        price_cap=filters.get("price_cap"),
        beds=filters.get("beds"),
        baths=filters.get("baths")
    )
    
    # Run the search workflow
    raw_results = zillow_node.run_search(query)
    listings = normalizer.normalize_results(raw_results)
    
    return listings


# For backward compatibility and direct imports
__all__ = ["search_properties", "Listing", "SearchQuery"] 