"""集成测试：多模型 + 流式 — ModelRouter 合并 + SSE 链路。"""
import pytest
from jig.adapters.model_provider import ModelRouter


class _MockProvider:
    def __init__(self, name="mock"):
        self._name = name

    @property
    def model_name(self):
        return self._name

    def chat(self, messages, **kw):
        class MockResp:
            content = f"mock from {self._name}"
        return MockResp()

    async def chat_stream(self, messages, **kw):
        class MockChunk:
            content = "mock chunk"
            event = "chunk"
        yield MockChunk()


def test_model_router_register_and_get():
    """注册 provider 后应能获取。"""
    router = ModelRouter()
    router.register("deepseek", _MockProvider("deepseek-v4-flash"))
    p = router.get("deepseek")
    assert p is not None
    assert p.model_name == "deepseek-v4-flash"


def test_model_router_default_provider():
    """第一个注册的 provider 应为默认。"""
    router = ModelRouter()
    router.register("ds", _MockProvider("ds"))
    router.register("openai", _MockProvider("gpt-4o"))
    assert router._default_provider == "ds"


def test_model_router_route_creates_session():
    """route() 应创建 session_id。"""
    router = ModelRouter()
    r = router.route("flash")
    assert "session_id" in r
    assert r["model_grade"] == "flash"


def test_model_router_route_reuses_session():
    """同一 model_grade 应复用 session。"""
    router = ModelRouter()
    r1 = router.route("flash")
    r2 = router.route("flash")
    assert r1["session_id"] == r2["session_id"]


def test_model_router_reset_session():
    """reset_session 应清除 session。"""
    router = ModelRouter()
    r1 = router.route("pro")
    router.reset_session("pro")
    r2 = router.route("pro")
    assert r1["session_id"] != r2["session_id"]


def test_model_router_available():
    """available 应列出已注册的 provider。"""
    router = ModelRouter()
    router.register("a", _MockProvider("a"))
    router.register("b", _MockProvider("b"))
    assert "a" in router.available
    assert "b" in router.available


def test_model_router_chat():
    """chat() 应路由到指定 provider。"""
    router = ModelRouter()
    router.register("ds", _MockProvider("ds"), set_default=True)
    resp = router.chat([{"role": "user", "content": "hi"}])
    assert resp is not None
    assert "mock" in resp.content
