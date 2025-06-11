"""
BM25 Hybrid Test Endpoints - For testing Vector + BM25 + AI combination
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging
from pydantic import BaseModel

from app.models.property import PropertySearchRequest, Property
from app.services.bm25_hybrid_service import BM25HybridService
from app.services.ai_rerank_service import AIRerankService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hybrid-test", tags=["Hybrid Test Endpoints"])

# Initialize services
bm25_hybrid_service = BM25HybridService()
ai_rerank_service = AIRerankService()

class HybridSearchRequest(BaseModel):
    """Search request for hybrid testing"""
    query: str
    limit: int = 10

@router.get("/health/")
async def hybrid_health():
    """Health check for hybrid test endpoints"""
    return {
        "status": "healthy",
        "service": "BM25 Hybrid Search Test Service",
        "components": {
            "vector_search": True,
            "bm25": True,
            "ai_rerank": ai_rerank_service.openai_client is not None
        }
    }

@router.post("/hybrid-search/", response_model=Dict[str, Any])
async def hybrid_search_properties(request: HybridSearchRequest):
    """
    TEST ENDPOINT: BM25 + Vector + AI hybrid search
    
    This combines:
    1. Vector search for semantic similarity
    2. BM25 for exact keyword matching
    3. AI re-ranking for contextual understanding
    """
    try:
        # Convert to PropertySearchRequest
        search_request = PropertySearchRequest(
            query=request.query,
            page_size=request.limit,
            page=1
        )
        
        # Perform hybrid search
        properties, timing_metrics = await bm25_hybrid_service.hybrid_search_and_rerank(search_request)
        
        # Extract detailed metrics
        scoring_analysis = timing_metrics.get('scoring_analysis', {})
        token_usage = timing_metrics.get('token_usage', {})
        
        # Calculate token totals
        total_tokens = sum(batch.get('total_tokens', 0) for batch in token_usage.values())
        total_prompt_tokens = sum(batch.get('prompt_tokens', 0) for batch in token_usage.values())
        total_completion_tokens = sum(batch.get('completion_tokens', 0) for batch in token_usage.values())
        
        # Create comprehensive response
        response = {
            "query": request.query,
            "total_results": len(properties),
            "properties": [_serialize_property_safe(prop) for prop in properties],
            "timing": {
                "vector_search_ms": timing_metrics.get('vector_search_ms', 0),
                "bm25_calculation_ms": timing_metrics.get('bm25_calculation_ms', 0),
                "hybrid_scoring_ms": timing_metrics.get('hybrid_scoring_ms', 0),
                "ai_rerank_ms": timing_metrics.get('ai_rerank_ms', 0),
                "corpus_build_ms": timing_metrics.get('corpus_build_ms', 0),
                "total_ms": timing_metrics.get('total_ms', 0)
            },
            "hybrid_search": True,
            "scoring_weights": {
                "vector_weight": bm25_hybrid_service.vector_weight,
                "bm25_weight": bm25_hybrid_service.bm25_weight,
                "ai_weight": bm25_hybrid_service.ai_weight
            },
            "scoring_analysis": scoring_analysis,
            "token_usage": {
                "total_tokens": total_tokens,
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "batch_details": token_usage
            },
            "message": f"Hybrid search found {len(properties)} properties (Vector+BM25+AI: {timing_metrics.get('total_ms', 0)}ms, Tokens: {total_tokens})"
        }
        
        logger.info(f"Hybrid search completed: {timing_metrics}")
        return response
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {str(e)}"
        )

@router.post("/compare-search/", response_model=Dict[str, Any])
async def compare_hybrid_vs_ai_search(request: HybridSearchRequest):
    """
    COMPARISON ENDPOINT: Side-by-side comparison of Hybrid vs AI-only search
    """
    try:
        # Convert to PropertySearchRequest
        search_request = PropertySearchRequest(
            query=request.query,
            page_size=request.limit,
            page=1
        )
        
        # Run both searches simultaneously
        import asyncio
        hybrid_task = bm25_hybrid_service.hybrid_search_and_rerank(search_request)
        ai_only_task = ai_rerank_service.search_and_rerank(search_request)
        
        (hybrid_properties, hybrid_timing), (ai_only_properties, ai_only_timing) = await asyncio.gather(
            hybrid_task, ai_only_task
        )
        
        # Compare results
        comparison = {
            "query": request.query,
            "hybrid_results": {
                "count": len(hybrid_properties),
                "scores": [prop.searchScore for prop in hybrid_properties[:5]],
                "timing": hybrid_timing.get('total_ms', 0),
                "tokens": sum(batch.get('total_tokens', 0) for batch in hybrid_timing.get('token_usage', {}).values())
            },
            "ai_only_results": {
                "count": len(ai_only_properties),
                "scores": [prop.searchScore for prop in ai_only_properties[:5]],
                "timing": ai_only_timing.get('total_ms', 0),
                "tokens": sum(batch.get('total_tokens', 0) for batch in ai_only_timing.get('token_usage', {}).values())
            },
            "performance_comparison": {
                "speed_improvement": f"{((ai_only_timing.get('total_ms', 0) - hybrid_timing.get('total_ms', 0)) / ai_only_timing.get('total_ms', 1)) * 100:.1f}%",
                "token_difference": hybrid_timing.get('token_usage', {}) and ai_only_timing.get('token_usage', {}),
                "hybrid_breakdown": {
                    "vector_ms": hybrid_timing.get('vector_search_ms', 0),
                    "bm25_ms": hybrid_timing.get('bm25_calculation_ms', 0),
                    "ai_ms": hybrid_timing.get('ai_rerank_ms', 0)
                }
            },
            "score_analysis": {
                "hybrid_score_range": {
                    "min": min([prop.searchScore for prop in hybrid_properties]) if hybrid_properties else 0,
                    "max": max([prop.searchScore for prop in hybrid_properties]) if hybrid_properties else 0
                },
                "ai_only_score_range": {
                    "min": min([prop.searchScore for prop in ai_only_properties]) if ai_only_properties else 0,
                    "max": max([prop.searchScore for prop in ai_only_properties]) if ai_only_properties else 0
                }
            }
        }
        
        logger.info(f"Comparison completed - Hybrid: {hybrid_timing.get('total_ms', 0)}ms vs AI-only: {ai_only_timing.get('total_ms', 0)}ms")
        return comparison
        
    except Exception as e:
        logger.error(f"Comparison search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison search failed: {str(e)}"
        )

@router.post("/hybrid-debug/", response_model=Dict[str, Any])
async def hybrid_debug_search(request: HybridSearchRequest):
    """
    DEBUG ENDPOINT: Shows detailed hybrid scoring breakdown
    """
    try:
        # Convert to PropertySearchRequest
        search_request = PropertySearchRequest(
            query=request.query,
            page_size=min(request.limit, 3),  # Limit for debugging
            page=1
        )
        
        # Perform hybrid search with debug info
        properties, timing_metrics = await bm25_hybrid_service.hybrid_search_and_rerank(search_request)
        
        # Create detailed debug response
        debug_info = {
            "query": request.query,
            "properties_analyzed": len(properties),
            "detailed_scoring": [],
            "timing_breakdown": timing_metrics,
            "bm25_parameters": {
                "k1": bm25_hybrid_service.k1,
                "b": bm25_hybrid_service.b,
                "corpus_built": bm25_hybrid_service.corpus_built,
                "corpus_size": len(bm25_hybrid_service.properties_corpus)
            },
            "hybrid_weights": {
                "vector_weight": bm25_hybrid_service.vector_weight,
                "bm25_weight": bm25_hybrid_service.bm25_weight,
                "ai_weight": bm25_hybrid_service.ai_weight
            }
        }
        
        # Add detailed scoring for each property
        for prop in properties:
            prop_debug = {
                "listing_number": prop.listing_number,
                "location": f"{prop.location.neighborhood}, {prop.location.city}" if prop.location else "Unknown",
                "type": str(prop.type) if prop.type else "Unknown",
                "bedrooms": prop.bedrooms,
                "final_score": getattr(prop, 'searchScore', 0),
                "component_scores": {
                    "vector_score": getattr(prop, 'vector_score', 0),
                    "bm25_score": getattr(prop, 'bm25_score', 0),
                    "hybrid_base_score": getattr(prop, 'hybrid_base_score', 0),
                    "ai_score": getattr(prop, 'ai_score', 0)
                }
            }
            debug_info["detailed_scoring"].append(prop_debug)
        
        logger.info(f"Hybrid debug completed for query: {request.query}")
        return debug_info
        
    except Exception as e:
        logger.error(f"Hybrid debug failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid debug failed: {str(e)}"
        )

def _serialize_property_safe(prop):
    """Safely serialize complete property profile with all fields and scoring breakdown"""
    try:
        # Build comprehensive property response with all available fields
        prop_data = {
            # Core identification
            "id": getattr(prop, 'id', None),
            "listing_number": getattr(prop, 'listing_number', None),
            "url": getattr(prop, 'url', None),  # PROPERTY URL - CRITICAL FIELD
            
            # Basic property information
            "title": getattr(prop, 'title', ''),
            "description": getattr(prop, 'description', ''),
            "price": getattr(prop, 'price', 0),
            "currency": getattr(prop, 'currency', 'ZAR'),
            "type": str(getattr(prop, 'type', 'APARTMENT')),
            "status": str(getattr(prop, 'status', 'FOR_SALE')),
            
            # Property specifications
            "bedrooms": getattr(prop, 'bedrooms', 0),
            "bathrooms": getattr(prop, 'bathrooms', 0),
            "area": getattr(prop, 'area', 0),
            "areaUnit": getattr(prop, 'areaUnit', 'm²'),
            "kitchens": getattr(prop, 'kitchens', None),
            "garages": getattr(prop, 'garages', None),
            "parking": getattr(prop, 'parking', None),
            "parking_spaces": getattr(prop, 'parking_spaces', None),
            
            # Size information
            "floor_size": getattr(prop, 'floor_size', None),
            "erf_size": getattr(prop, 'erf_size', None),
            
            # Financial information
            "levies": getattr(prop, 'levies', None),
            "rates": getattr(prop, 'rates', None),
            "rates_and_taxes": getattr(prop, 'rates_and_taxes', None),
            "no_transfer_duty": getattr(prop, 'no_transfer_duty', None),
            
            # Location information - comprehensive
            "location": {},
            "street_address": getattr(prop, 'street_address', None),
            "suburb": getattr(prop, 'suburb', None),
            "province": getattr(prop, 'province', None),
            
            # Features and amenities
            "features": getattr(prop, 'features', []) or [],
            "pets_allowed": getattr(prop, 'pets_allowed', None),
            "garden": getattr(prop, 'garden', None),
            "pools": getattr(prop, 'pools', None),
            "security": getattr(prop, 'security', None),
            "solar_panels": getattr(prop, 'solar_panels', None),
            "backup_power": getattr(prop, 'backup_power', None),
            "fibre_internet": getattr(prop, 'fibre_internet', None),
            "additional_rooms": getattr(prop, 'additional_rooms', None),
            "external_features": getattr(prop, 'external_features', None),
            "building_features": getattr(prop, 'building_features', None),
            
            # Media
            "images": getattr(prop, 'images', []) or [],
            
            # Listing details
            "listedDate": getattr(prop, 'listedDate', ''),
            "agent_name": getattr(prop, 'agent_name', None),
            
            # AI-Centric Hybrid Search Score (MAIN RESULT)
            "searchScore": getattr(prop, 'searchScore', 0),
            
            # Points of Interest - complete data
            "points_of_interest": [],
            
            # Enhanced scoring breakdown for analysis
            "scoring_breakdown": {
                "vector_score_raw": getattr(prop, 'vector_score', None),
                "vector_100": getattr(prop, 'vector_100', None),
                "bm25_score_raw": getattr(prop, 'bm25_score', None),
                "bm25_contribution": getattr(prop, 'bm25_contribution', None),
                "hybrid_base_score": getattr(prop, 'hybrid_base_score', None),
                "ai_score": getattr(prop, 'ai_score', None),
                "final_score": getattr(prop, 'searchScore', None),
                "scoring_method": getattr(prop, 'final_score_method', None)
            }
        }
        
        # Handle location object safely - complete location data
        if hasattr(prop, 'location') and prop.location:
            loc = prop.location
            prop_data["location"] = {
                "address": getattr(loc, 'address', ''),
                "neighborhood": getattr(loc, 'neighborhood', ''),
                "city": getattr(loc, 'city', ''),
                "postalCode": getattr(loc, 'postalCode', None),
                "country": getattr(loc, 'country', 'South Africa')
            }
        
        # Handle points of interest - complete POI data for location intelligence
        if hasattr(prop, 'points_of_interest') and prop.points_of_interest:
            for poi in prop.points_of_interest:
                poi_data = {
                    "name": getattr(poi, 'name', ''),
                    "category": getattr(poi, 'category', ''),
                    "distance": getattr(poi, 'distance', 0.0),
                    "distance_str": getattr(poi, 'distance_str', '')
                }
                prop_data["points_of_interest"].append(poi_data)
        
        return prop_data
        
    except Exception as e:
        logger.warning(f"Error in comprehensive serialization for property {getattr(prop, 'listing_number', 'unknown')}: {e}")
        # Ultra-minimal fallback with core fields
        return {
            "listing_number": str(getattr(prop, 'listing_number', 'unknown')),
            "url": getattr(prop, 'url', None),  # Always try to include URL
            "title": getattr(prop, 'title', ''),
            "price": getattr(prop, 'price', 0),
            "searchScore": float(getattr(prop, 'searchScore', 0)),
            "error": "minimal_serialization_fallback"
        } 