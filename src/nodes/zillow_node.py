"""Zillow node for scraping property data using Apify actor"""

import json
import urllib.parse
import sys
import os
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from typing import List, Dict, Any
from apify_client import ApifyClient
from ..config import APIFY_TOKEN, ZILLOW_ACTOR_ID, MAX_RESULTS
from ..models import SearchQuery


def build_zillow_url(query: SearchQuery) -> str:
    """
    Build Zillow search URL from SearchQuery parameters
    
    Args:
        query: SearchQuery containing search criteria
        
    Returns:
        Zillow search URL with encoded filters
    """
    # Calculate map bounds based on coordinates and radius
    if query.latitude and query.longitude:
        # Convert radius from miles to approximate degrees
        # 1 degree lat ≈ 69 miles, 1 degree lng varies by latitude
        lat_offset = (query.radius_miles or 5.0) / 69.0
        lng_offset = (query.radius_miles or 5.0) / (69.0 * abs(query.latitude) * 0.01745329)  # cos(lat in radians)
        
        map_bounds = {
            "west": query.longitude - lng_offset,
            "east": query.longitude + lng_offset, 
            "south": query.latitude - lat_offset,
            "north": query.latitude + lat_offset
        }
        
        # Use generic URL for coordinate-based search
        base_url = "https://www.zillow.com/homes/"
    
    # Build filter state
    filter_state = {
        "sort": {"value": "days"}  # Sort by newest
    }
    
    # Add price filters
    if query.listing_type == "sale" or query.listing_type == "both":
        price_filter = {}
        if query.min_sale_price:
            price_filter["min"] = query.min_sale_price
        if query.max_sale_price:
            price_filter["max"] = query.max_sale_price
        if price_filter:
            filter_state["price"] = price_filter
    
    if query.listing_type == "rental" or query.listing_type == "both":
        rent_filter = {}
        if query.min_rent_price:
            rent_filter["min"] = query.min_rent_price
        if query.max_rent_price:
            rent_filter["max"] = query.max_rent_price
        if rent_filter:
            filter_state["monthlyPayment"] = rent_filter
    
    # Add bedroom filters
    if query.min_beds or query.max_beds:
        beds_filter = {}
        if query.min_beds:
            beds_filter["min"] = query.min_beds
        if query.max_beds:
            beds_filter["max"] = query.max_beds
        filter_state["beds"] = beds_filter
    
    # Add bathroom filters
    if query.min_baths or query.max_baths:
        baths_filter = {}
        if query.min_baths:
            baths_filter["min"] = query.min_baths
        if query.max_baths:
            baths_filter["max"] = query.max_baths
        filter_state["baths"] = baths_filter
    
    # Add home type filters
    if query.home_types:
        filter_state["homeType"] = {ht: {"value": True} for ht in query.home_types}
    
    # Add listing type filter
    if query.listing_type == "sale":
        filter_state["isForSaleByAgent"] = {"value": True}
        filter_state["isForSaleByOwner"] = {"value": True}
    elif query.listing_type == "rental":
        filter_state["isForRent"] = {"value": True}
    
    # Build search query state
    search_query_state = {
        "isMapVisible": True,
        "mapBounds": map_bounds,
        "filterState": filter_state,
        "isListVisible": True
    }
    
    # Encode the search query state
    encoded_state = urllib.parse.quote(json.dumps(search_query_state, separators=(',', ':')))
    
    return f"{base_url}?searchQueryState={encoded_state}"


def run_search(query: SearchQuery) -> List[Dict[str, Any]]:
    """
    Run property search using Zillow scraper via Apify
    
    Args:
        query: SearchQuery containing search criteria
        
    Returns:
        List of raw property data dictionaries from Zillow
        
    Raises:
        Exception: If API call fails or returns no data
    """
    if not APIFY_TOKEN:
        raise ValueError("APIFY_TOKEN environment variable is required")
    
    # Initialize Apify client
    client = ApifyClient(APIFY_TOKEN)
    
    # Build dynamic Zillow URL from search query
    search_url = build_zillow_url(query)
    
    # Build actor input using searchUrls format
    actor_input = {
        "searchUrls": [
            {
                "url": search_url
            }
        ],
        "extractionMethod": "MAP_MARKERS",  # Fastest mode for testing
        "maxItems": MAX_RESULTS
    }
    
    # Run the actor
    try:
        # Redirect stdout and stderr to suppress APIFY output
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            # Run actor silently
            run = client.actor(ZILLOW_ACTOR_ID).call(run_input=actor_input)
            
            # Fetch results silently
            results = []
            dataset_id = run["defaultDatasetId"]
            
            for item in client.dataset(dataset_id).iterate_items():
                results.append(item)
        
        return results
        
    except Exception as e:
        print(f"❌ Error calling APIFY Zillow scraper: {e}")
        print(f"🔧 APIFY Token configured: {'Yes' if APIFY_TOKEN else 'No'}")
        raise 