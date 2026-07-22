"""LLM 冒烟测试 — 验证 DeepSeek API 真实可达。

IDEA-033: 真实 API 冒烟测试。需要 DEEPSEEK_API_KEY 环境变量。
在 CI 中自动跳过（无 API Key 时）。
"""

import os
import pytest
import json
from typing import Optional

pytestmark = pytest.mark.skipif(
    not os.environ.get("DEEPSEEK_API_KEY")
    and not os.environ.get("JIG_API_KEY"),
    reason="需要 DEEPSEEK_API_KEY 或 JIG_API_KEY 环境变量",
)


def _get_api_key() -> Optional[str]:
    return os.environ.get("JIG_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")


def _build_request(messages: list, model: str = "deepseek-v4-flash") -> dict:
    return {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 100,
    }


class TestDeepSeekReachability:
    """DeepSeek API 真实连通性测试。"""

    API_URL = "https://api.deepseek.com/v1/chat/completions"

    @pytest.mark.network
    def test_basic_chat_completion(self):
        """基础对话：发送简单的 Hello 消息，验证返回格式。"""
        api_key = _get_api_key()
        if not api_key:
            pytest.skip("No API key configured")

        import httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = _build_request([
            {"role": "user", "content": "Reply with just the word: OK"},
        ])

        with httpx.Client(timeout=15) as client:
            response = client.post(self.API_URL, json=payload, headers=headers)

        assert response.status_code == 200, f"API returned {response.status_code}: {response.text}"
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        content = data["choices"][0].get("message", {}).get("content", "")
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.network
    def test_flash_model_works(self):
        """Flash 模型可正常调用。"""
        api_key = _get_api_key()
        if not api_key:
            pytest.skip("No API key configured")

        import httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = _build_request(
            [{"role": "user", "content": "Say hello in one word"}],
            model="deepseek-v4-flash",
        )

        with httpx.Client(timeout=15) as client:
            response = client.post(self.API_URL, json=payload, headers=headers)

        assert response.status_code == 200
        assert response.json()["choices"][0]["message"]["content"]

    @pytest.mark.network
    def test_pro_model_works(self):
        """Pro 模型可正常调用。"""
        api_key = _get_api_key()
        if not api_key:
            pytest.skip("No API key configured")

        import httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = _build_request(
            [{"role": "user", "content": "Return JSON: {\"status\":\"ok\"}"}],
            model="deepseek-v4-pro",
        )

        with httpx.Client(timeout=30) as client:
            response = client.post(self.API_URL, json=payload, headers=headers)

        assert response.status_code == 200

    @pytest.mark.network
    def test_error_on_invalid_key(self):
        """无效 API Key 应返回 401。"""
        headers = {
            "Authorization": "Bearer sk-invalid-key",
            "Content-Type": "application/json",
        }
        payload = _build_request([{"role": "user", "content": "hi"}])

        import httpx
        with httpx.Client(timeout=10) as client:
            response = client.post(self.API_URL, json=payload, headers=headers)

        assert response.status_code == 401
