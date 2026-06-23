"""
Qdrant Vector DB client — init, upsert, search, and playbook seeding.
Collection: lexai_playbooks
Vector size: 384 (all-MiniLM-L6-v2)
"""
import logging
import uuid
from typing import Optional

from core.config import settings

logger = logging.getLogger(__name__)

# Payload schema stored alongside each vector:
# {
#   "clause_type": str,
#   "playbook_id": str,
#   "playbook_clause_id": str,
#   "title": str,
#   "standard_text": str,
#   "playbook": str,         # e.g. "Standard Corporate Playbook §4.3"
#   "contract_type": str | null
# }


def get_qdrant_client():
    from qdrant_client import QdrantClient

    kwargs: dict = {"url": settings.QDRANT_URL}
    if settings.QDRANT_API_KEY:
        kwargs["api_key"] = settings.QDRANT_API_KEY
    return QdrantClient(**kwargs)


async def init_qdrant():
    """Create collection on startup if it doesn't exist."""
    try:
        from qdrant_client.models import VectorParams, Distance

        client = get_qdrant_client()
        existing = [c.name for c in client.get_collections().collections]

        if settings.QDRANT_COLLECTION not in existing:
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=settings.QDRANT_VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"[Qdrant] Created collection '{settings.QDRANT_COLLECTION}'")
        else:
            logger.info(f"[Qdrant] Collection '{settings.QDRANT_COLLECTION}' ready.")
    except ImportError:
        logger.warning("[Qdrant] qdrant-client not installed. Vector search disabled.")
    except Exception as e:
        logger.warning(f"[Qdrant] Startup check failed: {e}")


def get_embedder():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(settings.EMBEDDING_MODEL)
    except ImportError:
        return None


def embed_texts(texts: list[str], embedder=None) -> list[list[float]]:
    if embedder is None:
        embedder = get_embedder()
    if embedder:
        return embedder.encode(
            texts,
            normalize_embeddings=True,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
        ).tolist()
    # Stub embeddings
    import hashlib
    result = []
    for text in texts:
        h = int(hashlib.md5(text.encode()).hexdigest(), 16)
        result.append([(((h >> i) & 0xFF) / 255.0) for i in range(settings.QDRANT_VECTOR_SIZE)])
    return result


async def upsert_playbook_clauses(
    playbook_id: str,
    playbook_name: str,
    contract_type: Optional[str],
    clauses: list[dict],           # list of {clause_type, title, standard_text, id?}
) -> dict[str, str]:
    """
    Embeds and upserts playbook clauses into Qdrant.
    Returns mapping of clause id -> qdrant vector id.
    """
    try:
        from qdrant_client.models import PointStruct

        client = get_qdrant_client()
        embedder = get_embedder()

        texts = [c["standard_text"] for c in clauses]
        vectors = embed_texts(texts, embedder)

        points = []
        vector_ids = []
        for clause, vector in zip(clauses, vectors):
            vid = str(uuid.uuid4())
            vector_ids.append(vid)
            points.append(PointStruct(
                id=vid,
                vector=vector,
                payload={
                    "clause_type": clause["clause_type"],
                    "playbook_id": playbook_id,
                    "playbook_clause_id": clause.get("id", ""),
                    "title": clause["title"],
                    "standard_text": clause["standard_text"],
                    "playbook": playbook_name,
                    "contract_type": contract_type,
                },
            ))

        client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
        logger.info(f"[Qdrant] Upserted {len(points)} vectors for playbook '{playbook_name}'")
        return {
            clause.get("id", ""): vid
            for clause, vid in zip(clauses, vector_ids)
            if clause.get("id")
        }

    except Exception as e:
        logger.error(f"[Qdrant] Upsert failed: {e}")
        return {}


def search_similar_clauses(
    clause_text: str,
    clause_type: Optional[str] = None,
    top_k: int = 5,
) -> list[dict]:
    """Synchronous search for use in non-async contexts."""
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = get_qdrant_client()
        vector = embed_texts([clause_text])[0]

        query_filter = None
        if clause_type:
            query_filter = Filter(
                must=[FieldCondition(key="clause_type", match=MatchValue(value=clause_type))]
            )

        hits = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "id": str(h.id),
                "score": round(h.score, 4),
                **h.payload,
            }
            for h in hits
        ]
    except Exception as e:
        logger.warning(f"[Qdrant] Search failed: {e}")
        return []


async def delete_playbook_vectors(playbook_id: str) -> bool:
    """Remove all vectors for a given playbook (e.g., on playbook update)."""
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = get_qdrant_client()
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[FieldCondition(key="playbook_id", match=MatchValue(value=playbook_id))]
            ),
        )
        logger.info(f"[Qdrant] Deleted vectors for playbook {playbook_id}")
        return True
    except Exception as e:
        logger.error(f"[Qdrant] Delete failed: {e}")
        return False


def get_collection_info() -> dict:
    """Return stats about the Qdrant collection."""
    try:
        client = get_qdrant_client()
        info = client.get_collection(settings.QDRANT_COLLECTION)
        return {
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "status": info.status,
        }
    except Exception as e:
        return {"error": str(e), "vectors_count": 0}
