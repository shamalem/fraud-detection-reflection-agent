"""Embedding calls against LLMod.ai, used both to build and to query the Pinecone index."""
from config import settings
from llm.llmod_client import get_client


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = get_client().embeddings.create(model=settings.embed_model, input=texts)
    return [item.embedding for item in response.data]
