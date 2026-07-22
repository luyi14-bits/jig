"""配置管理模块 — Pydantic BaseSettings 驱动。

遵循第三荣（配置管理用最佳实践）：使用 Pydantic BaseSettings + .env 文件。
遵循第十四荣（敏感数据加密）：API Key 通过环境变量注入，不硬编码。
"""

from __future__ import annotations

from typing import Dict, Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置，从环境变量 / .env 文件加载。

    配置加载顺序（优先级从高到低）：
    1. 环境变量（export DEEPSEEK_API_KEY=...）
    2. .env 文件（项目根目录）
    3. 默认值（仅安全可公开的配置有默认值）
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── DeepSeek API ──
    deepseek_api_key: str = Field(default="", description="DeepSeek API Key，通过环境变量注入")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="DeepSeek API 基础 URL",
    )

    # ── 模型配置 ──
    pro_model: str = Field(
        default="deepseek-v4-pro",
        description="Pro 模型名称（复杂推理场景）",
    )
    flash_model: str = Field(
        default="deepseek-v4-flash",
        description="Flash 模型名称（快速执行场景）",
    )
    pro_temperature: float = Field(
        default=0.1, ge=0.0, le=2.0,
        description="Pro 模型 temperature，建议 ≤0.3 保证参数稳定",
    )
    flash_temperature: float = Field(
        default=0.3, ge=0.0, le=2.0,
        description="Flash 模型 temperature，略高以增加灵活性",
    )

    # ── 缓存配置 ──
    cache_prefix_order: str = Field(
        default="base_prompt,output_style,language,memory,skill_index",
        description="缓存前缀组装顺序（逗号分隔）",
    )
    cache_diagnostic_enabled: bool = Field(
        default=True,
        description="是否启用缓存诊断日志",
    )

    # ── Session 配置 ──
    session_timeout_seconds: int = Field(
        default=1800,
        description="Session 超时时间（秒），默认 30 分钟",
    )

    # ── SOP 配置 ──
    max_sop_depth: int = Field(
        default=5,
        description="树形 SOP 最大嵌套深度",
    )

    # ── 默认模型映射（skill 类型 → 模型等级） ──
    default_model_mapping: Dict[str, Literal["pro", "flash"]] = Field(
        default={
            "pm": "pro",
            "spec": "pro",
            "security": "pro",
            "mentor": "pro",
            "coding": "flash",
            "tdd": "flash",
            "acceptance": "flash",
            "secretary": "flash",
        },
        description="按 skill 类型分配的默认模型映射",
    )

    @property
    def api_key_configured(self) -> bool:
        """检查 API Key 是否已配置。"""
        return bool(self.deepseek_api_key) and self.deepseek_api_key != ""


settings = Settings()
"""全局单例配置实例。"""
