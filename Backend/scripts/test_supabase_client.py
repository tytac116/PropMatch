#!/usr/bin/env python3
"""
Test Supabase connection using the Supabase client
Alternative to direct PostgreSQL connection
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_client():
    """Test Supabase connection using official client"""
    try:
        from supabase import create_client, Client
        
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url:
            print("❌ SUPABASE_URL not found in environment")
            print("💡 Add SUPABASE_URL to your .env file")
            return False
            
        if not supabase_key:
            print("❌ SUPABASE_ANON_KEY not found in environment")
            print("💡 Add SUPABASE_ANON_KEY to your .env file")
            return False
        
        print(f"🔗 Supabase URL: {supabase_url}")
        print(f"🔑 Anon Key: {supabase_key[:20]}...")
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test connection by querying properties table with correct columns
        print("🔍 Testing Supabase client connection...")
        
        result = supabase.table('properties').select("listing_number,title,city,price,bedrooms").limit(5).execute()
        
        if result.data:
            print(f"✅ Supabase client connection successful!")
            print(f"📈 Found {len(result.data)} properties (showing first 5)")
            
            for prop in result.data:
                listing_num = prop.get('listing_number')
                title = prop.get('title', 'No title')
                city = prop.get('city', 'Unknown city')
                price = prop.get('price', 0)
                bedrooms = prop.get('bedrooms', 'Unknown')
                print(f"📝 Property {listing_num}: {title[:50]}... in {city} - R{price:,} ({bedrooms} bed)")
            
            # Get total count
            count_result = supabase.table('properties').select("listing_number", count="exact").execute()
            total_count = count_result.count if hasattr(count_result, 'count') else len(result.data)
            print(f"📊 Total properties in database: {total_count}")
            
            # Test POI data
            print("\n🔍 Testing points of interest data...")
            poi_result = supabase.table('properties').select("listing_number,points_of_interest").limit(1).execute()
            
            if poi_result.data and poi_result.data[0].get('points_of_interest'):
                poi_data = poi_result.data[0]['points_of_interest']
                print(f"✅ POI data available - sample categories: {list(poi_data.keys())}")
                
                # Show sample POI
                for category, pois in poi_data.items():
                    if pois and len(pois) > 0:
                        sample_poi = pois[0]
                        print(f"   {category}: {sample_poi.get('name')} ({sample_poi.get('distance')})")
                        break
            
            return True
        else:
            print("❌ No data returned from properties table")
            return False
            
    except ImportError:
        print("❌ Supabase client not installed")
        print("💡 Install with: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Supabase client connection failed: {e}")
        return False

def main():
    """Test Supabase connection using client"""
    print("🚀 Testing Supabase Client Connection")
    print("=" * 40)
    
    success = test_supabase_client()
    
    if success:
        print("\n🎉 Supabase client connection successful!")
        print("✅ Your properties table is accessible via Supabase API")
        print("✅ POI data is available for distance-based searches")
        print("🚀 Ready to proceed with Phase 2: Vector Search!")
    else:
        print("\n❌ Supabase client connection failed")
        print("💡 Check your SUPABASE_URL and SUPABASE_ANON_KEY in .env")

if __name__ == "__main__":
    main() 