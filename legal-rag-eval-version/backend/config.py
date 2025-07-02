from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal

class Settings(BaseSettings):
    azure_api_key: str = Field(..., alias="AZURE_API_KEY")
    azure_endpoint: str = Field(..., alias="AZURE_ENDPOINT")
    azure_deployment: str = Field("gpt-4o-mini-toni", alias="AZURE_DEPLOYMENT")
    qdrant_url: str = Field("http://qdrant:6333", alias="QDRANT_URL")
    
    embedding_batch_size: int = 64
    upload_batch_size: int = 500
    max_memory_usage_percent: int = 80
    enable_text_preprocessing: bool = True
    
    # =================================
    # INFRASTRUCTURE PATHS
    # =================================
    bm25_path: str = Field("/indexes/bm25.pkl", alias="BM25_PATH")
    bm25_corpus_path: str = Field("/indexes/bm25_corpus.npy", alias="BM25_CORPUS_PATH")
    
    # =================================
    # FACTORY CONFIGURATIONS
    # =================================
    
    # Strategy Selection
    processing_mode: Literal["standard", "enriched"] = Field("standard", alias="PROCESSING_MODE")
    search_strategy: Literal["hybrid", "hybrid_enriched"] = Field("hybrid", alias="SEARCH_STRATEGY") 
    llm_provider: Literal["azure"] = Field("azure", alias="LLM_PROVIDER")
    rag_strategy: Literal["standard", "enriched"] = Field("standard", alias="RAG_STRATEGY")
    
    # Data Processing Parameters
    max_paragraph_length: int = Field(300, alias="MAX_PARAGRAPH_LENGTH")
    processing_batch_size: int = Field(1000, alias="PROCESSING_BATCH_SIZE")
    embedding_batch_size: int = Field(64, alias="EMBEDDING_BATCH_SIZE")
    upload_batch_size: int = Field(500, alias="UPLOAD_BATCH_SIZE")
    
    # Search Parameters
    dense_search_limit: int = Field(30, alias="DENSE_SEARCH_LIMIT")
    lexical_search_limit: int = Field(30, alias="LEXICAL_SEARCH_LIMIT")
    enable_reranking: bool = Field(True, alias="ENABLE_RERANKING")
    enable_query_caching: bool = Field(True, alias="ENABLE_QUERY_CACHING")
    
    # LLM Parameters
    llm_max_tokens: int = Field(300, alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(0.1, alias="LLM_TEMPERATURE")
    llm_timeout: int = Field(30, alias="LLM_TIMEOUT")
    llm_max_retries: int = Field(3, alias="LLM_MAX_RETRIES")
    
    # RAG Parameters
    max_results_per_query: int = Field(8, alias="MAX_RESULTS_PER_QUERY")
    rag_enable_streaming: bool = Field(False, alias="RAG_ENABLE_STREAMING")
    
    # Performance & System
    max_memory_usage_percent: int = Field(80, alias="MAX_MEMORY_USAGE_PERCENT")
    enable_text_preprocessing: bool = Field(True, alias="ENABLE_TEXT_PREPROCESSING")
    
    # =================================
    # PERFORMANCE OPTIMIZATION
    # =================================
    query_timeout: int = Field(45, alias="QUERY_TIMEOUT")
    enable_fast_mode: bool = Field(True, alias="ENABLE_FAST_MODE")
    skip_slow_reranking: bool = Field(False, alias="SKIP_SLOW_RERANKING")
    cache_size_limit: int = Field(200, alias="CACHE_SIZE_LIMIT")
    
    # Factory Control
    factory_log_level: Literal["DEBUG", "INFO", "WARNING"] = Field("INFO", alias="FACTORY_LOG_LEVEL")
    factory_lazy_loading: bool = Field(True, alias="FACTORY_LAZY_LOADING")
    factory_cache_instances: bool = Field(True, alias="FACTORY_CACHE_INSTANCES")

    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton pattern
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# =================================
# FACTORY HELPER FUNCTIONS
# =================================

def get_factory_config() -> dict:
    """Retorna configuración específica para factories"""
    settings = get_settings()
    return {
        "processing_mode": settings.processing_mode,
        "search_strategy": settings.search_strategy,
        "llm_provider": settings.llm_provider,
        "rag_strategy": settings.rag_strategy,
        "lazy_loading": settings.factory_lazy_loading,
        "cache_instances": settings.factory_cache_instances,
        "log_level": settings.factory_log_level
    }

def get_processing_config() -> dict:
    """Configuración específica para data processing"""
    settings = get_settings()
    return {
        "max_paragraph_length": settings.max_paragraph_length,
        "batch_size": settings.processing_batch_size
    }

def get_search_config() -> dict:
    """Configuración específica para search"""
    settings = get_settings()
    return {
        "k_dense": settings.dense_search_limit,
        "k_lex": settings.lexical_search_limit,
        "enable_reranking": settings.enable_reranking,
        "enable_caching": settings.enable_query_caching
    }

def get_llm_config() -> dict:
    """Configuración específica para LLM"""
    settings = get_settings()
    return {
        "max_tokens": settings.llm_max_tokens,
        "temperature": settings.llm_temperature,
        "timeout": settings.llm_timeout,
        "max_retries": settings.llm_max_retries
    }

def get_rag_config() -> dict:
    """Configuración específica para RAG"""
    settings = get_settings()
    return {
        "max_results": settings.max_results_per_query,
        "enable_streaming": settings.rag_enable_streaming
    }
