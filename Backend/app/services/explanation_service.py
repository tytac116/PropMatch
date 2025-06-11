"""
AI Property Explanation Service
Generates structured explanations for property matches with streaming support
"""

import logging
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from app.core.config import settings
from app.core.redis_cache import explanation_cache
from app.models.property import Property

logger = logging.getLogger(__name__)

class ExplanationPoint(BaseModel):
    """Individual explanation point (positive or negative)"""
    point: str
    details: str

class PropertyExplanation(BaseModel):
    """Structured property explanation response"""
    search_query: str
    listing_number: str
    property_title: str
    match_score: float
    positive_points: List[ExplanationPoint]
    negative_points: List[ExplanationPoint]
    overall_summary: str
    cached: bool = False

class PropertyExplanationService:
    """Service for generating AI property match explanations"""
    
    def __init__(self):
        self.openai_client = None
        self.streaming_llm = None
        self._initialize_openai()
        
    def _initialize_openai(self):
        """Initialize OpenAI LangChain client"""
        try:
            if not settings.OPENAI_API_KEY:
                logger.error("OpenAI API key not configured")
                return
            
            # Standard LLM for cached responses
            self.openai_client = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.3,
                openai_api_key=settings.OPENAI_API_KEY,
                max_tokens=800
            )
            
            # Streaming LLM for real-time responses
            self.streaming_llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.3,
                openai_api_key=settings.OPENAI_API_KEY,
                max_tokens=800,
                streaming=True
            )
            
            logger.info("OpenAI LangChain clients initialized for explanation service")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.openai_client = None
            self.streaming_llm = None
    
    def _build_explanation_prompt(self, search_query: str, property_data: Dict[str, Any]) -> str:
        """Build comprehensive prompt for property explanation generation"""
        
        # Extract key property information
        location = property_data.get('location', {})
        features = property_data.get('features', [])
        pois = property_data.get('points_of_interest', [])
        
        location_str = f"{location.get('neighborhood', '')}, {location.get('city', '')}" if location else "Location not specified"
        features_str = ', '.join(features) if features else "No specific features listed"
        
        # Build POI context
        poi_context = ""
        if pois:
            poi_by_category = {}
            for poi in pois[:10]:  # Limit to top 10 POIs
                category = poi.get('category', 'Other')
                if category not in poi_by_category:
                    poi_by_category[category] = []
                poi_by_category[category].append(f"{poi.get('name', 'Unknown')} ({poi.get('distance_str', 'unknown distance')})")
            
            for category, items in poi_by_category.items():
                poi_context += f"\n- {category}: {', '.join(items[:3])}"  # Top 3 per category
        
        prompt = f"""You are a knowledgeable Cape Town property expert analyzing how well a specific property matches a user's search requirements.

**USER'S SEARCH:** "{search_query}"

**PROPERTY DETAILS:**
- Title: {property_data.get('title', 'Not specified')}
- Type: {property_data.get('type', 'Not specified')}
- Location: {location_str}
- Price: R{property_data.get('price', 0):,}
- Bedrooms: {property_data.get('bedrooms', 'Not specified')}
- Bathrooms: {property_data.get('bathrooms', 'Not specified')}
- Area: {property_data.get('area', 'Not specified')} {property_data.get('areaUnit', '')}
- Features: {features_str}

**NEARBY POINTS OF INTEREST:** {poi_context if poi_context else "No POI data available"}

**DESCRIPTION:** {property_data.get('description', 'No description available')[:500]}...

**INSTRUCTIONS:**
Analyze this property against the user's search requirements and provide a structured explanation in the following JSON format:

{{
    "positive_points": [
        {{"point": "Brief positive aspect", "details": "Detailed explanation of how this satisfies the user's needs"}},
        {{"point": "Another positive", "details": "More detailed explanation"}}
    ],
    "negative_points": [
        {{"point": "Area of concern or missing feature", "details": "Explanation of what might not fully meet the user's requirements"}},
        {{"point": "Another concern", "details": "Detailed explanation"}}
    ],
    "overall_summary": "2-3 sentence summary of how well this property matches the user's search"
}}

**GUIDELINES:**
- Be specific and reference actual property features and user requirements
- For positive points: Highlight exact matches, great location benefits, value propositions
- For negative points: Point out missing features, potential concerns, or aspects that might not fully satisfy
- If the property is an excellent match, it's okay to have fewer or minor negative points
- If it's a poor match, focus on major gaps
- Keep explanations conversational but informative
- Reference Cape Town context when relevant (traffic, lifestyle, neighborhoods)

Respond ONLY with the JSON structure above."""

        return prompt
    
    def _safe_float(self, value, default: float = 0.0) -> float:
        """Safely convert value to float with fallback"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    async def generate_explanation(
        self, 
        search_query: str, 
        listing_number: str, 
        property_data: Dict[str, Any]
    ) -> PropertyExplanation:
        """Generate cached explanation for property match"""
        
        # Check cache first
        cached_explanation = await explanation_cache.get_explanation(search_query, listing_number)
        if cached_explanation and cached_explanation.get('explanation'):
            logger.info(f"Returning cached explanation for property {listing_number}")
            explanation_data = cached_explanation['explanation']
            explanation_data['cached'] = True
            return PropertyExplanation(**explanation_data)
        
        # Generate new explanation
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        try:
            prompt = self._build_explanation_prompt(search_query, property_data)
            
            # Generate explanation using LangChain
            response = await self.openai_client.ainvoke([HumanMessage(content=prompt)])
            
            # Parse JSON response
            response_text = response.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            parsed_response = json.loads(response_text)
            
            # Create structured explanation
            explanation = PropertyExplanation(
                search_query=search_query,
                listing_number=listing_number,
                property_title=property_data.get('title', 'Property'),
                match_score=self._safe_float(property_data.get('searchScore')),
                positive_points=[ExplanationPoint(**point) for point in parsed_response.get('positive_points', [])],
                negative_points=[ExplanationPoint(**point) for point in parsed_response.get('negative_points', [])],
                overall_summary=parsed_response.get('overall_summary', ''),
                cached=False
            )
            
            # Cache the explanation
            await explanation_cache.set_explanation(
                search_query, 
                listing_number, 
                explanation.model_dump()
            )
            
            logger.info(f"Generated and cached new explanation for property {listing_number}")
            return explanation
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response JSON: {e}")
            raise Exception(f"Invalid AI response format: {e}")
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            raise Exception(f"Failed to generate explanation: {e}")
    
    async def stream_explanation(
        self, 
        search_query: str, 
        listing_number: str, 
        property_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Stream explanation generation in real-time"""
        
        # Check cache first - if found, yield the full cached response
        cached_explanation = await explanation_cache.get_explanation(search_query, listing_number)
        if cached_explanation and cached_explanation.get('explanation'):
            logger.info(f"Streaming cached explanation for property {listing_number}")
            explanation_data = cached_explanation['explanation']
            explanation_data['cached'] = True
            
            # Stream the cached response as structured chunks
            yield f"data: {json.dumps({'type': 'cached', 'cached': True})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'explanation': explanation_data})}\n\n"
            yield "data: [DONE]\n\n"
            return
        
        # Generate streaming explanation
        if not self.streaming_llm:
            raise Exception("Streaming LLM not initialized")
        
        try:
            prompt = self._build_explanation_prompt(search_query, property_data)
            
            # Indicate streaming start
            yield f"data: {json.dumps({'type': 'start', 'cached': False})}\n\n"
            
            # Collect full response while streaming
            full_response = ""
            
            # Stream from LangChain
            async for chunk in self.streaming_llm.astream([HumanMessage(content=prompt)]):
                if chunk.content:
                    full_response += chunk.content
                    # Stream each chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content})}\n\n"
            
            # Parse and structure the complete response
            response_text = full_response.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            parsed_response = json.loads(response_text)
            
            # Create structured explanation
            explanation = PropertyExplanation(
                search_query=search_query,
                listing_number=listing_number,
                property_title=property_data.get('title', 'Property'),
                match_score=self._safe_float(property_data.get('searchScore')),
                positive_points=[ExplanationPoint(**point) for point in parsed_response.get('positive_points', [])],
                negative_points=[ExplanationPoint(**point) for point in parsed_response.get('negative_points', [])],
                overall_summary=parsed_response.get('overall_summary', ''),
                cached=False
            )
            
            # Send structured final response
            yield f"data: {json.dumps({'type': 'complete', 'explanation': explanation.model_dump()})}\n\n"
            
            # Cache for future requests
            await explanation_cache.set_explanation(
                search_query, 
                listing_number, 
                explanation.model_dump()
            )
            
            # End stream
            yield "data: [DONE]\n\n"
            
            logger.info(f"Streamed and cached new explanation for property {listing_number}")
            
        except Exception as e:
            logger.error(f"Error streaming explanation: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

# Global instance
explanation_service = PropertyExplanationService() 