from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.database import get_db, PropertyDB
from app.models.property import Property, PropertySearchFilters
from app.services.property_service import PropertyService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize property service
property_service = PropertyService()

@router.get("/", response_model=List[Property])
async def get_properties(
    skip: int = Query(0, ge=0, description="Number of properties to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of properties to return"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    min_price: Optional[int] = Query(None, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, description="Maximum price filter"),
    bedrooms: Optional[int] = Query(None, description="Number of bedrooms"),
    city: Optional[str] = Query(None, description="Filter by city"),
    suburb: Optional[str] = Query(None, description="Filter by suburb"),
    db: Session = Depends(get_db)
):
    """
    Get all properties with optional filtering and pagination
    """
    try:
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
            db=db,
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return properties
        
    except Exception as e:
        logger.error(f"Error fetching properties: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{property_id}", response_model=Property)
async def get_property(
    property_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific property by ID
    """
    try:
        property_data = await property_service.get_property_by_id(
            db=db,
            property_id=property_id
        )
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return property_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching property {property_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/listing/{listing_number}", response_model=Property)
async def get_property_by_listing(
    listing_number: str,
    db: Session = Depends(get_db)
):
    """
    Get a property by its listing number
    """
    try:
        property_data = await property_service.get_property_by_listing_number(
            db=db,
            listing_number=listing_number
        )
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return property_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching property by listing {listing_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats/summary")
async def get_property_stats(db: Session = Depends(get_db)):
    """
    Get summary statistics about properties
    """
    try:
        stats = await property_service.get_property_statistics(db=db)
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching property statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 