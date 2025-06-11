"""
Property Explanation Endpoints
AI-powered property match explanations with caching and streaming
"""

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import json

from app.services.explanation_service import explanation_service, PropertyExplanation
from app.core.redis_cache import explanation_cache
from app.services.supabase_property_service import SupabasePropertyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/explanations", tags=["Property Explanations"])

# Initialize property service
property_service = SupabasePropertyService()

class ExplanationRequest(BaseModel):
    """Request model for property explanation"""
    search_query: str
    listing_number: str

class StreamingExplanationRequest(BaseModel):
    """Request model for streaming property explanation"""
    search_query: str

@router.get("/health/")
async def explanation_health():
    """Health check for explanation service"""
    cache_stats = explanation_cache.get_cache_stats()
    
    return {
        "status": "healthy",
        "service": "Property Explanation Service",
        "components": {
            "openai_client": explanation_service.openai_client is not None,
            "streaming_llm": explanation_service.streaming_llm is not None,
            "redis_cache": cache_stats["redis_connected"],
            "langchain_cache": cache_stats["langchain_cache_enabled"]
        },
        "cache_stats": cache_stats
    }

@router.post("/generate/", response_model=PropertyExplanation)
async def generate_property_explanation(request: ExplanationRequest):
    """
    Generate AI explanation for property match (cached)
    
    Returns structured explanation with positive/negative points based on user's search query
    """
    try:
        # Validate input
        if not request.search_query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query is required"
            )
        
        if not request.listing_number.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Listing number is required"
            )
        
        # Get property data from search service
        property_data = await _get_property_data(request.listing_number)
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {request.listing_number} not found"
            )
        
        # Generate explanation
        explanation = await explanation_service.generate_explanation(
            search_query=request.search_query,
            listing_number=request.listing_number,
            property_data=property_data
        )
        
        logger.info(f"Generated explanation for property {request.listing_number} (cached: {explanation.cached})")
        return explanation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )

@router.post("/stream/{listing_number}")
async def stream_property_explanation(
    listing_number: str, 
    request: StreamingExplanationRequest
):
    """
    Stream AI explanation generation in real-time
    
    Returns Server-Sent Events (SSE) stream for real-time explanation generation
    """
    try:
        # Validate input
        if not request.search_query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query is required"
            )
        
        if not listing_number.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Listing number is required"
            )
        
        # Get property data
        property_data = await _get_property_data(listing_number)
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {listing_number} not found"
            )
        
        # Stream explanation
        return StreamingResponse(
            explanation_service.stream_explanation(
                search_query=request.search_query,
                listing_number=listing_number,
                property_data=property_data
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream explanation: {str(e)}"
        )

@router.get("/cache/stats/")
async def get_cache_statistics():
    """Get detailed cache performance statistics"""
    return {
        "cache_statistics": explanation_cache.get_cache_stats(),
        "service_status": {
            "explanation_service_initialized": explanation_service.openai_client is not None,
            "streaming_enabled": explanation_service.streaming_llm is not None
        }
    }

@router.delete("/cache/property/{listing_number}")
async def clear_property_cache(listing_number: str):
    """Clear all cached explanations for a specific property"""
    try:
        deleted_count = await explanation_cache.invalidate_property_explanations(listing_number)
        
        return {
            "message": f"Cleared cache for property {listing_number}",
            "deleted_entries": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing property cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )

@router.delete("/cache/all/")
async def clear_all_explanation_cache():
    """Clear all explanation cache entries (maintenance endpoint)"""
    try:
        deleted_count = await explanation_cache.clear_all_explanations()
        
        return {
            "message": "Cleared all explanation cache entries",
            "deleted_entries": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing all cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )

@router.get("/test-property/{listing_number}")
async def test_property_retrieval(listing_number: str):
    """Test endpoint to verify property data retrieval"""
    try:
        property_data = await _get_property_data(listing_number)
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {listing_number} not found"
            )
        
        return {
            "listing_number": listing_number,
            "property_found": True,
            "basic_info": {
                "title": property_data.get('title', 'N/A'),
                "type": property_data.get('type', 'N/A'),
                "location": property_data.get('location', {}),
                "price": property_data.get('price', 0),
                "bedrooms": property_data.get('bedrooms', 'N/A'),
                "features_count": len(property_data.get('features', [])),
                "poi_count": len(property_data.get('points_of_interest', []))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing property retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve property: {str(e)}"
        )

async def _get_property_data(listing_number: str) -> Optional[Dict[str, Any]]:
    """Helper function to retrieve complete property data"""
    try:
        # Use the property search service to get property by listing number
        # Convert string to int as the service expects an integer
        listing_num = int(listing_number)
        property_obj = await property_service.get_property_by_listing_number(listing_num)
        
        if not property_obj:
            return None
        
        # Convert property object to dict with all fields
        property_data = {
            # Core identification
            "id": getattr(property_obj, 'id', None),
            "listing_number": getattr(property_obj, 'listing_number', None),
            "url": getattr(property_obj, 'url', None),
            
            # Basic information
            "title": getattr(property_obj, 'title', ''),
            "description": getattr(property_obj, 'description', ''),
            "price": getattr(property_obj, 'price', 0),
            "currency": getattr(property_obj, 'currency', 'ZAR'),
            "type": str(getattr(property_obj, 'type', 'APARTMENT')),
            "status": str(getattr(property_obj, 'status', 'FOR_SALE')),
            
            # Specifications
            "bedrooms": getattr(property_obj, 'bedrooms', 0),
            "bathrooms": getattr(property_obj, 'bathrooms', 0),
            "area": getattr(property_obj, 'area', 0),
            "areaUnit": getattr(property_obj, 'areaUnit', 'm²'),
            "garages": getattr(property_obj, 'garages', None),
            "parking": getattr(property_obj, 'parking', None),
            
            # Features
            "features": getattr(property_obj, 'features', []) or [],
            "garden": getattr(property_obj, 'garden', None),
            "pools": getattr(property_obj, 'pools', None),
            "security": getattr(property_obj, 'security', None),
            
            # Location
            "location": {},
            
            # Points of interest
            "points_of_interest": [],
            
            # Search score if available
            "searchScore": getattr(property_obj, 'searchScore', 0)
        }
        
        # Handle location object
        if hasattr(property_obj, 'location') and property_obj.location:
            loc = property_obj.location
            property_data["location"] = {
                "address": getattr(loc, 'address', ''),
                "neighborhood": getattr(loc, 'neighborhood', ''),
                "city": getattr(loc, 'city', ''),
                "postalCode": getattr(loc, 'postalCode', None),
                "country": getattr(loc, 'country', 'South Africa')
            }
        
        # Handle points of interest
        if hasattr(property_obj, 'points_of_interest') and property_obj.points_of_interest:
            for poi in property_obj.points_of_interest:
                poi_data = {
                    "name": getattr(poi, 'name', ''),
                    "category": getattr(poi, 'category', ''),
                    "distance": getattr(poi, 'distance', 0.0),
                    "distance_str": getattr(poi, 'distance_str', '')
                }
                property_data["points_of_interest"].append(poi_data)
        
        return property_data
        
    except Exception as e:
        logger.error(f"Error retrieving property data for {listing_number}: {e}")
        return None 