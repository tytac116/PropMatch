from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
import json
import logging

from app.db.database import PropertyDB
from app.models.property import Property, PropertySearchFilters, Location, PointOfInterest, PropertyType, PropertyStatus

logger = logging.getLogger(__name__)

class PropertyService:
    """Service class for property-related operations"""
    
    def __init__(self):
        pass
    
    async def get_properties(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[PropertySearchFilters] = None
    ) -> List[Property]:
        """Get properties with optional filtering and pagination"""
        
        query = db.query(PropertyDB)
        
        # Apply filters if provided
        if filters:
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
                query = query.filter(PropertyDB.transaction_type == status_map.get(filters.status.value, filters.status.value))
        
        # Get paginated results
        db_properties = query.offset(skip).limit(limit).all()
        
        # Convert to Pydantic models
        properties = []
        for db_prop in db_properties:
            try:
                prop = await self._convert_db_to_pydantic(db_prop)
                properties.append(prop)
            except Exception as e:
                logger.error(f"Error converting property {db_prop.id}: {e}")
                continue
        
        return properties
    
    async def get_property_by_id(self, db: Session, property_id: str) -> Optional[Property]:
        """Get a single property by ID"""
        
        db_property = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not db_property:
            return None
        
        return await self._convert_db_to_pydantic(db_property)
    
    async def get_property_by_listing_number(self, db: Session, listing_number: str) -> Optional[Property]:
        """Get a single property by listing number"""
        
        db_property = db.query(PropertyDB).filter(PropertyDB.listing_number == listing_number).first()
        
        if not db_property:
            return None
        
        return await self._convert_db_to_pydantic(db_property)
    
    async def get_property_statistics(self, db: Session) -> Dict[str, Any]:
        """Get summary statistics about properties"""
        
        try:
            # Basic counts
            total_properties = db.query(PropertyDB).count()
            for_sale_count = db.query(PropertyDB).filter(PropertyDB.transaction_type == "for-sale").count()
            for_rent_count = db.query(PropertyDB).filter(PropertyDB.transaction_type == "for-rent").count()
            
            # Property type distribution
            type_stats = db.query(
                PropertyDB.property_type,
                func.count(PropertyDB.id).label('count')
            ).group_by(PropertyDB.property_type).all()
            
            # Price statistics
            price_stats = db.query(
                func.min(PropertyDB.price).label('min_price'),
                func.max(PropertyDB.price).label('max_price'),
                func.avg(PropertyDB.price).label('avg_price')
            ).first()
            
            # City distribution
            city_stats = db.query(
                PropertyDB.city,
                func.count(PropertyDB.id).label('count')
            ).group_by(PropertyDB.city).order_by(func.count(PropertyDB.id).desc()).limit(10).all()
            
            return {
                "total_properties": total_properties,
                "for_sale": for_sale_count,
                "for_rent": for_rent_count,
                "property_types": [{"type": stat.property_type, "count": stat.count} for stat in type_stats],
                "price_range": {
                    "min": price_stats.min_price,
                    "max": price_stats.max_price,
                    "average": int(price_stats.avg_price) if price_stats.avg_price else 0
                },
                "top_cities": [{"city": stat.city, "count": stat.count} for stat in city_stats]
            }
            
        except Exception as e:
            logger.error(f"Error getting property statistics: {e}")
            return {}
    
    async def _convert_db_to_pydantic(self, db_property: PropertyDB) -> Property:
        """Convert database model to Pydantic model"""
        
        # Parse JSON fields safely
        features = db_property.features if db_property.features else []
        images = db_property.images if db_property.images else []
        
        # Build location
        location = Location(
            address=db_property.street_address or db_property.location or "",
            neighborhood=db_property.suburb or "",
            city=db_property.city or "",
            postalCode=None,
            country="South Africa"
        )
        
        # Parse points of interest
        points_of_interest = []
        if db_property.points_of_interest:
            try:
                poi_data = db_property.points_of_interest
                for category, pois in poi_data.items():
                    if isinstance(pois, list):
                        for poi in pois:
                            if isinstance(poi, dict) and 'name' in poi and 'distance' in poi:
                                # Extract distance as float
                                distance_str = poi['distance']
                                distance_km = float(distance_str.replace('km', ''))
                                
                                points_of_interest.append(PointOfInterest(
                                    name=poi['name'],
                                    category=category,
                                    distance=distance_km,
                                    distance_str=distance_str
                                ))
            except Exception as e:
                logger.warning(f"Error parsing POI for property {db_property.id}: {e}")
        
        # Map property type
        property_type = PropertyType.APARTMENT  # default
        if db_property.property_type:
            type_mapping = {
                "house": PropertyType.HOUSE,
                "apartment": PropertyType.APARTMENT,
                "villa": PropertyType.VILLA,
                "condo": PropertyType.CONDO,
                "townhouse": PropertyType.TOWNHOUSE
            }
            property_type = type_mapping.get(db_property.property_type.lower(), PropertyType.APARTMENT)
        
        # Map status
        status = PropertyStatus.FOR_SALE  # default
        if db_property.transaction_type:
            status_mapping = {
                "for-sale": PropertyStatus.FOR_SALE,
                "for-rent": PropertyStatus.FOR_RENT
            }
            status = status_mapping.get(db_property.transaction_type, PropertyStatus.FOR_SALE)
        
        return Property(
            id=db_property.id,
            title=db_property.title,
            description=db_property.description,
            price=db_property.price,
            currency="ZAR",
            type=property_type,
            bedrooms=db_property.bedrooms or 0,
            bathrooms=db_property.bathrooms or 0,
            area=db_property.floor_size or 0,
            areaUnit="m²",
            location=location,
            images=images,
            features=features,
            status=status,
            listedDate=db_property.listing_date or "",
            listing_number=db_property.listing_number,
            url=db_property.url,
            street_address=db_property.street_address,
            suburb=db_property.suburb,
            province=db_property.province,
            kitchens=db_property.kitchens,
            garages=db_property.garages,
            parking=db_property.parking,
            parking_spaces=db_property.parking_spaces,
            floor_size=db_property.floor_size,
            erf_size=db_property.erf_size,
            levies=db_property.levies,
            rates=db_property.rates,
            rates_and_taxes=db_property.rates_and_taxes,
            no_transfer_duty=db_property.no_transfer_duty,
            agent_name=db_property.agent_name,
            pets_allowed=db_property.pets_allowed,
            garden=db_property.garden,
            pools=db_property.pools,
            security=db_property.security,
            solar_panels=db_property.solar_panels,
            backup_power=db_property.backup_power,
            fibre_internet=db_property.fibre_internet,
            additional_rooms=db_property.additional_rooms,
            external_features=db_property.external_features,
            building_features=db_property.building_features,
            points_of_interest=points_of_interest
        ) 