"""
RAG Pipeline: Embedding + ChromaDB vector store + retrieval.
Uses sentence-transformers locally (no API key required).
Uses native chromadb client directly (avoids langchain_community deprecation issues).
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from app.core.config import get_settings


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline using native ChromaDB client.
    Embeds documents using SentenceTransformers (local, free).
    """

    def __init__(self):
        settings = get_settings()
        self._persist_dir = Path(settings.chroma_persist_dir)
        self._collection_name = settings.chroma_collection_name
        self._top_k = settings.rag_top_k
        self._chunk_size = settings.rag_chunk_size
        self._chunk_overlap = settings.rag_chunk_overlap
        self._embedding_model_name = settings.embedding_model

        self._persist_dir.mkdir(parents=True, exist_ok=True)

        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        self._ef = SentenceTransformerEmbeddingFunction(
            model_name=self._embedding_model_name
        )
        self._client: chromadb.ClientAPI | None = None
        self._collection: chromadb.Collection | None = None

    def init_vectorstore(self) -> None:
        """Initialize or load existing ChromaDB persistent store."""
        try:
            self._client = chromadb.PersistentClient(path=str(self._persist_dir))
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )
            count = self._collection.count()
            logger.info(
                f"ChromaDB ready — collection '{self._collection_name}' "
                f"has {count} documents."
            )
        except Exception as exc:
            logger.error(f"Failed to init ChromaDB: {exc}")
            self._collection = None

    def ingest_documents(self, documents: List[Document]) -> int:
        """Split and embed documents into ChromaDB. Returns chunk count."""
        if self._collection is None:
            self.init_vectorstore()
        if self._collection is None:
            return 0

        chunks = self._text_splitter.split_documents(documents)
        if not chunks:
            return 0

        try:
            ids = [f"doc_{i}" for i in range(self._collection.count(), self._collection.count() + len(chunks))]
            texts = [c.page_content for c in chunks]
            metadatas = [c.metadata for c in chunks]
            self._collection.add(documents=texts, metadatas=metadatas, ids=ids)
            logger.info(f"Ingested {len(chunks)} chunks into ChromaDB.")
            return len(chunks)
        except Exception as exc:
            logger.error(f"Ingestion error: {exc}")
            return 0

    def retrieve(self, query: str, k: int | None = None) -> List[Tuple[Document, float]]:
        """Retrieve top-k relevant documents. Returns (Document, score) tuples."""
        if self._collection is None:
            return []

        top_k = k or self._top_k
        count = self._collection.count()
        if count == 0:
            return []

        top_k = min(top_k, count)
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            docs_out: List[Tuple[Document, float]] = []
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            for text, meta, dist in zip(documents, metadatas, distances):
                score = max(0.0, 1.0 - dist)  # cosine distance → similarity
                docs_out.append((Document(page_content=text, metadata=meta or {}), score))
            return docs_out
        except Exception as exc:
            logger.error(f"Retrieval error: {exc}")
            return []

    def retrieve_as_context(self, query: str, k: int | None = None) -> str:
        """Return retrieved chunks as a formatted context string."""
        results = self.retrieve(query, k)
        if not results:
            return ""
        parts = []
        for i, (doc, score) in enumerate(results, 1):
            source = doc.metadata.get("source", "Knowledge Base")
            parts.append(f"[Source {i}: {source} | Relevance: {score:.2f}]\n{doc.page_content}")
        return "\n\n---\n\n".join(parts)

    @property
    def is_ready(self) -> bool:
        if self._collection is None:
            return False
        try:
            return self._collection.count() > 0
        except Exception:
            return False


# Module-level singleton
_rag_pipeline: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
        _rag_pipeline.init_vectorstore()
    return _rag_pipeline
