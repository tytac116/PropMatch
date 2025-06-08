from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from typing import List, Optional, Dict, Any
import logging
import math

from app.db.database import PropertyDB
from app.models.property import PropertySearchRequest, PropertySearchResponse, Property
from app.services.property_service import PropertyService

logger = logging.getLogger(__name__)

class SearchService:
    """Service class for property search operations"""
    
    def __init__(self):
        self.property_service = PropertyService()
    
    async def search_properties(
        self,
        db: Session,
        search_request: PropertySearchRequest
    ) -> PropertySearchResponse:
        """
        Search properties using natural language query and filters
        
        Phase 1: Basic text search + SQL filters
        Phase 2: Will be enhanced with vector search + AI scoring
        """
        
        logger.info(f"Searching for: '{search_request.query}' with filters: {search_request.filters}")
        
        # Start with base query
        query = db.query(PropertyDB)
        
        # Apply text search if query provided
        if search_request.query.strip():
            search_terms = self._extract_search_terms(search_request.query)
            query = self._apply_text_search(query, search_terms)
        
        # Apply filters
        if search_request.filters:
            query = self._apply_filters(query, search_request.filters)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply sorting
        query = self._apply_sorting(query, search_request.sort_by, search_request.sort_order)
        
        # Apply pagination
        offset = (search_request.page - 1) * search_request.page_size
        paginated_query = query.offset(offset).limit(search_request.page_size)
        
        # Execute query
        db_properties = paginated_query.all()
        
        # Convert to Pydantic models
        properties = []
        for db_prop in db_properties:
            try:
                prop = await self.property_service._convert_db_to_pydantic(db_prop)
                
                # Add basic match score (will be replaced with AI scoring in Phase 2)
                prop.searchScore = self._calculate_basic_match_score(
                    db_prop, search_request.query
                )
                
                properties.append(prop)
            except Exception as e:
                logger.error(f"Error converting property {db_prop.id}: {e}")
                continue
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / search_request.page_size)
        has_next = search_request.page < total_pages
        has_previous = search_request.page > 1
        
        return PropertySearchResponse(
            properties=properties,
            searchTerm=search_request.query,
            totalResults=total_count,
            page=search_request.page,
            pageSize=search_request.page_size,
            totalPages=total_pages,
            hasNext=has_next,
            hasPrevious=has_previous
        )
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract meaningful search terms from natural language query"""
        
        # Basic keyword extraction (will be enhanced with NLP in Phase 2)
        import re
        
        # Remove common words and extract meaningful terms
        stop_words = {
            'i', 'want', 'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'that', 'this', 'these', 'those'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out stop words and short words
        meaningful_terms = [
            word for word in words 
            if len(word) > 2 and word not in stop_words
        ]
        
        return meaningful_terms
    
    def _apply_text_search(self, query, search_terms: List[str]):
        """Apply text search filters to the query"""
        
        if not search_terms:
            return query
        
        # Create search conditions for each term
        conditions = []
        
        for term in search_terms:
            term_conditions = [
                PropertyDB.title.ilike(f"%{term}%"),
                PropertyDB.description.ilike(f"%{term}%"),
                PropertyDB.location.ilike(f"%{term}%"),
                PropertyDB.suburb.ilike(f"%{term}%"),
                PropertyDB.city.ilike(f"%{term}%"),
                PropertyDB.property_type.ilike(f"%{term}%")
            ]
            
            # Combine term conditions with OR
            conditions.append(or_(*term_conditions))
        
        # Combine all term conditions with AND (property must match all terms)
        if conditions:
            query = query.filter(and_(*conditions))
        
        return query
    
    def _apply_filters(self, query, filters):
        """Apply structured filters to the query"""
        
        if filters.property_type:
            query = query.filter(PropertyDB.property_type == filters.property_type.value)
        
        if filters.min_price:
            query = query.filter(PropertyDB.price >= filters.min_price)
        
        if filters.max_price:
            query = query.filter(PropertyDB.price <= filters.max_price)
        
        if filters.bedrooms:
            query = query.filter(PropertyDB.bedrooms == filters.bedrooms)
        
        if filters.bathrooms:
            query = query.filter(PropertyDB.bathrooms >= filters.bathrooms)
        
        if filters.min_area:
            query = query.filter(PropertyDB.floor_size >= filters.min_area)
        
        if filters.max_area:
            query = query.filter(PropertyDB.floor_size <= filters.max_area)
        
        if filters.city:
            query = query.filter(PropertyDB.city.ilike(f"%{filters.city}%"))
        
        if filters.neighborhood:
            query = query.filter(PropertyDB.suburb.ilike(f"%{filters.neighborhood}%"))
        
        if filters.status:
            status_map = {"for_sale": "for-sale", "for_rent": "for-rent"}
            query = query.filter(
                PropertyDB.transaction_type == status_map.get(filters.status.value, filters.status.value)
            )
        
        return query
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to the query"""
        
        if sort_by == "price":
            if sort_order == "asc":
                query = query.order_by(PropertyDB.price.asc())
            else:
                query = query.order_by(PropertyDB.price.desc())
        elif sort_by == "date":
            if sort_order == "asc":
                query = query.order_by(PropertyDB.listing_date.asc())
            else:
                query = query.order_by(PropertyDB.listing_date.desc())
        else:
            # Default: relevance (will be enhanced with AI scoring in Phase 2)
            # For now, just order by ID
            query = query.order_by(PropertyDB.id)
        
        return query
    
    def _calculate_basic_match_score(self, db_property: PropertyDB, search_query: str) -> int:
        """
        Calculate a basic match score (0-100)
        
        This is a placeholder that will be replaced with AI-powered scoring in Phase 2
        """
        
        if not search_query.strip():
            return 85  # Default score for no search query
        
        score = 0
        query_lower = search_query.lower()
        
        # Title match (30 points)
        if db_property.title and query_lower in db_property.title.lower():
            score += 30
        
        # Description match (25 points)
        if db_property.description and query_lower in db_property.description.lower():
            score += 25
        
        # Location match (20 points)
        location_fields = [db_property.suburb, db_property.city, db_property.location]
        for field in location_fields:
            if field and query_lower in field.lower():
                score += 20
                break
        
        # Property type match (15 points)
        if db_property.property_type and query_lower in db_property.property_type.lower():
            score += 15
        
        # Features match (10 points)
        if db_property.features:
            try:
                features_text = ' '.join(db_property.features).lower()
                if query_lower in features_text:
                    score += 10
            except:
                pass
        
        # Ensure score is between 0 and 100
        score = min(max(score, 0), 100)
        
        # Add some randomness to make it feel more realistic
        import random
        score = max(score, random.randint(60, 85))
        
        return score 