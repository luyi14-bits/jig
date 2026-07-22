"""Tests for ImageReader multimodal bridge."""

from jig.tools.image_reader import ImageReader
from jig.adapters.model_provider import ModelRouter


class TestImageReader:
    def test_init(self):
        router = ModelRouter()
        tool = ImageReader(router=router, provider="openai")
        assert tool._provider == "openai"

    def test_nonexistent_file(self):
        tool = ImageReader()
        result = tool.read("/nonexistent/photo.jpg")
        assert "无法加载" in result

    def test_call_shortcut(self):
        tool = ImageReader()
        result = tool("/nonexistent/photo.jpg")
        assert "无法加载" in result

    def test_max_size_check(self):
        tool = ImageReader(max_size_mb=1)  # 1MB
        assert tool._max_bytes == 1048576

    def test_no_router_configured(self):
        tool = ImageReader()
        result = tool.read("/some/file.jpg")
        assert "无法加载" in result or "未配置" in result
