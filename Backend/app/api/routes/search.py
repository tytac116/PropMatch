from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.models.property import PropertySearchRequest, PropertySearchResponse, PropertyExplanationResponse
from app.services.enhanced_search_service import EnhancedSearchService
from app.services.search_service import SearchService  # Keep for fallback

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services - Phase 2 enhanced service with fallback
enhanced_search_service = EnhancedSearchService()
fallback_search_service = SearchService()

@router.post("/", response_model=PropertySearchResponse)
async def search_properties(
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
    """
    try:
        logger.info(f"Search request: '{search_request.query}' with AI={use_ai}")
        
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
        
        logger.info(f"Search returned {results.totalResults} results")
        return results
        
    except Exception as e:
        logger.error(f"Error searching properties: {e}")
        import traceback
        traceback.print_exc()
        # If enhanced search fails, try fallback
        if use_ai:
            try:
                logger.info("Enhanced search failed, trying fallback method")
                results = await fallback_search_service.search_properties(
                    db=db,
                    search_request=search_request
                )
                return results
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {fallback_error}")
        
        raise HTTPException(status_code=500, detail="Search service temporarily unavailable")

@router.post("/simple")
async def simple_search(
    query: str = Body(..., embed=True),
    limit: int = Body(20, embed=True),
    use_ai: bool = Body(True, embed=True),
    db: Session = Depends(get_db)
):
    """
    Simple search endpoint for quick testing with AI capabilities
    """
    try:
        from app.models.property import PropertySearchRequest
        
        search_request = PropertySearchRequest(
            query=query,
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
            "query": query,
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
        
    except Exception as e:
        logger.error(f"Error in simple search: {e}")
        raise HTTPException(status_code=500, detail="Search service temporarily unavailable")

@router.get("/test-vector")
async def test_vector_search(
    query: str = Query("3 bedroom house near schools", description="Test query"),
    limit: int = Query(5, description="Number of results")
):
    """
    Test endpoint for vector search functionality
    Returns detailed scoring information for debugging
    """
    try:
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
        vector_results = await vector_service.search_similar_properties(query, top_k=limit)
        
        if not vector_results:
            return {
                "status": "no_results",
                "query": query,
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
            "query": query,
            "results": formatted_results,
            "index_stats": index_stats
        }
        
    except Exception as e:
        logger.error(f"Error in vector search test: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/health")
async def search_health_check():
    """
    Health check for search services
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