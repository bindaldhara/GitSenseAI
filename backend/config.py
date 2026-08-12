from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "GitSense AI"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    redis_url: str 
    qdrant_url: str
    repository_clone_dir: str
    llm_provider: str = "ollama"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    bm25_index_dir: str = "data/bm25_indices"
    hybrid_search_enabled: bool = True
    hybrid_rrf_k: int = 60
    hybrid_candidate_multiplier: int = 4
    rerank_enabled: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    semantic_cache_enabled: bool = True
    semantic_cache_similarity_threshold: float = 0.85
    semantic_cache_ttl_seconds: int = 86_400
    semantic_cache_max_entries_per_repo: int = 100
    agents_enabled: bool = True
    graph_rag_enabled: bool = True
    auth_enabled: bool = True
    admin_email: str = "admin@gmail.com"
    supabase_url: str
    supabase_jwt_secret: str | None = None

    @computed_field
    @property
    def bm25_index_path(self) -> Path:
        path = Path(self.bm25_index_dir)
        if path.is_absolute():
            return path.resolve()
        return (BACKEND_ROOT / path).resolve()

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def repository_clone_path(self) -> Path:
        path = Path(self.repository_clone_dir)
        if path.is_absolute():
            return path.resolve()
        return (BACKEND_ROOT / path).resolve()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
