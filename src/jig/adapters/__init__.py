"""Adapters — DeepSeek API 适配层 + 上下文压缩体系。"""
from .model_router import ModelRouter, ModelRoute
from .deepseek_adapter import DeepSeekAdapter
from .cache_engine import CacheEngine, CacheDiagnostic, CacheStats, PrefixSnapshot
from .context import ContextPartitioner, PartitionedContext
from .model_provider import BaseModelProvider, DeepSeekProvider, ModelResponse, StreamChunk
from .cost_aware_router import CostAwareRouter, TokenBudget
from .streaming import StreamManager, StreamEvent
from .external_agent import ExternalAgentAdapter, MetaHarness
from .mcp_client import MCPClient

__all__ = [
    "ModelRouter",
    "ModelRoute",
    "DeepSeekAdapter",
    "CacheEngine",
    "CacheDiagnostic",
    "CacheStats",
    "PrefixSnapshot",
    "ContextPartitioner",
    "PartitionedContext",
    "BaseModelProvider",
    "DeepSeekProvider",
    "ModelResponse",
    "StreamChunk",
    "CostAwareRouter",
    "TokenBudget",
    "StreamManager",
    "StreamEvent",
    "ExternalAgentAdapter",
    "MetaHarness",
    "MCPClient",
]
