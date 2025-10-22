"""
app/core/strategy.py

Loads and validates the hybrid strategy configuration and exposes
helpers to select providers, routing, and feature flags.
"""

from __future__ import annotations

from pydantic import BaseModel
from pathlib import Path
import json
from typing import List, Dict, Optional


class IntentClassificationCfg(BaseModel):
    primary: str
    secondary: Optional[str] = None
    backup: List[str] = []
    cache: Optional[str] = None
    confidence_threshold: float = 0.7


class EmbeddingsCfg(BaseModel):
    primary: str
    backup: List[str] = []
    fallback: str = "hash"
    cache: Optional[str] = None


class ResponseRoutingCfg(BaseModel):
    factual: Optional[str] = None
    creative: Optional[str] = None
    code: Optional[str] = None


class ResponseGenerationCfg(BaseModel):
    primary: str
    backup: List[str] = []
    static_fallback: str = "Sorry, I couldn’t process that request."
    routing: ResponseRoutingCfg = ResponseRoutingCfg()


class ExternalCfg(BaseModel):
    web_search: List[str] = ["google_cse", "serpapi"]
    youtube: List[str] = ["youtube_data_v3"]
    calendar: List[str] = ["google_calendar"]
    gmail: List[str] = ["gmail_api"]


class MemoryCfg(BaseModel):
    short_term: str = "redis"
    long_term: str = "pinecone"
    graph: str = "neo4j"
    auth: str = "mongodb"
    local_backup: bool = True


class SystemMonitorCfg(BaseModel):
    health_check_interval: str = "5m"
    rate_limit_auto_switch: bool = True
    log_to: Optional[str] = None


class HybridStrategy(BaseModel):
    intent_classification: IntentClassificationCfg
    embeddings: EmbeddingsCfg
    response_generation: ResponseGenerationCfg
    external: ExternalCfg
    memory: MemoryCfg
    system_monitor: SystemMonitorCfg

    def provider_chain(self, category: str) -> List[str]:
        if category == "intent":
            chain = [self.intent_classification.primary]
            if self.intent_classification.secondary:
                chain.append(self.intent_classification.secondary)
            chain.extend(self.intent_classification.backup)
            return chain
        if category == "embeddings":
            chain = [self.embeddings.primary]
            chain.extend(self.embeddings.backup)
            chain.append(self.embeddings.fallback)
            return chain
        if category == "generation":
            chain = [self.response_generation.primary]
            chain.extend(self.response_generation.backup)
            return chain
        raise ValueError(f"Unknown category: {category}")


_strategy: Optional[HybridStrategy] = None


def load_strategy(config_path: Optional[str] = None) -> HybridStrategy:
    global _strategy
    if _strategy is not None:
        return _strategy

    path = Path(config_path) if config_path else Path(__file__).with_name("hybrid_strategy.json")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    _strategy = HybridStrategy.model_validate(data)
    return _strategy


def get_strategy() -> HybridStrategy:
    if _strategy is None:
        return load_strategy()
    return _strategy


def should_use_cache(category: str) -> bool:
    s = get_strategy()
    if category == "intent":
        return (s.intent_classification.cache or "").lower() == "redis"
    if category == "embeddings":
        return (s.embeddings.cache or "").lower() == "redis"
    return False


def route_for(tag: str) -> Optional[str]:
    s = get_strategy()
    r = s.response_generation.routing
    return getattr(r, tag, None)
