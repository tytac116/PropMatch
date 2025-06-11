"""
BM25 Hybrid Search Service
Combines BM25 keyword matching with vector search and AI re-ranking for maximum precision
"""

import logging
import asyncio
import time
import math
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
import re

from app.models.property import Property, PropertySearchRequest
from app.services.supabase_property_service import SupabasePropertyService
from app.services.vector_service import VectorService
from app.services.ai_rerank_service import AIRerankService

logger = logging.getLogger(__name__)

class BM25HybridService:
    """
    Hybrid search combining BM25 keyword matching + Vector similarity + AI re-ranking
    This should provide the best of all worlds: exact matching, semantic similarity, and intelligent reasoning
    """
    
    def __init__(self):
        self.property_service = SupabasePropertyService()
        self.vector_service = VectorService()
        self.ai_rerank_service = AIRerankService()
        
        # BM25 parameters (tuned for property search)
        self.k1 = 1.5  # Term frequency saturation parameter
        self.b = 0.75  # Length normalization parameter
        
        # NEW HYBRID SCORING WEIGHTS - AI-DOMINANT APPROACH
        # AI gets the highest weight because it has superior reasoning and context understanding
        self.vector_weight = 0.3    # Vector semantic similarity weight (reduced)
        self.bm25_weight = 0.2      # BM25 keyword matching weight (reduced)
        self.ai_weight = 0.5        # AI contextual understanding weight (INCREASED - now dominant)
        
        # Property corpus for BM25 (will be built on first use)
        self.corpus_built = False
        self.properties_corpus = []
        self.doc_lengths = []
        self.avgdl = 0
        self.doc_freqs = {}
        self.idf_cache = {}
        
    async def hybrid_search_and_rerank(self, search_request: PropertySearchRequest) -> Tuple[List[Property], Dict[str, Any]]:
        """
        Perform hybrid search: Vector + BM25 + AI re-ranking
        Returns: (ranked_properties, detailed_metrics)
        """
        
        timing = {}
        start_time = time.time()
        
        logger.info(f"Starting BM25 Hybrid search for: {search_request.query}")
        
        try:
            # Step 1: Get larger candidate set from vector search
            vector_start = time.time()
            vector_results = await self.vector_service.search_similar_properties(
                query=search_request.query,
                top_k=min(search_request.page_size * 6, 60),  # Larger candidate pool
                filter_dict=None
            )
            
            if not vector_results:
                return [], {"error": "No vector results found"}
            
            # Get properties for BM25 and AI processing
            property_ids = [int(prop_id) for prop_id, _, _ in vector_results]
            candidate_properties = await self.property_service.get_properties_batch(property_ids)
            
            if not candidate_properties:
                return [], {"error": "No properties found"}
            
            # Store vector scores
            vector_scores = {str(prop_id): score for prop_id, score, _ in vector_results}
            timing['vector_search_ms'] = round((time.time() - vector_start) * 1000, 1)
            
            # Step 2: Build BM25 corpus if needed
            corpus_start = time.time()
            if not self.corpus_built:
                await self._build_bm25_corpus()
            timing['corpus_build_ms'] = round((time.time() - corpus_start) * 1000, 1)
            
            # Step 3: Calculate BM25 scores
            bm25_start = time.time()
            bm25_scores = self._calculate_bm25_scores(search_request.query, candidate_properties)
            timing['bm25_calculation_ms'] = round((time.time() - bm25_start) * 1000, 1)
            
            # Step 4: Apply hybrid scoring (Vector + BM25)
            hybrid_start = time.time()
            hybrid_scored_properties = self._apply_hybrid_scoring(
                candidate_properties, vector_scores, bm25_scores
            )
            timing['hybrid_scoring_ms'] = round((time.time() - hybrid_start) * 1000, 1)
            logger.info(f"Hybrid scoring completed, got {len(hybrid_scored_properties)} properties")
            
            # Step 5: AI re-ranking for final intelligence layer
            ai_start = time.time()
            if self.ai_rerank_service.openai_client:  # Re-enable AI
                # Take top candidates for AI re-ranking
                top_candidates = hybrid_scored_properties[:search_request.page_size * 2]
                logger.info(f"Sending {len(top_candidates)} properties to AI re-ranking")
                
                # Use AI service but preserve our hybrid base scores
                ai_ranked_properties = await self.ai_rerank_service._intelligent_rerank_with_batching(
                    top_candidates, search_request.query
                )
                
                # Combine hybrid scores with AI scores using weighted approach
                final_properties = self._combine_hybrid_and_ai_scores(
                    ai_ranked_properties, hybrid_scored_properties
                )
                logger.info(f"AI re-ranking completed, got {len(final_properties)} final properties")
            else:
                logger.info("AI not available - using hybrid scores only")
                final_properties = hybrid_scored_properties
            
            timing['ai_rerank_ms'] = round((time.time() - ai_start) * 1000, 1)
            
            # Final selection
            result_properties = final_properties[:search_request.page_size]
            
            # Compile detailed metrics
            timing['total_ms'] = round((time.time() - start_time) * 1000, 1)
            timing['token_usage'] = getattr(self.ai_rerank_service, 'token_usage', {})
            
            # Add scoring breakdown for analysis (this might be where the error occurs)
            try:
                scoring_analysis = self._analyze_scoring_breakdown(result_properties, vector_scores, bm25_scores)
                timing['scoring_analysis'] = scoring_analysis
            except Exception as e:
                logger.error(f"Error in scoring analysis: {e}")
                timing['scoring_analysis'] = {"error": str(e)}
            
            logger.info(f"BM25 Hybrid search completed in {timing['total_ms']}ms")
            logger.info(f"Vector: {timing['vector_search_ms']}ms, BM25: {timing['bm25_calculation_ms']}ms, AI: {timing['ai_rerank_ms']}ms")
            
            return result_properties, timing
            
        except Exception as e:
            logger.error(f"Error in hybrid_search_and_rerank: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e
    
    async def _build_bm25_corpus(self):
        """Build BM25 corpus from all properties for accurate IDF calculations"""
        
        logger.info("Building BM25 corpus for property search...")
        
        # Get a representative sample of properties for corpus building
        # In production, you might want to build this offline
        sample_properties = await self.property_service.get_properties_sample(1000)  # Sample for corpus
        
        self.properties_corpus = []
        self.doc_lengths = []
        term_doc_count = defaultdict(int)
        total_length = 0
        
        for prop in sample_properties:
            # Create searchable text from property
            doc_text = self._create_bm25_document_text(prop)
            doc_terms = self._tokenize_text(doc_text)
            
            self.properties_corpus.append(doc_terms)
            doc_length = len(doc_terms)
            self.doc_lengths.append(doc_length)
            total_length += doc_length
            
            # Count document frequency for each term
            unique_terms = set(doc_terms)
            for term in unique_terms:
                term_doc_count[term] += 1
        
        # Calculate average document length and IDF values
        self.avgdl = total_length / len(self.properties_corpus) if self.properties_corpus else 0
        
        # Calculate IDF for each term
        total_docs = len(self.properties_corpus)
        for term, doc_freq in term_doc_count.items():
            self.idf_cache[term] = math.log((total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
        
        self.corpus_built = True
        logger.info(f"BM25 corpus built: {total_docs} documents, {len(self.idf_cache)} unique terms")
    
    def _create_bm25_document_text(self, prop: Property) -> str:
        """Create searchable text representation of a property for BM25"""
        
        text_parts = []
        
        # Property type and basics
        text_parts.append(str(prop.type).lower() if prop.type else "")
        text_parts.append(f"{prop.bedrooms} bedroom" if prop.bedrooms else "")
        text_parts.append(f"{prop.bathrooms} bathroom" if prop.bathrooms else "")
        
        # Location information
        if prop.location:
            text_parts.append(prop.location.neighborhood.lower())
            text_parts.append(prop.location.city.lower())
            # Add province if it exists
            if hasattr(prop.location, 'province') and prop.location.province:
                text_parts.append(prop.location.province.lower())
        
        # Features
        if prop.features:
            for feature in prop.features:
                text_parts.append(feature.lower())
        
        # POIs - important for location-based queries
        if prop.points_of_interest:
            for poi in prop.points_of_interest[:10]:  # Top 10 POIs
                text_parts.append(poi.name.lower())
        
        # Price range context
        if prop.price:
            if prop.price < 1500000:
                text_parts.append("affordable budget")
            elif prop.price < 3000000:
                text_parts.append("mid range")
            elif prop.price > 6000000:
                text_parts.append("luxury premium")
        
        return " ".join(filter(None, text_parts))
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25 processing"""
        
        # Simple but effective tokenization for property search
        text = text.lower()
        # Remove special characters but keep numbers and letters
        text = re.sub(r'[^\w\s]', ' ', text)
        # Split and filter short tokens
        tokens = [token for token in text.split() if len(token) > 1]
        
        return tokens
    
    def _calculate_bm25_scores(self, query: str, properties: List[Property]) -> Dict[str, float]:
        """Calculate BM25 scores for query against properties"""
        
        query_terms = self._tokenize_text(query)
        bm25_scores = {}
        
        for prop in properties:
            doc_text = self._create_bm25_document_text(prop)
            doc_terms = self._tokenize_text(doc_text)
            doc_length = len(doc_terms)
            
            # Calculate BM25 score
            score = 0.0
            term_frequencies = Counter(doc_terms)
            
            for term in query_terms:
                if term in term_frequencies:
                    tf = term_frequencies[term]
                    idf = self.idf_cache.get(term, 0)  # Default IDF of 0 for unknown terms
                    
                    # BM25 formula
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avgdl))
                    score += idf * (numerator / denominator)
            
            bm25_scores[str(prop.listing_number)] = max(0, score)  # Ensure non-negative
        
        return bm25_scores
    
    def _apply_hybrid_scoring(self, properties: List[Property], vector_scores: Dict[str, float], 
                            bm25_scores: Dict[str, float]) -> List[Property]:
        """Apply hybrid scoring combining vector and BM25 scores with improved normalization"""
        
        hybrid_properties = []
        
        # Get BM25 score statistics for intelligent scaling
        bm25_vals = list(bm25_scores.values())
        bm25_max = max(bm25_vals) if bm25_vals else 0
        bm25_avg = sum(bm25_vals) / len(bm25_vals) if bm25_vals else 0
        
        for prop in properties:
            prop_id = str(prop.listing_number)
            
            # Vector scores are already in 0-100 range - use them directly!
            vector_score = vector_scores.get(prop_id, 0)
            # Convert to 0-100 scale (vector scores are typically 0-1)
            vector_100 = vector_score * 100 if vector_score <= 1.0 else vector_score
            
            # BM25 score processing - scale intelligently
            raw_bm25 = bm25_scores.get(prop_id, 0)
            
            # Scale BM25 to contribute meaningfully but not dominate
            if bm25_max > 0:
                # Scale BM25 to 0-20 range (so it enhances but doesn't overpower vector scores)
                bm25_contribution = min(20, (raw_bm25 / bm25_max) * 20)
            else:
                bm25_contribution = 0
            
            # Hybrid base score: Vector foundation + BM25 enhancement
            # Formula: Strong vector base + BM25 boost for exact matches
            hybrid_score = vector_100 + (bm25_contribution * 0.5)  # BM25 provides up to 10 point boost
            
            # Ensure reasonable bounds
            hybrid_score = min(100, max(10, hybrid_score))
            
            # Store component scores for analysis
            prop_copy = prop.model_copy(deep=True)
            prop_copy.searchScore = hybrid_score
            
            # Store detailed component scores
            setattr(prop_copy, 'vector_score', vector_score)
            setattr(prop_copy, 'vector_100', vector_100)
            setattr(prop_copy, 'bm25_score', raw_bm25)
            setattr(prop_copy, 'bm25_contribution', bm25_contribution)
            setattr(prop_copy, 'hybrid_base_score', hybrid_score)
            
            hybrid_properties.append(prop_copy)
        
        # Sort by hybrid score
        hybrid_properties.sort(key=lambda x: x.searchScore, reverse=True)
        
        return hybrid_properties
    
    def _combine_hybrid_and_ai_scores(self, ai_properties: List[Property], 
                                    hybrid_properties: List[Property]) -> List[Property]:
        """
        NEW AI-CENTRIC SCORING: Let AI lead, with vector+BM25 providing enhancement
        AI has the most sophisticated understanding, so it should be the primary driver
        """
        
        # Create mapping of hybrid base scores
        hybrid_base_scores = {}
        for prop in hybrid_properties:
            hybrid_base_scores[str(prop.listing_number)] = getattr(prop, 'hybrid_base_score', 50.0)
        
        final_properties = []
        
        for prop in ai_properties:
            prop_id = str(prop.listing_number)
            ai_score = getattr(prop, 'searchScore', 50.0)
            hybrid_base = hybrid_base_scores.get(prop_id, 50.0)
            
            # NEW AI-DOMINANT SCORING LOGIC
            # Philosophy: AI knows best, use hybrid as enhancement only when it helps
            
            if ai_score >= 85:
                # AI found excellent match - trust it completely with small hybrid boost if helpful
                if hybrid_base >= 75:
                    final_score = ai_score + 2  # Small boost for confirming hybrid signals
                else:
                    final_score = ai_score  # Trust AI completely
                    
            elif ai_score >= 70:
                # AI found good match - blend favorably with hybrid confirmation
                if hybrid_base >= 70:
                    final_score = 0.7 * ai_score + 0.3 * hybrid_base + 3  # Strong AI with hybrid confirmation
                else:
                    final_score = 0.8 * ai_score + 0.2 * hybrid_base  # Mostly trust AI
                    
            elif ai_score >= 50:
                # AI found moderate match - let hybrid provide more input
                final_score = 0.6 * ai_score + 0.4 * hybrid_base
                
            elif ai_score <= 30:
                # AI detected poor/impossible match - trust this completely, don't let hybrid inflate
                if hybrid_base <= 40:
                    final_score = ai_score  # Both agree it's poor - trust AI
                else:
                    final_score = 0.8 * ai_score + 0.2 * hybrid_base  # Mostly trust AI's poor assessment
                    
            else:
                # Standard middle-ground blending (31-49 range)
                final_score = 0.65 * ai_score + 0.35 * hybrid_base
            
            # Ensure reasonable bounds with AI-appropriate ranges
            final_score = min(100, max(10, final_score))
            
            # Store final score and components
            prop_copy = prop.model_copy(deep=True)
            prop_copy.searchScore = final_score
            setattr(prop_copy, 'ai_score', ai_score)
            setattr(prop_copy, 'hybrid_base_score', hybrid_base)
            setattr(prop_copy, 'final_score_method', self._get_ai_centric_scoring_method(ai_score, hybrid_base))
            
            final_properties.append(prop_copy)
        
        # Final sort by AI-centric combined score
        final_properties.sort(key=lambda x: x.searchScore, reverse=True)
        
        return final_properties
    
    def _get_ai_centric_scoring_method(self, ai_score: float, hybrid_base: float) -> str:
        """Get description of which AI-centric scoring method was used"""
        if ai_score >= 85:
            return "ai_excellent_trusted" if hybrid_base < 75 else "ai_excellent_with_hybrid_boost"
        elif ai_score >= 70:
            return "ai_good_hybrid_confirmed" if hybrid_base >= 70 else "ai_good_mostly_trusted"
        elif ai_score >= 50:
            return "ai_hybrid_balanced"
        elif ai_score <= 30:
            return "ai_poor_trusted" if hybrid_base <= 40 else "ai_poor_mostly_trusted"
        else:
            return "ai_moderate_blend"
    
    def _analyze_scoring_breakdown(self, properties: List[Property], vector_scores: Dict[str, float], 
                                 bm25_scores: Dict[str, float]) -> Dict[str, Any]:
        """Analyze scoring breakdown for debugging and optimization"""
        
        analysis = {
            "properties_analyzed": len(properties),
            "score_distribution": {},
            "component_averages": {},
            "score_ranges": {}
        }
        
        if not properties:
            return analysis
        
        # Collect component scores safely
        final_scores = [getattr(prop, 'searchScore', 0) for prop in properties]
        ai_scores = [getattr(prop, 'ai_score', 0) for prop in properties if hasattr(prop, 'ai_score')]
        hybrid_base_scores = [getattr(prop, 'hybrid_base_score', 0) for prop in properties if hasattr(prop, 'hybrid_base_score')]
        
        # Calculate statistics with safe defaults
        analysis["component_averages"] = {
            "final_score": sum(final_scores) / len(final_scores) if final_scores else 0,
            "ai_score": sum(ai_scores) / len(ai_scores) if ai_scores else 0,
            "hybrid_base": sum(hybrid_base_scores) / len(hybrid_base_scores) if hybrid_base_scores else 0
        }
        
        analysis["score_ranges"] = {
            "final": {"min": min(final_scores) if final_scores else 0, "max": max(final_scores) if final_scores else 0},
            "ai": {"min": min(ai_scores) if ai_scores else 0, "max": max(ai_scores) if ai_scores else 0},
            "hybrid_base": {"min": min(hybrid_base_scores) if hybrid_base_scores else 0, "max": max(hybrid_base_scores) if hybrid_base_scores else 0}
        }
        
        # Weight effectiveness
        analysis["hybrid_weights"] = {
            "vector_weight": self.vector_weight,
            "bm25_weight": self.bm25_weight,
            "ai_weight": self.ai_weight
        }
        
        # Add corpus information
        analysis["bm25_corpus_stats"] = {
            "corpus_built": self.corpus_built,
            "corpus_size": len(self.properties_corpus) if self.corpus_built else 0,
            "unique_terms": len(self.idf_cache) if self.corpus_built else 0
        }
        
        return analysis 