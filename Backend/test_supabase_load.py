#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')
from app.services.supabase_property_service import SupabasePropertyService

async def test_load():
    service = SupabasePropertyService()
    props = await service.get_properties(skip=0, limit=5)
    print(f'Successfully loaded {len(props)} properties')
    if props:
        prop = props[0]
        print(f'Sample: {prop.title} - R{prop.price:,} in {prop.location.city}')
        print(f'Listing number: {prop.listing_number}')
        print(f'Features: {len(prop.features)}')
        print(f'POI: {len(prop.points_of_interest)}')
    return len(props) > 0

if __name__ == "__main__":
    result = asyncio.run(test_load())
    print(f'Test result: {result}') 