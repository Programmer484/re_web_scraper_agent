#!/usr/bin/env python3
"""Test script for the property search function"""

from src.models import SearchFilters
from src.run_agent import main

def test_search():
    # Test with 0.1 mile radius around downtown San Francisco
    filters = SearchFilters(
        listing_type='both',
        latitude=37.7749,
        longitude=-122.4194,
        radius_miles=0.2,
        min_beds=1,
        max_sale_price=1000000
    )

    print(f'Testing property search with {filters.radius_miles} mile radius...')
    print(f'Location: {filters.latitude}, {filters.longitude}')
    print(f'Radius: {filters.radius_miles} miles')
    print('---')

    try:
        main(filters)
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search() 