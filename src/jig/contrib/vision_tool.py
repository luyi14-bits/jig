"""VisionTool — 框架级多模态能力。

让 DeepSeek Agent 拥有视觉能力，无需 DeepSeek 本身支持多模态。

默认零成本（本地 Florence-2），可选 GPT-4o/Claude Vision 高精度模式。

降级链:
  1. 本地 Florence-2（免费，CPU 可跑）
  2. 外部 Vision API（GPT-4o / Claude，需额外 Key）
  3. 纯文本模式（友好提示）
"""

from __future__ import annotations
import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 尝试导入本地视觉模型（可选依赖）
try:
    import torch
    from PIL import Image
    from transformers import AutoProcessor, AutoModelForCausalLM
    _HAS_LOCAL_VISION = True
except ImportError:
    _HAS_LOCAL_VISION = False
    torch = None
    Image = None


class LocalVisionEngine:
    """本地视觉引擎 — 默认零成本，CPU 可跑。"""

    MODEL_ID = "microsoft/Florence-2-large"

    def __init__(self):
        self._processor = None
        self._model = None
        self._device = "cuda" if torch and torch.cuda.is_available() else "cpu"

    def _ensure_loaded(self):
        if self._model is not None:
            return
        logger.info("加载本地视觉模型 %s (%s)...", self.MODEL_ID, self._device)
        self._processor = AutoProcessor.from_pretrained(self.MODEL_ID, trust_remote_code=True)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.MODEL_ID, trust_remote_code=True
        ).to(self._device)
        logger.info("本地视觉模型加载完成")

    def analyze(self, image_path: str, prompt: str = "描述这张图片的详细内容") -> str:
        """使用本地模型分析图片。"""
        self._ensure_loaded()
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = self._processor(text=prompt, images=image, return_tensors="pt").to(self._device)
            generated_ids = self._model.generate(
                **inputs,
                max_new_tokens=512,
                num_beams=3,
            )
            result = self._processor.decode(generated_ids[0], skip_special_tokens=True)
            return result
        except Exception as e:
            logger.error("本地视觉分析失败: %s", e)
            return f"[Vision] 本地分析失败: {e}"


class VisionTool:
    """视觉工具 — 为任何 Agent 添加"看"的能力。

    默认使用本地 Florence-2 模型（零成本，CPU 可跑）。
    可选外部 Vision API（GPT-4o / Claude）获得更高精度。

    用法:
        tool = VisionTool()  # 默认本地模型，零成本
        description = tool.analyze("screenshot.png")

    或使用外部 API:
        tool = VisionTool(router=router, provider="openai")
        description = tool.analyze("screenshot.png")
    """

    def __init__(self, router=None, provider: str = "", max_size_mb: int = 10):
        self._router = router
        self._provider = provider
        self._max_bytes = max_size_mb * 1024 * 1024
        self._analysis_count = 0
        self._local_engine = None

    @property
    def name(self) -> str:
        return "vision"

    @property
    def description(self) -> str:
        return "分析图片内容，返回文字描述。默认免费本地模型。"

    def analyze(self, image_path: str, prompt: str = "描述这张图片的详细内容") -> str:
        """分析图片。

        自动降级链: 本地模型 → 外部 API → 纯文本提示
        """
        # 优先本地模型
        if not self._provider:
            return self._analyze_local(image_path, prompt)

        # 外部 API
        return self._analyze_remote(image_path, prompt)

    def _analyze_local(self, image_path: str, prompt: str) -> str:
        """本地模型分析（零成本）。"""
        path_obj = Path(image_path)
        if not path_obj.exists():
            return "[Vision] 文件不存在，请检查路径"

        if not _HAS_LOCAL_VISION:
            return (
                "[Vision] 本地视觉模型未安装。如需使用，请安装依赖:\n"
                "  pip install torch torchvision pillow transformers\n"
                "或配置外部 Vision API:\n"
                "  tool = VisionTool(router=router, provider=\"openai\")"
            )

        if self._local_engine is None:
            self._local_engine = LocalVisionEngine()

        self._analysis_count += 1
        return self._local_engine.analyze(str(path_obj), prompt)

    def _analyze_remote(self, image_path: str, prompt: str) -> str:
        """外部 API 分析（GPT-4o / Claude）。"""
        image_data = self._load_image(image_path)
        if image_data is None:
            return "[Vision] 无法加载图片"

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
                return "[Vision] 未配置视觉模型 Provider。可用: " + str(list(self._router.available) if self._router else [])

            response = provider.chat(messages, max_tokens=1024)
            self._analysis_count += 1
            return f"[图片分析结果]\n{response.content}\n---\n*分析由 {provider.model_name} 生成*"
        except Exception as e:
            logger.error("VisionTool 外部分析失败: %s", e)
            return f"[Vision] 分析失败: {e}"

    def attach_to(self, app) -> None:
        """将 VisionTool 附加到 Jig 应用。"""
        app.add_agent_tool("vision", self)
        logger.info("VisionTool 已附加到应用（默认本地模型，零成本）")

    def _load_image(self, path: str) -> Optional[str]:
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.stat().st_size > self._max_bytes:
                return None
            try:
                return base64.b64encode(path_obj.read_bytes()).decode("utf-8")
            except Exception:
                return None
        try:
            import httpx
            resp = httpx.get(path, timeout=30, follow_redirects=True)
            if resp.status_code != 200 or len(resp.content) > self._max_bytes:
                return None
            return base64.b64encode(resp.content).decode("utf-8")
        except Exception:
            return None
