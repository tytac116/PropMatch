from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request
from sqlalchemy.orm import Session
import logging
import time

from app.db.database import get_db
from app.models.property import PropertySearchRequest, PropertySearchResponse, PropertyExplanationResponse
from app.services.enhanced_search_service import EnhancedSearchService
from app.services.search_service import SearchService  # Keep for fallback
from app.core.security import (
    rate_limit_search,
    rate_limit_general,
    rate_limit_strict,
    validate_search_input,
    security_middleware
)

# Use search-specific logger
search_logger = logging.getLogger('search')
logger = logging.getLogger(__name__)  # Add general logger for error handling

router = APIRouter()

# Initialize services - Phase 2 enhanced service with fallback
enhanced_search_service = EnhancedSearchService()
fallback_search_service = SearchService()

@router.post("/", response_model=PropertySearchResponse)
@rate_limit_search
async def search_properties(
    request: Request,
    search_request: PropertySearchRequest,
    db: Session = Depends(get_db),
    use_ai: bool = Query(True, description="Use AI-powered vector search (Phase 2)")
):
    """
    Search properties using natural language query and filters
    
    Phase 2: Enhanced with vector similarity search and AI scoring
    - Vector search for semantic understanding
    - Multi-dimensional scoring
    - Enhanced location-based filtering
    
    Security: Rate limited to 5 requests/minute per IP
    """
    start_time = time.time()
    try:
        # Validate and sanitize search input
        sanitized_query = validate_search_input(search_request.query)
        search_request.query = sanitized_query
        
        search_logger.info(f"🔍 SEARCH: '{search_request.query}' (AI={use_ai})")
        
        if use_ai:
            # Use Phase 2 enhanced search with vector similarity - create fresh instance
            fresh_enhanced_service = EnhancedSearchService()
            results = await fresh_enhanced_service.search_properties(search_request)
        else:
            # Fallback to Phase 1 basic search
            results = await fallback_search_service.search_properties(
                db=db,
                search_request=search_request
            )
        
        # Log search performance and results
        duration = time.time() - start_time
        avg_score = sum(getattr(prop, 'searchScore', 0) for prop in results.properties) / len(results.properties) if results.properties else 0
        search_logger.info(f"✅ RESULTS: {results.totalResults} properties found in {duration:.2f}s (avg score: {avg_score:.1f}%)")
        
        return results
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as e:
        search_logger.error(f"❌ SEARCH ERROR: {e}")
        # If enhanced search fails, try fallback
        if use_ai:
            try:
                search_logger.info("🔄 Trying fallback search method")
                results = await fallback_search_service.search_properties(
                    db=db,
                    search_request=search_request
                )
                return results
            except Exception as fallback_error:
                search_logger.error(f"❌ FALLBACK ERROR: {fallback_error}")
        
        raise HTTPException(status_code=500, detail="Search service temporarily unavailable")

@router.post("/simple")
@rate_limit_search
async def simple_search(
    request: Request,
    query: str = Body(..., embed=True),
    limit: int = Body(20, embed=True),
    use_ai: bool = Body(True, embed=True),
    db: Session = Depends(get_db)
):
    """
    Simple search endpoint for quick testing with AI capabilities
    
    Security: Rate limited to 10 requests/minute per IP
    """
    try:
        # Validate and sanitize search input
        sanitized_query = validate_search_input(query)
        
        # Limit result count to prevent resource abuse
        if limit > 50:
            limit = 50
        
        from app.models.property import PropertySearchRequest
        
        search_request = PropertySearchRequest(
            query=sanitized_query,
            filters=None,
            page=1,
            page_size=limit
        )
        
        if use_ai:
            fresh_enhanced_service = EnhancedSearchService()
            results = await fresh_enhanced_service.search_properties(search_request)
        else:
            results = await fallback_search_service.search_properties(
                db=db,
                search_request=search_request
            )
        
        return {
            "query": sanitized_query,
            "found": results.totalResults,
            "ai_powered": use_ai,
            "properties": [
                {
                    "id": prop.id,
                    "title": prop.title,
                    "price": prop.price,
                    "location": f"{prop.location.neighborhood}, {prop.location.city}",
                    "type": prop.type.value if hasattr(prop.type, 'value') else str(prop.type),
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "searchScore": getattr(prop, 'searchScore', 0),
                    "url": prop.url
                }
                for prop in results.properties
            ]
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as e:
        logger.error(f"Error in simple search: {e}")
        raise HTTPException(status_code=500, detail="Search service temporarily unavailable")

@router.get("/test-vector")
@rate_limit_strict
async def test_vector_search(
    request: Request,
    query: str = Query("3 bedroom house near schools", description="Test query"),
    limit: int = Query(5, description="Number of results")
):
    """
    Test endpoint for vector search functionality
    Returns detailed scoring information for debugging
    
    Security: Strict rate limiting (3 requests/minute per IP)
    """
    try:
        # Validate and sanitize search input
        sanitized_query = validate_search_input(query)
        
        # Limit result count
        if limit > 10:
            limit = 10
            
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        if not vector_service.initialized:
            return {
                "status": "error",
                "message": "Vector service not initialized",
                "suggestions": [
                    "Check OpenAI API key",
                    "Check Pinecone API key", 
                    "Run vector loading script"
                ]
            }
        
        # Get vector search results
        vector_results = await vector_service.search_similar_properties(sanitized_query, top_k=limit)
        
        if not vector_results:
            return {
                "status": "no_results",
                "query": sanitized_query,
                "message": "No properties found in vector database"
            }
        
        # Format results with detailed scores
        formatted_results = []
        for property_id, score, metadata in vector_results:
            formatted_results.append({
                "property_id": property_id,
                "vector_score": round(score, 4),
                "metadata": {
                    "property_type": metadata.get("property_type"),
                    "price": metadata.get("price"),
                    "bedrooms": metadata.get("bedrooms"),
                    "city": metadata.get("city"),
                    "neighborhood": metadata.get("neighborhood")
                }
            })
        
        # Get index stats
        index_stats = vector_service.get_index_stats()
        
        return {
            "status": "success",
            "query": sanitized_query,
            "results": formatted_results,
            "index_stats": index_stats
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as e:
        logger.error(f"Error in vector search test: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/health")
@rate_limit_general
async def search_health_check(request: Request):
    """
    Health check for search services
    
    Security: General rate limiting (100 requests/minute per IP)
    """
    try:
        # Check vector service
        from app.services.vector_service import VectorService
        vector_service = VectorService()
        
        # Check Supabase service  
        from app.services.supabase_property_service import SupabasePropertyService
        supabase_service = SupabasePropertyService()
        
        health_status = {
            "vector_search": {
                "available": vector_service.initialized,
                "index_stats": vector_service.get_index_stats() if vector_service.initialized else None
            },
            "supabase_connection": {
                "available": supabase_service.supabase is not None
            },
            "enhanced_search": {
                "available": vector_service.initialized and supabase_service.supabase is not None
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# This endpoint will be fully implemented in Phase 3
@router.post("/explanation/{property_id}", response_model=PropertyExplanationResponse)
async def get_property_explanation(
    property_id: str,
    search_query: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Generate AI explanation for why a property matches a search query
    (To be implemented in Phase 3 - AI Explanation Generation)
    """
    try:
        # Placeholder for now - will be implemented in Phase 3
        return PropertyExplanationResponse(
            property_id=property_id,
            search_query=search_query,
            explanation={
                "positive_points": [
                    "This endpoint will be implemented in Phase 3",
                    "Will provide detailed AI explanations",
                    "Including feature matches and location benefits"
                ],
                "negative_points": [],
                "summary": "AI explanation generation coming in Phase 3",
                "confidence_score": 0
            },
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 