"""
Supabase Property Service for PropMatch
Direct integration with Supabase API for property operations
"""

import logging
from typing import List, Optional, Dict, Any
import json
import random

from app.core.config import settings
from app.models.property import Property, PropertySearchFilters, Location, PointOfInterest, PropertyType, PropertyStatus
from app.db.database import get_supabase_client

logger = logging.getLogger(__name__)

class SupabasePropertyService:
    """Service class for property operations using Supabase client"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        if not self.supabase:
            logger.error("Failed to initialize Supabase client")
    
    async def get_properties(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[PropertySearchFilters] = None
    ) -> List[Property]:
        """Get properties with optional filtering and pagination using Supabase"""
        
        if not self.supabase:
            logger.error("Supabase client not available")
            return []
        
        try:
            # Start with base query
            query = self.supabase.table('properties').select("*")
            
            # Apply filters if provided
            if filters:
                if filters.property_type:
                    query = query.eq('property_type', filters.property_type.value)
                
                if filters.min_price:
                    query = query.gte('price', filters.min_price)
                
                if filters.max_price:
                    query = query.lte('price', filters.max_price)
                
                if filters.bedrooms:
                    query = query.eq('bedrooms', str(filters.bedrooms))
                
                if filters.bathrooms:
                    query = query.gte('bathrooms', filters.bathrooms)
                
                if filters.city:
                    query = query.ilike('city', f'%{filters.city}%')
                
                if filters.neighborhood:
                    query = query.ilike('suburb', f'%{filters.neighborhood}%')
                
                if filters.status:
                    status_map = {"for_sale": "for-sale", "for_rent": "for-rent"}
                    transaction_type = status_map.get(filters.status.value, filters.status.value)
                    query = query.eq('transaction_type', transaction_type)
            
            # Apply pagination
            result = query.range(skip, skip + limit - 1).execute()
            
            if not result.data:
                return []
            
            # Convert to Pydantic models
            properties = []
            for db_prop in result.data:
                try:
                    prop = self._convert_supabase_to_pydantic(db_prop)
                    properties.append(prop)
                except Exception as e:
                    listing_num = db_prop.get('listing_number', 'unknown')
                    logger.error(f"Error converting property {listing_num}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(properties)} properties from Supabase")
            return properties
            
        except Exception as e:
            logger.error(f"Error fetching properties from Supabase: {e}")
            return []
    
    async def get_all_properties_for_vectorization(self, batch_size: int = 100) -> List[Property]:
        """Get all properties for vector embedding - used for bulk operations"""
        
        if not self.supabase:
            logger.error("Supabase client not available")
            return []
        
        all_properties = []
        offset = 0
        
        try:
            while True:
                # Get batch of properties
                result = self.supabase.table('properties').select("*").range(offset, offset + batch_size - 1).execute()
                
                if not result.data:
                    break
                
                # Convert batch to Pydantic models
                batch_properties = []
                for db_prop in result.data:
                    try:
                        prop = self._convert_supabase_to_pydantic(db_prop)
                        batch_properties.append(prop)
                    except Exception as e:
                        listing_num = db_prop.get('listing_number', 'unknown')
                        logger.warning(f"Skipping property {listing_num} due to conversion error: {e}")
                        continue
                
                all_properties.extend(batch_properties)
                
                # Log progress
                logger.info(f"Loaded {len(all_properties)} properties for vectorization...")
                
                # If we got less than batch_size, we're done
                if len(result.data) < batch_size:
                    break
                
                offset += batch_size
            
            logger.info(f"Successfully loaded {len(all_properties)} properties for vectorization")
            return all_properties
            
        except Exception as e:
            logger.error(f"Error loading properties for vectorization: {e}")
            return all_properties  # Return what we have so far
    
    async def get_property_by_listing_number(self, listing_number: int) -> Optional[Property]:
        """Get a single property by listing number"""
        
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table('properties').select("*").eq('listing_number', listing_number).execute()
            
            if not result.data:
                return None
            
            return self._convert_supabase_to_pydantic(result.data[0])
            
        except Exception as e:
            logger.error(f"Error fetching property {listing_number}: {e}")
            return None
    
    async def get_properties_batch(self, listing_numbers: List[int]) -> List[Property]:
        """PERFORMANCE CRITICAL: Batch fetch multiple properties by listing numbers"""
        
        if not self.supabase or not listing_numbers:
            return []
        
        try:
            # Single query for all properties - MAJOR PERFORMANCE IMPROVEMENT
            result = self.supabase.table('properties').select("*").in_('listing_number', listing_numbers).execute()
            
            if not result.data:
                logger.warning(f"No properties found for {len(listing_numbers)} listing numbers")
                return []
            
            # Convert all properties at once
            properties = []
            for db_prop in result.data:
                try:
                    prop = self._convert_supabase_to_pydantic(db_prop)
                    properties.append(prop)
                except Exception as e:
                    listing_num = db_prop.get('listing_number', 'unknown')
                    logger.warning(f"Error converting property {listing_num}: {e}")
                    continue
            
            logger.info(f"Batch fetched {len(properties)} properties from {len(listing_numbers)} requested")
            return properties
            
        except Exception as e:
            logger.error(f"Error in batch fetch for {len(listing_numbers)} properties: {e}")
            return []
    
    async def get_properties_sample(self, sample_size: int = 1000) -> List[Property]:
        """Get a random sample of properties for BM25 corpus building"""
        
        if not self.supabase:
            logger.error("Supabase client not available")
            return []
        
        try:
            # Get total count first
            count_result = self.supabase.table('properties').select("listing_number", count="exact").execute()
            total_count = count_result.count if hasattr(count_result, 'count') else 0
            
            if total_count == 0:
                logger.warning("No properties found in database")
                return []
            
            # Calculate offset for random sampling
            max_offset = max(0, total_count - sample_size)
            random_offset = random.randint(0, max_offset) if max_offset > 0 else 0
            
            # Get a sample using offset
            result = self.supabase.table('properties').select("*").range(random_offset, random_offset + sample_size - 1).execute()
            
            if not result.data:
                logger.warning("No properties found for sample")
                return []
            
            # Convert to Pydantic models
            properties = []
            for db_prop in result.data:
                try:
                    prop = self._convert_supabase_to_pydantic(db_prop)
                    properties.append(prop)
                except Exception as e:
                    listing_num = db_prop.get('listing_number', 'unknown')
                    logger.warning(f"Error converting property {listing_num} in sample: {e}")
                    continue
            
            logger.info(f"Retrieved {len(properties)} properties for BM25 corpus sample")
            return properties
            
        except Exception as e:
            logger.error(f"Error fetching property sample: {e}")
            # Fallback to first N properties if random sampling fails
            try:
                result = self.supabase.table('properties').select("*").limit(sample_size).execute()
                if result.data:
                    properties = []
                    for db_prop in result.data:
                        try:
                            prop = self._convert_supabase_to_pydantic(db_prop)
                            properties.append(prop)
                        except Exception:
                            continue
                    logger.info(f"Retrieved {len(properties)} properties using fallback method")
                    return properties
            except Exception as e2:
                logger.error(f"Fallback sample method also failed: {e2}")
            
            return []
    
    async def get_property_statistics(self) -> Dict[str, Any]:
        """Get summary statistics about properties"""
        
        if not self.supabase:
            return {}
        
        try:
            # Get total count
            total_result = self.supabase.table('properties').select("listing_number", count="exact").execute()
            total_count = total_result.count if hasattr(total_result, 'count') else 0
            
            # Get property type distribution
            types_result = self.supabase.table('properties').select("property_type").execute()
            type_counts = {}
            for prop in types_result.data:
                prop_type = prop.get('property_type', 'unknown')
                type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
            
            # Get city distribution
            cities_result = self.supabase.table('properties').select("city").execute()
            city_counts = {}
            for prop in cities_result.data:
                city = prop.get('city', 'unknown')
                city_counts[city] = city_counts.get(city, 0) + 1
            
            # Get price statistics
            prices_result = self.supabase.table('properties').select("price").execute()
            prices = [prop.get('price', 0) for prop in prices_result.data if prop.get('price')]
            
            price_stats = {}
            if prices:
                price_stats = {
                    "min": min(prices),
                    "max": max(prices),
                    "average": int(sum(prices) / len(prices))
                }
            
            # Get transaction type distribution  
            transaction_result = self.supabase.table('properties').select("transaction_type").execute()
            for_sale_count = sum(1 for prop in transaction_result.data if prop.get('transaction_type') == 'for-sale')
            for_rent_count = sum(1 for prop in transaction_result.data if prop.get('transaction_type') == 'for-rent')
            
            return {
                "total_properties": total_count,
                "for_sale": for_sale_count,
                "for_rent": for_rent_count,
                "property_types": [{"type": k, "count": v} for k, v in type_counts.items()],
                "price_range": price_stats,
                "top_cities": [{"city": k, "count": v} for k, v in sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
            }
            
        except Exception as e:
            logger.error(f"Error getting property statistics: {e}")
            return {}
    
    def _convert_supabase_to_pydantic(self, db_property: Dict[str, Any]) -> Property:
        """Convert Supabase dict to Pydantic model"""
        
        # Parse JSON fields safely
        features = db_property.get('features', []) or []
        images = db_property.get('images', []) or []
        
        # Build location
        location = Location(
            address=db_property.get('street_address') or db_property.get('location') or "",
            neighborhood=db_property.get('suburb') or "",
            city=db_property.get('city') or "",
            postalCode=None,
            country="South Africa"
        )
        
        # Parse points of interest
        points_of_interest = []
        poi_data = db_property.get('points_of_interest')
        if poi_data:
            try:
                for category, pois in poi_data.items():
                    if isinstance(pois, list):
                        for poi in pois:
                            if isinstance(poi, dict) and 'name' in poi and 'distance' in poi:
                                # Extract distance as float from strings like "1.26km"
                                distance_str = poi['distance']
                                try:
                                    distance_km = float(distance_str.replace('km', '').replace('(', '').replace(')', '').strip())
                                except:
                                    distance_km = 0.0
                                
                                points_of_interest.append(PointOfInterest(
                                    name=poi['name'],
                                    category=category,
                                    distance=distance_km,
                                    distance_str=distance_str
                                ))
            except Exception as e:
                logger.warning(f"Error parsing POI for property {db_property.get('listing_number')}: {e}")
        
        # Map property type
        property_type = PropertyType.APARTMENT  # default
        prop_type_str = db_property.get('property_type', '').lower()
        if prop_type_str:
            type_mapping = {
                "house": PropertyType.HOUSE,
                "apartment": PropertyType.APARTMENT,
                "villa": PropertyType.VILLA,
                "condo": PropertyType.CONDO,
                "townhouse": PropertyType.TOWNHOUSE
            }
            property_type = type_mapping.get(prop_type_str, PropertyType.APARTMENT)
        
        # Map status
        status = PropertyStatus.FOR_SALE  # default
        transaction_type = db_property.get('transaction_type')
        if transaction_type:
            status_mapping = {
                "for-sale": PropertyStatus.FOR_SALE,
                "for-rent": PropertyStatus.FOR_RENT
            }
            status = status_mapping.get(transaction_type, PropertyStatus.FOR_SALE)
        
        # Handle numeric fields that might be strings
        def safe_int(value, default=0):
            if value is None:
                return default
            try:
                # Handle float values by rounding them first
                if isinstance(value, float):
                    return int(round(value))
                # Handle string values that might contain decimals
                if isinstance(value, str) and '.' in value:
                    return int(round(float(value)))
                return int(str(value))
            except:
                return default
        
        def safe_float(value, default=0.0):
            if value is None:
                return default
            try:
                # Handle string values that might be formatted with commas
                if isinstance(value, str):
                    value = value.replace(',', '')
                return float(value)
            except:
                return default
        
        def safe_bool(value, default=False):
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ['true', 'yes', '1', 'on']
            return bool(value)
        
        # Convert bedrooms from string to int
        bedrooms = safe_int(db_property.get('bedrooms'), 0)
        bathrooms = safe_float(db_property.get('bathrooms'), 0.0)
        
        # Handle floor_size which might be a string like "120m²"
        floor_size_raw = db_property.get('floor_size')
        area = 0
        if floor_size_raw:
            try:
                # Extract numeric part from strings like "120m²" or "120"
                import re
                numbers = re.findall(r'\d+', str(floor_size_raw))
                if numbers:
                    area = int(numbers[0])
            except:
                area = 0
        
        # Get listing number and convert to string
        listing_number = db_property.get('listing_number')
        listing_number_str = str(listing_number) if listing_number is not None else None
        
        return Property(
            id=listing_number_str,  # Use listing_number as ID
            title=db_property.get('title') or '',
            description=db_property.get('description') or '',
            price=safe_int(db_property.get('price'), 0),
            currency="ZAR",
            type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            area=area,
            areaUnit="m²",
            location=location,
            images=images,
            features=features,
            status=status,
            listedDate=db_property.get('listing_date') or "",
            listing_number=listing_number_str,  # Convert to string
            url=db_property.get('url'),
            street_address=db_property.get('street_address'),
            suburb=db_property.get('suburb'),
            province=db_property.get('province'),
            kitchens=safe_int(db_property.get('kitchens'), None) if db_property.get('kitchens') else None,
            garages=safe_int(db_property.get('garages'), None) if db_property.get('garages') else None,
            parking=safe_bool(db_property.get('parking'), None) if db_property.get('parking') else None,
            parking_spaces=safe_int(db_property.get('parking_spaces'), None) if db_property.get('parking_spaces') else None,
            floor_size=safe_int(db_property.get('floor_size'), None) if db_property.get('floor_size') else None,
            erf_size=safe_int(db_property.get('erf_size'), None) if db_property.get('erf_size') else None,
            levies=db_property.get('levies'),
            rates=db_property.get('rates'),
            rates_and_taxes=db_property.get('rates_and_taxes'),
            no_transfer_duty=safe_bool(db_property.get('no_transfer_duty'), None) if db_property.get('no_transfer_duty') is not None else None,
            agent_name=db_property.get('agent_name'),
            pets_allowed=safe_bool(db_property.get('pets_allowed'), None) if db_property.get('pets_allowed') else None,
            garden=safe_bool(db_property.get('garden'), None) if db_property.get('garden') else None,
            pools=safe_bool(db_property.get('pools'), None) if db_property.get('pools') else None,
            security=safe_bool(db_property.get('security'), None) if db_property.get('security') else None,
            solar_panels=safe_bool(db_property.get('solar_panels'), None) if db_property.get('solar_panels') else None,
            backup_power=safe_bool(db_property.get('backup_power'), None) if db_property.get('backup_power') else None,
            fibre_internet=safe_bool(db_property.get('fibre_internet'), None) if db_property.get('fibre_internet') else None,
            additional_rooms=db_property.get('additional_rooms'),
            external_features=db_property.get('external_features'),
            building_features=db_property.get('building_features'),
            points_of_interest=points_of_interest
        ) 