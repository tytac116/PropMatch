"""
Vector Search Service for PropMatch
Handles property embeddings and similarity search using Pinecone
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import numpy as np
from dataclasses import dataclass

# AI and Vector DB imports
from langchain_openai import OpenAIEmbeddings
import openai
from pinecone import Pinecone as PineconeClient

from app.core.config import settings
from app.models.property import Property

logger = logging.getLogger(__name__)

@dataclass
class PropertyEmbeddingData:
    """Data structure for property embeddings"""
    property_id: str
    embedding: List[float]
    metadata: Dict[str, Any]
    text_content: str

class VectorService:
    """Service for vector operations and similarity search"""
    
    def __init__(self):
        self.embeddings = None
        self.pinecone_client = None
        self.index = None
        self.initialized = False
        
        # Initialize if API keys are available
        if settings.OPENAI_API_KEY and settings.PINECONE_API_KEY:
            self._initialize()
    
    def _initialize(self):
        """Initialize OpenAI embeddings and Pinecone client"""
        try:
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL,
                client=None  # Explicitly set client to None to avoid proxy issues
            )
            
            # Initialize Pinecone
            self.pinecone_client = PineconeClient(api_key=settings.PINECONE_API_KEY)
            
            # Check if index exists, create if not
            index_name = settings.PINECONE_INDEX_NAME
            existing_indexes = [index.name for index in self.pinecone_client.list_indexes()]
            
            if index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {index_name}")
                self.pinecone_client.create_index(
                    name=index_name,
                    dimension=1536,  # OpenAI text-embedding-3-small dimension
                    metric='cosine',
                    spec={
                        'serverless': {
                            'cloud': 'aws',
                            'region': 'us-east-1'
                        }
                    }
                )
            
            self.index = self.pinecone_client.Index(index_name)
            self.initialized = True
            logger.info("Vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            self.initialized = False
    
    def create_property_text(self, property_data: Property) -> str:
        """Create searchable text content from property data"""
        
        # Core property info
        text_parts = [
            f"Property type: {property_data.type.value if hasattr(property_data.type, 'value') else property_data.type}",
            f"Title: {property_data.title}",
            f"Price: R{property_data.price:,}",
            f"Location: {property_data.location.neighborhood}, {property_data.location.city}",
            f"Bedrooms: {property_data.bedrooms}",
            f"Bathrooms: {property_data.bathrooms}",
            f"Area: {property_data.area}m²"
        ]
        
        # Add description
        if property_data.description:
            text_parts.append(f"Description: {property_data.description}")
        
        # Add features
        if property_data.features:
            features_text = ", ".join(property_data.features)
            text_parts.append(f"Features: {features_text}")
        
        # Add points of interest for location context
        if property_data.points_of_interest:
            poi_texts = []
            for poi in property_data.points_of_interest[:10]:  # Limit to avoid token limits
                poi_texts.append(f"{poi.name} ({poi.distance_str})")
            
            if poi_texts:
                text_parts.append(f"Nearby: {', '.join(poi_texts)}")
        
        return " | ".join(text_parts)
    
    def create_property_metadata(self, property_data: Property) -> Dict[str, Any]:
        """Create metadata for filtering and retrieval"""
        
        metadata = {
            "property_id": property_data.id,
            "property_type": property_data.type.value if hasattr(property_data.type, 'value') else str(property_data.type),
            "price": property_data.price,
            "bedrooms": property_data.bedrooms,
            "bathrooms": property_data.bathrooms,
            "area": property_data.area,
            "city": property_data.location.city,
            "neighborhood": property_data.location.neighborhood,
            "status": property_data.status.value if hasattr(property_data.status, 'value') else str(property_data.status)
        }
        
        # Add points of interest for distance-based filtering
        if property_data.points_of_interest:
            # Find closest schools, hospitals, etc.
            poi_by_category = {}
            for poi in property_data.points_of_interest:
                category = poi.category.lower()
                if category not in poi_by_category or poi.distance < poi_by_category[category]:
                    poi_by_category[category] = poi.distance
            
            # Add closest POI distances to metadata
            for category, distance in poi_by_category.items():
                metadata[f"closest_{category}_km"] = round(distance, 2)
        
        return metadata
    
    async def embed_property(self, property_data: Property) -> Optional[PropertyEmbeddingData]:
        """Create embedding for a single property"""
        
        if not self.initialized:
            logger.warning("Vector service not initialized")
            return None
        
        try:
            # Create text content
            text_content = self.create_property_text(property_data)
            
            # Generate embedding (using synchronous method)
            embedding = self.embeddings.embed_query(text_content)
            
            # Create metadata
            metadata = self.create_property_metadata(property_data)
            
            return PropertyEmbeddingData(
                property_id=property_data.id,
                embedding=embedding,
                metadata=metadata,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Failed to embed property {property_data.id}: {e}")
            return None
    
    async def upsert_property(self, property_data: Property) -> bool:
        """Add or update property in vector database"""
        
        if not self.initialized:
            logger.warning("Vector service not initialized")
            return False
        
        try:
            # Create embedding
            embedding_data = await self.embed_property(property_data)
            if not embedding_data:
                return False
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[{
                    "id": embedding_data.property_id,
                    "values": embedding_data.embedding,
                    "metadata": embedding_data.metadata
                }]
            )
            
            logger.info(f"Successfully upserted property {property_data.id} to vector DB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert property {property_data.id}: {e}")
            return False
    
    async def search_similar_properties(
        self,
        query: str,
        top_k: int = 50,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar properties using vector similarity
        
        Returns: List of (property_id, similarity_score, metadata) tuples
        """
        
        if not self.initialized:
            logger.warning("Vector service not initialized")
            return []
        
        try:
            # Create query embedding (using synchronous method)
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in Pinecone
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Process results
            results = []
            for match in search_results.matches:
                results.append((
                    match.id,
                    float(match.score),
                    match.metadata or {}
                ))
            
            logger.info(f"Vector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def bulk_upsert_properties(self, properties: List[Property], batch_size: int = 100) -> int:
        """
        Bulk upsert multiple properties to vector database
        
        Returns: Number of successfully processed properties
        """
        
        if not self.initialized:
            logger.warning("Vector service not initialized")
            return 0
        
        success_count = 0
        total_properties = len(properties)
        
        logger.info(f"Starting bulk upsert of {total_properties} properties")
        
        # Process in batches
        for i in range(0, total_properties, batch_size):
            batch = properties[i:i + batch_size]
            batch_vectors = []
            
            # Create embeddings for batch
            for property_data in batch:
                try:
                    embedding_data = await self.embed_property(property_data)
                    if embedding_data:
                        batch_vectors.append({
                            "id": embedding_data.property_id,
                            "values": embedding_data.embedding,
                            "metadata": embedding_data.metadata
                        })
                except Exception as e:
                    logger.error(f"Failed to process property {property_data.id}: {e}")
                    continue
            
            # Upsert batch to Pinecone
            if batch_vectors:
                try:
                    self.index.upsert(vectors=batch_vectors)
                    success_count += len(batch_vectors)
                    logger.info(f"Processed batch {i//batch_size + 1}, {success_count}/{total_properties} properties")
                except Exception as e:
                    logger.error(f"Failed to upsert batch: {e}")
        
        logger.info(f"Bulk upsert completed: {success_count}/{total_properties} properties processed")
        return success_count
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index"""
        
        if not self.initialized:
            return {"status": "not_initialized"}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                "status": "initialized",
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"status": "error", "error": str(e)} 