"""Tree-SOP Agent 配置管理器 — 用户配置持久化。

支持：DS API Key、MCP Server、模型覆盖、显示名、权限覆盖。
配置存储：~/.tree-sop/config.toml
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict


CONFIG_DIR = Path.home() / ".tree-sop"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class MCPEndpoint:
    """MCP Server 端点配置。"""
    name: str = ""
    type: str = "stdio"  # stdio / http / sse
    command: str = ""
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class AgentOverride:
    """Agent 级覆盖配置。"""
    model: Optional[str] = None        # pro / flash / None(默认)
    display_name: Optional[str] = None # 自定义显示名
    allow_tools: List[str] = field(default_factory=list)   # 白名单覆盖
    deny_tools: List[str] = field(default_factory=list)    # 黑名单追加


@dataclass
class AppConfig:
    """应用配置。"""
    deepseek_api_key: str = ""
    mcp_servers: List[MCPEndpoint] = field(default_factory=list)
    agent_overrides: Dict[str, AgentOverride] = field(default_factory=dict)
    risk_mode: bool = False
    risk_mode_acknowledged_at: Optional[str] = None


class ConfigManager:
    """配置管理器 — 读取/写入/合并用户配置。"""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._path = Path(config_path) if config_path else CONFIG_PATH
        self._config = AppConfig()
        self._load()

    def _load(self) -> None:
        """从 JSON 文件加载配置。"""
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._config = AppConfig(
                deepseek_api_key=data.get("deepseek_api_key", ""),
                mcp_servers=[MCPEndpoint(**s) for s in data.get("mcp_servers", [])],
                agent_overrides={
                    k: AgentOverride(**v) for k, v in data.get("agent_overrides", {}).items()
                },
                risk_mode=data.get("risk_mode", False),
                risk_mode_acknowledged_at=data.get("risk_mode_acknowledged_at"),
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("读取配置文件失败: %s", e)

    def save(self) -> None:
        """保存配置到 JSON 文件。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "deepseek_api_key": self._config.deepseek_api_key,
            "mcp_servers": [asdict(s) for s in self._config.mcp_servers],
            "agent_overrides": {
                k: {kk: vv for kk, vv in asdict(o).items() if vv is not None and vv != []}
                for k, o in self._config.agent_overrides.items()
            },
            "risk_mode": self._config.risk_mode,
            "risk_mode_acknowledged_at": self._config.risk_mode_acknowledged_at,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── API Key ──
    @property
    def api_key(self) -> str:
        return self._config.deepseek_api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        self._config.deepseek_api_key = value
        self.save()

    # ── MCP Servers ──
    @property
    def mcp_servers(self) -> List[MCPEndpoint]:
        return self._config.mcp_servers

    def add_mcp_server(self, endpoint: MCPEndpoint) -> None:
        self._config.mcp_servers.append(endpoint)
        self.save()

    def remove_mcp_server(self, name: str) -> None:
        self._config.mcp_servers = [s for s in self._config.mcp_servers if s.name != name]
        self.save()

    # ── Agent Overrides ──
    @property
    def agent_overrides(self) -> Dict[str, AgentOverride]:
        return self._config.agent_overrides

    def set_agent_model(self, agent_name: str, model: str) -> None:
        if agent_name not in self._config.agent_overrides:
            self._config.agent_overrides[agent_name] = AgentOverride()
        self._config.agent_overrides[agent_name].model = model
        self.save()

    def set_agent_display_name(self, agent_name: str, display_name: str) -> None:
        if agent_name not in self._config.agent_overrides:
            self._config.agent_overrides[agent_name] = AgentOverride()
        self._config.agent_overrides[agent_name].display_name = display_name
        self.save()

    def get_agent_display_name(self, agent_name: str, default: str = "") -> str:
        override = self._config.agent_overrides.get(agent_name)
        if override and override.display_name:
            return override.display_name
        return default

    def get_agent_model(self, agent_name: str, default: str = "") -> str:
        override = self._config.agent_overrides.get(agent_name)
        if override and override.model:
            return override.model
        return default

    # ── Risk Mode ──
    def enable_risk_mode(self) -> None:
        from datetime import datetime
        self._config.risk_mode = True
        self._config.risk_mode_acknowledged_at = datetime.now().isoformat()
        self.save()

    def disable_risk_mode(self) -> None:
        self._config.risk_mode = False
        self.save()

    @property
    def risk_mode_enabled(self) -> bool:
        return self._config.risk_mode
