"""
Property Explanation Endpoints
AI-powered property match explanations with caching and streaming
"""

from fastapi import APIRouter, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import json

from app.services.explanation_service import explanation_service, PropertyExplanation
from app.core.redis_cache import explanation_cache
from app.services.supabase_property_service import SupabasePropertyService
from app.core.security import (
    rate_limit_explanation,
    rate_limit_general,
    rate_limit_strict,
    validate_search_input,
    security_middleware
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/explanations", tags=["Property Explanations"])

# Initialize property service
property_service = SupabasePropertyService()

class ExplanationRequest(BaseModel):
    """Request model for property explanation"""
    search_query: str
    listing_number: str
    
    class Config:
        # Add validation
        str_strip_whitespace = True
        min_anystr_length = 1
        max_anystr_length = 500

class StreamingExplanationRequest(BaseModel):
    """Request model for streaming property explanation"""
    search_query: str
    
    class Config:
        # Add validation
        str_strip_whitespace = True
        min_anystr_length = 1
        max_anystr_length = 500

@router.get("/health/")
@rate_limit_general
async def explanation_health(request: Request):
    """
    Health check for explanation service
    
    Security: General rate limiting (100 requests/minute per IP)
    """
    cache_stats = explanation_cache.get_cache_stats()
    
    return {
        "status": "healthy",
        "service": "Property Explanation Service",
        "security": "enabled",
        "components": {
            "openai_client": explanation_service.openai_client is not None,
            "streaming_llm": explanation_service.streaming_llm is not None,
            "redis_cache": cache_stats["redis_connected"],
            "langchain_cache": cache_stats["langchain_cache_enabled"]
        },
        "cache_stats": cache_stats
    }

@router.post("/generate/", response_model=PropertyExplanation)
@rate_limit_explanation
async def generate_property_explanation(request: Request, explanation_request: ExplanationRequest):
    """
    Generate AI explanation for property match (cached)
    
    Returns structured explanation with positive/negative points based on user's search query
    
    Security: Rate limited to 5 requests/minute per IP, input validation, prompt injection protection
    """
    try:
        # Validate and sanitize search input
        sanitized_query = validate_search_input(explanation_request.search_query)
        
        # Validate listing number (basic sanitization)
        listing_number = explanation_request.listing_number.strip()
        if not listing_number or len(listing_number) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid listing number"
            )
        
        # Get property data from search service
        property_data = await _get_property_data(listing_number)
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {listing_number} not found"
            )
        
        # Generate explanation with sanitized input
        explanation = await explanation_service.generate_explanation(
            search_query=sanitized_query,
            listing_number=listing_number,
            property_data=property_data
        )
        
        logger.info(f"Generated explanation for property {listing_number} (cached: {explanation.cached})")
        return explanation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation"
        )

@router.post("/stream/{listing_number}")
@rate_limit_explanation
async def stream_property_explanation(
    request: Request,
    listing_number: str, 
    streaming_request: StreamingExplanationRequest
):
    """
    Stream AI explanation generation in real-time
    
    Returns Server-Sent Events (SSE) stream for real-time explanation generation
    
    Security: Rate limited to 5 requests/minute per IP, input validation, prompt injection protection
    """
    try:
        # Validate and sanitize search input
        sanitized_query = validate_search_input(streaming_request.search_query)
        
        # Validate listing number
        listing_number = listing_number.strip()
        if not listing_number or len(listing_number) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid listing number"
            )
        
        # Get property data
        property_data = await _get_property_data(listing_number)
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {listing_number} not found"
            )
        
        # Stream explanation with sanitized input
        return StreamingResponse(
            explanation_service.stream_explanation(
                search_query=sanitized_query,
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
            detail="Failed to stream explanation"
        )

@router.get("/cache/stats/")
@rate_limit_general
async def get_cache_statistics(request: Request):
    """
    Get detailed cache performance statistics
    
    Security: General rate limiting (100 requests/minute per IP)
    """
    return {
        "cache_statistics": explanation_cache.get_cache_stats(),
        "service_status": {
            "explanation_service_initialized": explanation_service.openai_client is not None,
            "streaming_enabled": explanation_service.streaming_llm is not None
        }
    }

@router.delete("/cache/property/{listing_number}")
@rate_limit_strict
async def clear_property_cache(request: Request, listing_number: str):
    """
    Clear all cached explanations for a specific property
    
    Security: Strict rate limiting (3 requests/minute per IP)
    """
    try:
        # Validate listing number
        listing_number = listing_number.strip()
        if not listing_number or len(listing_number) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid listing number"
            )
            
        deleted_count = await explanation_cache.invalidate_property_explanations(listing_number)
        
        return {
            "message": f"Cleared cache for property {listing_number}",
            "deleted_entries": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing property cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )

@router.delete("/cache/all/")
@rate_limit_strict
async def clear_all_explanation_cache(request: Request):
    """
    Clear all explanation cache entries (maintenance endpoint)
    
    Security: Strict rate limiting (3 requests/minute per IP)
    """
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
            detail="Failed to clear cache"
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