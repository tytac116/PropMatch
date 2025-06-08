"""
Database Configuration and Models for Supabase PostgreSQL
=========================================================

This module handles:
- Supabase connection setup
- SQLAlchemy models for property data
- Database operations (CRUD)
- Data migration from JSON to PostgreSQL

Author: AI Assistant
Date: 2025-06-06
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()

class Property(Base):
    """SQLAlchemy model for property data"""
    __tablename__ = 'properties'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Property identification
    listing_number = Column(String(50), unique=True, index=True)
    url = Column(Text)
    
    # Basic property info
    title = Column(Text)
    street_address = Column(Text)
    price = Column(Float)
    location = Column(String(100))
    suburb = Column(String(100))
    city = Column(String(100))
    province = Column(String(100))
    property_type = Column(String(50))
    
    # Property details
    bedrooms = Column(Float)
    bathrooms = Column(Float)
    kitchens = Column(Float)
    garages = Column(Integer)
    parking = Column(Integer)
    parking_spaces = Column(Integer)
    floor_size = Column(Float)
    erf_size = Column(Float)
    
    # Financial info
    levies = Column(Float)
    rates_and_taxes = Column(String(100))
    
    # Additional info
    description = Column(Text)
    agent_name = Column(String(200))
    pets_allowed = Column(Boolean)
    listing_date = Column(String(50))
    
    # Complex data as JSON
    additional_rooms = Column(JSON)
    external_features = Column(JSON)
    building_features = Column(JSON)
    points_of_interest = Column(JSON)
    images = Column(JSON)
    
    # Metadata
    transaction_type = Column(String(20))
    scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.setup_connection()
    
    def setup_connection(self):
        """Setup Supabase PostgreSQL connection"""
        # Get Supabase credentials from environment
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        if not supabase_url or not supabase_password:
            raise ValueError("Missing Supabase credentials in environment variables")
        
        # Extract database connection details from Supabase URL
        # Supabase URL format: https://xxx.supabase.co
        project_id = supabase_url.replace('https://', '').replace('.supabase.co', '')
        
        # Construct PostgreSQL connection string
        DATABASE_URL = f"postgresql://postgres:{supabase_password}@db.{project_id}.supabase.co:5432/postgres"
        
        try:
            self.engine = create_engine(DATABASE_URL, echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info("✅ Successfully connected to Supabase PostgreSQL")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            raise
    
    def create_tables(self):
        """Create database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def migrate_json_to_db(self, json_file_path: str = "data/property24_production_20250605_165810.json"):
        """Migrate property data from JSON file to PostgreSQL"""
        
        if not os.path.exists(json_file_path):
            logger.error(f"JSON file not found: {json_file_path}")
            return False
        
        session = self.get_session()
        
        try:
            # Load JSON data
            with open(json_file_path, 'r', encoding='utf-8') as f:
                properties_data = json.load(f)
            
            logger.info(f"📥 Loading {len(properties_data)} properties from JSON...")
            
            # Process each property
            successful_imports = 0
            failed_imports = 0
            
            for prop_data in properties_data:
                try:
                    # Check if property already exists
                    existing = session.query(Property).filter_by(
                        listing_number=prop_data.get('listing_number')
                    ).first()
                    
                    if existing:
                        logger.debug(f"Property {prop_data.get('listing_number')} already exists, skipping")
                        continue
                    
                    # Create new property record
                    property_record = Property(
                        listing_number=prop_data.get('listing_number'),
                        url=prop_data.get('url'),
                        title=prop_data.get('title'),
                        street_address=prop_data.get('street_address'),
                        price=prop_data.get('price'),
                        location=prop_data.get('location'),
                        suburb=prop_data.get('suburb'),
                        city=prop_data.get('city'),
                        province=prop_data.get('province'),
                        property_type=prop_data.get('property_type'),
                        bedrooms=prop_data.get('bedrooms'),
                        bathrooms=prop_data.get('bathrooms'),
                        kitchens=prop_data.get('kitchens'),
                        garages=prop_data.get('garages'),
                        parking=prop_data.get('parking'),
                        parking_spaces=prop_data.get('parking_spaces'),
                        floor_size=prop_data.get('floor_size'),
                        erf_size=prop_data.get('erf_size'),
                        levies=self._extract_numeric_value(prop_data.get('rates_and_taxes', '')),
                        rates_and_taxes=prop_data.get('rates_and_taxes'),
                        description=prop_data.get('description'),
                        agent_name=prop_data.get('agent_name'),
                        pets_allowed=prop_data.get('pets_allowed'),
                        listing_date=prop_data.get('listing_date'),
                        additional_rooms=prop_data.get('additional_rooms', {}),
                        external_features=prop_data.get('external_features', {}),
                        building_features=prop_data.get('building_features', {}),
                        points_of_interest=prop_data.get('points_of_interest', {}),
                        images=prop_data.get('images', []),
                        transaction_type=prop_data.get('transaction_type'),
                        scraped_at=self._parse_datetime(prop_data.get('scraped_at'))
                    )
                    
                    session.add(property_record)
                    successful_imports += 1
                    
                    # Commit in batches of 100
                    if successful_imports % 100 == 0:
                        session.commit()
                        logger.info(f"📝 Imported {successful_imports} properties...")
                
                except Exception as e:
                    logger.warning(f"Failed to import property {prop_data.get('listing_number', 'unknown')}: {e}")
                    failed_imports += 1
                    continue
            
            # Final commit
            session.commit()
            
            logger.info(f"✅ Migration completed!")
            logger.info(f"   - Successful imports: {successful_imports}")
            logger.info(f"   - Failed imports: {failed_imports}")
            logger.info(f"   - Total in database: {session.query(Property).count()}")
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Migration failed: {e}")
            return False
        
        finally:
            session.close()
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract numeric value from text like 'R 1,500'"""
        if not text:
            return None
        
        import re
        # Remove currency symbols and extract numbers
        numbers = re.findall(r'[\d,]+', str(text))
        if numbers:
            try:
                return float(numbers[0].replace(',', ''))
            except:
                return None
        return None
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse datetime string"""
        if not datetime_str:
            return None
        
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            return None
    
    def get_property_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        session = self.get_session()
        
        try:
            total_properties = session.query(Property).count()
            
            # Property type distribution
            property_types = session.query(Property.property_type, Property.id).all()
            type_counts = {}
            for prop_type, _ in property_types:
                type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
            
            # Average prices
            avg_price = session.query(Property.price).filter(Property.price.isnot(None)).all()
            avg_price_value = sum(p[0] for p in avg_price if p[0]) / len(avg_price) if avg_price else 0
            
            return {
                "total_properties": total_properties,
                "property_types": type_counts,
                "average_price": avg_price_value,
                "database_size": "Connected to Supabase PostgreSQL"
            }
            
        finally:
            session.close()

def main():
    """Test database connection and migration"""
    print("🗄️ Supabase Database Setup")
    print("=" * 50)
    
    try:
        # Initialize database manager
        db = DatabaseManager()
        
        # Create tables
        db.create_tables()
        
        # Migrate data
        print("\n📥 Starting data migration...")
        success = db.migrate_json_to_db()
        
        if success:
            # Show stats
            stats = db.get_property_stats()
            print(f"\n📊 Database Statistics:")
            print(f"   - Total properties: {stats['total_properties']}")
            print(f"   - Average price: R {stats['average_price']:,.0f}")
            print(f"   - Property types: {stats['property_types']}")
            
        print("\n✅ Database setup complete!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")

if __name__ == "__main__":
    main() 