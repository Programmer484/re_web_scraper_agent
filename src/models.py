"""Pydantic data models for PropertySearch-Agent"""

from datetime import datetime
from typing import List, Optional, Literal
from dataclasses import dataclass
from pydantic import BaseModel, Field, HttpUrl, field_validator


class Listing(BaseModel):
    """Pydantic model for property listings - updated to match Zillow scraper output"""
    # Zillow identifiers
    zpid: Optional[str] = Field(None, description="Zillow Property ID")
    
    # Listing classification
    listing_type: Optional[Literal["sale", "rental"]] = Field(None, description="Type of listing: sale or rental")
    home_type: Optional[str] = Field(None, description="Property type (CONDO, SINGLE_FAMILY, etc.)")
    home_status: Optional[str] = Field(None, description="Listing status (FOR_SALE, SOLD, etc.)")
    
    # Pricing information
    sale_price: Optional[int] = Field(None, description="Property purchase price (for sale listings)")
    rental_price: Optional[int] = Field(None, description="Monthly rental price (for rental listings)")
    zestimate: Optional[int] = Field(None, description="Zillow's estimated property value")
    rent_zestimate: Optional[int] = Field(None, description="Zillow's estimated monthly rent")
    
    # Property details
    address: Optional[str] = Field(None, description="Full property address")
    beds: Optional[int] = Field(None, description="Number of bedrooms")
    baths: Optional[float] = Field(None, description="Number of bathrooms")
    living_area: Optional[int] = Field(None, description="Living area in square feet")
    lot_size: Optional[str] = Field(None, description="Lot size information")
    year_built: Optional[int] = Field(None, description="Year property was built")
    
    # Location data
    latitude: Optional[float] = Field(None, description="Property latitude")
    longitude: Optional[float] = Field(None, description="Property longitude")
    
    # Listing metadata
    source_url: Optional[HttpUrl] = Field(None, description="Zillow property page URL")
    broker_name: Optional[str] = Field(None, description="Listing broker name")
    
    # System fields
    building: bool = Field(default=False, description="Whether this is a building listing (vs individual property)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when listing was processed")

    @property
    def price(self) -> Optional[int]:
        """Convenience property that returns the appropriate price based on listing type"""
        return self.sale_price if self.sale_price is not None else self.rental_price


class SearchFilters(BaseModel):
    """Consolidated search filters model for both API and internal use"""
    # Listing type filter
    listing_type: Literal["sale", "rental", "both"] = Field(default=None, description="Type of listings to search")
    
    # Location (using coordinates for now as requested)
    latitude: Optional[float] = Field(None, description="Center latitude for search")
    longitude: Optional[float] = Field(None, description="Center longitude for search")
    radius_miles: float = Field(None, description="Search radius in miles")
    
    # Price filters
    min_sale_price: Optional[int] = Field(None, description="Minimum sale price")
    max_sale_price: Optional[int] = Field(None, description="Maximum sale price")
    min_rent_price: Optional[int] = Field(None, description="Minimum monthly rent")
    max_rent_price: Optional[int] = Field(None, description="Maximum monthly rent")
    
    # Property details
    min_beds: Optional[int] = Field(None, description="Minimum number of bedrooms")
    max_beds: Optional[int] = Field(None, description="Maximum number of bedrooms")
    min_baths: Optional[float] = Field(None, description="Minimum number of bathrooms")
    max_baths: Optional[float] = Field(None, description="Maximum number of bathrooms")
    
    # Additional filters
    home_types: Optional[List[str]] = Field(default=None, description="Property types to include (CONDO, SINGLE_FAMILY, etc.)")

    @field_validator('listing_type')
    def validate_listing_type(cls, v):
        if v not in ['sale', 'rental', 'both']:
            raise ValueError('listing_type must be "sale", "rental", or "both"')
        return v

    @field_validator('radius_miles')
    def validate_radius(cls, v):
        from src.config import MAX_RADIUS_MILES
        if v <= 0 or v > MAX_RADIUS_MILES:
            raise ValueError('radius_miles must be between 0 and MAX_RADIUS_MILES')
        return v

    @field_validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
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
