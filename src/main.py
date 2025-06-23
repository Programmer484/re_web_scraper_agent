"""Entry point for Agent"""

import json
from typing import List
from .nodes import profile_builder, zillow_node, normalizer
from .models import Listing


def main():
    """
    Main orchestration function that wires together the workflow:
    1. Build query from profile_builder
    2. Run search via zillow_node
    3. Normalize results via normalizer
    4. Output results as JSON
    """
    try:
        print("Starting Agent...")
        
        # Step 1: Build search query
        print("Building search query...")
        query = profile_builder.build_query()
        print(f"Search query: {query}")
        
        # Step 2: Run Zillow search
        print("Running Zillow search...")
        raw_results = zillow_node.run_search(query)
        
        # Step 3: Normalize results
        print("Normalizing results...")
        listings = normalizer.normalize_results(raw_results)
        
        # Step 4: Output results
        print("Outputting results...")
        output_results(listings)
        
        print(f"Agent completed successfully! Found {len(listings)} properties.")
        
    except Exception as e:
        print(f"Error in Agent: {e}")
        raise


def output_results(listings: List[Listing]):
    """
    Output the normalized listings as JSON.
    For MVP, prints to stdout. Later versions may save to file or database.
    """
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
    
    # Pretty print JSON to stdout
    print("\n" + "="*50)
    print("NORMALIZED PROPERTY LISTINGS:")
    print("="*50)
    print(f"📊 Summary: {len(listings)} total listings")
    print(f"🏠 For Sale: {sale_count} listings")
    print(f"🏢 For Rent: {rental_count} listings")
    print("="*50)
    print(json.dumps(listings_data, indent=2, default=str))
    
    # Optional: save to file
    with open("results.json", "w") as f:
        json.dump(listings_data, f, indent=2, default=str)
    print(f"\nResults also saved to results.json")
    
    # Show example of the new structure
    if listings:
        print("\n" + "="*50)
        print("EXAMPLE LISTING STRUCTURE:")
        print("="*50)
        example = listings[0]
        print(f"Listing Type: {example.listing_type}")
        if example.sale_price:
            print(f"Sale Price: ${example.sale_price:,}")
        if example.rental_price:
            print(f"Monthly Rent: ${example.rental_price:,}")
        if example.zestimate:
            print(f"Estimated Value (Zestimate): ${example.zestimate:,}")
        if example.rent_zestimate:
            print(f"Estimated Rent: ${example.rent_zestimate:,}")
        print(f"Address: {example.address}")
        print(f"Beds/Baths: {example.beds}bd/{example.baths}ba")


if __name__ == "__main__":
    main() 