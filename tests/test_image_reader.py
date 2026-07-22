"""Tests for contrib ImageReader (optional plugin)."""

from jig.contrib.image_reader import ImageReader


class TestImageReader:
    def test_init(self):
        tool = ImageReader()
        assert tool is not None

    def test_nonexistent_file(self):
        tool = ImageReader()
        result = tool.read("/nonexistent/photo.jpg")
        assert "无法加载" in result
