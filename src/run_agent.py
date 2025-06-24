#!/usr/bin/env python3
"""
Standalone runner for Zillow-Agent
This script can be run directly from the project root to execute the agent.
"""

import json
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
        """
        This is the full workflow.
        """
        # raw_results = zillow_node.run_search(filters)
        # listings = normalizer.normalize_results(raw_results)

        """
        This is the test data for the normalizer.
        """
        # Load test data from results_rentcast.json
        with open('data/results_rentcast.json', 'r') as f:
            rentcast_data = json.load(f)
        
        # Convert rentcast data directly to Listing objects
        listings = []
        for i, item in enumerate(rentcast_data):
            listing_data = {
                'zpid': str(i),
                'building': False,
                'listing_type': item.get('listing_type'),
                'sale_price': item.get('sale_price'),
                'rental_price': item.get('rental_price'),
                'zestimate': item.get('estimated_value'),
                'rent_zestimate': item.get('estimated_rent'),
                'address': item.get('address'),
                'beds': item.get('beds'),
                'baths': item.get('baths'),
            }
            listing = Listing(**listing_data)
            listings.append(listing)
        
        print(f"Found {len(listings)} listings")
        if listings:
            first = listings[0]
            print(f'First result: {first.address} - ${first.price}')
            print(f'Type: {first.listing_type}, Building: {first.building}')
            print(f'Beds: {first.beds}, Baths: {first.baths}')
        return listings
    except Exception as e:
        raise e


if __name__ == "__main__":
    # Test search for Calgary property: 1726 11th St SW Calgary AB T2T 3L6
    # Calgary coordinates: 51.0447° N, 114.0719° W
    filters = SearchFilters(
        latitude=51.0447,
        longitude=-114.0719,
        radius_miles=0.1,
        listing_type="both"  # Search both sale and rental
    )
    main(filters)