"""
Enhanced Search Service for PropMatch Phase 2 - High Performance Version
Optimized for speed with batch queries and minimal data transfer
"""

import logging
import asyncio
import time
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np

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
        """Hybrid property-retrieval scoring: semantic similarity + property context intelligence"""
        
        # Create lookup for vector scores
        vector_scores = {prop_id: score for prop_id, score in vector_results}
        
        if not vector_scores:
            return []
        
        # Analyze query for property retrieval context
        query_context = self._analyze_property_query_context(search_request.query)
        
        # Analyze vector scores for normalization
        all_vector_scores = [score for _, score in vector_results]
        min_vector = min(all_vector_scores)
        max_vector = max(all_vector_scores)
        vector_range = max_vector - min_vector if max_vector > min_vector else 0.1
        
        scored_properties = []
        
        for prop in properties:
            raw_vector_score = vector_scores.get(str(prop.listing_number), 0.5)
            
            # Apply property-context aware scoring
            final_score = self._apply_property_context_scoring(
                prop, raw_vector_score, all_vector_scores, query_context
            )
            
            # Hard constraints
            final_score = min(final_score, 100.0)
            final_score = max(final_score, 15.0)
            final_score = round(final_score, 1)
            
            # Assign score to property  
            prop.searchScore = final_score
            scored_properties.append(prop)
        
        # Sort by score (highest first)
        scored_properties.sort(key=lambda x: x.searchScore, reverse=True)
        
        return scored_properties
    
    def _analyze_property_query_context(self, query: str) -> Dict[str, Any]:
        """Analyze query for property-specific context vs general semantic search"""
        query_lower = query.lower()
        
        context = {
            'is_property_focused': True,
            'impossibility_penalty': 0.0,
            'core_property_terms': [],
            'unrealistic_combinations': [],
            'price_constraints': [],
            'location_terms': []
        }
        
        # Core property terms that should exist in real estate
        property_terms = {
            'types': ['apartment', 'house', 'flat', 'townhouse', 'villa', 'property'],
            'rooms': ['bedroom', 'bathroom', 'bed', 'bath'],
            'features': ['pool', 'garden', 'garage', 'balcony', 'view', 'parking'],
            'locations': ['area', 'neighborhood', 'district', 'suburb', 'city', 'cbd', 'centre', 'center'],
            'descriptors': ['luxury', 'modern', 'spacious', 'furnished', 'unfurnished'],
            'proximity': ['walking distance', 'close to', 'near', 'uct', 'waterfront', 'v&a'],
            'price': ['under', 'below', 'over', 'above', 'million', 'rand', 'budget', 'cheap', 'expensive']
        }
        
        # Extract all relevant terms (including price and location terms)
        property_term_count = 0
        for category, terms in property_terms.items():
            for term in terms:
                if term in query_lower:
                    context['core_property_terms'].append(term)
                    property_term_count += 1
                    
                    # Categorize for constraint enforcement
                    if category == 'price':
                        context['price_constraints'].append(term)
                    elif category == 'locations' or category == 'proximity':
                        context['location_terms'].append(term)
        
        # Add the full query for constraint parsing
        context['core_property_terms'].append(query_lower)
        
        # Detect impossible/unrealistic property concepts
        impossible_terms = [
            'castle', 'moat', 'medieval', 'underwater', 'submarine', 'spaceship',
            'pyramid', 'temple', 'church', 'cathedral', 'palace', 'fortress',
            'eiffel tower', 'flying', 'floating', 'underground mansion'
        ]
        
        impossible_count = 0
        for term in impossible_terms:
            if term in query_lower:
                context['unrealistic_combinations'].append(term)
                impossible_count += 1
        
        # Calculate impossibility penalty based on ratio
        total_terms = len(query_lower.split())
        if total_terms > 0:
            impossible_ratio = impossible_count / total_terms
            property_ratio = property_term_count / total_terms
            
            # Strong penalty if query is mostly impossible terms with few property terms
            if impossible_ratio > 0.3 and property_ratio < 0.3:
                context['impossibility_penalty'] = 0.6  # 60% penalty
            elif impossible_ratio > 0.2:
                context['impossibility_penalty'] = 0.3  # 30% penalty
            elif impossible_ratio > 0.1:
                context['impossibility_penalty'] = 0.15  # 15% penalty
        
        context['is_property_focused'] = property_ratio > impossible_ratio
        
        return context
    
    def _apply_property_context_scoring(
        self, 
        prop: Property, 
        raw_vector_score: float, 
        all_vector_scores: List[float],
        query_context: Dict[str, Any]
    ) -> float:
        """Apply property-context aware scoring that properly enforces constraints and leverages POI data"""
        
        min_vector = min(all_vector_scores)
        max_vector = max(all_vector_scores)
        vector_range = max_vector - min_vector if max_vector > min_vector else 0.1
        
        # Normalize vector score to 20-100% range (removed artificial 95% cap)
        normalized_vector = (raw_vector_score - min_vector) / vector_range if vector_range > 0 else 0.5
        base_score = 20 + (normalized_vector * 80)  # 20% to 100% range
        
        # Apply impossibility penalty - this is key for property retrieval vs semantic similarity
        if query_context['impossibility_penalty'] > 0:
            penalty_factor = 1.0 - query_context['impossibility_penalty']
            base_score *= penalty_factor
            
            # Additional penalty for high vector scores on impossible queries
            if base_score > 70 and query_context['impossibility_penalty'] > 0.3:
                base_score *= 0.5  # Further 50% reduction
        
        # CRITICAL: Apply hard constraint penalties using actual property data
        base_score = self._apply_hard_constraints(prop, query_context, base_score)
        
        # Apply proximity bonuses using actual POI distance data
        base_score = self._apply_proximity_bonuses(prop, query_context, base_score)
        
        # Apply minimal core criteria penalties (bedroom/type mismatches)
        final_score = self._apply_core_criteria_only(prop, ' '.join(query_context['core_property_terms']), base_score)
        
        return final_score
    
    def _apply_hard_constraints(self, prop: Property, query_context: Dict[str, Any], current_score: float) -> float:
        """Apply hard constraints that must be satisfied - price, location, etc."""
        
        query_lower = ' '.join(query_context['core_property_terms']).lower()
        
        # PRICE CONSTRAINTS - These must be strictly enforced
        import re
        
        # "under X million" or "below X million" patterns
        price_under_match = re.search(r'(?:under|below|less than)\s+(\d+(?:\.\d+)?)\s*(?:million|mil|m)', query_lower)
        if price_under_match:
            price_limit = float(price_under_match.group(1)) * 1000000
            if prop.price > price_limit:
                # MAJOR penalty for exceeding price limit
                current_score *= 0.3  # Reduce to 30% for price violations
        
        # "over X million" or "above X million" patterns  
        price_over_match = re.search(r'(?:over|above|more than)\s+(\d+(?:\.\d+)?)\s*(?:million|mil|m)', query_lower)
        if price_over_match:
            price_minimum = float(price_over_match.group(1)) * 1000000
            if prop.price < price_minimum:
                current_score *= 0.3  # Major penalty for being under minimum
        
        # GEOGRAPHIC CONSTRAINTS - Detect impossible locations
        impossible_locations = [
            'johannesburg', 'joburg', 'jozi', 'gauteng',
            'durban', 'kwazulu', 'natal', 
            'pretoria', 'tshwane',
            'bloemfontein', 'free state',
            'port elizabeth', 'gqeberha', 'eastern cape',
            'polokwane', 'limpopo',
            'kimberley', 'northern cape',
            'nelspruit', 'mbombela', 'mpumalanga',
            'rustenburg', 'north west',
            'london', 'new york', 'paris', 'dubai'
        ]
        
        for location in impossible_locations:
            if location in query_lower:
                # Heavy penalty for impossible geographic requests
                current_score *= 0.2  # Reduce to 20% for impossible locations
                break
        
        return current_score
    
    def _apply_proximity_bonuses(self, prop: Property, query_context: Dict[str, Any], current_score: float) -> float:
        """Apply proximity bonuses using actual POI distance data"""
        
        query_lower = ' '.join(query_context['core_property_terms']).lower()
        
        if not prop.points_of_interest:
            return current_score
        
        # UCT proximity detection and scoring
        if any(term in query_lower for term in ['uct', 'university of cape town', 'university cape town']):
            uct_pois = [
                poi for poi in prop.points_of_interest 
                if 'uct' in poi.name.lower() or 
                   ('university' in poi.name.lower() and 'cape town' in poi.name.lower()) or
                   'university of cape town' in poi.name.lower()
            ]
            
            if uct_pois:
                closest_uct = min(uct_pois, key=lambda x: x.distance)
                uct_distance = closest_uct.distance
                
                # Determine if "walking distance" was specified
                walking_requested = any(term in query_lower for term in [
                    'walking distance', 'walk to', 'walkable', 'walking'
                ])
                
                if walking_requested:
                    # Strict walking distance criteria (realistic walking in Cape Town)
                    if uct_distance <= 1.0:  # Within 1km = excellent walking distance
                        current_score *= 1.4  # 40% bonus
                    elif uct_distance <= 1.5:  # 1-1.5km = good walking distance  
                        current_score *= 1.25  # 25% bonus
                    elif uct_distance <= 2.0:  # 1.5-2km = manageable walk
                        current_score *= 1.1   # 10% bonus
                    else:  # > 2km = not really walking distance
                        current_score *= 0.7   # 30% penalty for false claims
                else:
                    # Just "close to UCT" without walking specified
                    if uct_distance <= 2.0:
                        current_score *= 1.2   # 20% bonus for being close
                    elif uct_distance <= 4.0:
                        current_score *= 1.1   # 10% bonus for reasonable distance
        
        # V&A Waterfront proximity
        if any(term in query_lower for term in ['v&a', 'waterfront', 'v and a']):
            waterfront_pois = [
                poi for poi in prop.points_of_interest 
                if 'waterfront' in poi.name.lower() or 'v&a' in poi.name.lower()
            ]
            
            if waterfront_pois:
                closest_waterfront = min(waterfront_pois, key=lambda x: x.distance)
                if closest_waterfront.distance <= 2.0:
                    current_score *= 1.15  # 15% bonus for waterfront proximity
        
        # CBD proximity
        if any(term in query_lower for term in ['cbd', 'city centre', 'city center', 'downtown']):
            # Properties already in CBD areas should get bonus
            cbd_areas = ['cape town city centre', 'foreshore', 'city bowl']
            if any(area in prop.location.neighborhood.lower() for area in cbd_areas):
                current_score *= 1.1  # 10% bonus for being in CBD
        
        return current_score
    
    def _apply_core_criteria_only(self, prop: Property, query_lower: str, base_score: float) -> float:
        """Apply only essential criteria enforcement - trust the vector for everything else"""
        
        # Bedroom enforcement - ONLY if explicitly mentioned
        import re
        bedroom_match = re.search(r'(\d+)\s*(?:bed|bedroom)', query_lower)
        if bedroom_match:
            requested_beds = int(bedroom_match.group(1))
            try:
                prop_beds = int(prop.bedrooms) if prop.bedrooms else 0
                if prop_beds != requested_beds:
                    # Moderate penalty - the vector should handle most of this
                    base_score *= 0.7  # 30% penalty for bedroom mismatch
            except:
                pass
        
        # Property type enforcement - ONLY if explicitly mentioned  
        type_keywords = ['apartment', 'flat', 'house', 'townhouse']
        mentioned_type = None
        for keyword in type_keywords:
            if keyword in query_lower:
                mentioned_type = keyword
                break
        
        if mentioned_type:
            prop_type = prop.type.value.lower()
            # Allow some flexibility in type matching
            type_matches = {
                'apartment': ['apartment', 'flat'],
                'flat': ['apartment', 'flat'], 
                'house': ['house', 'villa'],
                'townhouse': ['townhouse', 'town house']
            }
            
            expected_types = type_matches.get(mentioned_type, [mentioned_type])
            if not any(t in prop_type for t in expected_types):
                # Light penalty - let vector handle semantic similarity
                base_score *= 0.85  # 15% penalty for type mismatch
        
        return base_score
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze query to understand user intent and extract specific requirements"""
        query_lower = query.lower()
        
        analysis = {
            'is_specific': False,
            'requested_features': [],
            'proximity_terms': [],
            'quality_terms': [],
            'price_constraints': [],
            'impossible_combinations': []
        }
        
        # Detect specific feature requests
        feature_keywords = {
            'pool': ['pool', 'swimming pool'],
            'garden': ['garden', 'yard', 'outdoor space'],
            'garage': ['garage', 'parking', 'carport'],
            'view': ['view', 'sea view', 'ocean view', 'mountain view', 'table mountain'],
            'balcony': ['balcony', 'terrace', 'patio'],
            'security': ['security', 'secure', 'gated'],
            'modern': ['modern', 'contemporary', 'newly renovated'],
            'luxury': ['luxury', 'luxurious', 'upmarket', 'high-end']
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                analysis['requested_features'].append(feature)
                analysis['is_specific'] = True
        
        # Detect proximity requirements with distance sensitivity
        proximity_patterns = {
            'walking_distance': ['walking distance', 'walk to', 'walkable'],
            'close_to': ['close to', 'near', 'nearby', 'next to'],
            'within': ['within', 'less than', 'under']
        }
        
        for prox_type, keywords in proximity_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                analysis['proximity_terms'].append(prox_type)
                analysis['is_specific'] = True
        
        # Detect quality/price terms
        if any(term in query_lower for term in ['luxury', 'upmarket', 'premium', 'high-end']):
            analysis['quality_terms'].append('luxury')
            analysis['is_specific'] = True
        
        if any(term in query_lower for term in ['affordable', 'budget', 'cheap', 'under']):
            analysis['quality_terms'].append('budget')
            analysis['is_specific'] = True
        
        # Detect impossible/conflicting combinations for Cape Town
        impossible_checks = [
            (['airport', 'walking'], ['ocean', 'sea view']),  # Airport + ocean view
            (['eiffel tower', 'paris'], ['cape town']),        # European landmarks
            (['castle', 'moat'], ['apartment', 'modern']),     # Medieval + modern
            (['underwater', 'submarine'], ['house', 'apartment']) # Impossible structures
        ]
        
        for combo1, combo2 in impossible_checks:
            has_combo1 = any(term in query_lower for term in combo1)
            has_combo2 = any(term in query_lower for term in combo2)
            if has_combo1 and has_combo2:
                analysis['impossible_combinations'].append((combo1, combo2))
        
        return analysis
    
    def _determine_scoring_scenario(self, median_score: float, std_dev: float, query_analysis: Dict) -> str:
        """Determine which of the 4 scenarios applies"""
        
        # Quality thresholds adjusted for actual vector score ranges we're seeing  
        high_quality_threshold = 0.62  # Median vector score > 0.62 (adjusted based on observations)
        high_variance_threshold = 0.04  # Standard deviation > 0.04 (tighter variance threshold)
        
        is_high_quality = median_score > high_quality_threshold
        is_high_variance = std_dev > high_variance_threshold
        
        # Check for impossible combinations (overrides quality assessment)
        has_impossible = len(query_analysis['impossible_combinations']) > 0
        
        if has_impossible:
            return "low_quality_high_variance"  # Impossible queries always low quality
        elif is_high_quality and not is_high_variance:
            return "high_quality_low_variance"   # Good simple matches
        elif is_high_quality and is_high_variance:
            return "high_quality_high_variance"  # Good specific matches
        elif not is_high_quality and not is_high_variance:
            return "low_quality_low_variance"    # Poor simple matches
        else:
            return "low_quality_high_variance"   # Poor scattered matches
    
    def _apply_scenario_scoring(
        self, 
        prop: Property, 
        raw_vector_score: float, 
        all_vector_scores: List[float],
        scenario: str,
        query_analysis: Dict
    ) -> float:
        """Apply scenario-specific scoring logic"""
        
        min_score = min(all_vector_scores)
        max_score = max(all_vector_scores)
        score_range = max_score - min_score if max_score > min_score else 0.1
        
        # Normalize vector score position (0-1)
        normalized_position = (raw_vector_score - min_score) / score_range if score_range > 0 else 0.5
        
        if scenario == "high_quality_low_variance":
            # Simple query with good matches - high scores, tight distribution
            base_score = 75 + (normalized_position * 20)  # 75-95%
            bonus = self._calculate_targeted_bonuses(prop, query_analysis, max_bonus=5)
            
        elif scenario == "high_quality_high_variance":
            # Specific query with good matches - wide distribution, high top scores
            base_score = 40 + (normalized_position * 50)  # 40-90%
            bonus = self._calculate_targeted_bonuses(prop, query_analysis, max_bonus=15)
            
        elif scenario == "low_quality_low_variance":
            # Simple query, poor matches - low scores, tight distribution
            base_score = 20 + (normalized_position * 15)  # 20-35%
            bonus = self._calculate_targeted_bonuses(prop, query_analysis, max_bonus=3)
            
        else:  # low_quality_high_variance
            # Impossible/conflicting query - wide distribution, all low scores
            base_score = 15 + (normalized_position * 25)  # 15-40%
            bonus = self._calculate_targeted_bonuses(prop, query_analysis, max_bonus=5)
        
        # Add small variance for uniqueness
        import random
        random.seed(hash(str(prop.id)))
        variance = random.uniform(-1.5, 1.5)
        
        final_score = base_score + bonus + variance
        
        # Hard constraints
        final_score = min(final_score, 100.0)
        final_score = max(final_score, 15.0)
        
        return round(final_score, 1)
    
    def _calculate_targeted_bonuses(self, prop: Property, query_analysis: Dict, max_bonus: float) -> float:
        """Calculate bonuses ONLY for specifically requested features"""
        bonus = 0.0
        bonus_per_feature = max_bonus / max(len(query_analysis['requested_features']) + 1, 1)
        
        # Only award bonuses for explicitly requested features
        for requested_feature in query_analysis['requested_features']:
            if self._property_has_feature(prop, requested_feature):
                bonus += bonus_per_feature
        
        # Proximity bonuses only if specifically requested
        if query_analysis['proximity_terms'] and prop.points_of_interest:
            # Award bonus based on POI richness if proximity was requested
            poi_count = len(prop.points_of_interest)
            if poi_count > 15:
                bonus += bonus_per_feature * 0.5  # Half bonus for proximity
        
        return min(bonus, max_bonus)
    
    def _property_has_feature(self, prop: Property, feature: str) -> bool:
        """Check if property has a specific feature"""
        if not prop.features:
            return False
        
        feature_mappings = {
            'pool': ['pool', 'swimming'],
            'garden': ['garden', 'yard', 'landscaped'],
            'garage': ['garage', 'parking', 'carport'],
            'view': ['view', 'sea', 'ocean', 'mountain'],
            'balcony': ['balcony', 'terrace', 'patio'],
            'security': ['security', 'secure', 'access', 'gate'],
            'modern': ['modern', 'contemporary', 'renovated'],
            'luxury': ['luxury', 'upmarket', 'premium']
        }
        
        keywords = feature_mappings.get(feature, [feature])
        return any(keyword.lower() in ' '.join(prop.features).lower() for keyword in keywords)
    
    def _enforce_core_criteria(self, prop: Property, query: str, current_score: float) -> float:
        """Enforce core criteria - bedroom count and property type must match"""
        query_lower = query.lower()
        
        # Bedroom enforcement - this is critical
        import re
        bedroom_match = re.search(r'(\d+)\s*(?:bed|bedroom)', query_lower)
        if bedroom_match:
            requested_beds = int(bedroom_match.group(1))
            try:
                prop_beds = int(prop.bedrooms) if prop.bedrooms else 0
                if prop_beds != requested_beds:
                    # Major penalty for wrong bedroom count
                    current_score *= 0.4  # Reduce to 40% of original score
            except:
                pass
        
        # Property type enforcement
        type_keywords = {
            'apartment': ['apartment', 'flat', 'unit'],
            'house': ['house', 'home', 'villa'],
            'townhouse': ['townhouse', 'town house']
        }
        
        for prop_type, keywords in type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                if prop.type.value.lower() != prop_type:
                    # Moderate penalty for wrong property type
                    current_score *= 0.7  # Reduce to 70% of original score
                break
        
        return current_score
    
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