#!/usr/bin/env python3
"""
FastAPI server for PropertySearch-Agent
Provides REST API endpoints for React frontend integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from run_agent import search_properties

app = FastAPI(title="PropertySearch API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for running sync operations
executor = ThreadPoolExecutor(max_workers=4)


class SearchFilters(BaseModel):
    """API model for search filters"""
    listing_type: str = "both"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_miles: float = 10.0
    min_sale_price: Optional[int] = None
    max_sale_price: Optional[int] = None
    min_rent_price: Optional[int] = None
    max_rent_price: Optional[int] = None
    min_beds: Optional[int] = None
    max_beds: Optional[int] = None
    min_baths: Optional[float] = None
    max_baths: Optional[float] = None
    home_types: Optional[List[str]] = None


class SearchResponse(BaseModel):
    """API response model"""
    success: bool
    count: int
    listings: List[dict]
    message: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "PropertySearch API is running"}


@app.get("/health")
async def health():
    """Health check endpoint for load balancer"""
    return {"status": "healthy", "service": "PropertySearch API"}


@app.post("/search", response_model=SearchResponse)
async def search_properties_endpoint(filters: SearchFilters):
    """
    Search properties with given filters
    
    Returns list of property listings matching the criteria
    """
    try:
        # Run the search in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        listings = await loop.run_in_executor(
            executor,
            search_properties,
            filters.listing_type,
            filters.latitude,
            filters.longitude,
            filters.radius_miles,
            filters.min_sale_price,
            filters.max_sale_price,
            filters.min_rent_price,
            filters.max_rent_price,
            filters.min_beds,
            filters.max_beds,
            filters.min_baths,
            filters.max_baths,
            filters.home_types
        )
        
        # Convert Pydantic models to dicts for JSON response
        listings_data = []
        for listing in listings:
            listing_dict = listing.model_dump()
            # Convert datetime to ISO string
            if listing_dict.get("timestamp"):
                listing_dict["timestamp"] = listing_dict["timestamp"].isoformat()
            # Convert HttpUrl to string
            if listing_dict.get("source_url"):
                listing_dict["source_url"] = str(listing_dict["source_url"])
            listings_data.append(listing_dict)
        
        return SearchResponse(
            success=True,
            count=len(listings_data),
            listings=listings_data,
            message=f"Found {len(listings_data)} properties"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/search/examples")
async def get_search_examples():
    """Get example filter configurations"""
    examples = {
        "austin_rentals": {
            "listing_type": "rental",
            "latitude": 30.2672,
            "longitude": -97.7431,
            "radius_miles": 15.0,
            "min_rent_price": 1000,
            "max_rent_price": 4000,
            "min_beds": 1
        },
        "downtown_condos": {
            "listing_type": "sale",
            "latitude": 30.2672,
            "longitude": -97.7431,
            "radius_miles": 5.0,
            "min_sale_price": 300000,
            "max_sale_price": 800000,
            "home_types": ["CONDO"]
        },
        "family_homes": {
            "listing_type": "both",
            "latitude": 30.2672,
            "longitude": -97.7431,
            "radius_miles": 20.0,
            "min_beds": 3,
            "min_baths": 2.0,
            "home_types": ["SINGLE_FAMILY"]
        }
    }
    return examples


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 