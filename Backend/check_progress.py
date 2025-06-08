#!/usr/bin/env python3
"""
Check Vector Loading Progress
Simple script to monitor Pinecone index stats during loading
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from app.services.vector_service import VectorService

async def check_progress():
    """Check current progress of vector loading"""
    
    print("🔍 Checking Vector Database Progress...")
    print("=" * 40)
    
    try:
        vector_service = VectorService()
        
        if not vector_service.initialized:
            print("❌ Vector service not initialized")
            return
        
        # Get index stats
        stats = vector_service.get_index_stats()
        
        print(f"📊 Current Index Stats:")
        print(f"   Status: {stats.get('status', 'unknown')}")
        print(f"   Total Vectors: {stats.get('total_vectors', 0):,}")
        print(f"   Dimension: {stats.get('dimension', 'unknown')}")
        print(f"   Index Fullness: {stats.get('index_fullness', 'unknown')}")
        
        # Estimate progress if we know total properties
        total_vectors = stats.get('total_vectors', 0)
        if total_vectors > 0:
            # We expect around 1,438 properties based on earlier reports
            estimated_total = 1438
            progress_pct = (total_vectors / estimated_total) * 100
            remaining = max(0, estimated_total - total_vectors)
            
            print(f"\n📈 Estimated Progress:")
            print(f"   Loaded: {total_vectors:,}/{estimated_total:,} ({progress_pct:.1f}%)")
            print(f"   Remaining: ~{remaining:,} properties")
        
        # Test a quick search
        if total_vectors > 0:
            print(f"\n🔍 Testing search functionality...")
            results = await vector_service.search_similar_properties("house", top_k=1)
            if results:
                prop_id, score, metadata = results[0]
                print(f"✅ Search working! Sample: Property {prop_id} (score: {score:.3f})")
            else:
                print("⚠️ Search returned no results")
        
    except Exception as e:
        print(f"❌ Error checking progress: {e}")

if __name__ == "__main__":
    asyncio.run(check_progress()) 