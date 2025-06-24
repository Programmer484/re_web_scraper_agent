#!/usr/bin/env python3
"""
Standalone runner for Zillow-Agent
This script can be run directly from the project root to execute the agent.
"""

from typing import List
from src.nodes import zillow_node, normalizer
from src.models import Listing, SearchFilters


def main(filters: SearchFilters):
    """
    Main orchestration function that wires together the Zillow workflow:
    1. Run search via zillow_node
    2. Normalize results via normalizer
    3. Return results as JSON
    
    Args:
        filters: SearchFilters object containing search criteria
    """
    try:
        # Step 1: Run Zillow search
        raw_results = zillow_node.run_search(filters)
        # Step 2: Normalize results
        listings = normalizer.normalize_results(raw_results)
        print(f"Found {len(listings)} listings")
        if listings:
            first = listings[0]
            print(f'First result: {first.address} - ${first.price}')
            print(f'Type: {first.listing_type}')
            print(f'Beds: {first.beds}, Baths: {first.baths}')
        return listings
    except Exception as e:
        raise


if __name__ == "__main__":
    # For CLI usage, create a basic SearchFilters object
    # In practice, this would be called from API with proper SearchFilters
    filters = SearchFilters(
        latitude=40.7128,
        longitude=-74.0060,
        radius_miles=5.0
    )
    main(filters)