"""Query interface over the Pinecone fraud-policy index.

Unlike a fixed lookup, the search query itself is written by the Planner LLM based on
the evidence gathered so far - this module only embeds that query and returns matches.
"""
from config import settings
from rag.embeddings import embed_texts
from rag.pinecone_client import get_index


def search_fraud_knowledge(query: str, top_k: int = settings.retrieval_top_k) -> list[dict]:
    query_embedding = embed_texts([query])[0]

    result = get_index().query(vector=query_embedding, top_k=top_k, include_metadata=True)

    matches = []
    for match in result.matches:
        matches.append(
            {
                "score": float(match.score),
                "source": match.metadata.get("source"),
                "page": match.metadata.get("page"),
                "chunk_number": match.metadata.get("chunk_number"),
                "text": match.metadata.get("text"),
            }
        )
    return matches
