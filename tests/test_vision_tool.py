"""Tests for VisionTool."""

from jig.tools.vision_tool import VisionTool
from jig.adapters.model_provider import ModelRouter


class TestVisionTool:
    def test_init(self):
        router = ModelRouter()
        tool = VisionTool(router=router)
        assert tool.name == "vision"
        assert "图片" in tool.description

    def test_nonexistent_file(self):
        tool = VisionTool()
        result = tool.analyze("/nonexistent/image.png")
        assert "无法加载" in result or "[Vision]" in result

    def test_no_router(self):
        tool = VisionTool()
        result = tool.analyze("test.png")
        assert result

    def test_analysis_count(self):
        tool = VisionTool()
        assert tool._analysis_count == 0
        tool.analyze("/nonexistent/file.jpg")
        assert tool._analysis_count == 0  # failed, not counted

    def test_max_size_bytes(self):
        tool = VisionTool(max_size_mb=5)
        assert tool._max_bytes == 5 * 1024 * 1024

    def test_attach_to_app(self):
        """Test that attach_to doesn't error on mock app."""
        tool = VisionTool()

        class MockApp:
            def add_agent_tool(self, name, tool):
                self._tool = (name, tool)

        app = MockApp()
        tool.attach_to(app)
        assert hasattr(app, "_tool")
        assert app._tool[0] == "vision"
