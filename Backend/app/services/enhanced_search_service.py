"""
Enhanced Search Service for PropMatch Phase 2 - High Performance Version
Optimized for speed with batch queries and minimal data transfer
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from app.models.property import PropertySearchRequest, PropertySearchResponse, Property
from app.services.supabase_property_service import SupabasePropertyService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Lightweight search result"""
    property: Property
    final_score: float

class EnhancedSearchService:
    """High-performance search service optimized for speed"""
    
    def __init__(self):
        self.property_service = SupabasePropertyService()
        self.vector_service = VectorService()
    
    async def search_properties(self, search_request: PropertySearchRequest) -> PropertySearchResponse:
        """Optimized main search method"""
        try:
            # Phase 1: Fast vector search
            vector_results = await self._fast_vector_search(search_request)
            
            if not vector_results:
                logger.warning(f"No vector results found for query: {search_request.query}")
                return await self._fast_fallback_search(search_request)
            
            # Phase 2: Batch fetch properties (MAJOR OPTIMIZATION)
            properties = await self._batch_fetch_properties(vector_results, search_request)
            
            if not properties:
                logger.info(f"No properties found for query: {search_request.query}")
                return PropertySearchResponse(
                    properties=[],
                    totalResults=0,
                    searchTerm=search_request.query,
                    page=search_request.page,
                    pageSize=search_request.page_size,
                    totalPages=0,
                    hasNext=False,
                    hasPrevious=False
                )
            
            # Phase 3: Fast scoring and ranking
            scored_properties = self._fast_score_and_rank(properties, vector_results, search_request)
            
            # Phase 4: Pagination
            total_results = len(scored_properties)
            total_pages = (total_results + search_request.page_size - 1) // search_request.page_size
            
            start_idx = (search_request.page - 1) * search_request.page_size
            end_idx = start_idx + search_request.page_size
            paginated_properties = scored_properties[start_idx:end_idx]
            
            logger.info(f"Fast search completed: {len(paginated_properties)} properties returned in optimized pipeline")
            
            return PropertySearchResponse(
                properties=paginated_properties,
                totalResults=total_results,
                searchTerm=search_request.query,
                page=search_request.page,
                pageSize=search_request.page_size,
                totalPages=total_pages,
                hasNext=search_request.page < total_pages,
                hasPrevious=search_request.page > 1
            )
            
        except Exception as e:
            logger.error(f"Fast search failed: {e}")
            import traceback
            traceback.print_exc()
            return await self._fast_fallback_search(search_request)
    
    async def _fast_vector_search(self, search_request: PropertySearchRequest) -> List[Tuple[str, float]]:
        """Optimized vector search with minimal data"""
        
        # Simple query without heavy processing
        query = search_request.query
        
        # Fast vector search
        vector_results = await self.vector_service.search_similar_properties(
            query=query,
            top_k=min(100, search_request.page_size * 5),  # Reduced candidates for speed
            filter_dict=self._fast_build_filters(search_request.filters)
        )
        
        # Return simplified tuples (id, score)
        simple_results = [(prop_id, score) for prop_id, score, _ in vector_results]
        
        logger.info(f"Fast vector search returned {len(simple_results)} candidates")
        return simple_results
    
    def _fast_build_filters(self, filters) -> Optional[Dict[str, Any]]:
        """Fast filter building"""
        if not filters:
            return None
        
        pinecone_filter = {}
        
        # Only essential filters for speed
        if filters.property_type:
            pinecone_filter["property_type"] = {"$eq": filters.property_type.value}
        
        if filters.bedrooms:
            pinecone_filter["bedrooms"] = {"$eq": filters.bedrooms}
        
        return pinecone_filter if pinecone_filter else None
    
    async def _batch_fetch_properties(
        self, 
        vector_results: List[Tuple[str, float]], 
        search_request: PropertySearchRequest
    ) -> List[Property]:
        """MAJOR OPTIMIZATION: Batch fetch all properties at once"""
        
        property_ids = [int(prop_id) for prop_id, _ in vector_results]
        
        # Single batch query instead of N individual queries
        properties = await self.property_service.get_properties_batch(property_ids)
        
        # Apply any remaining filters
        if search_request.filters:
            properties = [p for p in properties if self._fast_filter_check(p, search_request.filters)]
        
        logger.info(f"Batch fetched {len(properties)} properties")
        return properties
    
    def _fast_filter_check(self, property_obj: Property, filters) -> bool:
        """Lightning-fast filter check"""
        if not filters:
            return True
        
        # Essential filters only
        if filters.property_type and property_obj.type.value.lower() != filters.property_type.lower():
            return False
        
        if filters.min_price and property_obj.price < filters.min_price:
            return False
        if filters.max_price and property_obj.price > filters.max_price:
            return False
        
        if filters.bedrooms:
            try:
                if int(property_obj.bedrooms or 0) != filters.bedrooms:
                    return False
            except:
                pass
        
        return True
    
    def _fast_score_and_rank(
        self, 
        properties: List[Property], 
        vector_results: List[Tuple[str, float]], 
        search_request: PropertySearchRequest
    ) -> List[Property]:
        """Ultra-fast scoring with proper vector score normalization"""
        
        # Create lookup for vector scores
        vector_scores = {prop_id: score for prop_id, score in vector_results}
        
        # Analyze vector score distribution for proper normalization
        all_vector_scores = [score for _, score in vector_results]
        if all_vector_scores:
            min_vector_score = min(all_vector_scores)
            max_vector_score = max(all_vector_scores)
            vector_range = max_vector_score - min_vector_score
        else:
            min_vector_score, max_vector_score, vector_range = 0.6, 0.95, 0.35
        
        scored_properties = []
        query_lower = search_request.query.lower()
        
        for prop in properties:
            # Get base vector score
            raw_vector_score = vector_scores.get(str(prop.listing_number), 0.7)
            
            # PROPER NORMALIZATION: Map vector scores to realistic 20-75% range
            if vector_range > 0:
                normalized_vector = ((raw_vector_score - min_vector_score) / vector_range)
            else:
                normalized_vector = 0.5
            
            # Scale to 20-75% base range (more realistic for semantic similarity)
            base_score = 20 + (normalized_vector * 55)  # 20% to 75%
            
            # Calculate bonuses (smaller and more realistic)
            bonus = self._calculate_realistic_bonuses(prop, query_lower)
            
            # Add meaningful variance based on property characteristics
            variance = self._calculate_property_variance(prop, query_lower)
            
            # Final score calculation - NEVER above 100%
            final_score = base_score + bonus + variance
            final_score = min(final_score, 100.0)  # Hard cap at 100%
            final_score = max(final_score, 15.0)   # Minimum viable match
            
            # Round to 1 decimal place for clean presentation
            final_score = round(final_score, 1)
            
            # Assign score to property
            prop.searchScore = final_score
            scored_properties.append(prop)
        
        # Sort by score (highest first)
        scored_properties.sort(key=lambda x: x.searchScore, reverse=True)
        
        return scored_properties
    
    def _calculate_realistic_bonuses(self, property_obj: Property, query_lower: str) -> float:
        """Calculate smaller, more realistic bonuses"""
        bonus = 0.0
        
        # Bedroom matching (worth up to +15% instead of +25%)
        if 'bedroom' in query_lower:
            try:
                if str(property_obj.bedrooms) in query_lower:
                    bonus += 15.0  # Perfect bedroom match
                elif property_obj.bedrooms:
                    # Partial bonus for close matches
                    import re
                    bedroom_match = re.search(r'(\d+)\s*bedroom', query_lower)
                    if bedroom_match:
                        requested_beds = int(bedroom_match.group(1))
                        prop_beds = int(property_obj.bedrooms)
                        if abs(prop_beds - requested_beds) == 1:
                            bonus += 8.0  # Close match
            except:
                pass
        
        # Property type matching (worth up to +12% instead of +20%)
        if property_obj.type.value.lower() in query_lower:
            bonus += 12.0
        
        # Location bonus (worth up to +10% instead of +15%)
        location_text = f"{property_obj.location.neighborhood} {property_obj.location.city}".lower()
        location_keywords = ['clifton', 'camps bay', 'bantry bay', 'sea point', 'newlands', 
                           'claremont', 'rondebosch', 'constantia', 'southern suburbs']
        
        for location in location_keywords:
            if location in query_lower and location in location_text:
                bonus += 10.0
                break
        
        # Feature bonuses (smaller bonuses: +1.5% each instead of +2%)
        if property_obj.features:
            feature_words = ['pool', 'garden', 'garage', 'security', 'view']
            for word in feature_words:
                if word in query_lower and any(word.lower() in f.lower() for f in property_obj.features):
                    bonus += 1.5
        
        # Price matching bonus (worth up to +8% instead of +15%)
        if 'under' in query_lower and 'million' in query_lower:
            try:
                import re
                price_match = re.search(r'under\s+(\d+)\s*million', query_lower)
                if price_match:
                    price_limit = float(price_match.group(1)) * 1000000
                    if property_obj.price <= price_limit:
                        bonus += 8.0  # Within budget
                    elif property_obj.price <= price_limit * 1.15:  # Within 15%
                        bonus += 4.0  # Close to budget
            except:
                pass
        
        return min(bonus, 25.0)  # Cap bonuses at +25% total
    
    def _calculate_property_variance(self, property_obj: Property, query_lower: str) -> float:
        """Add meaningful variance based on property characteristics"""
        variance = 0.0
        
        # Price-based variance (luxury properties get slight boost)
        if property_obj.price > 10000000:  # 10M+
            variance += 2.0
        elif property_obj.price > 5000000:   # 5-10M
            variance += 1.0
        elif property_obj.price < 1000000:   # Under 1M
            variance -= 1.0
        
        # Feature richness variance
        if property_obj.features:
            feature_count = len(property_obj.features)
            if feature_count > 15:
                variance += 1.5
            elif feature_count > 10:
                variance += 1.0
            elif feature_count < 5:
                variance -= 0.5
        
        # POI richness variance
        if property_obj.points_of_interest:
            poi_count = len(property_obj.points_of_interest)
            if poi_count > 20:
                variance += 1.0
            elif poi_count > 15:
                variance += 0.5
            elif poi_count < 5:
                variance -= 0.5
        
        # Add small random component for uniqueness (smaller range)
        import random
        random.seed(hash(str(property_obj.id)))
        random_factor = random.uniform(-0.8, 0.8)  # Smaller random range
        variance += random_factor
        
        return variance
    
    async def _fast_fallback_search(self, search_request: PropertySearchRequest) -> PropertySearchResponse:
        """Fast fallback search"""
        
        logger.info("Using fast fallback search")
        
        # Quick property fetch
        properties = await self.property_service.get_properties(
            skip=(search_request.page - 1) * search_request.page_size,
            limit=search_request.page_size,
            filters=search_request.filters
        )
        
        # Simple scoring
        for prop in properties:
            prop.searchScore = round(75.0 + (hash(str(prop.id)) % 20), 1)
        
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
        """Calculate comprehensive scores as true percentages (0-100) with decimal precision"""
        
        scored_results = []
        
        for property_obj, vector_score, metadata in filtered_results:
            # Start with vector score as base percentage (0-100)
            # Pinecone returns 0-1, convert to 0-100
            base_score = vector_score * 100
            
            # Quick metadata bonuses (simplified for speed)
            metadata_bonus = self._calculate_quick_metadata_bonus(property_obj, search_request)
            
            # Quick location bonus (simplified for speed)  
            location_bonus = self._calculate_quick_location_bonus(property_obj, search_request)
            
            # Calculate final score as true percentage
            final_score = base_score + metadata_bonus + location_bonus
            
            # Cap at 100% but allow high scores for good matches
            final_score = min(final_score, 100.0)
            
            # Ensure minimum score for returned results
            final_score = max(final_score, 15.0)
            
            # Add tiny random component for uniqueness (0.01-0.99)
            import random
            random.seed(hash(property_obj.id))  # Consistent per property
            uniqueness_factor = random.uniform(0.01, 0.99)
            final_score = round(final_score + uniqueness_factor, 1)  # 1 decimal place
            
            scored_results.append(SearchResult(
                property=property_obj,
                final_score=final_score
            ))
        
        return scored_results
    
    def _calculate_quick_metadata_bonus(self, property_obj: Property, search_request: PropertySearchRequest) -> float:
        """Fast metadata matching with significant bonuses for good matches"""
        bonus = 0.0
        query_lower = search_request.query.lower()
        
        # Bedroom matching (worth up to +25%)
        if any(word in query_lower for word in ['bedroom', 'bed', 'br']):
            import re
            bedroom_match = re.search(r'(\d+)\s*(?:bed|bedroom|br)', query_lower)
            if bedroom_match:
                requested_beds = int(bedroom_match.group(1))
                try:
                    prop_beds = int(property_obj.bedrooms) if property_obj.bedrooms else 0
                    if prop_beds == requested_beds:
                        bonus += 25.0  # Perfect bedroom match
                    elif abs(prop_beds - requested_beds) == 1:
                        bonus += 15.0  # Close match
                except:
                    pass
        
        # Property type matching (worth up to +20%)
        type_keywords = {
            'apartment': ['apartment', 'flat', 'unit'],
            'house': ['house', 'home', 'villa'],
            'townhouse': ['townhouse', 'town house']
        }
        
        for prop_type, keywords in type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                if property_obj.type.value.lower() == prop_type:
                    bonus += 20.0
                break
        
        # Price range matching (worth up to +15%)
        if 'under' in query_lower or 'below' in query_lower:
            import re
            price_match = re.search(r'(?:under|below)\s+(?:r\s*)?(\d+(?:\.\d+)?)\s*(?:million|mil|m)', query_lower)
            if price_match:
                try:
                    price_limit = float(price_match.group(1)) * 1000000
                    if property_obj.price <= price_limit:
                        bonus += 15.0  # Within price range
                    elif property_obj.price <= price_limit * 1.2:  # Within 20%
                        bonus += 8.0
                except:
                    pass
        
        # Feature matching (worth up to +10% total)
        feature_keywords = ['pool', 'garden', 'garage', 'parking', 'security', 'view']
        for keyword in feature_keywords:
            if keyword in query_lower:
                if property_obj.features and any(keyword.lower() in f.lower() for f in property_obj.features):
                    bonus += 2.0  # +2% per matching feature
        
        return min(bonus, 30.0)  # Cap metadata bonus at +30%
    
    def _calculate_quick_location_bonus(self, property_obj: Property, search_request: PropertySearchRequest) -> float:
        """Fast location scoring with bonuses for area matches"""
        bonus = 0.0
        query_lower = search_request.query.lower()
        
        # Specific location mentions (worth up to +15%)
        location_keywords = [
            'clifton', 'camps bay', 'bantry bay', 'sea point', 'newlands', 
            'claremont', 'rondebosch', 'constantia', 'southern suburbs', 
            'northern suburbs', 'city bowl', 'atlantic seaboard'
        ]
        
        prop_location = f"{property_obj.location.neighborhood} {property_obj.location.city}".lower()
        
        for location in location_keywords:
            if location in query_lower:
                if location in prop_location or any(word in prop_location for word in location.split()):
                    bonus += 15.0  # Perfect location match
                    break
        
        # Proximity keywords (worth up to +10%)
        proximity_keywords = ['near', 'close to', 'walking distance']
        if any(keyword in query_lower for keyword in proximity_keywords):
            # Simple bonus if property has good POI coverage
            if property_obj.points_of_interest and len(property_obj.points_of_interest) > 10:
                bonus += 10.0
            elif property_obj.points_of_interest and len(property_obj.points_of_interest) > 5:
                bonus += 5.0
        
        return min(bonus, 20.0)  # Cap location bonus at +20%
    
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
    
    def _calculate_basic_fallback_score(self, property_obj: Property, query: str) -> float:
        """Basic scoring for fallback search - return as decimal percentage"""
        
        if not query.strip():
            return 75.0
        
        score = 50.0
        query_lower = query.lower()
        
        if query_lower in property_obj.title.lower():
            score += 25.0
        
        if query_lower in property_obj.description.lower():
            score += 15.0
        
        if query_lower in property_obj.location.city.lower():
            score += 10.0
        
        # Add uniqueness
        import random
        random.seed(hash(property_obj.id))
        uniqueness_factor = random.uniform(0.01, 0.99)
        
        return round(min(score + uniqueness_factor, 100.0), 1) 