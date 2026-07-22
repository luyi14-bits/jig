"""Tests for ModelProvider and streaming."""

import pytest
from jig.adapters.model_provider import (
    ModelRouter,
    DeepSeekProvider,
    OpenAIProvider,
    ModelResponse,
    StreamChunk,
)


class TestModelRouter:
    def test_register_and_get(self):
        router = ModelRouter()
        provider = DeepSeekProvider(api_key="test", model="deepseek-v4-flash")
        router.register("deepseek", provider, set_default=True)
        assert router.get("deepseek") is provider
        assert router.get() is provider

    def test_default_provider(self):
        router = ModelRouter()
        d1 = DeepSeekProvider(api_key="k1")
        d2 = DeepSeekProvider(api_key="k2")
        router.register("a", d1)
        router.register("b", d2, set_default=True)
        assert router.get() is d2

    def test_available_list(self):
        router = ModelRouter()
        router.register("a", DeepSeekProvider(api_key="k"))
        router.register("b", OpenAIProvider(api_key="k"))
        assert set(router.available) == {"a", "b"}

    def test_get_nonexistent_raises(self):
        router = ModelRouter()
        with pytest.raises(KeyError):
            router.get("nonexistent")

    def test_count_tokens(self):
        provider = DeepSeekProvider(api_key="test")
        count = provider.count_tokens("hello world")
        assert count > 0

    def test_openai_provider_init(self):
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o", base_url="https://api.openai.com/v1")
        assert provider.model_name == "gpt-4o"
        assert provider._api_key == "test-key"

    def test_deepseek_provider_init(self):
        provider = DeepSeekProvider(api_key="sk-test", model="deepseek-v4-pro")
        assert provider.model_name == "deepseek-v4-pro"
        assert provider._api_key == "sk-test"


class TestStreamChunk:
    def test_basic_chunk(self):
        chunk = StreamChunk(content="hello", done=False)
        assert chunk.content == "hello"
        assert not chunk.done

    def test_done_chunk(self):
        chunk = StreamChunk(content="", done=True, finish_reason="stop")
        assert chunk.done
        assert chunk.finish_reason == "stop"


class TestModelResponse:
    def test_basic_response(self):
        resp = ModelResponse(
            content="Hello!",
            model="deepseek-v4-flash",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )
        assert resp.content == "Hello!"
        assert resp.usage["prompt_tokens"] == 10
