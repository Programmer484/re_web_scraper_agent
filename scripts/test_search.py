#!/usr/bin/env python3
"""Test script for the property search function"""

from src.models import SearchFilters, Listing
from src.run_agent import main
from typing import List
import json


def test_search():
    filters = SearchFilters(
        listing_type='both',
        latitude=37.772266,
        longitude=-122.42329,
        radius_miles=0.01,
    )

    print(f'Testing property search with {filters.radius_miles} mile radius...')
    print(f'Location: {filters.latitude}, {filters.longitude}')
    print(f'Radius: {filters.radius_miles} miles')
    print('---')

    try:
        listings = main(filters)
        output_results_to_json(listings)
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()


def output_results_to_json(listings: List[Listing]):
    """
    Output the normalized listings to a JSON file for testing and debugging.
    """
    if not listings:
        print("No listings to save")
        return
    
    # Convert listings to serializable format
    listings_data = []
    for listing in listings:
        listing_dict = listing.model_dump()
        # Handle datetime serialization
        if listing_dict.get("timestamp"):
            listing_dict["timestamp"] = listing_dict["timestamp"].isoformat()
        # Handle URL serialization
        if listing_dict.get("source_url"):
            listing_dict["source_url"] = str(listing_dict["source_url"])
        listings_data.append(listing_dict)
    
    # Save to JSON file
    output_file = "test_search_results.json"
    with open(output_file, 'w') as f:
        json.dump(listings_data, f, indent=2)
    
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    test_search() 