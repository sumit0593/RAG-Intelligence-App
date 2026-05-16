import os
import math
from pinecone import Pinecone
from rank_bm25 import BM25Okapi
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Dict, Any

class EnterpriseRetriever:
    def __init__(self):
        self.api_key = os.environ.get("PINECONE_API_KEY", "")
        self.index_name = os.environ.get("PINECONE_INDEX_NAME", "enterprise-rag-index")
        self._corpus: List[str] = []  # In-memory BM25 corpus for current session
        self._bm25: BM25Okapi = None

        # Initialize Pinecone (official 'pinecone' SDK v6+)
        try:
            self.pc = Pinecone(api_key=self.api_key)
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            print(f"Failed to initialize Pinecone: {e}")
            self.index = None

        # Initialize Gemini Embeddings
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="gemini-embedding-001",
                google_api_key=os.environ.get("GEMINI_API_KEY", "")
            )
        except Exception as e:
            print(f"Failed to initialize Gemini Embeddings: {e}")
            self.embeddings = None

    def _build_bm25(self, corpus: List[str]):
        """Build or rebuild BM25 index from a list of texts."""
        tokenized = [doc.lower().split() for doc in corpus]
        self._bm25 = BM25Okapi(tokenized)
        self._corpus = corpus

    def _bm25_scores(self, query: str, corpus: List[str]) -> List[float]:
        """Return normalized BM25 scores for each corpus document given the query."""
        if not corpus:
            return []
        tokenized = [doc.lower().split() for doc in corpus]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())
        # Normalize to [0, 1]
        max_score = max(scores) if max(scores) > 0 else 1.0
        return [float(s / max_score) for s in scores]

    def index_documents(self, chunks: List[Dict[str, Any]]):
        """Embed and upsert document chunks into Pinecone."""
        if not self.index or not self.embeddings:
            print("Pinecone index or embeddings not available.")
            return

        vectors = []
        for i, chunk in enumerate(chunks):
            text = chunk["page_content"]
            metadata = chunk["metadata"]

            # Dense embedding via Gemini
            try:
                dense_vec = self.embeddings.embed_query(text)
            except Exception as e:
                print(f"Embedding error for chunk {i}: {e}")
                continue

            vectors.append({
                "id": metadata.get("chunk_id", f"chunk_{i}"),
                "values": dense_vec,
                "metadata": metadata
            })

        # Batch upsert to Pinecone
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            self.index.upsert(vectors=vectors[i:i + batch_size])

        print(f"Indexed {len(vectors)} chunks into Pinecone.")

    def hybrid_search(self, query: str, allowed_roles: List[str], top_k: int = 5, alpha: float = 0.7) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval: dense Pinecone vector search + BM25 keyword re-scoring.
        alpha controls blend weight: 1.0 = fully dense, 0.0 = fully keyword.
        RBAC is enforced via Pinecone metadata filter on 'allowed_roles'.
        """
        if not self.index or not self.embeddings:
            return []

        # ── Step 1: Dense vector search with metadata RBAC filter ────────────
        try:
            dense_vec = self.embeddings.embed_query(query)
        except Exception as e:
            print(f"Embedding error: {e}")
            return []

        filter_dict = {"allowed_roles": {"$in": allowed_roles}}

        try:
            results = self.index.query(
                vector=dense_vec,
                top_k=top_k * 2,          # Fetch extra for reranking
                include_metadata=True,
                filter=filter_dict
            )
        except Exception as e:
            print(f"Pinecone query error: {e}")
            return []

        matches = results.get("matches", [])
        if not matches:
            return []

        # ── Step 2: BM25 keyword re-scoring over retrieved chunks ────────────
        texts = [m["metadata"].get("text", "") for m in matches]
        bm25_scores = self._bm25_scores(query, texts)

        # ── Step 3: Combine scores (alpha-weighted hybrid) ───────────────────
        combined = []
        for i, match in enumerate(matches):
            dense_score = match.get("score", 0.0)
            sparse_score = bm25_scores[i] if i < len(bm25_scores) else 0.0
            hybrid_score = (alpha * dense_score) + ((1.0 - alpha) * sparse_score)
            combined.append({
                "chunk_id": match["id"],
                "score": round(hybrid_score, 4),
                "dense_score": round(dense_score, 4),
                "bm25_score": round(sparse_score, 4),
                "text": match["metadata"].get("text", ""),
                "metadata": match["metadata"]
            })

        # Sort by hybrid score descending, return top_k
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]
