#!/usr/bin/env python3
"""Test property lookup functionality"""

import asyncio
from app.services.supabase_property_service import SupabasePropertyService

async def test_property_lookup():
    """Test property lookup by listing number"""
    service = SupabasePropertyService()
    
    print("Testing property lookup...")
    
    # Try to get a property we know exists from vector search
    listing_numbers = [115918507, 115930399, 112036221]
    
    for listing_num in listing_numbers:
        try:
            prop = await service.get_property_by_listing_number(listing_num)
            if prop:
                print(f"✅ Found property {listing_num}: {prop.title[:50]}...")
                return True
            else:
                print(f"❌ Property {listing_num} not found")
        except Exception as e:
            print(f"❌ Error getting property {listing_num}: {e}")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_property_lookup())
    print(f"\nProperty lookup {'working' if success else 'failed'}") 