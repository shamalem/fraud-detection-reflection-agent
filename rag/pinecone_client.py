"""Pinecone index connection for the fraud-policy knowledge base."""
from functools import lru_cache

from pinecone import Pinecone

from config import settings


@lru_cache(maxsize=1)
def get_index():
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index)
