"""
Factory Manager Centralizado
Gestiona la creación y configuración de todos los componentes usando config centralizada
"""
import logging
from typing import Dict, Any, Optional
from .config import get_settings, get_factory_config

logger = logging.getLogger(__name__)

class FactoryManager:
    """Manager centralizado para todos los factories"""
    
    def __init__(self):
        self.settings = get_settings()
        self.config = get_factory_config()
        self._instances = {} if self.config["cache_instances"] else None
        
        # Setup logging level para factories
        factory_logger = logging.getLogger("backend")
        factory_logger.setLevel(self.config["log_level"])
        
        logger.info(f"🏭 FactoryManager initialized with strategies:")
        logger.info(f"   Data: {self.settings.processing_mode}")
        logger.info(f"   Search: {self.settings.search_strategy}")
        logger.info(f"   LLM: {self.settings.llm_provider}")
        logger.info(f"   RAG: {self.settings.rag_strategy}")
    
    def get_processor(self, mode: Optional[str] = None, **kwargs):
        """Get data processor usando configuración centralizada"""
        mode = mode or self.settings.processing_mode
        
        if self._should_cache("processor", mode):
            if f"processor_{mode}" in self._instances:
                logger.debug(f"♻️ Reusing cached processor_{mode}")
                return self._instances[f"processor_{mode}"]
        
        from .data import get_processor
        from .config import get_processing_config
        
        config = get_processing_config()
        processor = get_processor(mode, **{**config, **kwargs})
        
        if self._should_cache("processor", mode):
            self._instances[f"processor_{mode}"] = processor
            logger.debug(f"💾 Cached processor_{mode}")
            
        return processor
    
    def get_retriever(self, strategy: Optional[str] = None, **kwargs):
        """Get retriever usando configuración centralizada"""
        strategy = strategy or self.settings.search_strategy
        
        if self._should_cache("retriever", strategy):
            if f"retriever_{strategy}" in self._instances:
                logger.debug(f"♻️ Reusing cached retriever_{strategy}")
                return self._instances[f"retriever_{strategy}"]
        
        from .search import get_retriever
        from .config import get_search_config
        
        config = get_search_config()
        retriever = get_retriever(strategy, **{**config, **kwargs})
        
        if self._should_cache("retriever", strategy):
            self._instances[f"retriever_{strategy}"] = retriever
            logger.debug(f"💾 Cached retriever_{strategy}")
            
        return retriever
    
    def get_llm_provider(self, provider: Optional[str] = None, **kwargs):
        """Get LLM provider usando configuración centralizada"""
        provider = provider or self.settings.llm_provider
        
        if self._should_cache("llm", provider):
            if f"llm_{provider}" in self._instances:
                logger.debug(f"♻️ Reusing cached llm_{provider}")
                return self._instances[f"llm_{provider}"]
        
        from .llm import get_llm_provider
        from .config import get_llm_config
        
        config = get_llm_config()
        llm = get_llm_provider(provider, **{**config, **kwargs})
        
        if self._should_cache("llm", provider):
            self._instances[f"llm_{provider}"] = llm
            logger.debug(f"💾 Cached llm_{provider}")
            
        return llm
    
    def get_rag_pipeline(self, strategy: Optional[str] = None, **kwargs):
        """Get RAG pipeline usando configuración centralizada"""
        strategy = strategy or self.settings.rag_strategy
        
        if self._should_cache("rag", strategy):
            if f"rag_{strategy}" in self._instances:
                logger.debug(f"♻️ Reusing cached rag_{strategy}")
                return self._instances[f"rag_{strategy}"]
        
        from .rag import get_rag_pipeline
        
        # No pasar config para standard, ya que lee de env vars
        if strategy == "standard":
            pipeline = get_rag_pipeline(strategy)
        else:
            from .config import get_rag_config
            config = get_rag_config()
            pipeline = get_rag_pipeline(strategy, **{**config, **kwargs})
        
        if self._should_cache("rag", strategy):
            self._instances[f"rag_{strategy}"] = pipeline
            logger.debug(f"💾 Cached rag_{strategy}")
            
        return pipeline
    
    def _should_cache(self, component: str, strategy: str) -> bool:
        """Determina si debe cachear la instancia"""
        return self._instances is not None and self.config["cache_instances"]
    
    def clear_cache(self, component: Optional[str] = None):
        """Limpia cache de instancias"""
        if self._instances is None:
            return
        
        if component:
            keys_to_remove = [k for k in self._instances.keys() if k.startswith(f"{component}_")]
            for key in keys_to_remove:
                del self._instances[key]
            logger.info(f"🗑️ Cleared {component} cache ({len(keys_to_remove)} instances)")
        else:
            count = len(self._instances)
            self._instances.clear()
            logger.info(f"🗑️ Cleared all factory cache ({count} instances)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del factory manager"""
        cached_count = len(self._instances) if self._instances else 0
        return {
            "strategies": {
                "processing_mode": self.settings.processing_mode,
                "search_strategy": self.settings.search_strategy,
                "llm_provider": self.settings.llm_provider,
                "rag_strategy": self.settings.rag_strategy
            },
            "config": {
                "lazy_loading": self.config["lazy_loading"],
                "cache_instances": self.config["cache_instances"],
                "log_level": self.config["log_level"]
            },
            "cached_instances": cached_count,
            "cached_components": list(self._instances.keys()) if self._instances else []
        }

# Singleton global
_factory_manager = None

def get_factory_manager() -> FactoryManager:
    """Singleton para el factory manager"""
    global _factory_manager
    if _factory_manager is None:
        _factory_manager = FactoryManager()
    return _factory_manager

# Funciones de conveniencia que usan el manager
def get_configured_processor(**kwargs):
    """Get processor con configuración automática"""
    return get_factory_manager().get_processor(**kwargs)

def get_configured_retriever(**kwargs):
    """Get retriever con configuración automática"""
    return get_factory_manager().get_retriever(**kwargs)

def get_configured_llm(**kwargs):
    """Get LLM con configuración automática"""
    return get_factory_manager().get_llm_provider(**kwargs)

def get_configured_rag(**kwargs):
    """Get RAG con configuración automática"""
    return get_factory_manager().get_rag_pipeline(**kwargs)