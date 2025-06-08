from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, Boolean, JSON, DateTime, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Properties table model matching actual Supabase schema
class PropertyDB(Base):
    """SQLAlchemy model for properties table - matching actual Supabase schema"""
    __tablename__ = "properties"
    
    # Use listing_number as primary key (as it exists in your table)
    listing_number = Column(Integer, primary_key=True)
    url = Column(String)
    title = Column(String, nullable=False)
    street_address = Column(String)
    price = Column(Integer, nullable=False)
    location = Column(String)
    suburb = Column(String, index=True)
    city = Column(String, index=True)
    province = Column(String, index=True)
    property_type = Column(String, nullable=False, index=True)
    bedrooms = Column(String)  # Note: stored as string in your DB
    bathrooms = Column(Float)
    kitchens = Column(String)  # Note: stored as string in your DB
    garages = Column(String)   # Note: stored as string in your DB
    parking = Column(String)   # Note: stored as string in your DB
    parking_spaces = Column(String)  # Note: stored as string in your DB
    floor_size = Column(String)  # Note: stored as string in your DB
    erf_size = Column(String)    # Note: stored as string in your DB
    levies = Column(String)
    rates = Column(String)
    rates_and_taxes = Column(String)
    no_transfer_duty = Column(Boolean)
    description = Column(Text, nullable=False)
    agent_name = Column(String)
    pets_allowed = Column(String)  # Note: stored as string in your DB
    listing_date = Column(String)
    garden = Column(String)
    pools = Column(String)
    security = Column(String)
    solar_panels = Column(String)
    backup_power = Column(String)
    fibre_internet = Column(String)
    additional_rooms = Column(JSON)
    external_features = Column(JSON)
    building_features = Column(JSON)
    features = Column(JSON)  # Array of feature strings
    images = Column(JSON)  # Array of image URLs
    points_of_interest = Column(JSON)  # Structured POI data
    transaction_type = Column(String, nullable=False, index=True)

# Database dependency
def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database initialization
def create_tables():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        # Test simple query using text()
        result = db.execute(text("SELECT 1")).fetchone()
        db.close()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

# Supabase client for direct API access
def get_supabase_client():
    """Get Supabase client for API access"""
    try:
        from supabase import create_client, Client
        
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_ANON_KEY
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials")
            return None
        
        return create_client(supabase_url, supabase_key)
    except ImportError:
        logger.error("Supabase client not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None

# Data migration utilities
def migrate_csv_to_db():
    """Migrate data from CSV to PostgreSQL"""
    import pandas as pd
    import json
    from datetime import datetime
    
    logger.info("Starting CSV to database migration...")
    
    try:
        # Read CSV data
        csv_path = "data/property24_for_supabase_fixed.csv"
        df = pd.read_csv(csv_path)
        
        logger.info(f"Found {len(df)} properties in CSV")
        
        db = SessionLocal()
        
        for idx, row in df.iterrows():
            try:
                # Parse JSON fields
                features = []
                if pd.notna(row['features']):
                    try:
                        features = json.loads(row['features'])
                    except:
                        features = []
                
                images = []
                if pd.notna(row['images']):
                    try:
                        images = json.loads(row['images'])
                    except:
                        images = []
                
                points_of_interest = {}
                if pd.notna(row['points_of_interest']):
                    try:
                        points_of_interest = json.loads(row['points_of_interest'])
                    except:
                        points_of_interest = {}
                
                additional_rooms = {}
                if pd.notna(row['additional_rooms']):
                    try:
                        additional_rooms = json.loads(row['additional_rooms'])
                    except:
                        additional_rooms = {}
                
                external_features = {}
                if pd.notna(row['external_features']):
                    try:
                        external_features = json.loads(row['external_features'])
                    except:
                        external_features = {}
                
                building_features = {}
                if pd.notna(row['building_features']):
                    try:
                        building_features = json.loads(row['building_features'])
                    except:
                        building_features = {}
                
                # Create property record
                property_record = PropertyDB(
                    listing_number=int(row['listing_number']) if pd.notna(row['listing_number']) else None,
                    url=row['url'] if pd.notna(row['url']) else None,
                    title=row['title'],
                    street_address=row['street_address'] if pd.notna(row['street_address']) else None,
                    price=int(row['price']) if pd.notna(row['price']) else 0,
                    location=row['location'] if pd.notna(row['location']) else None,
                    suburb=row['suburb'] if pd.notna(row['suburb']) else None,
                    city=row['city'] if pd.notna(row['city']) else None,
                    province=row['province'] if pd.notna(row['province']) else None,
                    property_type=row['property_type'] if pd.notna(row['property_type']) else 'apartment',
                    bedrooms=str(row['bedrooms']) if pd.notna(row['bedrooms']) else "0",
                    bathrooms=float(row['bathrooms']) if pd.notna(row['bathrooms']) else 0,
                    kitchens=str(row['kitchens']) if pd.notna(row['kitchens']) else None,
                    garages=str(row['garages']) if pd.notna(row['garages']) else None,
                    parking=str(row['parking']) if pd.notna(row['parking']) else None,
                    parking_spaces=str(row['parking_spaces']) if pd.notna(row['parking_spaces']) else None,
                    floor_size=str(row['floor_size']) if pd.notna(row['floor_size']) else None,
                    erf_size=str(row['erf_size']) if pd.notna(row['erf_size']) else None,
                    levies=row['levies'] if pd.notna(row['levies']) else None,
                    rates=row['rates'] if pd.notna(row['rates']) else None,
                    rates_and_taxes=row['rates_and_taxes'] if pd.notna(row['rates_and_taxes']) else None,
                    no_transfer_duty=bool(row['no_transfer_duty']) if pd.notna(row['no_transfer_duty']) else None,
                    description=row['description'],
                    agent_name=row['agent_name'] if pd.notna(row['agent_name']) else None,
                    pets_allowed=str(row['pets_allowed']) if pd.notna(row['pets_allowed']) else None,
                    listing_date=row['listing_date'] if pd.notna(row['listing_date']) else None,
                    garden=str(row['garden']) if pd.notna(row['garden']) else None,
                    pools=str(row['pools']) if pd.notna(row['pools']) else None,
                    security=str(row['security']) if pd.notna(row['security']) else None,
                    solar_panels=str(row['solar_panels']) if pd.notna(row['solar_panels']) else None,
                    backup_power=str(row['backup_power']) if pd.notna(row['backup_power']) else None,
                    fibre_internet=str(row['fibre_internet']) if pd.notna(row['fibre_internet']) else None,
                    additional_rooms=additional_rooms,
                    external_features=external_features,
                    building_features=building_features,
                    features=features,
                    images=images,
                    points_of_interest=points_of_interest,
                    transaction_type=row['transaction_type'] if pd.notna(row['transaction_type']) else 'for-sale'
                )
                
                db.add(property_record)
                
                if (idx + 1) % 100 == 0:
                    db.commit()
                    logger.info(f"Migrated {idx + 1} properties...")
                    
            except Exception as e:
                logger.error(f"Error migrating property {idx}: {e}")
                continue
        
        db.commit()
        db.close()
        
        logger.info(f"Successfully migrated {len(df)} properties to database")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False 