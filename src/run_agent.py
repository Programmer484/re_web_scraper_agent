#!/usr/bin/env python3
"""
Standalone runner for Zillow-Agent
This script can be run directly from the project root to execute the agent.
"""

import json
from pathlib import Path
from typing import List
from src.nodes import profile_builder, zillow_node, normalizer
from src.models import Listing


def main(filters: dict = None, filters_file: str = None):
    """
    Main orchestration function that wires together the Zillow workflow:
    1. Build query from filters dict or JSON file
    2. Run search via zillow_node
    3. Normalize results via normalizer
    4. Output results as JSON
    
    Args:
        filters: Dictionary of search filters (preferred for agent workflows)
        filters_file: Path to JSON file containing search filters (fallback)
    """
    try:
        # Step 1: Build search query from filters
        if filters:
            pass
        elif filters_file:
            pass
        else:
            pass
        query = profile_builder.build_query(filters, filters_file)
        # Step 2: Run Zillow search
        raw_results = zillow_node.run_search(query)
        # Step 3: Normalize results
        listings = normalizer.normalize_results(raw_results)
        # Step 4: Output results
        output_results(listings)
        return listings
    except Exception as e:
        raise


def search_properties(
    listing_type: str = None,
    latitude: float = None,
    longitude: float = None,
    radius_miles: float = None,
    min_sale_price: int = None,
    max_sale_price: int = None,
    min_rent_price: int = None,
    max_rent_price: int = None,
    min_beds: int = None,
    max_beds: int = None,
    min_baths: float = None,
    max_baths: float = None,
    home_types: List[str] = None
) -> List[Listing]:
    """
    Search properties with filters (all parameters optional)
    """
    params = locals()
    filters = {k: v for k, v in params.items() if v is not None}
    return main(filters=filters)


def output_results(listings: List[Listing]):
    """
    Output the normalized listings as JSON.
    For MVP, prints to stdout. Later versions may save to file or database.
    """
    if not listings:
        return
    listings_data = []
    sale_count = 0
    rental_count = 0
    for listing in listings:
        listing_dict = listing.model_dump()
        if listing_dict.get("timestamp"):
            listing_dict["timestamp"] = listing_dict["timestamp"].isoformat()
        if listing_dict.get("source_url"):
            listing_dict["source_url"] = str(listing_dict["source_url"])
        listings_data.append(listing_dict)
        if listing.listing_type == "sale":
            sale_count += 1
        elif listing.listing_type == "rental":
            rental_count += 1
    with open("results.json", "w") as f:
        json.dump(listings_data, f, indent=2, default=str)


if __name__ == "__main__":
    import sys
    filters_file = sys.argv[1] if len(sys.argv) > 1 else "search_filters.json"
    if not Path(filters_file).exists() and filters_file == "search_filters.json":
        profile_builder.create_example_filters()
    main(filters_file) 