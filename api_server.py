#!/usr/bin/env python3
"""
FastAPI server for PropertySearch-Agent
Provides REST API endpoints for React frontend integration
"""

import time
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from run_agent import search_properties
from src.config import logger

app = FastAPI(title="PropertySearch API", version="1.0.0")

# Enable CORS for broader API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for webhook/API usage
    allow_credentials=False,  # Disable credentials for public API
    allow_methods=["GET", "POST", "OPTIONS"],  # Specific methods for API
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Thread pool for running sync operations
executor = ThreadPoolExecutor(max_workers=4)

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with DEBUG level detail"""
    start_time = time.time()
    
    # Log request details
    logger.debug(f"🌐 INCOMING REQUEST: {request.method} {request.url}")
    logger.debug(f"📋 Request headers: {dict(request.headers)}")
    logger.debug(f"📍 Client IP: {request.client.host if request.client else 'Unknown'}")
    
    # If request has body, try to log it
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                logger.debug(f"📦 Request body: {body.decode('utf-8')}")
        except Exception as e:
            logger.debug(f"⚠️ Could not read request body: {e}")
    
    # Process request
    response = await call_next(request)
    
    # Log response details
    process_time = time.time() - start_time
    logger.debug(f"✅ REQUEST COMPLETED: {request.method} {request.url}")
    logger.debug(f"⏱️ Processing time: {process_time:.4f}s")
    logger.debug(f"📤 Response status: {response.status_code}")
    
    return response


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
    logger.debug("🏠 Root endpoint called - health check")
    return {"message": "PropertySearch API is running"}


@app.get("/health")
async def health():
    """Health check endpoint for load balancer"""
    logger.debug("❤️ Health endpoint called - load balancer check")
    return {"status": "healthy", "service": "PropertySearch API"}


@app.post("/search", response_model=SearchResponse)
async def search_properties_endpoint(filters: SearchFilters):
    """
    Search properties with given filters
    
    Returns list of property listings matching the criteria
    """
    request_start = time.time()
    
    logger.debug("🔍 PROPERTY SEARCH REQUEST INITIATED")
    logger.debug(f"📋 Search filters received: {filters.model_dump()}")
    
    try:
        # Log search parameters for debugging
        logger.debug(f"🎯 Search parameters:")
        logger.debug(f"   - Listing type: {filters.listing_type}")
        logger.debug(f"   - Location: ({filters.latitude}, {filters.longitude})")
        logger.debug(f"   - Radius: {filters.radius_miles} miles")
        logger.debug(f"   - Price range (sale): ${filters.min_sale_price} - ${filters.max_sale_price}")
        logger.debug(f"   - Price range (rent): ${filters.min_rent_price} - ${filters.max_rent_price}")
        logger.debug(f"   - Bedrooms: {filters.min_beds} - {filters.max_beds}")
        logger.debug(f"   - Bathrooms: {filters.min_baths} - {filters.max_baths}")
        logger.debug(f"   - Home types: {filters.home_types}")
        
        logger.debug("⚙️ Executing property search in thread pool...")
        
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
        
        logger.debug(f"🎉 Property search completed! Found {len(listings)} listings")
        
        # Convert Pydantic models to dicts for JSON response
        logger.debug("🔄 Converting listings to JSON format...")
        listings_data = []
        for i, listing in enumerate(listings):
            logger.debug(f"   Processing listing {i+1}/{len(listings)}")
            listing_dict = listing.model_dump()
            # Convert datetime to ISO string
            if listing_dict.get("timestamp"):
                listing_dict["timestamp"] = listing_dict["timestamp"].isoformat()
            # Convert HttpUrl to string
            if listing_dict.get("source_url"):
                listing_dict["source_url"] = str(listing_dict["source_url"])
            listings_data.append(listing_dict)
        
        response_time = time.time() - request_start
        logger.debug(f"⏱️ Total request processing time: {response_time:.4f}s")
        
        response = SearchResponse(
            success=True,
            count=len(listings_data),
            listings=listings_data,
            message=f"Found {len(listings_data)} properties"
        )
        
        logger.debug(f"📤 Sending response with {len(listings_data)} properties")
        return response
        
    except Exception as e:
        error_time = time.time() - request_start
        logger.error(f"❌ Property search failed after {error_time:.4f}s")
        logger.error(f"🐛 Error details: {str(e)}")
        logger.exception("Full error traceback:")
        
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/search/examples")
async def get_search_examples():
    """Get example filter configurations"""
    logger.debug("📚 Examples endpoint called - returning filter templates")
    
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
    
    logger.debug(f"📋 Returning {len(examples)} example configurations")
    return examples


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting PropertySearch API server...")
    logger.info("🔧 Server configuration: host=0.0.0.0, port=8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug") 