"""Adapters — DeepSeek API 适配层 + 上下文压缩体系。"""
from .model_router import ModelRouter, ModelRoute
from .deepseek_adapter import DeepSeekAdapter
from .cache_engine import CacheEngine, CacheDiagnostic, CacheStats, PrefixSnapshot
from .context import ContextPartitioner, PartitionedContext
from .repo_map import RepoMapBuilder, PySymbolExtractor
from .conversation_compressor import ConversationCompressor
from .embedding_index import EmbeddingIndex
from .model_provider import BaseModelProvider, DeepSeekProvider, OpenAIProvider, ModelResponse, StreamChunk
from .cost_aware_router import CostAwareRouter, TokenBudget
from .streaming import StreamManager, StreamEvent
from .external_agent import ExternalAgentAdapter, MetaHarness
from .mcp_client import MCPClient
from .a2a_protocol import A2AMessage, A2ARouter

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
    "RepoMapBuilder",
    "PySymbolExtractor",
    "ConversationCompressor",
    "EmbeddingIndex",
    "BaseModelProvider",
    "DeepSeekProvider",
    "OpenAIProvider",
    "ModelResponse",
    "StreamChunk",
    "CostAwareRouter",
    "TokenBudget",
    "StreamManager",
    "StreamEvent",
    "ExternalAgentAdapter",
    "MetaHarness",
    "MCPClient",
    "A2AMessage",
    "A2ARouter",
]
