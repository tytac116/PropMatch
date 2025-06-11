from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class POI:
    name: str
    distance: str


@dataclass
class PropertyData:
    # Basic info
    url: str = ""
    listing_number: str = ""
    title: str = ""
    street_address: str = ""
    price: Optional[float] = None
    location: str = ""
    suburb: str = ""
    city: str = ""
    province: str = ""
    
    # Property details (most common ones as direct fields)
    property_type: str = ""
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    kitchens: Optional[float] = None
    garages: Optional[float] = None
    parking: Optional[float] = None
    parking_spaces: Optional[float] = None  # Total number of parking spaces (garages + parking)
    floor_size: Optional[float] = None
    erf_size: Optional[float] = None
    
    # DYNAMIC: Additional rooms/facilities found in the property
    # This will capture any room type that appears: {"Reception Rooms": 4, "Entrance Halls": 1, "Laundry": 2, etc.}
    additional_rooms: Dict[str, float] = field(default_factory=dict)
    
    # DYNAMIC: External features with their counts/presence
    # {"Gardens": 1, "Pools": 1, "Security": 1, "Balcony": True, etc.}
    external_features: Dict[str, Any] = field(default_factory=dict)
    
    # DYNAMIC: Building characteristics and features
    # {"Facing": "Mountain View", "Solar Panels": True, "Backup Power": True, etc.}
    building_features: Dict[str, Any] = field(default_factory=dict)
    
    # Most common boolean features as direct fields for easy access
    garden: Optional[bool] = None
    pools: Optional[float] = None
    security: Optional[float] = None
    solar_panels: Optional[bool] = None
    backup_power: Optional[bool] = None
    fibre_internet: Optional[bool] = None
    
    # Content
    description: str = ""
    features: List[str] = field(default_factory=list)
    
    # Agent and costs
    agent_name: str = ""
    levies: Optional[float] = None
    rates: Optional[float] = None
    rates_and_taxes: str = ""
    
    # Additional info
    no_transfer_duty: bool = False
    pets_allowed: Optional[bool] = None
    listing_date: str = ""
    
    # Media and location info
    images: List[str] = field(default_factory=list)
    points_of_interest: Dict[str, List[POI]] = field(default_factory=dict)
    
    # Metadata
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    transaction_type: str = "for-sale"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {}
        for key, value in self.__dict__.items():
            if key == 'points_of_interest':
                # Convert POI objects to dicts
                poi_dict = {}
                for category, pois in value.items():
                    poi_dict[category] = [{"name": poi.name, "distance": poi.distance} for poi in pois]
                result[key] = poi_dict
            else:
                result[key] = value
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False) 