#!/usr/bin/env python3
"""
FastAPI server for PropertySearch-Agent
Provides REST API endpoints for React frontend integration
"""

import time
import logging
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

from run_agent import search_properties
from src.config import logger

# Security configuration
API_KEY = os.getenv("API_KEY", "")  # Set this in production
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",") if os.getenv("ALLOWED_IPS") else []
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB limit

app = FastAPI(title="PropertySearch API", version="1.0.0")
security = HTTPBearer(auto_error=False)

# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Enhanced security middleware"""
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    # Log webhook input (only for search endpoint)
    if request.url.path == "/search":
        logger.debug(f"🌐 WEBHOOK INPUT: {request.method} {request.url}")
        if request.method == "POST":
            try:
                body = await request.body()
                if body:
                    logger.debug(f"📦 Request data: {body.decode('utf-8')}")
            except Exception as e:
                logger.debug(f"⚠️ Could not read request body: {e}")
    
    # IP whitelist check (if configured)
    if ALLOWED_IPS and client_ip not in ALLOWED_IPS:
        logger.warning(f"🚫 Blocked request from unauthorized IP: {client_ip}")
        raise HTTPException(status_code=403, detail="IP not allowed")
    
    # Request size limit
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_SIZE:
        logger.warning(f"🚫 Request too large: {content_length} bytes from {client_ip}")
        raise HTTPException(status_code=413, detail="Request too large")
    
    # Process request
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Log completion only for search endpoint
    if request.url.path == "/search":
        process_time = time.time() - start_time
        logger.debug(f"✅ WEBHOOK COMPLETED: {process_time:.4f}s")
        logger.debug(f"📤 Response status: {response.status_code}")
    
    return response

# API Key authentication (optional)
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key if configured"""
    if not API_KEY:  # Skip if no API key is set
        return True
    
    if not credentials or credentials.credentials != API_KEY:
        logger.warning(f"🔑 Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

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
    """API model for search filters with validation"""
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

    @validator('listing_type')
    def validate_listing_type(cls, v):
        if v not in ['sale', 'rental', 'both']:
            raise ValueError('listing_type must be "sale", "rental", or "both"')
        return v

    @validator('radius_miles')
    def validate_radius(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('radius_miles must be between 0 and 100')
        return v

    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError('longitude must be between -180 and 180')
        return v


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
async def search_properties_endpoint(
    filters: SearchFilters, 
    authenticated: bool = Depends(verify_api_key)
):
    """
    Search properties with given filters
    
    Returns list of property listings matching the criteria
    """
    request_start = time.time()
    
    logger.debug("🔍 PROPERTY SEARCH REQUEST INITIATED")
    
    try:
        logger.debug("⚙️ Executing property search...")
        
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
        
        # Show first result for debugging
        if listings_data:
            first_item = listings_data[0]
            logger.debug(f"📋 First result: {first_item.get('address')} - ${first_item.get('sale_price') or first_item.get('rental_price')}")
        
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



if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting PropertySearch API server...")
    logger.info("🔧 Server configuration: host=0.0.0.0, port=8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug") 