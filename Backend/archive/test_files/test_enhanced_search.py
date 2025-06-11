#!/usr/bin/env python3
"""Test enhanced search service"""

import asyncio
from app.models.property import PropertySearchRequest
from app.services.enhanced_search_service import EnhancedSearchService

async def test_enhanced_search():
    """Test the enhanced search service"""
    service = EnhancedSearchService()
    
    print("Testing enhanced search...")
    print(f"Vector service initialized: {service.vector_service.initialized}")
    print(f"Property service initialized: {service.property_service.supabase is not None}")
    
    # Create a search request
    search_request = PropertySearchRequest(
        query="3 bedroom house with garden",
        page=1,
        page_size=3
    )
    
    try:
        print(f"\nSearching for: '{search_request.query}'")
        results = await service.search_properties(search_request)
        
        print(f"✅ Search completed!")
        print(f"   Total results: {results.totalResults}")
        print(f"   Properties returned: {len(results.properties)}")
        
        for i, prop in enumerate(results.properties, 1):
            print(f"   {i}. {prop.title[:50]}... - R{prop.price:,} ({prop.bedrooms} bed)")
            if hasattr(prop, 'searchScore'):
                print(f"      Search score: {prop.searchScore}")
        
        return len(results.properties) > 0
        
    except Exception as e:
        print(f"❌ Enhanced search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_search())
    print(f"\nEnhanced search {'working' if success else 'failed'}") 