"""Thin LLMod.ai client wrapper (OpenAI-compatible chat + embeddings API)."""
from functools import lru_cache

from openai import OpenAI

from config import settings


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(api_key=settings.llmod_api_key, base_url=settings.llmod_base_url)
