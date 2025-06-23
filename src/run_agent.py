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
        print("Starting Zillow-Agent...")
        
        # Step 1: Build search query from filters
        if filters:
            print("Building search query from provided filters...")
        elif filters_file:
            print(f"Building search query from {filters_file}...")
        else:
            print("Building search query with default parameters...")
            
        query = profile_builder.build_query(filters, filters_file)
        print(f"Search query: {query.model_dump()}")
        
        # Step 2: Run Zillow search
        raw_results = zillow_node.run_search(query)
        
        # Step 3: Normalize results
        listings = normalizer.normalize_results(raw_results)
        
        # Step 4: Output results
        output_results(listings)
        return listings
        
    except Exception as e:
        print(f"Error in Zillow-Agent: {e}")
        raise


def search_properties(
    listing_type: str = "both",
    latitude: float = None,
    longitude: float = None,
    radius_miles: float = 10.0,
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
    Convenient function for direct agent usage - search properties with filters
    
    Args:
        listing_type: "sale", "rental", or "both"
        latitude: Center latitude for search
        longitude: Center longitude for search
        radius_miles: Search radius in miles
        min_sale_price: Minimum sale price
        max_sale_price: Maximum sale price
        min_rent_price: Minimum monthly rent
        max_rent_price: Maximum monthly rent
        min_beds: Minimum bedrooms
        max_beds: Maximum bedrooms
        min_baths: Minimum bathrooms
        max_baths: Maximum bathrooms
        home_types: List of property types (e.g., ["CONDO", "SINGLE_FAMILY"])
        
    Returns:
        List of Listing objects
    """
    # Build filters dict from parameters
    filters = {
        "listing_type": listing_type,
        "radius_miles": radius_miles
    }
    
    # Add coordinates if provided
    if latitude is not None:
        filters["latitude"] = latitude
    if longitude is not None:
        filters["longitude"] = longitude
    
    # Add price filters
    if min_sale_price is not None:
        filters["min_sale_price"] = min_sale_price
    if max_sale_price is not None:
        filters["max_sale_price"] = max_sale_price
    if min_rent_price is not None:
        filters["min_rent_price"] = min_rent_price
    if max_rent_price is not None:
        filters["max_rent_price"] = max_rent_price
    
    # Add property detail filters
    if min_beds is not None:
        filters["min_beds"] = min_beds
    if max_beds is not None:
        filters["max_beds"] = max_beds
    if min_baths is not None:
        filters["min_baths"] = min_baths
    if max_baths is not None:
        filters["max_baths"] = max_baths
    
    # Add home types
    if home_types is not None:
        filters["home_types"] = home_types
    
    # Run the search
    return main(filters=filters)


def output_results(listings: List[Listing]):
    """
    Output the normalized listings as JSON.
    For MVP, prints to stdout. Later versions may save to file or database.
    """
    # Check if we have any actual results
    if not listings:
        print("\n" + "="*50)
        print("NO PROPERTIES FOUND")
        print("="*50)
        print("🚫 The search returned 0 properties.")
        print("")
        return
    
    # Convert Pydantic models to dict for JSON serialization
    listings_data = []
    sale_count = 0
    rental_count = 0
    
    for listing in listings:
        listing_dict = listing.model_dump()
        # Convert datetime to ISO string for JSON serialization
        if listing_dict.get("timestamp"):
            listing_dict["timestamp"] = listing_dict["timestamp"].isoformat()
        # Convert HttpUrl to string
        if listing_dict.get("source_url"):
            listing_dict["source_url"] = str(listing_dict["source_url"])
        listings_data.append(listing_dict)
        
        # Count listing types
        if listing.listing_type == "sale":
            sale_count += 1
        elif listing.listing_type == "rental":
            rental_count += 1
    
    # Show summary and first listing only for debug
    print("\n" + "="*50)
    print("NORMALIZED PROPERTY LISTINGS:")
    print("="*50)
    print(f"📊 Summary: {len(listings)} total listings")
    print(f"🏠 For Sale: {sale_count} listings")
    print(f"🏢 For Rent: {rental_count} listings")
    print("="*50)
    
    # Only show first listing for debug purposes
    if listings_data:
        print("🔍 First normalized result:")
        print(json.dumps([listings_data[0]], indent=2, default=str))
        if len(listings_data) > 1:
            print(f"... and {len(listings_data) - 1} more properties (saved to results.json)")
    else:
        print("No listings to display")
    
    # Only save to file if we have actual results
    with open("results.json", "w") as f:
        json.dump(listings_data, f, indent=2, default=str)
    print(f"\n✅ Results saved to results.json")


if __name__ == "__main__":
    import sys
    
    # Allow specifying filters file as command line argument
    filters_file = sys.argv[1] if len(sys.argv) > 1 else "search_filters.json"
    
    # Create example filters if none exist
    if not Path(filters_file).exists() and filters_file == "search_filters.json":
        print("No search filters found. Creating example...")
        profile_builder.create_example_filters()
        print("Rename example_search_filters.json to search_filters.json and modify as needed.")
        print("Running with default filters for now...")
    
    main(filters_file) 