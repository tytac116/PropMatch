from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class PropertyType(str, Enum):
    """Property type enumeration"""
    HOUSE = "house"
    APARTMENT = "apartment"
    CONDO = "condo"
    VILLA = "villa"
    TOWNHOUSE = "townhouse"

class PropertyStatus(str, Enum):
    """Property status enumeration"""
    FOR_SALE = "for_sale"
    FOR_RENT = "for_rent"

class Location(BaseModel):
    """Property location information"""
    address: str
    neighborhood: str
    city: str
    postalCode: Optional[str] = None
    country: str = "South Africa"

class PointOfInterest(BaseModel):
    """Point of interest near the property"""
    name: str
    category: str  # e.g., "Education", "Transport", "Health", etc.
    distance: float  # in kilometers
    distance_str: str  # e.g., "1.2km"

class Property(BaseModel):
    """Property model matching the frontend interface"""
    id: str
    title: str
    description: str
    price: int
    currency: str = "ZAR"
    type: PropertyType
    bedrooms: int
    bathrooms: Union[int, float]  # Can be 2.5, 3.5, etc.
    area: int
    areaUnit: str = "m²"
    location: Location
    images: List[str]
    features: List[str]
    status: PropertyStatus
    listedDate: str  # ISO format date string
    
    # AI-related fields (optional)
    searchScore: Optional[int] = None
    matchExplanation: Optional[str] = None
    
    # Additional property details from scraped data
    listing_number: Optional[str] = None
    url: Optional[str] = None
    street_address: Optional[str] = None
    suburb: Optional[str] = None
    province: Optional[str] = None
    kitchens: Optional[int] = None
    garages: Optional[int] = None
    parking: Optional[bool] = None
    parking_spaces: Optional[int] = None
    floor_size: Optional[int] = None
    erf_size: Optional[int] = None
    levies: Optional[str] = None
    rates: Optional[str] = None
    rates_and_taxes: Optional[str] = None
    no_transfer_duty: Optional[bool] = None
    agent_name: Optional[str] = None
    pets_allowed: Optional[bool] = None
    garden: Optional[bool] = None
    pools: Optional[bool] = None
    security: Optional[bool] = None
    solar_panels: Optional[bool] = None
    backup_power: Optional[bool] = None
    fibre_internet: Optional[bool] = None
    additional_rooms: Optional[Dict[str, Any]] = None
    external_features: Optional[Dict[str, Any]] = None
    building_features: Optional[Dict[str, Any]] = None
    points_of_interest: Optional[List[PointOfInterest]] = None
    
    class Config:
        extra = "allow"  # Allow dynamic attributes for scoring components
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PropertyCreate(BaseModel):
    """Model for creating new properties"""
    title: str
    description: str
    price: int
    currency: str = "ZAR"
    type: PropertyType
    bedrooms: int
    bathrooms: Union[int, float]
    area: int
    areaUnit: str = "m²"
    location: Location
    images: List[str]
    features: List[str]
    status: PropertyStatus

class PropertyUpdate(BaseModel):
    """Model for updating properties"""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    currency: Optional[str] = None
    type: Optional[PropertyType] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[Union[int, float]] = None
    area: Optional[int] = None
    areaUnit: Optional[str] = None
    location: Optional[Location] = None
    images: Optional[List[str]] = None
    features: Optional[List[str]] = None
    status: Optional[PropertyStatus] = None

class PropertySearchFilters(BaseModel):
    """Filters for property search"""
    property_type: Optional[PropertyType] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    min_area: Optional[int] = None
    max_area: Optional[int] = None
    location: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    features: Optional[List[str]] = None
    status: Optional[PropertyStatus] = None

class PropertySearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Natural language search query")
    filters: Optional[PropertySearchFilters] = None
    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Number of results per page")
    sort_by: Optional[str] = Field("relevance", description="Sort field: relevance, price, date")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc, desc")

class PropertySearchResponse(BaseModel):
    """Search response model"""
    properties: List[Property]
    searchTerm: str
    totalResults: int
    page: int
    pageSize: int
    totalPages: int
    hasNext: bool
    hasPrevious: bool

class MatchExplanation(BaseModel):
    """AI match explanation structure"""
    positive_points: List[str]
    negative_points: List[str]
    summary: str
    confidence_score: int = Field(ge=0, le=100)

class PropertyExplanationResponse(BaseModel):
    """Response for property explanation endpoint"""
    property_id: str
    search_query: str
    explanation: MatchExplanation
    cached: bool = False 