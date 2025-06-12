"""
Test Endpoints - For experimental features
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging
from pydantic import BaseModel

from app.models.property import PropertySearchRequest, PropertySearchResponse, Property
from app.services.ai_rerank_service import AIRerankService
from app.core.langsmith_config import get_langsmith_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/test", tags=["Test Endpoints"])

# Initialize AI rerank service
ai_rerank_service = AIRerankService()

class AISearchRequest(BaseModel):
    """Simplified search request for testing"""
    query: str
    limit: int = 20

@router.post("/ai-search/", response_model=Dict[str, Any])
async def ai_search_properties(request: AISearchRequest):
    """
    TEST ENDPOINT: AI-powered property search with re-ranking
    
    This endpoint uses vector search + GPT-4.1-mini for intelligent re-ranking.
    Returns same structure as main search but with timing metrics and token usage.
    """
    try:
        # Convert to PropertySearchRequest
        search_request = PropertySearchRequest(
            query=request.query,
            page_size=request.limit,
            page=1
        )
        
        # Perform AI-enhanced search
        properties, timing_metrics = await ai_rerank_service.search_and_rerank(search_request)
        
        # Extract token usage details
        token_usage = timing_metrics.get('token_usage', {})
        total_tokens = sum(batch.get('total_tokens', 0) for batch in token_usage.values())
        total_prompt_tokens = sum(batch.get('prompt_tokens', 0) for batch in token_usage.values())
        total_completion_tokens = sum(batch.get('completion_tokens', 0) for batch in token_usage.values())
        
        # Create response with enhanced timing and token info
        response = {
            "query": request.query,
            "total_results": len(properties),
            "properties": [prop.model_dump() for prop in properties],
            "timing": {
                "vector_search_ms": timing_metrics.get('vector_search_ms', 0),
                "ai_rerank_ms": timing_metrics.get('ai_rerank_ms', 0),
                "total_ms": timing_metrics.get('total_ms', 0)
            },
            "ai_enhanced": True,
            "model_details": {
                "primary_model": "gpt-4o-mini",
                "model_used": timing_metrics.get('model_used', 'unknown'),
                "fallback_available": True
            },
            "token_usage": {
                "total_tokens": total_tokens,
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "batch_details": token_usage
            },
            "message": f"Found {len(properties)} properties (Vector: {timing_metrics.get('vector_search_ms', 0)}ms, AI: {timing_metrics.get('ai_rerank_ms', 0)}ms, Tokens: {total_tokens})"
        }
        
        logger.info(f"AI search completed: {timing_metrics}")
        logger.info(f"Total tokens used: {total_tokens} (Prompt: {total_prompt_tokens}, Completion: {total_completion_tokens})")
        return response
        
    except Exception as e:
        logger.error(f"AI search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI search failed: {str(e)}"
        )

@router.post("/ai-debug/", response_model=Dict[str, Any])
async def ai_debug_search(request: AISearchRequest):
    """
    DEBUG ENDPOINT: Shows enhanced AI reasoning process with ultra-rich property profiles
    """
    try:
        # Convert to PropertySearchRequest
        search_request = PropertySearchRequest(
            query=request.query,
            page_size=min(request.limit, 3),  # Limit for debugging
            page=1
        )
        
        # Get vector search results first
        vector_results = await ai_rerank_service.vector_service.search_similar_properties(
            query=request.query,
            top_k=5,
            filter_dict=None
        )
        
        if not vector_results:
            return {"error": "No vector results found"}
        
        # Get properties
        property_ids = [int(prop_id) for prop_id, _, _ in vector_results]
        properties = await ai_rerank_service.property_service.get_properties_batch(property_ids)
        properties = properties[:3]  # Take only 3 for debugging
        
        if not properties:
            return {"error": "No properties found"}
        
        # Create ULTRA-RICH property summaries using the enhanced method
        property_summaries = []
        for i, prop in enumerate(properties):
            summary = ai_rerank_service._create_ultra_rich_property_summary(prop, i)
            property_summaries.append(summary)
        
        # Create ENHANCED prompt using the new method
        prompt = ai_rerank_service._create_enhanced_rerank_prompt_v2(request.query, property_summaries, "debug")
        
        # Call AI if available with enhanced model selection
        if ai_rerank_service.openai_client:
            try:
                logger.info(f"Attempting {ai_rerank_service.primary_model} for debug")
                response = await ai_rerank_service.openai_client.chat.completions.create(
                    model=ai_rerank_service.primary_model,  # Use the primary model
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert Cape Town property analyst with deep understanding of South African real estate, geography, and user needs. You excel at detecting impossible queries and providing nuanced, realistic scoring."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.05,
                    max_tokens=1000
                )
                model_used = ai_rerank_service.primary_model
                
            except Exception as e:
                if "model not found" in str(e).lower() or "not exist" in str(e).lower():
                    # Fallback to secondary model
                    logger.warning(f"{ai_rerank_service.primary_model} not available, falling back to {ai_rerank_service.fallback_model}")
                    try:
                        response = await ai_rerank_service.openai_client.chat.completions.create(
                            model=ai_rerank_service.fallback_model,
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "You are an expert Cape Town property analyst with deep understanding of South African real estate, geography, and user needs. You excel at detecting impossible queries and providing nuanced, realistic scoring."
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.05,
                            max_tokens=1000
                        )
                        model_used = ai_rerank_service.fallback_model
                    except Exception as e2:
                        # Final fallback
                        response = await ai_rerank_service.openai_client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "You are an expert Cape Town property analyst."
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.05,
                            max_tokens=1000
                        )
                        model_used = "gpt-3.5-turbo"
                else:
                    raise e
            
            ai_response = response.choices[0].message.content
            
            # Extract token usage
            usage = response.usage
            token_info = {
                "model": model_used,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens
            }
            
            return {
                "query": request.query,
                "enhanced_prompt": prompt,
                "ai_response": ai_response,
                "property_summaries": property_summaries,
                "properties_count": len(properties),
                "model_details": {
                    "requested_model": ai_rerank_service.primary_model,
                    "actual_model_used": model_used,
                    "fallback_chain": [ai_rerank_service.primary_model, ai_rerank_service.fallback_model, "gpt-3.5-turbo"]
                },
                "token_usage": token_info,
                "debug": "ultra_enhanced_version_v2"
            }
        else:
            return {"error": "AI not available"}
            
    except Exception as e:
        return {"error": f"Enhanced debug failed: {str(e)}"}

@router.post("/ai-scores-debug/", response_model=Dict[str, Any])
async def ai_scores_debug(request: AISearchRequest):
    """
    DEBUG ENDPOINT: Shows detailed scoring process
    """
    try:
        # Convert to PropertySearchRequest
        search_request = PropertySearchRequest(
            query=request.query,
            page_size=min(request.limit, 3),  # Limit for debugging
            page=1
        )
        
        # Get vector search results
        vector_results = await ai_rerank_service.vector_service.search_similar_properties(
            query=request.query,
            top_k=5,
            filter_dict=None
        )
        
        if not vector_results:
            return {"error": "No vector results found"}
        
        # Get properties
        property_ids = [int(prop_id) for prop_id, _, _ in vector_results]
        properties = await ai_rerank_service.property_service.get_properties_batch(property_ids)
        properties = properties[:2]  # Take only 2 for debugging
        
        if not properties:
            return {"error": "No properties found"}
        
        # Show original scores
        original_scores = [getattr(prop, 'searchScore', None) for prop in properties]
        
        # Create property summaries and prompt
        property_summaries = []
        for i, prop in enumerate(properties):
            summary = {
                "id": i,
                "type": prop.type.value if hasattr(prop.type, 'value') else str(prop.type),
                "bedrooms": prop.bedrooms,
                "price": f"R{prop.price:,}",
                "location": f"{prop.location.neighborhood}, {prop.location.city}",
            }
            property_summaries.append(summary)
        
        # Get AI ranking
        if ai_rerank_service.openai_client:
            # Create prompt
            properties_text = ""
            for prop in property_summaries:
                properties_text += f"""
Property {prop['id']}: {prop['type']}, {prop['bedrooms']} bed, {prop['price']}, {prop['location']}
"""
            
            prompt = f"""
User Query: "{request.query}"
Dataset: Cape Town properties only

Properties to rank:
{properties_text}

Rank these properties from most to least relevant for the user query. Consider:
1. Query feasibility (impossible requests get low scores)

Respond with ONLY a JSON array like this:
[{{"id": 0, "score": 85}}, {{"id": 1, "score": 20}}]

Scores: 15-100 (15=terrible match, 100=perfect match)
"""
            
            # Call AI
            response = await ai_rerank_service.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a property ranking expert. Rank properties by relevance to the user query and assign scores 15-100."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse AI response
            import json
            json_start = ai_response.find('[')
            json_end = ai_response.rfind(']') + 1
            ai_ranking = []
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                try:
                    ai_ranking = json.loads(json_str)
                except:
                    ai_ranking = []
            
            # Apply scores manually for debugging
            ai_scores = {item['id']: item['score'] for item in ai_ranking if 'id' in item and 'score' in item}
            
            # Apply AI scores
            for i, prop in enumerate(properties):
                if i in ai_scores:
                    prop.searchScore = float(ai_scores[i])
            
            final_scores = [prop.searchScore for prop in properties]
            
            return {
                "query": request.query,
                "original_scores": original_scores,
                "ai_response": ai_response,
                "ai_ranking": ai_ranking,
                "ai_scores_mapping": ai_scores,
                "final_scores": final_scores,
                "debug": "step_by_step"
            }
        else:
            return {"error": "AI not available"}
            
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}

@router.get("/health/")
async def test_health():
    """Health check for test endpoints"""
    return {
        "status": "healthy",
        "service": "AI Rerank Test Service",
        "ai_available": ai_rerank_service.openai_client is not None
    } 