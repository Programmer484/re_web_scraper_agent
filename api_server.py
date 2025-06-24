#!/usr/bin/env python3
"""
FastAPI server for PropertySearch-Agent
Provides REST API endpoints for React frontend integration
"""

import time
import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

from src.run_agent import main
from src.config import logger, MAX_RADIUS_MILES
from src.models import SearchFilters, SearchResponse

# Configuration
API_KEY = os.getenv("API_KEY", "")
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",") if os.getenv("ALLOWED_IPS") else []
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB

app = FastAPI(title="PropertySearch API", version="1.0.0")
security = HTTPBearer(auto_error=False)
executor = ThreadPoolExecutor(max_workers=2)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security and basic request logging middleware"""
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    # IP whitelist check
    if ALLOWED_IPS and client_ip not in ALLOWED_IPS:
        logger.warning(f"Blocked IP: {client_ip}")
        raise HTTPException(status_code=403, detail="IP not allowed")
    
    # Request size limit
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_SIZE:
        logger.warning(f"Request too large: {content_length} bytes")
        raise HTTPException(status_code=413, detail="Request too large")
    
    response = await call_next(request)
    
    # Security headers
    response.headers.update({
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    })
    
    if request.url.path == "/search":
        process_time = time.time() - start_time
        logger.info(f"Search completed in {process_time:.3f}s")
    
    return response

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key if configured"""
    if not API_KEY:
        return True
    
    if not credentials or credentials.credentials != API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

@app.get("/")
async def root():
    """API information endpoint"""
    return {"message": "PropertySearch API", "version": "1.0.0", "docs": "/docs"}

@app.get("/health")
async def health():
    """Health check for load balancers"""
    return {"status": "healthy", "service": "PropertySearch API"}

@app.post("/search", response_model=SearchResponse)
async def search_properties_endpoint(
    filters: SearchFilters, 
    authenticated: bool = Depends(verify_api_key)
):
    """Search properties with given filters"""
    try:
        logger.info("Property search initiated")
        
        # Run search in thread pool - pass SearchFilters object directly
        loop = asyncio.get_event_loop()
        listings = await loop.run_in_executor(executor, main, filters)
        
        # Convert models to dicts for JSON response
        listings_data = [listing.model_dump() for listing in listings]
        
        return SearchResponse(
            success=True,
            count=len(listings_data),
            listings=listings_data,
            message=f"Found {len(listings_data)} properties"
        )
        
    except Exception as e:
        logger.error(f"Property search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting PropertySearch API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 