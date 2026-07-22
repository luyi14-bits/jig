"""VisionTool — 框架级多模态能力。

让 DeepSeek Agent 拥有视觉能力，无需 DeepSeek 本身支持多模态。

原理:
  Agent 收到图片 → VisionTool 拦截 → 调用 GPT-4o/Claude Vision 分析
  → 返回文本描述 → 注入 Agent 上下文 → Agent 继续推理
"""

from __future__ import annotations
import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class VisionTool:
    """视觉工具 — 为任何 Agent 添加"看"的能力。

    用法:
        from jig.tools import VisionTool
        
        tool = VisionTool(router=model_router, provider="openai")
        tool.attach_to(app)  # 自动拦截图片消息
    
    或手动调用:
        description = tool.analyze("screenshot.png")
    """

    def __init__(self, router=None, provider: str = "openai", max_size_mb: int = 10):
        self._router = router
        self._provider = provider
        self._max_bytes = max_size_mb * 1024 * 1024
        self._analysis_count = 0

    @property
    def name(self) -> str:
        return "vision"

    @property
    def description(self) -> str:
        return "分析图片内容，返回文字描述。支持本地图片路径和URL。"

    def analyze(self, image_path: str, prompt: str = "请详细描述这张图片的内容") -> str:
        """分析图片。
        
        Args:
            image_path: 本地路径或 URL
            prompt: 视觉模型的提示词
            
        Returns:
            图片的文本描述
        """
        image_data = self._load_image(image_path)
        if image_data is None:
            return "[Vision] 无法加载图片"

        messages = self._build_vision_messages(prompt, image_data)

        try:
            provider = self._router.get(self._provider) if self._router else None
            if provider is None:
                return "[Vision] 未配置视觉模型 Provider"

            response = provider.chat(messages, max_tokens=1024)
            self._analysis_count += 1
            
            result = f"[图片分析结果]\n{response.content}\n---\n*此分析由 VisionTool 通过 {provider.model_name} 生成*"
            logger.info("VisionTool: 已完成 %d 次分析", self._analysis_count)
            return result
        except Exception as e:
            logger.error("VisionTool 分析失败: %s", e)
            return f"[Vision] 分析失败: {e}"

    def attach_to(self, app) -> None:
        """将 VisionTool 附加到 Jig 应用。
        
        这样 Agent 在收到图片时会自动触发视觉分析。
        """
        app.add_agent_tool("vision", self)
        logger.info("VisionTool 已附加到应用")

    # ---- 内部方法 ----

    def _build_vision_messages(self, prompt: str, image_b64: str) -> List[Dict]:
        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            }
        ]

    def _load_image(self, path: str) -> Optional[str]:
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.stat().st_size > self._max_bytes:
                logger.warning("图片过大: %s", path)
                return None
            try:
                return base64.b64encode(path_obj.read_bytes()).decode("utf-8")
            except Exception as e:
                logger.error("图片加载失败: %s", e)
                return None

        # URL
        try:
            import httpx
            resp = httpx.get(path, timeout=30, follow_redirects=True)
            if resp.status_code != 200:
                return None
            if len(resp.content) > self._max_bytes:
                return None
            return base64.b64encode(resp.content).decode("utf-8")
        except Exception as e:
            logger.error("URL图片加载失败: %s", e)
            return None
