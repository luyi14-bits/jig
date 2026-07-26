"""多模态桥接工具 — 让 DeepSeek Agent 拥有视觉能力。

DeepSeek V4 不支持多模态（无 Vision API）。Jig 通过 ModelRouter
将图片转发给支持视觉的模型（GPT-4o / Claude），返回文本给 DeepSeek。

用法:
    tool = ImageReader(router=model_router, provider="openai")
    description = tool.read("path/to/photo.jpg")
    # → "图片描述：一只猫在窗台上"
"""

from __future__ import annotations
import base64
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ImageReader:
    """图像读取工具 — 桥接到视觉模型。

    将图片转换为 Base64 → 调用视觉模型描述/分析图片 → 返回文本。
    DeepSeek Agent 将此文本作为上下文使用，间接获得视觉能力。
    """

    def __init__(self, router=None, provider: str = "openai", max_size_mb: int = 10):
        self._router = router
        self._provider = provider
        self._max_bytes = max_size_mb * 1024 * 1024

    def read(self, image_path: str, prompt: str = "请详细描述这张图片的内容") -> str:
        """读取并描述图片。

        Args:
            image_path: 图片文件路径或 URL
            prompt: 视觉模型的提示词

        Returns:
            图片描述文本
        """
        image_data = self._load_image(image_path)
        if image_data is None:
            return "[ImageReader] 无法加载图片: " + image_path

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ],
            }
        ]

        try:
            provider = self._router.get(self._provider) if self._router else None
            if provider is None:
                return "[ImageReader] 未配置视觉模型 Provider"

            response = provider.chat(messages, max_tokens=1024)
            return f"[图片分析结果]\n{response.content}"
        except Exception as e:
            logger.error("ImageReader failed: %s", e)
            return f"[ImageReader] 分析失败: {e}"

    def _load_image(self, path: str) -> Optional[str]:
        """加载图片并返回 Base64。"""
        path_obj = Path(path)
        if not path_obj.exists():
            # 可能是 URL
            return self._load_from_url(path)

        if path_obj.stat().st_size > self._max_bytes:
            logger.warning("图片过大: %s (%d bytes)", path, path_obj.stat().st_size)
            return None

        try:
            import imghdr
            data = path_obj.read_bytes()
            return base64.b64encode(data).decode("utf-8")
        except Exception as e:
            logger.error("图片加载失败: %s", e)
            return None

    def _load_from_url(self, url: str) -> Optional[str]:
        """从 URL 加载图片。"""
        try:
            import httpx
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            if resp.status_code != 200:
                return None
            if len(resp.content) > self._max_bytes:
                return None
            return base64.b64encode(resp.content).decode("utf-8")
        except Exception as e:
            logger.error("URL 图片加载失败: %s", e)
            return None

    def __call__(self, image_path: str, prompt: str = "请详细描述这张图片的内容") -> str:
        """快捷调用。"""
        return self.read(image_path, prompt)
