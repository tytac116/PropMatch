#!/usr/bin/env python3
"""
Load Properties into Pinecone Vector Database
Fetches all properties from Supabase and creates embeddings in Pinecone
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import logging
from app.services.supabase_property_service import SupabasePropertyService
from app.services.vector_service import VectorService
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def clear_vector_database():
    """Clear all vectors from the Pinecone index"""
    
    logger.info("🧹 Clearing Pinecone vector database...")
    
    try:
        vector_service = VectorService()
        
        if not vector_service.initialized:
            logger.error("❌ Vector service not initialized")
            return False
        
        # Get current stats
        stats = vector_service.get_index_stats()
        current_count = stats.get('total_vectors', 0)
        
        if current_count == 0:
            logger.info("✅ Vector database is already empty")
            return True
        
        logger.info(f"📊 Current vector count: {current_count}")
        
        # Delete all vectors (delete by namespace - empty namespace deletes all)
        vector_service.index.delete(delete_all=True)
        
        # Wait a moment for deletion to propagate
        await asyncio.sleep(2)
        
        # Verify deletion
        new_stats = vector_service.get_index_stats()
        new_count = new_stats.get('total_vectors', 0)
        
        if new_count == 0:
            logger.info("✅ Successfully cleared vector database")
            return True
        else:
            logger.warning(f"⚠️ Some vectors may remain: {new_count}")
            return True  # Still proceed
            
    except Exception as e:
        logger.error(f"❌ Failed to clear vector database: {e}")
        return False

async def load_properties_to_vector_db(clear_first: bool = False):
    """Load all properties from Supabase into Pinecone"""
    
    logger.info("🚀 Starting Property Vector Loading Process")
    logger.info("=" * 50)
    
    # Check required environment variables
    required_env_vars = [
        "SUPABASE_URL", 
        "SUPABASE_ANON_KEY", 
        "OPENAI_API_KEY", 
        "PINECONE_API_KEY"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file")
        return False
    
    # Initialize services
    logger.info("🔧 Initializing services...")
    
    try:
        property_service = SupabasePropertyService()
        vector_service = VectorService()
        
        if not vector_service.initialized:
            logger.error("❌ Vector service failed to initialize")
            logger.error("Check your OpenAI and Pinecone API keys")
            return False
        
        logger.info("✅ Services initialized successfully")
        
        # Clear database if requested
        if clear_first:
            success = await clear_vector_database()
            if not success:
                logger.error("❌ Failed to clear vector database")
                return False
        
        # Get vector index stats
        stats = vector_service.get_index_stats()
        logger.info(f"📊 Current Pinecone index stats: {stats}")
        
        # Load all properties from Supabase
        logger.info("📥 Loading properties from Supabase...")
        start_time = time.time()
        properties = await property_service.get_all_properties_for_vectorization()
        load_time = time.time() - start_time
        
        if not properties:
            logger.error("❌ No properties found in Supabase")
            return False
        
        logger.info(f"✅ Loaded {len(properties)} properties from Supabase in {load_time:.1f}s")
        
        # Show sample property for verification
        sample_prop = properties[0]
        logger.info(f"📝 Sample property: {sample_prop.title} - R{sample_prop.price:,} in {sample_prop.location.city}")
        logger.info(f"   Features: {sample_prop.features[:3]}..." if sample_prop.features else "   No features listed")
        logger.info(f"   POI: {len(sample_prop.points_of_interest)} points of interest")
        logger.info(f"   Description length: {len(sample_prop.description)} characters")
        
        # Bulk upsert to Pinecone with progress tracking
        logger.info("🔄 Starting bulk vector embedding and upload to Pinecone...")
        logger.info("This will create embeddings using: title, description, features, location, and POI data")
        logger.info(f"Processing {len(properties)} properties in batches of 50...")
        
        start_time = time.time()
        success_count = await bulk_upsert_with_progress(vector_service, properties, batch_size=50)
        total_time = time.time() - start_time
        
        if success_count > 0:
            logger.info(f"🎉 Successfully processed {success_count}/{len(properties)} properties!")
            logger.info(f"⏱️ Total processing time: {total_time:.1f}s ({total_time/success_count:.2f}s per property)")
            
            # Get updated stats
            final_stats = vector_service.get_index_stats()
            logger.info(f"📊 Final Pinecone index stats: {final_stats}")
            
            # Test search functionality
            logger.info("🔍 Testing vector search...")
            test_results = await vector_service.search_similar_properties(
                query="3 bedroom house near schools in southern suburbs", 
                top_k=3
            )
            
            if test_results:
                logger.info("✅ Vector search test successful!")
                logger.info("Top 3 search results:")
                for i, (prop_id, score, metadata) in enumerate(test_results, 1):
                    prop_type = metadata.get('property_type', 'unknown')
                    price = metadata.get('price', 0)
                    city = metadata.get('city', 'unknown')
                    bedrooms = metadata.get('bedrooms', 'unknown')
                    logger.info(f"   {i}. Property {prop_id}: {prop_type} with {bedrooms} bedrooms in {city} - R{price:,} (score: {score:.3f})")
            else:
                logger.warning("⚠️ Vector search test returned no results")
            
            return True
        else:
            logger.error("❌ Failed to process any properties")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during vector loading: {e}")
        import traceback
        traceback.print_exc()
        return False

async def bulk_upsert_with_progress(vector_service, properties, batch_size: int = 50) -> int:
    """
    Bulk upsert with detailed progress tracking
    """
    success_count = 0
    total_properties = len(properties)
    
    logger.info(f"🚀 Starting bulk upsert of {total_properties} properties")
    
    # Process in batches
    for i in range(0, total_properties, batch_size):
        batch_num = (i // batch_size) + 1
        total_batches = (total_properties + batch_size - 1) // batch_size
        
        batch = properties[i:i + batch_size]
        batch_start_time = time.time()
        
        logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} properties)")
        logger.info(f"   Range: Properties {i+1} to {min(i + batch_size, total_properties)}")
        
        batch_vectors = []
        
        # Create embeddings for batch
        for j, property_data in enumerate(batch):
            try:
                prop_start_time = time.time()
                embedding_data = await vector_service.embed_property(property_data)
                embedding_time = time.time() - prop_start_time
                
                if embedding_data:
                    batch_vectors.append({
                        "id": embedding_data.property_id,
                        "values": embedding_data.embedding,
                        "metadata": embedding_data.metadata
                    })
                    
                    # Show progress every 10 properties within batch
                    if (j + 1) % 10 == 0 or j == len(batch) - 1:
                        logger.info(f"     ✓ Embedded {j+1}/{len(batch)} properties in batch (last took {embedding_time:.2f}s)")
                        
            except Exception as e:
                logger.error(f"❌ Failed to process property {property_data.id}: {e}")
                continue
        
        # Upsert batch to Pinecone
        if batch_vectors:
            try:
                upsert_start_time = time.time()
                vector_service.index.upsert(vectors=batch_vectors)
                upsert_time = time.time() - upsert_start_time
                
                success_count += len(batch_vectors)
                batch_time = time.time() - batch_start_time
                
                # Calculate progress stats
                progress_pct = (success_count / total_properties) * 100
                remaining = total_properties - success_count
                
                logger.info(f"✅ Batch {batch_num} completed: {len(batch_vectors)} properties upserted in {upsert_time:.2f}s")
                logger.info(f"📊 Progress: {success_count}/{total_properties} ({progress_pct:.1f}%) | {remaining} remaining")
                logger.info(f"⏱️ Batch total time: {batch_time:.1f}s | Avg per property: {batch_time/len(batch_vectors):.2f}s")
                
                if remaining > 0:
                    estimated_time_remaining = (batch_time / len(batch_vectors)) * remaining
                    logger.info(f"🕐 Estimated time remaining: {estimated_time_remaining/60:.1f} minutes")
                
                logger.info("-" * 60)
                
            except Exception as e:
                logger.error(f"❌ Failed to upsert batch {batch_num}: {e}")
        else:
            logger.warning(f"⚠️ No valid vectors in batch {batch_num}")
    
    logger.info(f"🏁 Bulk upsert completed: {success_count}/{total_properties} properties processed")
    return success_count

async def test_vector_search():
    """Test the vector search functionality with sample queries"""
    
    logger.info("\n🔍 Testing Vector Search with Sample Queries")
    logger.info("=" * 50)
    
    vector_service = VectorService()
    
    if not vector_service.initialized:
        logger.error("❌ Vector service not initialized")
        return
    
    # Test queries
    test_queries = [
        "3 bedroom house with garden near schools",
        "luxury apartment in city center with parking",
        "affordable property under R2 million in southern suburbs",
        "house with swimming pool and security features",
        "modern apartment with fiber internet and backup power"
    ]
    
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n🔍 Test Query {i}: '{query}'")
        
        try:
            results = await vector_service.search_similar_properties(query, top_k=3)
            
            if results:
                logger.info(f"✅ Found {len(results)} results:")
                for j, (prop_id, score, metadata) in enumerate(results, 1):
                    prop_type = metadata.get('property_type', 'unknown')
                    price = metadata.get('price', 0)
                    city = metadata.get('city', 'unknown')
                    bedrooms = metadata.get('bedrooms', 'unknown')
                    logger.info(f"   {j}. Property {prop_id}: {prop_type} with {bedrooms} bedrooms in {city} - R{price:,} (score: {score:.3f})")
            else:
                logger.warning(f"⚠️ No results for query: '{query}'")
                
        except Exception as e:
            logger.error(f"❌ Error testing query '{query}': {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load properties into Pinecone vector database")
    parser.add_argument("--test-only", action="store_true", help="Only test vector search, don't load data")
    parser.add_argument("--skip-load", action="store_true", help="Skip loading, only run tests")
    parser.add_argument("--clear", action="store_true", help="Clear vector database before loading")
    
    args = parser.parse_args()
    
    async def run():
        if args.test_only or args.skip_load:
            await test_vector_search()
        else:
            success = await load_properties_to_vector_db(clear_first=args.clear)
            
            if success:
                logger.info("\n🎉 Vector loading completed successfully!")
                logger.info("✅ Properties are now searchable via semantic search")
                logger.info("✅ Embeddings include: title, description, features, location, and POI data")
                logger.info("🚀 Ready for Phase 2 implementation!")
                
                # Run search tests
                await test_vector_search()
            else:
                logger.error("\n❌ Vector loading failed")
                logger.error("Please check the logs above for error details")
    
    # Run the async function
    asyncio.run(run())

if __name__ == "__main__":
    main() 