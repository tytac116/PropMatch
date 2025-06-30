from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.database import get_db, PropertyDB
from app.models.property import Property, PropertySearchFilters
from app.services.supabase_property_service import SupabasePropertyService

logger = logging.getLogger(__name__)

router = APIRouter()

def add_cors_headers(response: Response):
    """Add CORS headers to response"""
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response

@router.get("/", response_model=List[Property])
async def get_properties(
    response: Response,
    skip: int = Query(0, ge=0, description="Number of properties to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of properties to return"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    min_price: Optional[int] = Query(None, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, description="Maximum price filter"),
    bedrooms: Optional[int] = Query(None, description="Number of bedrooms"),
    city: Optional[str] = Query(None, description="Filter by city"),
    suburb: Optional[str] = Query(None, description="Filter by suburb")
):
    """
    Get all properties with optional filtering and pagination
    """
    try:
        # Use Supabase service instead of direct PostgreSQL
        property_service = SupabasePropertyService()
        
        # Build filters
        filters = PropertySearchFilters(
            property_type=property_type,
            min_price=min_price,
            max_price=max_price,
            bedrooms=bedrooms,
            city=city,
            neighborhood=suburb
        )
        
        properties = await property_service.get_properties(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        response = JSONResponse(content=[prop.model_dump() for prop in properties])
        return add_cors_headers(response)
        
    except Exception as e:
        logger.error(f"Error fetching properties: {e}")
        error_response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
        return add_cors_headers(error_response)

@router.get("/{property_id}", response_model=Property)
async def get_property(
    response: Response,
    property_id: str
):
    """
    Get a specific property by ID (listing number)
    """
    try:
        property_service = SupabasePropertyService()
        
        # Convert to int for listing number lookup
        listing_number = int(property_id)
        property_data = await property_service.get_property_by_listing_number(listing_number)
        
        if not property_data:
            error_response = JSONResponse(
                status_code=404,
                content={"detail": "Property not found"}
            )
            return add_cors_headers(error_response)
        
        response = JSONResponse(content=property_data.model_dump())
        return add_cors_headers(response)
        
    except ValueError:
        error_response = JSONResponse(
            status_code=400,
            content={"detail": "Invalid property ID format"}
        )
        return add_cors_headers(error_response)
    except Exception as e:
        logger.error(f"Error fetching property {property_id}: {e}")
        error_response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
        return add_cors_headers(error_response)

@router.get("/listing/{listing_number}", response_model=Property)
async def get_property_by_listing(
    listing_number: str
):
    """
    Get a property by its listing number
    """
    try:
        property_service = SupabasePropertyService()
        
        listing_num = int(listing_number)
        property_data = await property_service.get_property_by_listing_number(listing_num)
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return property_data
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid listing number format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching property by listing {listing_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats/summary")
async def get_property_stats(response: Response):
    """
    Get summary statistics about properties
    """
    try:
        property_service = SupabasePropertyService()
        stats = await property_service.get_property_statistics()
        response = JSONResponse(content=stats)
        return add_cors_headers(response)
        
    except Exception as e:
        logger.error(f"Error fetching property statistics: {e}")
        error_response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
        return add_cors_headers(error_response) 