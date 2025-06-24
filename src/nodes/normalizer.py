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
        has_building_id = bool(item.get("buildingId"))  # Handle building listings
        has_coordinates = bool(item.get("latLong") or (item.get("latitude") and item.get("longitude")))
        
        if not any([has_address, has_price, has_zpid, has_building_id, has_coordinates]):
            continue
        
        try:
            # Check if this is a building vs individual property
            is_building = bool(item.get("isBuilding") or item.get("buildingId"))
            
            if is_building:
                # Process building with separate logic
                normalized_data = _process_building(item)
            else:
                # Process individual property with existing logic
                normalized_data = _process_individual_property(item)
            
            if not normalized_data:
                continue
            
            # Create deduplication key
            listing_type = normalized_data.get("listing_type")
            sale_price = normalized_data.get("sale_price")
            rental_price = normalized_data.get("rental_price")
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
        pass
    return listings


def _process_building(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process building listings with simplified logic
    
    Args:
        item: Raw building data from Zillow
        
    Returns:
        Normalized building data dict or None if invalid
    """
    # Extract basic building information
    address = _extract_address(item.get("address"))
    price = _extract_price(item.get("price"))
    lat, lon = _extract_coordinates(item)
    
    # Skip if no basic data
    if not address or not price:
        return None
    

    status_text = item.get("statusType", "").upper()
    is_rental = "RENT" in status_text
    
    return {
        # Identifiers
        "zpid": str(item.get("buildingId", "")),
        
        # Building flag
        "building": True,
        
        # Classification
        "listing_type": "rental" if is_rental else "sale",
        "home_status": item.get("statusType"),
        
        # Basic info
        "address": address,
        "sale_price": None if is_rental else price,
        "rental_price": price if is_rental else None,
        
        # Location
        "latitude": lat,
        "longitude": lon,
        
        # Building-specific (use min values as representative)
        "beds": _extract_number(item.get("minBeds")),
        "baths": _extract_number(item.get("minBaths"), float_allowed=True),
        "living_area": _extract_number(item.get("minArea")),
        
        # Metadata
        "source_url": _extract_url(item.get("detailUrl")),
    }


def _process_individual_property(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process individual property listings with full logic
    
    Args:
        item: Raw property data from Zillow
        
    Returns:
        Normalized property data dict or None if invalid
    """
    lat, lon = _extract_coordinates(item)
    address = _extract_address(item)
    price = _extract_price(item.get("price"))
    status_text = item.get("statusText", "")
    is_rental = "RENT" in status_text
    
    # Get hdpData as backup only
    hdp_data = item.get("hdpData", {}).get("homeInfo", {})
    
    return {
        # Zillow identifiers
        "zpid": str(item.get("zpid")),
        
        # Property flag
        "building": False,
        
        # Listing classification
        "listing_type": "rental" if is_rental else "sale",
        "home_type": item.get("homeType"),
        "home_status": item.get("statusType"),
        
        # Pricing information
        "sale_price": None if is_rental else price,
        "rental_price": price if is_rental else None,
        "zestimate": _extract_number(hdp_data.get("zestimate")),
        "rent_zestimate": _extract_number(hdp_data.get("rentZestimate")),
        
        # Property details
        "address": address,
        "beds": _extract_number(item.get("beds")),
        "baths": _extract_number(item.get("baths"), float_allowed=True),
        "living_area": _extract_number(item.get("area")),
        "lot_size": str(hdp_data.get("lotAreaValue")) if hdp_data.get("lotAreaValue") is not None else None,
        "year_built": _extract_number(hdp_data.get("yearBuilt")),
        
        # Location data
        "latitude": lat,
        "longitude": lon,
        
        # Listing metadata
        "source_url": _extract_url(item.get("detailUrl")),
        "broker_name": item.get("brokerName"),
        "days_on_zillow": _extract_number(item.get("timeOnZillow")),
    }


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
        # Handle range prices like "From $388,000" - extract the number
        if "from" in price_data.lower():
            # Extract number after "from"
            match = re.search(r'from\s*\$?([0-9,]+)', price_data.lower())
            if match:
                price_str = re.sub(r'[^\d]', '', match.group(1))
            else:
                price_str = re.sub(r'[^\d.]', '', price_data)
        else:
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


def _extract_number(number_data: Any, float_allowed: bool = False) -> Optional[float]:
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