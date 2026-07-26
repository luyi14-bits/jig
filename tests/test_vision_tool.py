"""Tests for contrib VisionTool (optional plugin)."""

from jig.contrib.vision_tool import VisionTool
from jig.adapters.model_provider import ModelRouter


class TestVisionTool:
    def test_init(self):
        router = ModelRouter()
        tool = VisionTool(router=router)
        assert tool.name == "vision"

    def test_nonexistent_file(self):
        tool = VisionTool()
        result = tool.analyze("/nonexistent/image.png")
        assert "[Vision]" in result

    def test_no_router(self):
        tool = VisionTool()
        result = tool.analyze("test.png")
        assert result

    def test_max_size_bytes(self):
        tool = VisionTool(max_size_mb=5)
        assert tool._max_bytes == 5 * 1024 * 1024

    def test_attach_to_app(self):
        tool = VisionTool()
        class MockApp:
            def add_agent_tool(self, name, tool):
                self._tool = (name, tool)
        app = MockApp()
        tool.attach_to(app)
        assert app._tool[0] == "vision"
