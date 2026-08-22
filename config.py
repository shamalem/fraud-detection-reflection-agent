"""Central configuration, read from environment variables (see .env.example)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # LLMod.ai (course-issued key, shared across the group)
    llmod_api_key: str = os.getenv("LLMOD_API_KEY", "")
    llmod_base_url: str = os.getenv("LLMOD_BASE_URL", "https://api.llmod.ai")

    # Models - must match the course spec exactly
    chat_model: str = os.getenv("CHAT_MODEL", "MB5R2CF-azure/gpt-5.4-mini")
    embed_model: str = os.getenv("EMBED_MODEL", "MB5R2CF-azure/text-embedding-3-small")

    # Supabase (primary transaction database)
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_SECRET_KEY", "")
    supabase_table: str = os.getenv("SUPABASE_TABLE", "fraud_dataset")

    # Pinecone (fraud-policy knowledge vector index)
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index: str = os.getenv("PINECONE_INDEX", "fraud-agent")
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))

    # Agent loop limits
    max_planner_iterations: int = int(os.getenv("MAX_PLANNER_ITERATIONS", "6"))
    max_reflection_cycles: int = int(os.getenv("MAX_REFLECTION_CYCLES", "3"))


settings = Settings()
