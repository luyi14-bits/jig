"""Model Provider 抽象层 — 多模型支持。

IDEA-058: 让 Jig 支持 DeepSeek / OpenAI / Anthropic / Ollama 等多种模型。
"""

from __future__ import annotations
import abc
import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    """统一模型响应格式。"""
    content: str
    model: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens
    finish_reason: str = "stop"
    cache_hit: bool = False


@dataclass
class StreamChunk:
    """流式输出块。"""
    content: str
    done: bool = False
    finish_reason: str = ""


class BaseModelProvider(abc.ABC):
    """模型提供者抽象基类。"""

    @abc.abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> ModelResponse:
        """同步对话。"""
        ...

    @abc.abstractmethod
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncIterator[StreamChunk]:
        """流式对话。"""
        ...

    @abc.abstractmethod
    def count_tokens(self, text: str) -> int:
        """估算 token 数。"""
        ...

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        """模型名称。"""
        ...


class DeepSeekProvider(BaseModelProvider):
    """DeepSeek 模型提供者（默认）。"""

    API_BASE = "https://api.deepseek.com/v1"

    def __init__(self, api_key: str = "", model: str = "deepseek-v4-flash"):
        self._api_key = api_key
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    def chat(self, messages: List[Dict], **kwargs) -> ModelResponse:
        import httpx
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", self._model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        if "reasoning_effort" in kwargs:
            payload["reasoning_effort"] = kwargs["reasoning_effort"]

        with httpx.Client(timeout=60) as client:
            resp = client.post(f"{self.API_BASE}/chat/completions", json=payload, headers=headers)

        if resp.status_code != 200:
            raise RuntimeError(f"DeepSeek API error: {resp.status_code} {resp.text}")

        data = resp.json()
        choice = data["choices"][0]
        return ModelResponse(
            content=choice["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncIterator[StreamChunk]:
        import httpx
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", self._model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.API_BASE}/chat/completions", json=payload, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk_data = line[6:].strip()
                    if chunk_data == "[DONE]":
                        yield StreamChunk(content="", done=True, finish_reason="stop")
                        return
                    try:
                        chunk = json.loads(chunk_data)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        finish = chunk["choices"][0].get("finish_reason", "")
                        yield StreamChunk(content=content, done=bool(finish), finish_reason=finish)
                    except json.JSONDecodeError:
                        continue

    def count_tokens(self, text: str) -> int:
        return int(len(text) * 1.3)  # rough estimate for Chinese + English


class OpenAIProvider(BaseModelProvider):
    """OpenAI 兼容 API 提供者（可对接任何 OpenAI 兼容服务）。"""

    def __init__(self, api_key: str = "", model: str = "gpt-4o", base_url: str = "https://api.openai.com/v1"):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    @property
    def model_name(self) -> str:
        return self._model

    def chat(self, messages: List[Dict], **kwargs) -> ModelResponse:
        import httpx
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", self._model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        with httpx.Client(timeout=60) as client:
            resp = client.post(f"{self._base_url}/chat/completions", json=payload, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"API error: {resp.status_code} {resp.text}")
        data = resp.json()
        choice = data["choices"][0]
        return ModelResponse(
            content=choice["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncIterator[StreamChunk]:
        import httpx
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", self._model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self._base_url}/chat/completions", json=payload, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk_data = line[6:].strip()
                    if chunk_data == "[DONE]":
                        yield StreamChunk(content="", done=True, finish_reason="stop")
                        return
                    try:
                        chunk = json.loads(chunk_data)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        finish = chunk["choices"][0].get("finish_reason", "")
                        yield StreamChunk(content=content, done=bool(finish), finish_reason=finish)
                    except json.JSONDecodeError:
                        continue

    def count_tokens(self, text: str) -> int:
        return int(len(text) * 1.3)


class ModelRouter:
    """模型路由器 — 管理 Provider 注册 + Pro/Flash session 路由。"""

    def __init__(self):
        self._providers: Dict[str, BaseModelProvider] = {}
        self._default_provider: str = ""
        # Pro/Flash session 管理（从 model_router 合并）
        self._sessions: Dict[str, str] = {}
        self._prefix_snapshots: Dict[str, str] = {}
        # 响应缓存（接线 ResponseCache）
        from .response_cache import ResponseCache
        self._cache = ResponseCache(ttl_seconds=300)

    def register(self, name: str, provider: BaseModelProvider, set_default: bool = False) -> None:
        self._providers[name] = provider
        if set_default or not self._default_provider:
            self._default_provider = name
        logger.info("Model provider registered: %s (%s)", name, provider.model_name)

    def get(self, name: str = "") -> BaseModelProvider:
        if not name:
            name = self._default_provider
        provider = self._providers.get(name)
        if not provider:
            raise KeyError(f"No provider registered: {name}. Available: {list(self._providers.keys())}")
        return provider

    def chat(self, messages: List[Dict], provider: str = "", **kwargs) -> ModelResponse:
        # 缓存命中（仅对非流式、无 tools 的请求）
        if not kwargs.get("tools"):
            prompt_key = str(messages)[-200:]
            cached = self._cache.get(prompt_key)
            if cached:
                return ModelResponse(
                    content=cached,
                    model=self.get(provider).model_name,
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    cache_hit=True,
                )
            response = self.get(provider).chat(messages, **kwargs)
            if response.content:
                self._cache.set(prompt_key, response.content)
            return response
        return self.get(provider).chat(messages, **kwargs)

    async def chat_stream(self, messages: List[Dict], provider: str = "", **kwargs) -> AsyncIterator[StreamChunk]:
        async for chunk in self.get(provider).chat_stream(messages, **kwargs):
            yield chunk

    def route(self, model_grade: str) -> Dict[str, Any]:
        """路由到指定模型等级的 session（Pro/Flash 兼容）。"""
        is_pro = model_grade == "pro"
        from ..settings import settings
        model_name = settings.pro_model if is_pro else settings.flash_model
        temperature = settings.pro_temperature if is_pro else settings.flash_temperature
        if model_grade not in self._sessions:
            import uuid
            session_id = f"session_{model_grade}_{uuid.uuid4().hex[:8]}"
            self._sessions[model_grade] = session_id
        return {"model_name": model_name, "model_grade": model_grade, "temperature": temperature,
                "session_id": self._sessions[model_grade]}

    def reset_session(self, model_grade: str) -> None:
        old_id = self._sessions.pop(model_grade, None)
        if old_id:
            logger.info("session 已重置: %s (model=%s)", old_id, model_grade)

    def get_session_id(self, model_grade: str) -> Optional[str]:
        return self._sessions.get(model_grade)

    @property
    def available(self) -> List[str]:
        return list(self._providers.keys())
