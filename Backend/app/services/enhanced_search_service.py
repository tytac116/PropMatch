"""
Enhanced Search Service for PropMatch Phase 2
Combines vector search with traditional filtering and AI scoring
"""

import logging
import math
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from app.models.property import PropertySearchRequest, PropertySearchResponse, Property
from app.services.supabase_property_service import SupabasePropertyService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Enhanced search result with multiple scoring dimensions"""
    property: Property
    vector_score: float
    metadata_match_score: float
    distance_score: float
    final_score: float

class EnhancedSearchService:
    """Phase 2 search service with vector similarity and AI scoring"""
    
    def __init__(self):
        self.property_service = SupabasePropertyService()
        self.vector_service = VectorService()
    
    async def search_properties(
        self,
        search_request: PropertySearchRequest
    ) -> PropertySearchResponse:
        """
        Enhanced property search using vector similarity + metadata filtering
        
        Multi-stage approach:
        1. Vector similarity search to get relevant properties
        2. Apply metadata filters 
        3. Calculate enhanced scoring
        4. Sort and paginate results
        """
        
        logger.info(f"Enhanced search for: '{search_request.query}' with filters")
        
        if not self.vector_service.initialized:
            logger.warning("Vector service not available, falling back to basic search")
            return await self._fallback_search(search_request)
        
        try:
            # Stage 1: Vector similarity search
            vector_results = await self._vector_search(search_request)
            
            if not vector_results:
                logger.info("No vector results found")
                return PropertySearchResponse(
                    properties=[],
                    searchTerm=search_request.query,
                    totalResults=0,
                    page=search_request.page,
                    pageSize=search_request.page_size,
                    totalPages=0,
                    hasNext=False,
                    hasPrevious=False
                )
            
            # Stage 2: Get full property details
            enhanced_results = await self._enrich_with_property_details(vector_results)
            
            # Stage 3: Apply metadata filters
            filtered_results = self._apply_enhanced_filters(enhanced_results, search_request.filters)
            
            # Stage 4: Calculate final scores
            scored_results = await self._calculate_enhanced_scores(filtered_results, search_request)
            
            # Stage 5: Sort by final score
            sorted_results = sorted(scored_results, key=lambda x: x.final_score, reverse=True)
            
            # Stage 6: Apply pagination
            total_results = len(sorted_results)
            start_idx = (search_request.page - 1) * search_request.page_size
            end_idx = start_idx + search_request.page_size
            page_results = sorted_results[start_idx:end_idx]
            
            # Convert to response format
            properties = []
            for result in page_results:
                # Add enhanced search score to property
                result.property.searchScore = int(result.final_score)
                properties.append(result.property)
            
            # Calculate pagination info
            total_pages = math.ceil(total_results / search_request.page_size)
            has_next = search_request.page < total_pages
            has_previous = search_request.page > 1
            
            logger.info(f"Enhanced search returned {len(properties)} properties from {total_results} total matches")
            
            return PropertySearchResponse(
                properties=properties,
                searchTerm=search_request.query,
                totalResults=total_results,
                page=search_request.page,
                pageSize=search_request.page_size,
                totalPages=total_pages,
                hasNext=has_next,
                hasPrevious=has_previous
            )
            
        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            return await self._fallback_search(search_request)
    
    async def _vector_search(self, search_request: PropertySearchRequest) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Perform vector similarity search"""
        
        # Create enhanced query string
        query_parts = [search_request.query]
        
        # Add filter context to improve vector search
        if search_request.filters:
            if search_request.filters.property_type:
                query_parts.append(f"property type {search_request.filters.property_type.value}")
            
            if search_request.filters.bedrooms:
                query_parts.append(f"{search_request.filters.bedrooms} bedrooms")
            
            if search_request.filters.city:
                query_parts.append(f"in {search_request.filters.city}")
            
            if search_request.filters.neighborhood:
                query_parts.append(f"in {search_request.filters.neighborhood}")
        
        enhanced_query = " ".join(query_parts)
        
        # Perform vector search with larger top_k for better filtering
        vector_results = await self.vector_service.search_similar_properties(
            query=enhanced_query,
            top_k=min(200, search_request.page_size * 10),  # Get more candidates for filtering
            filter_dict=self._build_pinecone_filters(search_request.filters)
        )
        
        logger.info(f"Vector search returned {len(vector_results)} candidates")
        return vector_results
    
    def _build_pinecone_filters(self, filters) -> Optional[Dict[str, Any]]:
        """Build Pinecone metadata filters from search filters"""
        
        if not filters:
            return None
        
        pinecone_filter = {}
        
        # Price range
        if filters.min_price or filters.max_price:
            price_filter = {}
            if filters.min_price:
                price_filter["$gte"] = filters.min_price
            if filters.max_price:
                price_filter["$lte"] = filters.max_price
            pinecone_filter["price"] = price_filter
        
        # Property type
        if filters.property_type:
            pinecone_filter["property_type"] = {"$eq": filters.property_type.value}
        
        # Bedrooms
        if filters.bedrooms:
            pinecone_filter["bedrooms"] = {"$eq": filters.bedrooms}
        
        # City
        if filters.city:
            pinecone_filter["city"] = {"$eq": filters.city}
        
        return pinecone_filter if pinecone_filter else None
    
    async def _enrich_with_property_details(
        self, 
        vector_results: List[Tuple[str, float, Dict[str, Any]]]
    ) -> List[Tuple[Property, float, Dict[str, Any]]]:
        """Get full property details for vector search results"""
        
        enriched_results = []
        
        for property_id, score, metadata in vector_results:
            try:
                # Convert property_id to listing_number for lookup
                listing_number = int(property_id)
                property_obj = await self.property_service.get_property_by_listing_number(listing_number)
                
                if property_obj:
                    enriched_results.append((property_obj, score, metadata))
                else:
                    logger.warning(f"Property {property_id} not found in database")
                    
            except Exception as e:
                logger.warning(f"Error fetching property {property_id}: {e}")
                continue
        
        logger.info(f"Enriched {len(enriched_results)} properties with full details")
        return enriched_results
    
    def _apply_enhanced_filters(
        self, 
        enriched_results: List[Tuple[Property, float, Dict[str, Any]]], 
        filters
    ) -> List[Tuple[Property, float, Dict[str, Any]]]:
        """Apply additional filters that weren't applied in vector search"""
        
        if not filters:
            return enriched_results
        
        filtered_results = []
        
        for property_obj, vector_score, metadata in enriched_results:
            # Apply filters not handled by Pinecone
            if filters.bathrooms and property_obj.bathrooms < filters.bathrooms:
                continue
            
            if filters.min_area and property_obj.area < filters.min_area:
                continue
            
            if filters.max_area and property_obj.area > filters.max_area:
                continue
            
            if filters.neighborhood and filters.neighborhood.lower() not in property_obj.location.neighborhood.lower():
                continue
            
            if filters.status and property_obj.status != filters.status:
                continue
            
            filtered_results.append((property_obj, vector_score, metadata))
        
        logger.info(f"Applied enhanced filters: {len(filtered_results)} properties remaining")
        return filtered_results
    
    async def _calculate_enhanced_scores(
        self, 
        filtered_results: List[Tuple[Property, float, Dict[str, Any]]], 
        search_request: PropertySearchRequest
    ) -> List[SearchResult]:
        """Calculate multi-dimensional scoring for final ranking"""
        
        scored_results = []
        
        for property_obj, vector_score, metadata in filtered_results:
            # 1. Vector similarity score (40% weight)
            normalized_vector_score = vector_score * 100  # Convert to 0-100 scale
            
            # 2. Metadata match score (30% weight)
            metadata_score = self._calculate_metadata_match_score(property_obj, search_request)
            
            # 3. Distance/location score (30% weight)
            distance_score = self._calculate_distance_score(property_obj, search_request)
            
            # Calculate weighted final score
            final_score = (
                normalized_vector_score * 0.4 +
                metadata_score * 0.3 +
                distance_score * 0.3
            )
            
            scored_results.append(SearchResult(
                property=property_obj,
                vector_score=normalized_vector_score,
                metadata_match_score=metadata_score,
                distance_score=distance_score,
                final_score=final_score
            ))
        
        return scored_results
    
    def _calculate_metadata_match_score(self, property_obj: Property, search_request: PropertySearchRequest) -> float:
        """Calculate score based on how well property matches search criteria"""
        
        score = 50.0  # Base score
        query = search_request.query.lower()
        
        # Bedroom match
        if "bedroom" in query:
            try:
                import re
                bedroom_matches = re.findall(r'(\d+)\s*bedroom', query)
                if bedroom_matches:
                    requested_bedrooms = int(bedroom_matches[0])
                    if property_obj.bedrooms == requested_bedrooms:
                        score += 20
                    elif abs(property_obj.bedrooms - requested_bedrooms) <= 1:
                        score += 10
            except:
                pass
        
        # Property type match
        if property_obj.type.value.lower() in query:
            score += 15
        
        # Location preferences
        location_terms = ["southern suburbs", "city center", "waterfront", "mountain", "sea"]
        for term in location_terms:
            if term in query:
                if term.replace(" ", "").lower() in property_obj.location.neighborhood.lower().replace(" ", ""):
                    score += 15
                    break
        
        # Features match
        feature_terms = ["pool", "garden", "garage", "security", "fiber", "solar"]
        for term in feature_terms:
            if term in query:
                if any(term in feature.lower() for feature in property_obj.features):
                    score += 10
        
        return min(score, 100.0)
    
    def _calculate_distance_score(self, property_obj: Property, search_request: PropertySearchRequest) -> float:
        """Calculate score based on proximity to desired amenities"""
        
        score = 50.0  # Base score
        query = search_request.query.lower()
        
        # Check for proximity preferences in query
        proximity_terms = {
            "school": ["education", "school"],
            "hospital": ["health", "hospital", "medical"],
            "shop": ["food", "shopping", "mall"],
            "transport": ["transport", "station", "taxi"]
        }
        
        for query_term, poi_categories in proximity_terms.items():
            if query_term in query or "near" in query:
                # Find closest POI in relevant categories
                min_distance = float('inf')
                for poi in property_obj.points_of_interest:
                    if any(cat in poi.category.lower() for cat in poi_categories):
                        min_distance = min(min_distance, poi.distance)
                
                if min_distance < float('inf'):
                    # Score based on distance (closer = better)
                    if min_distance <= 1.0:  # Within 1km
                        score += 20
                    elif min_distance <= 2.0:  # Within 2km
                        score += 15
                    elif min_distance <= 5.0:  # Within 5km
                        score += 10
        
        return min(score, 100.0)
    
    async def _fallback_search(self, search_request: PropertySearchRequest) -> PropertySearchResponse:
        """Fallback to basic search when vector search is unavailable"""
        
        logger.info("Using fallback search method")
        
        # Get properties using basic filtering
        properties = await self.property_service.get_properties(
            skip=(search_request.page - 1) * search_request.page_size,
            limit=search_request.page_size,
            filters=search_request.filters
        )
        
        # Add basic scores
        for prop in properties:
            prop.searchScore = self._calculate_basic_fallback_score(prop, search_request.query)
        
        return PropertySearchResponse(
            properties=properties,
            searchTerm=search_request.query,
            totalResults=len(properties),
            page=search_request.page,
            pageSize=search_request.page_size,
            totalPages=1,
            hasNext=False,
            hasPrevious=False
        )
    
    def _calculate_basic_fallback_score(self, property_obj: Property, query: str) -> int:
        """Basic scoring for fallback search"""
        
        if not query.strip():
            return 75
        
        score = 50
        query_lower = query.lower()
        
        if query_lower in property_obj.title.lower():
            score += 25
        
        if query_lower in property_obj.description.lower():
            score += 15
        
        if query_lower in property_obj.location.city.lower():
            score += 10
        
        return min(score, 100) 