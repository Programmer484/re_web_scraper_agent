"""Normalizer for harmonizing data fields"""

from typing import List, Dict, Any, Set, Tuple, Optional
from ..models import Listing
from pydantic import ValidationError
import re


def normalize_results(raw_items: List[Dict[str, Any]]) -> List[Listing]:
    """
    Converts raw property data from Zillow scraper to validated Listing objects.
    Also handles deduplication based on address and price.
    
    Args:
        raw_items: List of raw property dictionaries from Zillow scraper
        
    Returns:
        List of validated and deduplicated Listing objects
    """
    listings = []
    seen_properties: Set[str] = set()
    
    for i, item in enumerate(raw_items):
        # Skip empty or invalid items
        if not item or not isinstance(item, dict):
            continue
            
        # Check if item has any meaningful data
        has_address = bool(item.get("address"))
        has_price = bool(item.get("price") or item.get("unformattedPrice"))
        has_zpid = bool(item.get("zpid"))
        has_coordinates = bool(item.get("latLong") or (item.get("latitude") and item.get("longitude")))
        
        if not any([has_address, has_price, has_zpid, has_coordinates]):
            continue
        
        try:
            # Detect listing type and extract appropriate price
            listing_type, sale_price, rental_price = _extract_listing_type_and_prices(item)
            
            # Skip if we can't determine a valid listing type or price
            if not listing_type or (not sale_price and not rental_price):
                continue
            
            # Extract location data
            lat, lon = _extract_coordinates(item)
            
            # Extract other fields from raw Zillow data
            normalized_data = {
                # Zillow identifiers
                "zpid": str(item.get("zpid")) if item.get("zpid") else None,
                
                # Listing classification
                "listing_type": listing_type,
                "home_type": item.get("homeType"),
                "home_status": item.get("homeStatus", item.get("statusType")),
                
                # Pricing information
                "sale_price": sale_price,
                "rental_price": rental_price,
                "zestimate": _extract_number(item.get("zestimate")),
                "rent_zestimate": _extract_number(item.get("rentZestimate")),
                
                # Property details
                "address": _extract_address(item.get("address")),
                "beds": _extract_number(item.get("beds", item.get("bedrooms"))),
                "baths": _extract_number(item.get("baths", item.get("bathrooms")), float_allowed=True),
                "living_area": _extract_number(item.get("area", item.get("livingArea"))),
                "lot_size": item.get("lotSize"),
                "year_built": _extract_number(item.get("yearBuilt")),
                
                # Location data
                "latitude": lat,
                "longitude": lon,
                
                # Listing metadata
                "source_url": _extract_url(item.get("detailUrl", item.get("url"))),
                "broker_name": item.get("brokerName"),
                "days_on_zillow": _extract_number(item.get("daysOnZillow")),
            }
            
            # Create deduplication key using the appropriate price
            price_for_dedup = sale_price if sale_price is not None else rental_price
            dedup_key = f"{normalized_data['address']}_{price_for_dedup}_{listing_type}"
            
            # Skip duplicates
            if dedup_key in seen_properties:
                continue
                
            # Validate and create Listing object
            listing = Listing(**normalized_data)
            listings.append(listing)
            seen_properties.add(dedup_key)
            
        except ValidationError as e:
            continue
        except Exception as e:
            continue
    
    if len(listings) == 0:
        print("⚠️  No valid listings found. This could mean:")
        print("   1. APIFY returned empty/invalid data")
        print("   2. Search criteria too restrictive")
        print("   3. Zillow URL not generating results")
        print("   4. APIFY actor configuration issue")
    
    return listings


def _extract_listing_type_and_prices(item: Dict[str, Any]) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Determine listing type and extract appropriate prices for Zillow data
    
    Returns:
        Tuple of (listing_type, sale_price, rental_price)
    """
    # Extract price data from Zillow fields
    price = _extract_price(item.get("price", item.get("unformattedPrice")))
    
    # Determine listing type based on Zillow data structure
    url = item.get("detailUrl", item.get("url", ""))
    home_status = item.get("homeStatus", item.get("statusType", "")).upper()
    
    # Check if this is a rental listing
    is_rental_listing = (
        "/rental/" in url or 
        "/rent/" in url or
        "RENT" in home_status or
        item.get("isRental") or
        item.get("rentalCategory") is not None
    )
    
    if is_rental_listing:
        return "rental", None, price
    else:
        return "sale", price, None


def _extract_coordinates(item: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """Extract latitude and longitude from various possible fields"""
    # Try latLong object first
    lat_long = item.get("latLong", {})
    if lat_long:
        lat = lat_long.get("latitude")
        lon = lat_long.get("longitude")
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    
    # Try direct fields
    lat = item.get("latitude")
    lon = item.get("longitude")
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    
    return None, None


def _extract_price(price_data: Any) -> Optional[int]:
    """Extract and normalize price data"""
    if price_data is None:
        return None
        
    if isinstance(price_data, (int, float)):
        return int(price_data)
        
    if isinstance(price_data, str):
        # Remove common price formatting ($ , commas, etc.)
        price_str = re.sub(r'[^\d.]', '', price_data)
        try:
            return int(float(price_str))
        except ValueError:
            return None
    
    return None


def _extract_address(address_data: Any) -> Optional[str]:
    """Extract and normalize address data"""
    if address_data is None:
        return None
        
    if isinstance(address_data, str):
        return address_data.strip()
        
    if isinstance(address_data, dict):
        # Handle structured address objects
        parts = []
        for key in ["streetAddress", "address", "line1", "city", "state", "zip"]:
            if key in address_data and address_data[key]:
                parts.append(str(address_data[key]))
        return ", ".join(parts) if parts else None
    
    return str(address_data) if address_data else None


def _extract_number(number_data: Any, float_allowed: bool = False) -> Optional[int]:
    """Extract and normalize numeric data (beds, baths, etc.)"""
    if number_data is None:
        return None
        
    if isinstance(number_data, (int, float)):
        return float(number_data) if float_allowed else int(number_data)
        
    if isinstance(number_data, str):
        # Extract numbers from strings like "2 bedrooms" or "1.5"
        number_match = re.search(r'(\d+(?:\.\d+)?)', number_data)
        if number_match:
            num = float(number_match.group(1))
            return num if float_allowed else int(num)
    
    return None


def _extract_url(url_data: Any) -> Optional[str]:
    """Extract and normalize URL data"""
    if url_data is None:
        return None
        
    if isinstance(url_data, str):
        url = url_data.strip()
        # Ensure it's a valid URL format
        if url and not url.startswith(('http://', 'https://')):
            # Assume it's a Zillow URL if it doesn't have protocol
            if url.startswith('/'):
                url = f"https://www.zillow.com{url}"
            else:
                url = f"https://{url}"
        return url if url else None
    
    return str(url_data) if url_data else None 