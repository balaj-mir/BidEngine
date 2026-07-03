import os
import logging
from typing import List, Dict, Any
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb

logger = logging.getLogger("bidengine.rag")

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = os.getenv("CHROMA_PORT", "8001")

class HybridRAGEngine:
    def __init__(self):
        # 1. Load SentenceTransformer
        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("RAG Engine loaded SentenceTransformer 'all-MiniLM-L6-v2'")
        except Exception as e:
            logger.error(f"Failed to load RAG Encoder: {e}")
            self.encoder = None

        # 2. Load CrossEncoder for Reranking
        try:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("RAG Engine loaded CrossEncoder 'cross-encoder/ms-marco-MiniLM-L-6-v2'")
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder reranker: {e}. Reranking will use semantic scores.")
            self.reranker = None

        # 3. Connect to ChromaDB
        self.chroma_client = None
        self.collection = None
        try:
            # Try connecting to HTTP client
            self.chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=int(CHROMA_PORT))
            self.collection = self.chroma_client.get_or_create_collection(
                "capability_library",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Connected to ChromaDB HTTP Client at {CHROMA_HOST}:{CHROMA_PORT}")
        except Exception as e:
            logger.warning(f"Could not connect to ChromaDB server: {e}. Falling back to Ephemeral Chroma Client.")
            try:
                # Ephemeral fallback
                self.chroma_client = chromadb.EphemeralClient()
                self.collection = self.chroma_client.get_or_create_collection(
                    "capability_library",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("Created Ephemeral ChromaDB Client.")
            except Exception as ex:
                logger.error(f"Failed to create Ephemeral ChromaDB Client: {ex}. Vector search will be mocked.")
                self.collection = None

        self.bm25_index = None
        self.bm25_docs: List[Dict[str, Any]] = []
        self.bm25_corpus: List[List[str]] = []

    def ingest_capability_library(self, records: List[Dict[str, Any]]):
        """Ingest all capability records into both BM25 and ChromaDB indexes"""
        if not records:
            logger.warning("No capability records to ingest.")
            return

        texts = []
        for r in records:
            text = f"{r['title']}. {r['description']}. Sector: {r['sector']}. "
            text += f"Client: {r['client_type']}. Keywords: {', '.join(r.get('keywords', []))}. "
            text += f"Certifications: {', '.join(r.get('certifications', []))}."
            texts.append(text)

        # Build BM25 index
        self.bm25_corpus = [t.lower().split() for t in texts]
        self.bm25_index = BM25Okapi(self.bm25_corpus)
        self.bm25_docs = records
        logger.info(f"Ingested {len(records)} docs into BM25 index.")

        # Build ChromaDB embeddings
        if self.collection and self.encoder:
            try:
                embeddings = self.encoder.encode(texts, batch_size=32, show_progress_bar=False)
                # Format for ChromaDB upsert
                ids = [str(r.get('id', r.get('_id'))) for r in records]
                documents = texts
                metadatas = [{
                    "title": r['title'],
                    "sector": r['sector'],
                    "client_type": r['client_type'],
                    "year": r.get('year_completed', 0),
                    "value": r.get('contract_value', 0)
                } for r in records]

                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    documents=documents,
                    metadatas=metadatas
                )
                logger.info(f"Ingested {len(records)} docs into ChromaDB.")
            except Exception as e:
                logger.error(f"Failed to upsert to ChromaDB: {e}")

    def match_requirement(self, requirement_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval: BM25 + Semantic -> Reciprocal Rank Fusion -> CrossEncoder reranking
        """
        if not self.bm25_docs:
            logger.warning("RAG Index is empty. Cannot match.")
            return []

        candidates_k = min(top_k * 3, len(self.bm25_docs))

        # 1. BM25 Retrieval
        tokens = requirement_text.lower().split()
        bm25_scores = []
        bm25_top_indices = []
        if self.bm25_index:
            bm25_scores = self.bm25_index.get_scores(tokens)
            bm25_top_indices = np.argsort(bm25_scores)[::-1][:candidates_k]
        else:
            bm25_scores = [0.0] * len(self.bm25_docs)
            bm25_top_indices = list(range(candidates_k))

        # 2. Semantic Retrieval
        chroma_ids = []
        chroma_sims = {}
        if self.collection and self.encoder:
            try:
                query_embedding = self.encoder.encode([requirement_text])[0]
                chroma_results = self.collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=candidates_k,
                    include=['documents', 'distances', 'metadatas']
                )
                if chroma_results and chroma_results['ids'] and chroma_results['ids'][0]:
                    chroma_ids = chroma_results['ids'][0]
                    chroma_distances = chroma_results['distances'][0]
                    # Cosine distance to similarity translation (1 - distance)
                    chroma_sims = {str(id_): float(1.0 - dist) for id_, dist in zip(chroma_ids, chroma_distances)}
            except Exception as e:
                logger.error(f"ChromaDB search failed: {e}")

        # 3. Reciprocal Rank Fusion (RRF, constant k=60)
        rrf_scores = {}
        
        # Add BM25 ranks
        for rank, idx in enumerate(bm25_top_indices):
            doc_id = str(self.bm25_docs[idx].get('id', self.bm25_docs[idx].get('_id')))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (60.0 + rank + 1)
            
        # Add Chroma ranks
        for rank, doc_id in enumerate(chroma_ids):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (60.0 + rank + 1)

        # Get top candidates for reranking
        sorted_candidates = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        top_candidate_ids = sorted_candidates[:candidates_k]

        # Map IDs back to objects
        top_candidates = []
        for c_id in top_candidate_ids:
            for d in self.bm25_docs:
                d_id = str(d.get('id', d.get('_id')))
                if d_id == c_id:
                    top_candidates.append(d)
                    break

        if not top_candidates:
            # Fallback to absolute index order
            top_candidates = self.bm25_docs[:top_k]

        # 4. CrossEncoder Reranking
        pairs = [(requirement_text, self._record_to_text(c)) for c in top_candidates]
        rerank_scores = []
        if self.reranker and pairs:
            try:
                rerank_scores = self.reranker.predict(pairs)
            except Exception as e:
                logger.error(f"Reranking failed: {e}")
                # Fallback to mock rerank scores based on RRF scores
                rerank_scores = [rrf_scores.get(str(c.get('id', c.get('_id'))), 0.0) * 10 for c in top_candidates]
        else:
            # Fallback scores
            rerank_scores = [rrf_scores.get(str(c.get('id', c.get('_id'))), 0.0) * 10 for c in top_candidates]

        # Assemble final results
        results = []
        for idx, (cap, rerank_score) in enumerate(zip(top_candidates, rerank_scores)):
            cap_id = str(cap.get('id', cap.get('_id')))
            
            # Normalize BM25 score
            doc_idx = -1
            for i, d in enumerate(self.bm25_docs):
                if str(d.get('id', d.get('_id'))) == cap_id:
                    doc_idx = i
                    break
            
            max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 else 1e-9
            b_score = float(bm25_scores[doc_idx] / max_bm25) if doc_idx != -1 and max_bm25 > 0 else 0.0
            s_score = float(chroma_sims.get(cap_id, 0.0))

            # Normalize CrossEncoder score to [0, 1] range (sigmoid approximation: (score + 10) / 20)
            # Clip between 0 and 1
            final_normalized = float((rerank_score + 10.0) / 20.0)
            final_normalized = max(0.0, min(1.0, final_normalized))

            results.append({
                "capability": cap,
                "semantic_score": s_score,
                "bm25_score": b_score,
                "rerank_score": float(rerank_score),
                "final_score": final_normalized,
                "match_method": "hybrid"
            })

        # Sort by final rerank score desc
        results.sort(key=lambda x: x['rerank_score'], reverse=True)
        return results[:top_k]

    def _record_to_text(self, record: Dict[str, Any]) -> str:
        return f"{record['title']}. {record['description']}. {' '.join(record.get('keywords', []))}"
